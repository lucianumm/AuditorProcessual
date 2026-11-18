"""Motor determinístico de prescrição, decadência e prescrição intercorrente (Cível, CDC, Fazenda, Tributário e Improbidade).

Contempla CC arts. 202 (unicidade da interrupção), 205, 206, 207, 208 e 2.028; CDC arts. 26 e 27;
Decreto 20.910/1932 (e Súmula 383/STF); CTN arts. 150 § 4º, 173 I e 174; LEF art. 40 (1 + 5 anos,
STJ Temas 566–571); CPC art. 921 (Lei 14.195/2021) e Lei 8.429/1992 art. 23 (8 anos e 4 anos intercorrente,
Lei 14.230/2021 e STF Tema 1199).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

CC2002_EFFECTIVE_DATE = date(2003, 1, 11)
LEI_14195_DATE = date(2021, 8, 26)
LEI_14230_DATE = date(2021, 10, 26)

PROFILES: dict[str, dict] = {
    "art206_p1_1ano_seguro": {
        "domain": "civil",
        "nature": "prescricao",
        "unit": "years",
        "amount": 1,
        "normative_basis": "CC, art. 206, § 1º, II (segurado vs. segurador; Súmula 229/STJ suspende durante regulação do sinistro)",
    },
    "art206_p3_3anos_reparacao_civil_enriquecimento": {
        "domain": "civil",
        "nature": "prescricao",
        "unit": "years",
        "amount": 3,
        "normative_basis": "CC, art. 206, § 3º, IV e V (enriquecimento sem causa e reparação civil extracontratual)",
    },
    "art206_p5_5anos_divida_liquida_profissionais": {
        "domain": "civil",
        "nature": "prescricao",
        "unit": "years",
        "amount": 5,
        "normative_basis": "CC, art. 206, § 5º, I e II (dívida líquida em instrumento público/particular e honorários)",
    },
    "art205_10anos_geral": {
        "domain": "civil",
        "nature": "prescricao",
        "unit": "years",
        "amount": 10,
        "normative_basis": "CC, art. 205 (prazo geral ordinário e responsabilidade contratual — STJ EREsp 1.281.594)",
    },
    "art2028": {
        "domain": "civil",
        "nature": "prescricao_transicao",
        "unit": "years",
        "amount": 10,
        "normative_basis": "CC, art. 2.028 (regra de transição CC/1916 -> CC/2002 em 11/01/2003)",
    },
    "art26_30dias_vicio_nao_duravel": {
        "domain": "consumidor",
        "nature": "decadencia",
        "unit": "days",
        "amount": 30,
        "normative_basis": "CDC, art. 26, I e § 2º, I (vício aparente ou de fácil constatação em produto/serviço não durável)",
    },
    "art26_90dias_vicio_duravel": {
        "domain": "consumidor",
        "nature": "decadencia",
        "unit": "days",
        "amount": 90,
        "normative_basis": "CDC, art. 26, II, §§ 2º e 3º (vício em produto/serviço durável; vício oculto conta da evidência)",
    },
    "art27_5anos_fato_produto_servico": {
        "domain": "consumidor",
        "nature": "prescricao",
        "unit": "years",
        "amount": 5,
        "normative_basis": "CDC, art. 27 (pretensão à reparação pelos danos causados por fato do produto ou do serviço)",
    },
    "dl20910_art1_5anos": {
        "domain": "fazenda_publica",
        "nature": "prescricao_fazenda",
        "unit": "years",
        "amount": 5,
        "normative_basis": "Decreto 20.910/1932, arts. 1º, 4º e 9º; Súmula 383/STF",
    },
    "ctn_art150_p4_decadencia": {
        "domain": "tributario",
        "nature": "decadencia",
        "unit": "years",
        "amount": 5,
        "normative_basis": "CTN, art. 150, § 4º; Súmula 555/STJ (lançamento por homologação com pagamento antecipado sem dolo/fraude)",
    },
    "ctn_art173_i_decadencia": {
        "domain": "tributario",
        "nature": "decadencia",
        "unit": "years_next_exercise",
        "amount": 5,
        "normative_basis": "CTN, art. 173, I; STJ Tema 163 e Súmula 555/STJ (1º dia do exercício seguinte àquele em que o lançamento poderia ter sido efetuado)",
    },
    "ctn_art174_prescricao": {
        "domain": "tributario",
        "nature": "prescricao",
        "unit": "years",
        "amount": 5,
        "normative_basis": "CTN, art. 174, caput e parágrafo único; Súmula 622/STJ",
    },
    "lef_art40_intercorrente_1mais5": {
        "domain": "tributario",
        "nature": "intercorrente_1mais_n",
        "suspension_years": 1,
        "amount": 5,
        "normative_basis": "Lei 6.830/1980 (LEF), art. 40, §§ 1º a 4º; STJ, Temas 566 a 571 (REsp 1.340.553/RS)",
    },
    "cpc_art921_intercorrente": {
        "domain": "execucao_civil",
        "nature": "intercorrente_1mais_n",
        "suspension_years": 1,
        "amount": 5,
        "normative_basis": "CPC, art. 921, §§ 1º, 4º e 4º-A (redação da Lei 14.195/2021); Súmula 150/STF",
    },
    "l8429_art23_8anos_e_4anos_intercorrente": {
        "domain": "administrativo_improbidade",
        "nature": "improbidade_lei_14230",
        "amount": 8,
        "intercorrente_years": 4,
        "normative_basis": "Lei 8.429/1992, art. 23, caput e §§ 4º, 5º e 8º (Lei 14.230/2021); STF, Tema 1199",
    },
}

PROFILE_ALIASES = {"art2028_transicao": "art2028"}


def _add_civil_years(base: date, years: int) -> date:
    """CC, art. 132, § 3º: os prazos de anos expiram no dia de igual número do de início, ou no imediato se faltar."""
    target_y = base.year + years
    try:
        return date(target_y, base.month, base.day)
    except ValueError:
        # 29/02 em ano comum -> 28/02 ou 01/03; pelo art. 132 § 3º ("no imediato, se faltar exata correspondência"): 01/03,
        # salvo convenção de último dia de fevereiro; em anos pares/múltiplos de 4 mantém 29/02.
        return date(target_y, 3, 1)


def _add_civil_months(base: date, months: int) -> date:
    total_m = base.month + months
    y = base.year + (total_m - 1) // 12
    m = ((total_m - 1) % 12) + 1
    for d in range(base.day, 27, -1):
        try:
            return date(y, m, d)
        except ValueError:
            continue
    return date(y, m, base.day)


def _active_suspension_days(
    suspensions: list[dict],
    window_start: date,
    window_end: date,
    *,
    is_decadencia: bool,
    warnings: list[str],
) -> int:
    """Soma dias corridos de impedimento/suspensão sobrepostos ao curso do prazo, sem dupla contagem."""
    valid_intervals: list[tuple[date, date]] = []
    for item in suspensions:
        s = date.fromisoformat(str(item["start"]))
        e = date.fromisoformat(str(item["end"]))
        if s > e:
            raise ValueError(f"Período de suspensão invertido: {s} > {e}")
        kind = str(item.get("kind", "geral")).lower()
        if is_decadencia and kind not in {"absolutamente_incapaz", "cdc_art26_p2_reclamacao", "determinacao_legal"}:
            warnings.append(
                f"Suspensão '{item.get('reason', kind)}' ignorada em prazo decadencial (CC, art. 207 — salvo contra "
                "absolutamente incapaz, art. 208, ou obstáculo legal expresso como CDC art. 26 § 2º)."
            )
            continue
        valid_intervals.append((s, e))

    if not valid_intervals:
        return 0
    valid_intervals.sort()
    merged: list[tuple[date, date]] = []
    cs, ce = valid_intervals[0]
    for s, e in valid_intervals[1:]:
        if s <= ce + timedelta(days=1):
            ce = max(ce, e)
        else:
            merged.append((cs, ce))
            cs, ce = s, e
    merged.append((cs, ce))

    # Estende dinamicamente o termo final enquanto novas suspensões caírem dentro da janela estendida.
    cur_end = window_end
    applied_days = 0
    processed: set[int] = set()
    changed = True
    while changed:
        changed = False
        for idx, (s, e) in enumerate(merged):
            if idx in processed:
                continue
            ov_start = max(s, window_start)
            ov_end = min(e, cur_end)
            if ov_start <= ov_end:
                span = (ov_end - ov_start).days + 1
                applied_days += span
                cur_end += timedelta(days=span)
                processed.add(idx)
                changed = True
            elif s <= cur_end and e > cur_end:
                span = (e - max(s, window_start)).days + 1
                applied_days += span
                cur_end += timedelta(days=span)
                processed.add(idx)
                changed = True
    return applied_days


def check_limitation(spec: dict) -> dict:
    """Verifica prescrição, decadência ou prescrição intercorrente na data de referência/ajuizamento."""
    if not isinstance(spec, dict):
        raise ValueError("Especificação deve ser um dicionário JSON")
    raw_profile = str(spec["profile"]).strip()
    profile_id = PROFILE_ALIASES.get(raw_profile, raw_profile)
    if profile_id not in PROFILES:
        raise ValueError(f"Perfil desconhecido: {raw_profile!r}. Opções: {sorted(PROFILES)}")

    prof = PROFILES[profile_id]
    start_d = date.fromisoformat(str(spec["start_date"]))
    ref_d = date.fromisoformat(str(spec.get("reference_date") or spec.get("filing_date")))
    if ref_d < start_d:
        raise ValueError("reference_date / filing_date não pode ser anterior a start_date")

    suspensions = list(spec.get("impedimentos_suspensoes") or spec.get("suspensions") or [])
    interruptions = sorted(
        list(spec.get("interrupcoes") or spec.get("interruptions") or []),
        key=lambda item: str(item["date"]),
    )
    warnings: list[str] = []
    nature = prof["nature"]

    # 1. Regra de transição CC art. 2.028
    if nature == "prescricao_transicao":
        old_years = int(spec.get("old_cc1916_years", 20))
        new_years = int(spec.get("new_cc2002_years", 10))
        half_cutoff = _add_civil_years(start_d, old_years // 2)
        if start_d >= CC2002_EFFECTIVE_DATE:
            dies_a_quo = start_d
            applied_years = new_years
            rule_used = f"Fato já sob vigência do CC/2002 ({new_years} anos)"
        elif CC2002_EFFECTIVE_DATE > half_cutoff:
            # Mais da metade transcorrida em 11/01/2003 -> aplica prazo do CC/1916 desde a origem.
            dies_a_quo = start_d
            applied_years = old_years
            rule_used = f"CC, art. 2.028 (1ª parte): mais da metade de {old_years} anos transcorrida em 11/01/2003 -> mantém CC/1916"
        else:
            dies_a_quo = CC2002_EFFECTIVE_DATE
            applied_years = new_years
            rule_used = f"CC, art. 2.028 (2ª parte): metade ou menos transcorrida em 11/01/2003 -> prazo novo ({new_years} anos) contado de 11/01/2003"
        base_end = _add_civil_years(dies_a_quo, applied_years)
        susp_days = _active_suspension_days(suspensions, dies_a_quo, base_end, is_decadencia=False, warnings=warnings)
        final_deadline = base_end + timedelta(days=susp_days)
        return {
            "profile": profile_id,
            "domain": prof["domain"],
            "nature": "prescricao",
            "transition_rule_applied": rule_used,
            "dies_a_quo": dies_a_quo.isoformat(),
            "suspension_days_added": susp_days,
            "deadline_date": final_deadline.isoformat(),
            "reference_date": ref_d.isoformat(),
            "extinguished": ref_d > final_deadline,
            "normative_basis": prof["normative_basis"],
            "warnings": warnings,
            "legal_status": "deterministic_limitation_calculation",
        }

    # 2. Prescrição intercorrente 1 + N (LEF art. 40 Temas 566-571 / CPC art. 921 Lei 14.195/2021)
    if nature == "intercorrente_1mais_n":
        susp_years = int(prof["suspension_years"])
        interc_years = int(spec.get("underlying_years", prof["amount"]))
        susp_end = _add_civil_years(start_d, susp_years)
        interc_start = susp_end
        current_end = _add_civil_years(interc_start, interc_years)

        effective_ints: list[dict] = []
        for item in interruptions:
            int_d = date.fromisoformat(str(item["date"]))
            is_effective = bool(item.get("effective", True))
            if not is_effective:
                warnings.append(
                    f"Ato em {int_d.isoformat()} ('{item.get('reason', 'petição sem constrição')}') não interrompe a "
                    "prescrição intercorrente: apenas a efetiva constrição patrimonial ou a efetiva citação são aptas "
                    "a interromper o curso (STJ, Tema 568 / CPC, art. 921, § 4º-A)."
                )
                continue
            if int_d > current_end:
                warnings.append(f"Constrição/citação em {int_d.isoformat()} ocorreu após a consumação da prescrição intercorrente ({current_end.isoformat()}).")
                continue
            interc_start = int_d
            current_end = _add_civil_years(interc_start, interc_years)
            effective_ints.append({"date": int_d.isoformat(), "new_deadline": current_end.isoformat(), "reason": item.get("reason", "efetiva constrição/citação")})

        extra_susp = _active_suspension_days(suspensions, interc_start, current_end, is_decadencia=False, warnings=warnings)
        final_deadline = current_end + timedelta(days=extra_susp)
        if profile_id == "lef_art40_intercorrente_1mais5":
            warnings.append(
                "STJ, Temas 566 e 567: o prazo de 1 ano de suspensão (LEF, art. 40, §§ 1º e 2º) inicia automaticamente na "
                "data da ciência da Fazenda Pública acerca da não localização do devedor ou de bens penhoráveis, fluindo em "
                "seguida automaticamente o quinquênio da prescrição intercorrente."
            )
        return {
            "profile": profile_id,
            "domain": prof["domain"],
            "nature": "prescricao_intercorrente",
            "science_trigger_date": start_d.isoformat(),
            "one_year_suspension_end": susp_end.isoformat(),
            "intercorrente_dies_a_quo": interc_start.isoformat(),
            "intercorrente_years": interc_years,
            "effective_interruptions": effective_ints,
            "extra_suspension_days": extra_susp,
            "deadline_date": final_deadline.isoformat(),
            "reference_date": ref_d.isoformat(),
            "extinguished": ref_d > final_deadline,
            "normative_basis": prof["normative_basis"],
            "warnings": warnings,
            "legal_status": "deterministic_limitation_calculation",
        }

    # 3. Improbidade Administrativa (Lei 8.429/1992, art. 23, redação da Lei 14.230/2021 — 8 anos + 4 anos intercorrente)
    if nature == "improbidade_lei_14230":
        if start_d < LEI_14230_DATE:
            warnings.append(
                "STF, Tema 1199 (ARE 843.989): o novo regime prescricional da Lei 14.230/2021 (8 anos geral e 4 anos "
                "intercorrente) é irretroativo, aplicando-se os novos marcos a partir de 26/10/2021."
            )
        cur_start = start_d
        cur_end = _add_civil_years(cur_start, int(prof["amount"]))
        milestones_trace: list[dict] = []
        already_extinguished = False
        extinguished_at: date | None = None

        for item in interruptions:
            int_d = date.fromisoformat(str(item["date"]))
            if int_d > cur_end:
                already_extinguished = True
                extinguished_at = cur_end
                warnings.append(
                    f"Marco interruptivo '{item.get('reason', 'marco art. 23 § 4º')}' em {int_d.isoformat()} posterior "
                    f"à consumação da prescrição em {cur_end.isoformat()}."
                )
                break
            prev_end = cur_end
            cur_start = int_d
            # Art. 23, § 5º: interrompida a prescrição, recomeça a correr do dia da interrupção pela metade (4 anos).
            cur_end = _add_civil_years(cur_start, int(prof["intercorrente_years"]))
            milestones_trace.append({
                "milestone_date": int_d.isoformat(),
                "reason": item.get("reason", "Marco art. 23, § 4º, LIA"),
                "previous_deadline": prev_end.isoformat(),
                "restarted_intercorrente_deadline_4y": cur_end.isoformat(),
            })

        final_deadline = extinguished_at if already_extinguished and extinguished_at else cur_end
        is_ext = already_extinguished or (ref_d > final_deadline)
        return {
            "profile": profile_id,
            "domain": prof["domain"],
            "nature": "prescricao_improbidade_e_intercorrente",
            "dies_a_quo": start_d.isoformat(),
            "interruptions_trace": milestones_trace,
            "deadline_date": final_deadline.isoformat(),
            "reference_date": ref_d.isoformat(),
            "extinguished": is_ext,
            "normative_basis": prof["normative_basis"],
            "warnings": warnings,
            "legal_status": "deterministic_limitation_calculation",
        }

    # 4. Decadência e Prescrição Ordinária / Especial (CC, CDC, Fazenda Pública, CTN)
    is_dec = nature == "decadencia"
    unit = prof["unit"]
    amt = int(prof["amount"])

    if unit == "years_next_exercise":
        # CTN, art. 173, I: 1º dia do exercício seguinte -> 5 exercícios completos (01/01/A+1 a 31/12/A+5).
        dies_a_quo = date(start_d.year + 1, 1, 1)
        base_end = date(dies_a_quo.year + amt - 1, 12, 31)
    elif unit == "years":
        dies_a_quo = start_d
        base_end = _add_civil_years(dies_a_quo, amt)
    elif unit == "days":
        dies_a_quo = start_d
        base_end = dies_a_quo + timedelta(days=amt)
    else:
        raise ValueError(f"Unidade desconhecida no perfil: {unit}")

    susp_days = _active_suspension_days(suspensions, dies_a_quo, base_end, is_decadencia=is_dec, warnings=warnings)
    current_deadline = base_end + timedelta(days=susp_days)

    interruption_applied: dict | None = None
    if interruptions:
        if is_dec:
            warnings.append("Prazo decadencial não se sujeita a interrupção (CC, art. 207); interrupções informadas ignoradas.")
        else:
            first_int = interruptions[0]
            int_d = date.fromisoformat(str(first_int["date"]))
            if len(interruptions) > 1:
                warnings.append(
                    f"CC, art. 202, caput (unicidade da interrupção prescricional): apenas a primeira interrupção "
                    f"({int_d.isoformat()}) foi computada; {len(interruptions) - 1} interrupção(ões) subsequente(s) ignorada(s)."
                )
            if int_d > current_deadline:
                warnings.append(
                    f"Ato interruptivo em {int_d.isoformat()} posterior à consumação da prescrição ({current_deadline.isoformat()}); "
                    "pretensão já encoberta não se restaura."
                )
            else:
                if nature == "prescricao_fazenda":
                    # Decreto 20.910/1932, art. 9º e Súmula 383/STF: recomeça pela metade (2 anos e meio = 30 meses),
                    # sem jamais ficar reduzida aquém de 5 anos do termo inicial.
                    half_restart = _add_civil_months(int_d, 30)
                    floor_five_years = current_deadline
                    new_end = max(half_restart, floor_five_years)
                    post_susp = _active_suspension_days(suspensions, int_d, new_end, is_decadencia=False, warnings=warnings)
                    current_deadline = new_end + timedelta(days=post_susp)
                    interruption_applied = {
                        "date": int_d.isoformat(),
                        "reason": first_int.get("reason", "ato interruptivo"),
                        "rule": "Decreto 20.910/1932, art. 9º e Súmula 383/STF (2 anos e meio a partir do ato, respeitado o mínimo de 5 anos)",
                        "new_deadline": current_deadline.isoformat(),
                    }
                else:
                    new_base_end = _add_civil_years(int_d, amt) if unit == "years" else (int_d + timedelta(days=amt))
                    post_susp = _active_suspension_days(suspensions, int_d, new_base_end, is_decadencia=False, warnings=warnings)
                    current_deadline = new_base_end + timedelta(days=post_susp)
                    interruption_applied = {
                        "date": int_d.isoformat(),
                        "reason": first_int.get("reason", "ato interruptivo (CC, art. 202)"),
                        "rule": "CC, art. 202, caput e parágrafo único (reinício integral por única vez)",
                        "new_deadline": current_deadline.isoformat(),
                    }

    return {
        "profile": profile_id,
        "domain": prof["domain"],
        "nature": "decadencia" if is_dec else "prescricao",
        "dies_a_quo": dies_a_quo.isoformat(),
        "initial_uninterrupted_deadline": base_end.isoformat(),
        "suspension_days_added_initial": susp_days,
        "interruption_applied": interruption_applied,
        "deadline_date": current_deadline.isoformat(),
        "reference_date": ref_d.isoformat(),
        "extinguished": ref_d > current_deadline,
        "normative_basis": prof["normative_basis"],
        "warnings": warnings,
        "legal_status": "deterministic_limitation_calculation",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verificador determinístico de prescrição, decadência e prescrição intercorrente")
    parser.add_argument("--input", type=Path, help="Arquivo JSON de especificação para check_limitation")
    parser.add_argument("--list-profiles", action="store_true", help="Lista todos os perfis normativos disponíveis")
    args = parser.parse_args(argv)
    if args.list_profiles:
        print(json.dumps({"profiles": PROFILES, "count": len(PROFILES)}, ensure_ascii=False, indent=2))
        return 0
    try:
        if args.input:
            spec = json.loads(args.input.read_text(encoding="utf-8"))
        elif not sys.stdin.isatty():
            spec = json.loads(sys.stdin.read())
        else:
            parser.error("Informe --input ARQUIVO.json ou --list-profiles")
            return 2
        result = check_limitation(spec)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
