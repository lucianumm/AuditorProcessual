"""Motor determinístico de dosimetria penal (CP art. 68), prescrição (CP arts. 109–117) e progressão de regime (LEP art. 112).

Convenção penal explícita para operações de dosimetria: 1 ano = 12 meses, 1 mês = 30 dias (360 dias-pena/ano),
desprezando-se as frações de dia no resultado em benefício do réu (CP, art. 11).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

LEI_12234_DATE = date(2010, 5, 6)
LEI_11464_DATE = date(2007, 3, 29)
PACOTE_ANTICRIME_DATE = date(2020, 1, 23)
LEI_14843_DATE = date(2024, 4, 11)
LEI_14994_FEMINICIDIO_DATE = date(2024, 10, 10)


def penalty_to_days(value: dict | list | tuple | int) -> int:
    """Converte pena {years, months, days} (ou inteiro em dias-pena) para total em base 360 (1a=12m, 1m=30d)."""
    if isinstance(value, bool):
        raise ValueError("Pena inválida (booleano)")
    if isinstance(value, int):
        if value < 0:
            raise ValueError("Pena em dias não pode ser negativa")
        return value
    if isinstance(value, (list, tuple)):
        if len(value) != 3:
            raise ValueError("Tupla/lista de pena deve ter (years, months, days)")
        y, m, d = (int(x) for x in value)
    elif isinstance(value, dict):
        if "total_days_360" in value and not any(k in value for k in ("years", "months", "days")):
            return penalty_to_days(int(value["total_days_360"]))
        y = int(value.get("years", 0))
        m = int(value.get("months", 0))
        d = int(value.get("days", 0))
    else:
        raise ValueError(f"Formato de pena inválido: {type(value).__name__}")
    if y < 0 or m < 0 or d < 0:
        raise ValueError("Componentes de pena (years, months, days) não podem ser negativos")
    return y * 360 + m * 30 + d


def days_to_penalty(total_days: int) -> dict:
    """Converte dias-pena (base 360) em dicionário estruturado {years, months, days}."""
    if total_days < 0:
        total_days = 0
    years = total_days // 360
    rem = total_days % 360
    months = rem // 30
    days = rem % 30
    parts = []
    if years:
        parts.append(f"{years} ano" + ("s" if years != 1 else ""))
    if months:
        parts.append(f"{months} " + ("meses" if months != 1 else "mês"))
    if days or not parts:
        parts.append(f"{days} dia" + ("s" if days != 1 else ""))
    return {
        "years": years,
        "months": months,
        "days": days,
        "total_days_360": total_days,
        "formatted": ", ".join(parts),
    }


def _parse_fraction(raw: str | int | Fraction) -> Fraction:
    if isinstance(raw, Fraction):
        frac = raw
    elif isinstance(raw, int) and not isinstance(raw, bool):
        frac = Fraction(raw, 1)
    elif isinstance(raw, str):
        cleaned = raw.strip()
        if "/" in cleaned:
            num, den = cleaned.split("/", 1)
            frac = Fraction(int(num.strip()), int(den.strip()))
        else:
            frac = Fraction(Decimal(cleaned))
    else:
        raise ValueError(f"Fração inválida na dosimetria: {raw!r}")
    if frac < 0:
        raise ValueError("Fração de dosimetria não pode ser negativa")
    return frac


def _phase2_delta(factors: object, base_days: int, default_fraction: Fraction) -> tuple[int, list[dict]]:
    """Soma variações da 2ª fase sobre a pena-base."""
    if not factors:
        return 0, []
    if isinstance(factors, int) and not isinstance(factors, bool):
        if factors < 0:
            raise ValueError("Quantidade de agravantes/atenuantes não pode ser negativa")
        items = [{"label": f"fator_{i + 1}", "fraction": str(default_fraction)} for i in range(factors)]
    elif isinstance(factors, list):
        items = factors
    else:
        raise ValueError("aggravating/mitigating deve ser inteiro ou lista")

    total_delta = 0
    details: list[dict] = []
    for idx, item in enumerate(items, 1):
        if isinstance(item, str):
            frac = _parse_fraction(item)
            delta = int(Fraction(base_days) * frac)
            label = f"fator_{idx}"
            details.append({"label": label, "fraction": str(frac), "delta_days": delta})
        elif isinstance(item, dict):
            label = str(item.get("label", f"fator_{idx}"))
            if "delta" in item:
                delta = penalty_to_days(item["delta"])
                details.append({"label": label, "delta_days": delta})
            else:
                frac = _parse_fraction(item.get("fraction", str(default_fraction)))
                delta = int(Fraction(base_days) * frac)
                details.append({"label": label, "fraction": str(frac), "delta_days": delta})
        else:
            raise ValueError("Elemento inválido em aggravating/mitigating")
        total_delta += delta
    return total_delta, details


def _default_concurso_fraction(kind: str, count: int) -> Fraction:
    """Patamares objetivos consolidados pelo STJ conforme o número de infrações."""
    if count < 2:
        raise ValueError("Concurso formal ou crime continuado exige ao menos 2 infrações")
    if kind == "formal_proprio":
        mapping = {2: Fraction(1, 6), 3: Fraction(1, 5), 4: Fraction(1, 4), 5: Fraction(1, 3)}
        return mapping.get(count, Fraction(1, 2))
    mapping_cont = {
        2: Fraction(1, 6),
        3: Fraction(1, 5),
        4: Fraction(1, 4),
        5: Fraction(1, 3),
        6: Fraction(1, 2),
    }
    return mapping_cont.get(count, Fraction(2, 3))


def calculate_dosimetry(spec: dict) -> dict:
    """Executa dosimetria trifásica (CP art. 68), concurso de crimes, detração, regime inicial e substituição (art. 44)."""
    if not isinstance(spec, dict):
        raise ValueError("Especificação da dosimetria deve ser um dicionário JSON")
    min_days = penalty_to_days(spec["min_penalty"])
    max_days = penalty_to_days(spec["max_penalty"])
    if min_days <= 0 or min_days > max_days:
        raise ValueError("Limites abstratos min_penalty e max_penalty inválidos")

    warnings: list[str] = []

    # 1ª Fase — Circunstâncias judiciais (CP, art. 59)
    unfav_count = int(spec.get("unfavorable_circumstances_count", 0))
    if unfav_count < 0 or unfav_count > 8:
        raise ValueError("unfavorable_circumstances_count deve estar entre 0 e 8")

    phase1_clamped = False
    if "pena_base" in spec and spec["pena_base"] is not None:
        raw_base = penalty_to_days(spec["pena_base"])
        base_days = max(min_days, min(max_days, raw_base))
        if base_days != raw_base:
            phase1_clamped = True
            warnings.append("Pena-base ajustada aos limites abstratos [mínimo, máximo] do tipo penal.")
        phase1_criterion = "explicit_pena_base"
    else:
        step_mode = spec.get("phase1_step_mode", "one_eighth_interval")
        if step_mode == "one_eighth_interval":
            raw_base = min_days + int(Fraction(max_days - min_days, 8) * unfav_count)
        elif step_mode == "one_sixth_min":
            raw_base = min_days + int(Fraction(min_days, 6) * unfav_count)
        else:
            raise ValueError("phase1_step_mode deve ser 'one_eighth_interval' ou 'one_sixth_min'")
        base_days = max(min_days, min(max_days, raw_base))
        phase1_criterion = step_mode

    # 2ª Fase — Agravantes e atenuantes (CP, arts. 61–67 e Súmula 231/STJ)
    default_p2_frac = _parse_fraction(spec.get("phase2_default_fraction", "1/6"))
    if spec.get("compensate_equal"):
        agg_days, agg_details = 0, [{"label": "compensação integral (STJ Tema 585)", "delta_days": 0}]
        mit_days, mit_details = 0, []
    else:
        agg_days, agg_details = _phase2_delta(spec.get("aggravating"), base_days, default_p2_frac)
        mit_days, mit_details = _phase2_delta(spec.get("mitigating"), base_days, default_p2_frac)

    raw_intermediaria = base_days + agg_days - mit_days
    sumula_231_clipped = raw_intermediaria < min_days
    clipped_above_max = raw_intermediaria > max_days
    intermediaria_days = max(min_days, min(max_days, raw_intermediaria))
    if sumula_231_clipped:
        warnings.append(
            "Súmula 231/STJ e STF Tema 158 aplicados: a incidência de circunstância atenuante não pode conduzir "
            "à redução da pena abaixo do mínimo legal na segunda fase."
        )
    if clipped_above_max:
        warnings.append("Pena intermediária limitada ao máximo abstrato do tipo penal na segunda fase.")

    # 3ª Fase — Causas de aumento (majorantes) e de diminuição (minorantes) em cascata
    cur_days = intermediaria_days
    phase3_steps: list[dict] = []
    for idx, maj in enumerate(spec.get("majorantes") or [], 1):
        frac = _parse_fraction(maj["fraction"] if isinstance(maj, dict) else maj)
        label = maj.get("label", f"majorante_{idx}") if isinstance(maj, dict) else f"majorante_{idx}"
        if frac == 0:
            raise ValueError("Majorante deve possuir fração positiva")
        before = cur_days
        cur_days = int(Fraction(cur_days) * (1 + frac))
        phase3_steps.append({"kind": "majorante", "label": label, "fraction": str(frac), "before_days": before, "after_days": cur_days})

    for idx, mino in enumerate(spec.get("minorantes") or [], 1):
        frac = _parse_fraction(mino["fraction"] if isinstance(mino, dict) else mino)
        label = mino.get("label", f"minorante_{idx}") if isinstance(mino, dict) else f"minorante_{idx}"
        if frac <= 0 or frac >= 1:
            raise ValueError("Minorante deve estar estritamente entre 0 e 1 (ex.: '1/6', '2/3')")
        before = cur_days
        cur_days = int(Fraction(cur_days) * (1 - frac))
        phase3_steps.append({"kind": "minorante", "label": label, "fraction": str(frac), "before_days": before, "after_days": cur_days})

    phase3_days = cur_days

    # Concurso de crimes (CP, arts. 69, 70 e 71)
    concurso_mode = str(spec.get("concurso", "none")).lower().strip()
    extra_penalties = [penalty_to_days(p) for p in (spec.get("additional_penalties") or [])]
    concurso_detail: dict = {"mode": concurso_mode}

    if concurso_mode == "none":
        definitive_days = phase3_days
    elif concurso_mode == "material":
        definitive_days = phase3_days + sum(extra_penalties)
        concurso_detail["normative_basis"] = "CP, art. 69 (cúmulo material)"
    elif concurso_mode in {"formal_proprio", "crime_continuado"}:
        all_offenses = [phase3_days] + extra_penalties
        offenses_count = int(spec.get("offenses_count", max(2, len(all_offenses))))
        c_frac = (
            _parse_fraction(spec["concurso_fraction"])
            if spec.get("concurso_fraction") is not None
            else _default_concurso_fraction(concurso_mode, offenses_count)
        )
        base_severe = max(all_offenses)
        exacerbated = int(Fraction(base_severe) * (1 + c_frac))
        material_sum = sum(all_offenses) if len(all_offenses) >= 2 else base_severe * offenses_count
        beneficial_cap_applied = exacerbated > material_sum
        definitive_days = min(exacerbated, material_sum)
        concurso_detail.update({
            "offenses_count": offenses_count,
            "fraction_applied": str(c_frac),
            "exacerbated_days": exacerbated,
            "material_sum_days": material_sum,
            "cumulo_material_benefico_applied": beneficial_cap_applied,
            "normative_basis": "CP, art. 70, caput e parágrafo único" if concurso_mode == "formal_proprio" else "CP, art. 71",
        })
    else:
        raise ValueError("concurso deve ser 'none', 'material', 'formal_proprio' ou 'crime_continuado'")

    # Detração penal (CPP, art. 387, § 2º)
    detracao_days = penalty_to_days(spec.get("detracao", spec.get("detracao_days", 0)))
    remaining_days = max(0, definitive_days - detracao_days)

    # Regime inicial de cumprimento (CP, art. 33, §§ 2º e 3º)
    especie = str(spec.get("especie", "reclusao")).lower().strip()
    if especie not in {"reclusao", "detencao"}:
        raise ValueError("especie deve ser 'reclusao' ou 'detencao'")
    reincidente = bool(spec.get("reincidente", False))
    unfav_art59 = bool(spec.get("unfavorable_art59", base_days > min_days or unfav_count > 0))

    if especie == "detencao":
        if remaining_days > 1440 or reincidente or unfav_art59:
            initial_regime = "semiaberto"
        else:
            initial_regime = "aberto"
    else:
        if remaining_days > 2880:  # > 8 anos
            initial_regime = "fechado"
        elif remaining_days > 1440:  # > 4 a 8 anos
            initial_regime = "fechado" if (reincidente or unfav_art59) else "semiaberto"
        else:  # <= 4 anos
            if not reincidente and not unfav_art59:
                initial_regime = "aberto"
                warnings.append(
                    "Pena-base no mínimo legal e réu primário com pena <= 4 anos: vedada imposição de regime mais gravoso "
                    "com base apenas na gravidade abstrata do delito (Súmulas 718 e 719/STF e Súmula 440/STJ)."
                )
            elif reincidente and not unfav_art59:
                initial_regime = "semiaberto"
                warnings.append("Aplicada Súmula 269/STJ: admissível o regime semiaberto ao reincidente condenado a pena <= 4 anos com circunstâncias judiciais favoráveis.")
            elif not reincidente and unfav_art59:
                initial_regime = "semiaberto"
            else:
                initial_regime = "fechado"

    # Substituição por penas restritivas de direitos (CP, art. 44)
    culposo = bool(spec.get("culposo", False))
    violence = bool(spec.get("violence_or_grave_threat", False))
    dv_woman = bool(spec.get("domestic_violence_against_woman", False))
    reincidente_doloso = bool(spec.get("reincidente_doloso", reincidente and not culposo))

    prd_reasons: list[str] = []
    if dv_woman:
        prd_reasons.append("Vedada pela Súmula 588/STJ (violência doméstica ou familiar contra a mulher)")
    if not culposo and definitive_days > 1440:
        prd_reasons.append("Pena definitiva superior a 4 anos em crime doloso (CP, art. 44, I)")
    if not culposo and violence:
        prd_reasons.append("Crime doloso cometido com violência ou grave ameaça à pessoa (CP, art. 44, I)")
    if reincidente_doloso and not spec.get("art44_p3_socially_recommended", False):
        prd_reasons.append("Reincidência em crime doloso sem exceção do art. 44, § 3º, do CP (CP, art. 44, II)")
    if unfav_art59 and spec.get("art44_subjective_insufficient", False):
        prd_reasons.append("Circunstâncias subjetivas indicam insuficiência da substituição (CP, art. 44, III)")
    prd_eligible = len(prd_reasons) == 0

    return {
        "calendar_convention": "1 ano = 12 meses; 1 mês = 30 dias (360 dias-pena/ano); frações de dia desprezadas (CP, art. 11)",
        "abstract_bounds": {
            "min": days_to_penalty(min_days),
            "max": days_to_penalty(max_days),
        },
        "phase1_pena_base": {
            "penalty": days_to_penalty(base_days),
            "unfavorable_circumstances_count": unfav_count,
            "criterion": phase1_criterion,
            "clamped": phase1_clamped,
        },
        "phase2_pena_intermediaria": {
            "penalty": days_to_penalty(intermediaria_days),
            "raw_days_before_clamp": raw_intermediaria,
            "aggravating": agg_details,
            "mitigating": mit_details,
            "sumula_231_clipped": sumula_231_clipped,
            "clipped_above_max": clipped_above_max,
        },
        "phase3_pena_provisoria": {
            "penalty": days_to_penalty(phase3_days),
            "steps": phase3_steps,
        },
        "concurso": concurso_detail,
        "pena_definitiva": days_to_penalty(definitive_days),
        "detracao": days_to_penalty(detracao_days),
        "pena_restante_apos_detracao": days_to_penalty(remaining_days),
        "initial_regime": initial_regime,
        "especie": especie,
        "art44_prd_substitution": {
            "eligible": prd_eligible,
            "blocking_reasons": prd_reasons,
            "normative_basis": "CP, art. 44; Súmula 588/STJ",
        },
        "warnings": warnings,
        "legal_status": "deterministic_dosimetry_subject_to_judicial_individualization",
    }


def _add_years_months_penal_cp10(start: date, years_frac: Fraction) -> date:
    """Prazo penal (CP, art. 10): inclui o dia do começo; o último dia do prazo é véspera do aniversário."""
    total_months_frac = years_frac * 12
    whole_months = int(total_months_frac)
    rem_days = int((total_months_frac - whole_months) * 30)

    target_m = start.month + whole_months
    target_y = start.year + (target_m - 1) // 12
    target_m = ((target_m - 1) % 12) + 1
    for d in range(start.day, 27, -1):
        try:
            anniv = date(target_y, target_m, d)
            break
        except ValueError:
            continue
    else:
        anniv = date(target_y, target_m, start.day)
    # No art. 10 do CP, inclui-se o dia do começo, consumando-se a prescrição no dia de igual número (último dia válido = anniv - 1d).
    return anniv + timedelta(days=rem_days - 1)


def _art109_years(penalty_days: int, fact_date: date | None) -> tuple[int, str]:
    if penalty_days < 360:
        if fact_date is not None and fact_date < LEI_12234_DATE:
            return 2, "CP, art. 109, VI (redação anterior à Lei 12.234/2010 — fatos anteriores a 06/05/2010)"
        return 3, "CP, art. 109, VI (redação dada pela Lei 12.234/2010)"
    if penalty_days <= 720:
        return 4, "CP, art. 109, V"
    if penalty_days <= 1440:
        return 8, "CP, art. 109, IV"
    if penalty_days <= 2880:
        return 12, "CP, art. 109, III"
    if penalty_days <= 4320:
        return 16, "CP, art. 109, II"
    return 20, "CP, art. 109, I"


def calculate_penal_prescription(spec: dict) -> dict:
    """Calcula prescrição penal (CP arts. 109–117), redução etária (art. 115) e marcos interruptivos."""
    if not isinstance(spec, dict):
        raise ValueError("Especificação da prescrição penal deve ser um dicionário JSON")
    pen_days = penalty_to_days(spec["penalty"])
    milestones_in = dict(spec.get("milestones") or {})
    for key in ("fato", "recebimento_denuncia", "pronuncia", "confirmacao_pronuncia",
                "publicacao_sentenca", "acordao_confirmatorio", "transito_em_julgado", "reference_date"):
        if key in spec and key not in milestones_in and spec[key] is not None:
            milestones_in[key] = spec[key]
    if "fact_date" in spec and "fato" not in milestones_in and spec["fact_date"] is not None:
        milestones_in["fato"] = spec["fact_date"]

    fact_d = date.fromisoformat(str(milestones_in["fato"])) if milestones_in.get("fato") else None
    base_years, art109_ref = _art109_years(pen_days, fact_d)
    presc_years = Fraction(base_years, 1)

    mode = str(spec.get("mode", "punitiva")).lower().strip()
    if mode == "executoria" and spec.get("reincidente"):
        presc_years *= Fraction(4, 3)

    under_21 = bool(spec.get("under_21_at_fact", False))
    over_70 = bool(spec.get("over_70_at_sentence", False))
    if spec.get("birth_date"):
        b_d = date.fromisoformat(str(spec["birth_date"]))
        if fact_d is not None:
            anniv_21 = date(b_d.year + 21, b_d.month, 28 if (b_d.month == 2 and b_d.day == 29 and (b_d.year + 21) % 4 != 0) else b_d.day)
            if fact_d < anniv_21:
                under_21 = True
        sent_raw = milestones_in.get("publicacao_sentenca") or spec.get("sentence_date")
        if sent_raw:
            s_d = date.fromisoformat(str(sent_raw))
            anniv_70 = date(b_d.year + 70, b_d.month, 28 if (b_d.month == 2 and b_d.day == 29 and (b_d.year + 70) % 4 != 0) else b_d.day)
            if s_d >= anniv_70:
                over_70 = True

    art115_applied = under_21 or over_70
    if art115_applied:
        presc_years *= Fraction(1, 2)

    ordered_keys = [
        "fato",
        "recebimento_denuncia",
        "pronuncia",
        "confirmacao_pronuncia",
        "publicacao_sentenca",
        "acordao_confirmatorio",
        "transito_em_julgado",
        "reference_date",
    ]
    present = [(k, date.fromisoformat(str(milestones_in[k]))) for k in ordered_keys if milestones_in.get(k)]
    intervals: list[dict] = []
    any_prescribed = False
    warnings: list[str] = []

    for (k1, d1), (k2, d2) in zip(present, present[1:]):
        if d2 < d1:
            raise ValueError(f"Marco '{k2}' ({d2}) anterior a '{k1}' ({d1})")
        last_valid_day = _add_years_months_penal_cp10(d1, presc_years)
        prescribed = d2 > last_valid_day
        blocked_retroativa_lei_12234 = (
            k1 == "fato"
            and k2 == "recebimento_denuncia"
            and spec.get("penalty_kind", "concreta") == "concreta"
            and fact_d is not None
            and fact_d >= LEI_12234_DATE
        )
        effective_prescribed = prescribed and not blocked_retroativa_lei_12234
        if prescribed and blocked_retroativa_lei_12234:
            warnings.append(
                "Intervalo fato -> recebimento_denuncia superou o prazo da pena em concreto, mas para fatos a partir "
                "de 06/05/2010 a prescrição retroativa não alcança período anterior ao recebimento da denúncia "
                "(CP, art. 110, § 1º, Lei 12.234/2010); conferir apenas prescrição pela pena máxima em abstrato."
            )
        if effective_prescribed:
            any_prescribed = True
        intervals.append({
            "from_milestone": k1,
            "from_date": d1.isoformat(),
            "to_milestone": k2,
            "to_date": d2.isoformat(),
            "last_unprescribed_day": last_valid_day.isoformat(),
            "prescribed_on": (last_valid_day + timedelta(days=1)).isoformat(),
            "raw_exceeded": prescribed,
            "blocked_by_art110_p1_lei_12234": blocked_retroativa_lei_12234,
            "prescribed": effective_prescribed,
        })

    if any(k == "acordao_confirmatorio" for k, _ in present):
        warnings.append("STF, Tema 1192 (HC 176.473): o acórdão meramente confirmatório da condenação também interrompe a prescrição (CP, art. 117, IV).")

    return {
        "penalty": days_to_penalty(pen_days),
        "mode": mode,
        "art109_bracket_years": base_years,
        "art109_basis": art109_ref,
        "art115_reduced_by_half": art115_applied,
        "under_21_at_fact": under_21,
        "over_70_at_sentence": over_70,
        "effective_prescription_years": str(Decimal(presc_years.numerator) / Decimal(presc_years.denominator)),
        "intervals": intervals,
        "prescription_recognized": any_prescribed,
        "warnings": warnings,
        "legal_status": "deterministic_penal_prescription_check",
    }


def calculate_lep_progression(spec: dict) -> dict:
    """Calcula fração/percentual de progressão de regime (LEP, art. 112) conforme a data do fato e natureza do delito."""
    if not isinstance(spec, dict):
        raise ValueError("Especificação da progressão LEP deve ser um dicionário JSON")
    offense_d = date.fromisoformat(str(spec["offense_date"]))
    violence = bool(spec.get("violence_or_grave_threat", False))
    feminicidio = bool(spec.get("feminicidio", False))
    hediondo = bool(spec.get("hediondo", False) or feminicidio)
    result_death = bool(spec.get("result_death", False) or feminicidio)

    recid = spec.get("recidivism")
    if recid is None:
        if spec.get("reincidente_especifico"):
            recid = "reincidente_especifico"
        elif spec.get("reincidente"):
            recid = "reincidente_generico"
        else:
            recid = "primario"
    recid = str(recid).lower().strip()
    if recid not in {"primario", "reincidente_generico", "reincidente_especifico"}:
        raise ValueError("recidivism deve ser 'primario', 'reincidente_generico' ou 'reincidente_especifico'")

    warnings: list[str] = []
    livramento_vedado = False

    if offense_d < PACOTE_ANTICRIME_DATE:
        if not hediondo or offense_d < LEI_11464_DATE:
            frac = Fraction(1, 6)
            pct = Decimal("16.666667")
            label = "1/6"
            basis = (
                "LEP, art. 112 (redação anterior à Lei 13.964/2019)"
                if not hediondo
                else "LEP, art. 112; Súmula Vinculante 26/STF e Súmula 471/STJ (hediondo anterior a 29/03/2007)"
            )
        else:
            if recid == "primario":
                frac = Fraction(2, 5)
                pct = Decimal("40")
                label = "2/5 (40%)"
                basis = "Lei 8.072/1990, art. 2º, § 2º (redação da Lei 11.464/2007 — primário)"
            elif recid == "reincidente_generico" and not result_death:
                frac = Fraction(2, 5)
                pct = Decimal("40")
                label = "2/5 (40% — retroatividade benéfica)"
                basis = "STF, Tema 1169 / STJ, Tema 1084 (retroatividade benéfica do art. 112, V, da LEP ao reincidente não específico)"
                warnings.append("Aplicada retroatividade benéfica do Pacote Anticrime (40% = 2/5 em vez de 3/5) ao reincidente genérico em crime hediondo sem morte (STF Tema 1169).")
            elif recid == "reincidente_generico" and result_death:
                frac = Fraction(1, 2)
                pct = Decimal("50")
                label = "50% (retroatividade benéfica sobre 3/5)"
                basis = "STF, Tema 1169 c/c LEP, art. 112, VI, 'a' (50% mais benéfico que 3/5 anterior)"
                livramento_vedado = True
            else:
                frac = Fraction(3, 5)
                pct = Decimal("60")
                label = "3/5 (60%)"
                basis = "Lei 8.072/1990, art. 2º, § 2º (Lei 11.464/2007 — reincidente específico)"
    else:
        if feminicidio and offense_d >= LEI_14994_FEMINICIDIO_DATE:
            livramento_vedado = True
            if recid == "reincidente_especifico":
                frac = Fraction(70, 100)
                pct = Decimal("70")
                label = "70%"
                basis = "LEP, art. 112, VIII (reincidente específico em hediondo com resultado morte)"
            else:
                frac = Fraction(55, 100)
                pct = Decimal("55")
                label = "55%"
                basis = "LEP, art. 112, VI-A (incluído pela Lei 14.994/2024 — feminicídio, vedado livramento condicional)"
        elif not hediondo:
            if not violence:
                if recid == "primario":
                    frac, pct, label, basis = Fraction(16, 100), Decimal("16"), "16%", "LEP, art. 112, I"
                else:
                    frac, pct, label, basis = Fraction(20, 100), Decimal("20"), "20%", "LEP, art. 112, II"
            else:
                if recid == "primario":
                    frac, pct, label, basis = Fraction(25, 100), Decimal("25"), "25%", "LEP, art. 112, III"
                else:
                    frac, pct, label, basis = Fraction(30, 100), Decimal("30"), "30%", "LEP, art. 112, IV"
        else:
            if not result_death:
                if recid in {"primario", "reincidente_generico"}:
                    frac, pct, label = Fraction(40, 100), Decimal("40"), "40%"
                    basis = "LEP, art. 112, V" + (" c/c STF Tema 1169 (reincidente não específico)" if recid == "reincidente_generico" else "")
                else:
                    frac, pct, label, basis = Fraction(60, 100), Decimal("60"), "60%", "LEP, art. 112, VII"
            else:
                livramento_vedado = True
                if recid in {"primario", "reincidente_generico"}:
                    frac, pct, label = Fraction(50, 100), Decimal("50"), "50%"
                    basis = "LEP, art. 112, VI, 'a' (vedado livramento condicional)" + (
                        " c/c STF Tema 1169 (reincidente não específico)" if recid == "reincidente_generico" else ""
                    )
                else:
                    frac, pct, label, basis = Fraction(70, 100), Decimal("70"), "70%", "LEP, art. 112, VIII (vedado livramento condicional)"

    warnings.append(
        "Lei 14.843/2024: observar a redação atual do art. 112, § 1º, da LEP (exigência de exame criminológico) e do "
        "art. 122, § 2º, da LEP (vedação de saída temporária em crimes hediondos ou com violência/grave ameaça), "
        + ("aplicável diretamente ao delito posterior à vigência." if offense_d >= LEI_14843_DATE
           else "sujeita à análise de irretroatividade da lei penal mais gravosa (CF, art. 5º, XL) para fatos anteriores a 11/04/2024.")
    )

    result: dict = {
        "offense_date": offense_d.isoformat(),
        "hediondo_or_equiparado": hediondo,
        "feminicidio": feminicidio,
        "violence_or_grave_threat": violence,
        "result_death": result_death,
        "recidivism": recid,
        "progression_requirement_label": label,
        "progression_percentage": str(pct),
        "progression_fraction": f"{frac.numerator}/{frac.denominator}",
        "livramento_condicional_barred": livramento_vedado,
        "criminological_exam_lei_14843_applies_by_date": offense_d >= LEI_14843_DATE,
        "normative_basis": basis,
        "warnings": warnings,
        "legal_status": "deterministic_lep_progression_calculation",
    }

    if "total_penalty" in spec and spec["total_penalty"] is not None:
        pen_days = penalty_to_days(spec["total_penalty"])
        req_days = int(Fraction(pen_days) * frac)
        remicao = int(spec.get("remicao_days", 0))
        detracao = int(spec.get("detracao_days", 0))
        net_to_serve = max(0, req_days - remicao - detracao)
        result["required_days_360"] = req_days
        result["net_days_remaining_after_remicao_detracao"] = net_to_serve
        if spec.get("base_execution_date"):
            base_exec = date.fromisoformat(str(spec["base_execution_date"]))
            result["estimated_progression_date"] = (base_exec + timedelta(days=net_to_serve)).isoformat()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Motor determinístico de dosimetria penal, prescrição e execução penal (LEP)")
    parser.add_argument("--input", type=Path, help="Arquivo JSON de especificação")
    parser.add_argument("--operation", choices=["dosimetry", "prescription", "lep"], default="dosimetry")
    args = parser.parse_args(argv)
    try:
        if args.input:
            spec = json.loads(args.input.read_text(encoding="utf-8"))
        elif not sys.stdin.isatty():
            spec = json.loads(sys.stdin.read())
        else:
            parser.error("Informe --input ARQUIVO.json")
            return 2
        op = spec.get("operation", args.operation)
        if op == "dosimetry":
            result = calculate_dosimetry(spec)
        elif op == "prescription":
            result = calculate_penal_prescription(spec)
        elif op == "lep":
            result = calculate_lep_progression(spec)
        else:
            raise ValueError(f"Operação desconhecida: {op!r}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
