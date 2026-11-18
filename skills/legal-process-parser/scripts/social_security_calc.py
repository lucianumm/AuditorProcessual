"""Motor determinístico previdenciário (RGPS — Lei 8.213/1991 e EC 103/2019).

Elimina concomitância de vínculos no CNIS, converte tempo especial em comum estritamente até 13/11/2019
(EC 103/2019, art. 25, § 2º), avalia direito adquirido e regras de transição/permanentes (arts. 15, 16, 17,
18, 19 e 20 da EC 103/2019) e verifica decadência decenal e prescrição quinquenal (Lei 8.213/1991, art. 103).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path

EC103_DATE = date(2019, 11, 13)
DAYS_PER_YEAR = Decimal("365")

# Decreto 3.048/1999, art. 70 (conversão de tempo especial em comum até 13/11/2019).
SPECIAL_FACTORS: dict[str, dict[int, Decimal]] = {
    "M": {25: Decimal("1.4"), 20: Decimal("1.75"), 15: Decimal("2.33")},
    "F": {25: Decimal("1.2"), 20: Decimal("1.5"), 15: Decimal("2.0")},
}


def _normalize_sex(value: str) -> str:
    cleaned = str(value).strip().upper()
    if cleaned in {"M", "MASCULINO", "HOMEM"}:
        return "M"
    if cleaned in {"F", "FEMININO", "MULHER"}:
        return "F"
    raise ValueError("sex deve ser 'M' ou 'F'")


def _safe_anniversary(birth: date, year: int) -> date:
    try:
        return date(year, birth.month, birth.day)
    except ValueError:
        # Nascidos em 29/02 em ano não bissexto: 28/02 para aniversário civil.
        return date(year, 2, 28)


def _exact_age(birth: date, ref: date) -> tuple[int, int, Decimal]:
    """Retorna (anos_completos, dias_desde_ultimo_aniversario, idade_exata_em_anos_decimal)."""
    if ref < birth:
        raise ValueError("Data de referência anterior à data de nascimento")
    years = ref.year - birth.year
    anniv_this_year = _safe_anniversary(birth, ref.year)
    if ref < anniv_this_year:
        years -= 1
        last_anniv = _safe_anniversary(birth, ref.year - 1)
        next_anniv = anniv_this_year
    else:
        last_anniv = anniv_this_year
        next_anniv = _safe_anniversary(birth, ref.year + 1)
    rem_days = (ref - last_anniv).days
    span_days = (next_anniv - last_anniv).days
    with localcontext() as ctx:
        ctx.prec = 50
        exact_years = Decimal(years) + (Decimal(rem_days) / Decimal(span_days))
    return years, rem_days, exact_years


def _reached_years_and_six_months(birth: date, ref: date, target_years_half: Decimal) -> bool:
    """Verifica idade exata inteira ou com fração de 6 meses (ex.: 58.5 = 58 anos e 6 meses)."""
    whole_years = int(target_years_half)
    frac = target_years_half - Decimal(whole_years)
    base_anniv = _safe_anniversary(birth, birth.year + whole_years)
    if frac == Decimal("0"):
        return ref >= base_anniv
    if frac == Decimal("0.5"):
        m = base_anniv.month + 6
        y = base_anniv.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        # Ajusta último dia do mês se necessário (ex.: 31/08 + 6m -> 28/02 ou 29/02).
        for d in range(base_anniv.day, 27, -1):
            try:
                target_d = date(y, m, d)
                break
            except ValueError:
                continue
        else:
            target_d = date(y, m, base_anniv.day)
        return ref >= target_d
    _, _, exact_y = _exact_age(birth, ref)
    return exact_y >= target_years_half


def _format_ymd_from_days(days_val: Decimal) -> dict:
    whole_days = int(days_val)
    years = whole_days // 365
    rem = whole_days % 365
    months = rem // 30
    days = rem % 30
    return {"years": years, "months": months, "days": days, "total_days": str(days_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}


def merge_intervals(periods: list[dict]) -> list[dict]:
    """Funde vínculos concomitantes (sobrepostos) para impedir dupla contagem de dias no CNIS."""
    if not periods:
        return []
    parsed: list[tuple[date, date, dict]] = []
    for idx, item in enumerate(periods, 1):
        if not isinstance(item, dict) or "start" not in item or "end" not in item:
            raise ValueError(f"Período #{idx} inválido: informe 'start' e 'end' (YYYY-MM-DD)")
        s = date.fromisoformat(str(item["start"]))
        e = date.fromisoformat(str(item["end"]))
        if s > e:
            raise ValueError(f"Período #{idx} com data inicial ({s}) posterior à final ({e})")
        parsed.append((s, e, item))

    parsed.sort(key=lambda t: (t[0], t[1]))
    merged: list[dict] = []
    cur_s, cur_e, _ = parsed[0]
    raw_sum = (cur_e - cur_s).days + 1
    count = 1

    for s, e, _ in parsed[1:]:
        span = (e - s).days + 1
        if s <= cur_e:
            cur_e = max(cur_e, e)
            raw_sum += span
            count += 1
        else:
            net_days = (cur_e - cur_s).days + 1
            merged.append({
                "start": cur_s.isoformat(),
                "end": cur_e.isoformat(),
                "days": net_days,
                "merged_count": count,
                "concomitant_days_eliminated": raw_sum - net_days,
            })
            cur_s, cur_e = s, e
            raw_sum = span
            count = 1

    net_days = (cur_e - cur_s).days + 1
    merged.append({
        "start": cur_s.isoformat(),
        "end": cur_e.isoformat(),
        "days": net_days,
        "merged_count": count,
        "concomitant_days_eliminated": raw_sum - net_days,
    })
    return merged


def _non_overlapping_Factor_slices(periods: list[dict], sex: str, cap_date: date | None = None) -> tuple[list[dict], list[str]]:
    """Particiona a linha do tempo em fatias disjuntas escolhendo o maior fator aplicável em cada dia."""
    warnings: list[str] = []
    raw_slices: list[tuple[date, date, Decimal, bool, bool]] = []

    for idx, item in enumerate(periods, 1):
        s = date.fromisoformat(str(item["start"]))
        e = date.fromisoformat(str(item["end"]))
        if s > e:
            raise ValueError(f"Período #{idx} com datas invertidas ({s} > {e})")
        if cap_date is not None:
            if s > cap_date:
                continue
            e = min(e, cap_date)

        is_special = bool(item.get("is_special", False) or item.get("special_years") is not None)
        risk_years = int(item.get("special_years") or item.get("risk_years") or 25)
        if is_special and risk_years not in SPECIAL_FACTORS[sex]:
            raise ValueError(f"Grau de risco especial inválido ({risk_years}): use 15, 20 ou 25 anos")

        if not is_special:
            raw_slices.append((s, e, Decimal("1.0"), False, False))
        else:
            factor = SPECIAL_FACTORS[sex][risk_years]
            if e <= EC103_DATE:
                raw_slices.append((s, e, factor, True, False))
            elif s > EC103_DATE:
                raw_slices.append((s, e, Decimal("1.0"), True, True))
                warnings.append(
                    f"Período especial {s.isoformat()} a {e.isoformat()} posterior a 13/11/2019 computado com fator 1.0 "
                    "(EC 103/2019, art. 25, § 2º — vedada conversão de tempo especial em comum pós-reforma; ADI 6309 pendente no STF)."
                )
            else:
                raw_slices.append((s, EC103_DATE, factor, True, False))
                post_start = EC103_DATE + timedelta(days=1)
                raw_slices.append((post_start, e, Decimal("1.0"), True, True))
                warnings.append(
                    f"Período especial cindido em 13/11/2019: {s.isoformat()}..2019-11-13 com fator {factor} e "
                    f"2019-11-14..{e.isoformat()} com fator 1.0 (EC 103/2019, art. 25, § 2º)."
                )

    if not raw_slices:
        return [], warnings

    # Pontos elementares de fronteira para resolver concomitâncias preservando o maior fator em cada subintervalo.
    boundaries: set[date] = set()
    for s, e, _, _, _ in raw_slices:
        boundaries.add(s)
        boundaries.add(e + timedelta(days=1))
    sorted_bounds = sorted(boundaries)

    elementary: list[dict] = []
    for b_start, b_next in zip(sorted_bounds, sorted_bounds[1:]):
        b_end = b_next - timedelta(days=1)
        covering = [sl for sl in raw_slices if sl[0] <= b_start and sl[1] >= b_end]
        if not covering:
            continue
        best = max(covering, key=lambda sl: (sl[2], sl[3]))
        if elementary and elementary[-1]["end_date"] + timedelta(days=1) == b_start \
                and elementary[-1]["factor"] == best[2] and elementary[-1]["post_ec103_special"] == best[4]:
            elementary[-1]["end_date"] = b_end
        else:
            elementary.append({
                "start_date": b_start,
                "end_date": b_end,
                "factor": best[2],
                "is_special": best[3],
                "post_ec103_special": best[4],
            })

    segments: list[dict] = []
    with localcontext() as ctx:
        ctx.prec = 50
        for seg in elementary:
            raw_d = Decimal((seg["end_date"] - seg["start_date"]).days + 1)
            conv_d = raw_d * seg["factor"]
            segments.append({
                "start": seg["start_date"].isoformat(),
                "end": seg["end_date"].isoformat(),
                "raw_days": int(raw_d),
                "factor": str(seg["factor"]),
                "converted_days": str(conv_d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "converted_days_exact": conv_d,
                "bonus_days": str((conv_d - raw_d).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "is_special": seg["is_special"],
                "post_ec103_unconverted": seg["post_ec103_special"],
            })
    # Deduplica avisos preservando ordem.
    dedup_warnings = list(dict.fromkeys(warnings))
    return segments, dedup_warnings


def convert_special_time(periods: list[dict], sex: str) -> dict:
    """Converte períodos especiais em tempo comum respeitando a concomitância e o corte de 13/11/2019."""
    norm_sex = _normalize_sex(sex)
    segments, warnings = _non_overlapping_Factor_slices(periods, norm_sex, cap_date=None)
    with localcontext() as ctx:
        ctx.prec = 50
        total_raw = sum((Decimal(s["raw_days"]) for s in segments), Decimal("0"))
        total_conv = sum((s["converted_days_exact"] for s in segments), Decimal("0"))
        total_bonus = total_conv - total_raw
    public_segments = [{k: v for k, v in s.items() if k != "converted_days_exact"} for s in segments]
    return {
        "sex": norm_sex,
        "ec103_cutoff": EC103_DATE.isoformat(),
        "segments": public_segments,
        "total_raw_days": int(total_raw),
        "total_bonus_days": str(total_bonus.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "total_converted_days": str(total_conv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "summary_ymd": _format_ymd_from_days(total_conv),
        "warnings": warnings,
        "legal_status": "deterministic_rgps_time_conversion_subject_to_ppp_ltcat_proof",
    }


def _distinct_competences_count(periods: list[dict], cap_date: date) -> int:
    comps: set[tuple[int, int]] = set()
    for item in periods:
        s = date.fromisoformat(str(item["start"]))
        e = min(date.fromisoformat(str(item["end"])), cap_date)
        if s > e:
            continue
        y, m = s.year, s.month
        while (y, m) <= (e.year, e.month):
            comps.add((y, m))
            m += 1
            if m > 12:
                m = 1
                y += 1
    return len(comps)


def check_rgps_decadencia_prescricao(
    first_payment_date: str | None,
    claim_date: str,
    indeferimento_date: str | None = None,
) -> dict:
    """Calcula decadência decenal (Lei 8.213/1991, art. 103, caput) e prescrição quinquenal (art. 103, p.u.)."""
    claim_d = date.fromisoformat(claim_date)
    presc_cutoff = _safe_anniversary(claim_d, claim_d.year - 5)

    decadencia_dies_a_quo: date | None = None
    if first_payment_date:
        fp = date.fromisoformat(first_payment_date)
        # Art. 103, caput: dia primeiro do mês seguinte ao do recebimento da primeira prestação.
        if fp.month == 12:
            decadencia_dies_a_quo = date(fp.year + 1, 1, 1)
        else:
            decadencia_dies_a_quo = date(fp.year, fp.month + 1, 1)
    elif indeferimento_date:
        decadencia_dies_a_quo = date.fromisoformat(indeferimento_date)

    if decadencia_dies_a_quo is not None:
        decadencia_limit = _safe_anniversary(decadencia_dies_a_quo, decadencia_dies_a_quo.year + 10)
        decayed = claim_d > decadencia_limit
    else:
        decadencia_limit = None
        decayed = False

    return {
        "claim_date": claim_d.isoformat(),
        "decadencia_dies_a_quo": decadencia_dies_a_quo.isoformat() if decadencia_dies_a_quo else None,
        "decadencia_deadline_10y": decadencia_limit.isoformat() if decadencia_limit else None,
        "decadencia_occurred": decayed,
        "prescricao_quinquenal_unpaid_before": presc_cutoff.isoformat(),
        "normative_basis": "Lei 8.213/1991, art. 103, caput e parágrafo único; Súmula 85/STJ; STF Tema 313 e ADI 6096",
    }


def evaluate_rgps_eligibility(spec: dict) -> dict:
    """Avalia direito adquirido até 13/11/2019 e regras de transição e permanentes da EC 103/2019 na DER."""
    if not isinstance(spec, dict):
        raise ValueError("Especificação deve ser dicionário JSON")
    sex = _normalize_sex(spec["sex"])
    birth_d = date.fromisoformat(str(spec["birth_date"]))
    der_d = date.fromisoformat(str(spec["der"]))
    if der_d < birth_d:
        raise ValueError("DER anterior à data de nascimento")
    periods = spec.get("periods") or []
    if not isinstance(periods, list):
        raise ValueError("periods deve ser uma lista de vínculos")

    if spec.get("affiliation_date"):
        aff_d = date.fromisoformat(str(spec["affiliation_date"]))
    elif periods:
        aff_d = min(date.fromisoformat(str(p["start"])) for p in periods)
    else:
        aff_d = der_d
    pre_ec103_affiliated = aff_d <= EC103_DATE

    carencia = spec.get("carencia_months")
    if carencia is None:
        carencia = _distinct_competences_count(periods, der_d)
    carencia = int(carencia)
    carencia_ok = carencia >= 180

    segs_ec103, _ = _non_overlapping_Factor_slices(periods, sex, cap_date=min(der_d, EC103_DATE))
    segs_der, warnings = _non_overlapping_Factor_slices(periods, sex, cap_date=der_d)

    with localcontext() as ctx:
        ctx.prec = 50
        days_at_ec103 = sum((s["converted_days_exact"] for s in segs_ec103), Decimal("0"))
        days_at_der = sum((s["converted_days_exact"] for s in segs_der), Decimal("0"))
        years_at_ec103 = days_at_ec103 / DAYS_PER_YEAR
        years_at_der = days_at_der / DAYS_PER_YEAR

        age_years_int, _, age_exact_der = _exact_age(birth_d, der_d)
        points_at_der = age_exact_der + years_at_der

        target_years = Decimal("35") if sex == "M" else Decimal("30")
        target_days = target_years * DAYS_PER_YEAR
        missing_at_ec103 = max(Decimal("0"), target_days - days_at_ec103)

        # 1. Direito adquirido até 13/11/2019 (EC 103/2019, art. 3º)
        carencia_ec103 = spec.get("carencia_at_ec103")
        if carencia_ec103 is None:
            carencia_ec103 = _distinct_competences_count(periods, min(der_d, EC103_DATE))
        pre_tc_ok = pre_ec103_affiliated and days_at_ec103 >= target_days and int(carencia_ec103) >= 180
        pre_age_ok = False
        if birth_d <= min(der_d, EC103_DATE):
            pre_age_target = Decimal("65") if sex == "M" else Decimal("60")
            pre_age_ok = (
                pre_ec103_affiliated
                and _reached_years_and_six_months(birth_d, min(der_d, EC103_DATE), pre_age_target)
                and int(carencia_ec103) >= 180
            )

        # 2. Art. 15 — Pontos
        req_points = (
            min(Decimal("105"), Decimal("96") + Decimal(max(0, der_d.year - 2019)))
            if sex == "M"
            else min(Decimal("100"), Decimal("86") + Decimal(max(0, der_d.year - 2019)))
        )
        art15_ok = pre_ec103_affiliated and carencia_ok and days_at_der >= target_days and points_at_der >= req_points

        # 3. Art. 16 — Idade Mínima Progressiva
        req_prog_age = (
            min(Decimal("65.0"), Decimal("61.0") + Decimal("0.5") * Decimal(max(0, der_d.year - 2019)))
            if sex == "M"
            else min(Decimal("62.0"), Decimal("56.0") + Decimal("0.5") * Decimal(max(0, der_d.year - 2019)))
        )
        art16_ok = (
            pre_ec103_affiliated
            and carencia_ok
            and days_at_der >= target_days
            and _reached_years_and_six_months(birth_d, der_d, req_prog_age)
        )

        # 4. Art. 17 — Pedágio de 50% (>33a H / >28a M em 13/11/2019)
        gate_50_days = (Decimal("33") if sex == "M" else Decimal("28")) * DAYS_PER_YEAR
        eligible_gate_50 = pre_ec103_affiliated and days_at_ec103 > gate_50_days
        req_days_50 = target_days + (missing_at_ec103 * Decimal("0.5"))
        art17_ok = eligible_gate_50 and carencia_ok and days_at_der >= req_days_50

        # 5. Art. 20 — Pedágio de 100% + Idade Mínima (60a H / 57a M)
        req_age_20 = Decimal("60") if sex == "M" else Decimal("57")
        req_days_100 = target_days + missing_at_ec103
        art20_ok = (
            pre_ec103_affiliated
            and carencia_ok
            and _reached_years_and_six_months(birth_d, der_d, req_age_20)
            and days_at_der >= req_days_100
        )

        # 6. Arts. 18 e 19 — Aposentadoria por Idade / Programada
        if sex == "F":
            req_age_perm = (
                min(Decimal("62.0"), Decimal("60.0") + Decimal("0.5") * Decimal(max(0, der_d.year - 2019)))
                if pre_ec103_affiliated
                else Decimal("62.0")
            )
            req_tc_perm_days = Decimal("15") * DAYS_PER_YEAR
        else:
            req_age_perm = Decimal("65.0")
            req_tc_perm_days = (Decimal("15") if pre_ec103_affiliated else Decimal("20")) * DAYS_PER_YEAR
        art18_19_ok = (
            carencia_ok
            and _reached_years_and_six_months(birth_d, der_d, req_age_perm)
            and days_at_der >= req_tc_perm_days
        )

    rules = {
        "direito_adquirido_pre_ec103": {
            "eligible": pre_tc_ok or pre_age_ok,
            "by_contribution_time": pre_tc_ok,
            "by_pre_reform_age": pre_age_ok,
            "days_on_2019_11_13": str(days_at_ec103.quantize(Decimal("0.01"))),
            "required_days_tc": str(target_days),
            "normative_basis": "EC 103/2019, art. 3º; Lei 8.213/1991, arts. 48 e 52",
        },
        "ec103_art15_points": {
            "eligible": art15_ok,
            "points_at_der": str(points_at_der.quantize(Decimal("0.0001"))),
            "required_points": str(req_points),
            "required_days": str(target_days),
            "normative_basis": "EC 103/2019, art. 15",
        },
        "ec103_art16_progressive_age": {
            "eligible": art16_ok,
            "age_years_at_der": str(age_exact_der.quantize(Decimal("0.0001"))),
            "required_age_years": str(req_prog_age),
            "required_days": str(target_days),
            "normative_basis": "EC 103/2019, art. 16",
        },
        "ec103_art17_toll_50": {
            "eligible": art17_ok,
            "passed_2019_entry_gate": eligible_gate_50,
            "entry_gate_min_days_exclusive": str(gate_50_days),
            "required_days_with_toll": str(req_days_50.quantize(Decimal("0.01"))),
            "normative_basis": "EC 103/2019, art. 17",
        },
        "ec103_art20_toll_100": {
            "eligible": art20_ok,
            "required_age_years": str(req_age_20),
            "required_days_with_toll": str(req_days_100.quantize(Decimal("0.01"))),
            "normative_basis": "EC 103/2019, art. 20",
        },
        "ec103_art18_19_age": {
            "eligible": art18_19_ok,
            "required_age_years": str(req_age_perm),
            "required_days": str(req_tc_perm_days),
            "normative_basis": "EC 103/2019, art. 18 (transição) / art. 19 (regra permanente)",
        },
    }

    dec_presc = check_rgps_decadencia_prescricao(
        spec.get("first_benefit_payment_date"),
        str(spec.get("revision_claim_date") or der_d.isoformat()),
        spec.get("administrative_denial_date"),
    )

    return {
        "sex": sex,
        "birth_date": birth_d.isoformat(),
        "der": der_d.isoformat(),
        "affiliation_date": aff_d.isoformat(),
        "affiliated_up_to_ec103": pre_ec103_affiliated,
        "age_at_der_completed_years": age_years_int,
        "carencia_months": carencia,
        "carencia_180_satisfied": carencia_ok,
        "contribution_at_ec103": _format_ymd_from_days(days_at_ec103),
        "contribution_at_der": _format_ymd_from_days(days_at_der),
        "merged_employment_intervals": merge_intervals(periods),
        "rules": rules,
        "eligible_rules": [k for k, v in rules.items() if v["eligible"]],
        "decadencia_and_prescription": dec_presc,
        "warnings": warnings,
        "legal_status": "deterministic_rgps_eligibility_verify_cnis_carencia_and_ppp",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Motor determinístico previdenciário (RGPS — EC 103/2019 e Lei 8.213/1991)")
    parser.add_argument("--input", type=Path, help="Arquivo JSON de especificação para evaluate_rgps_eligibility")
    args = parser.parse_args(argv)
    try:
        if args.input:
            spec = json.loads(args.input.read_text(encoding="utf-8"))
        elif not sys.stdin.isatty():
            spec = json.loads(sys.stdin.read())
        else:
            parser.error("Informe --input ARQUIVO.json")
            return 2
        result = evaluate_rgps_eligibility(spec)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
