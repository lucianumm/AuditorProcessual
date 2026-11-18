"""Motor determinístico multi-regime de atualização monetária, juros, imputação (CC art. 354) e revisional bancária.

Zero ponto flutuante (exclusivamente Decimal). Não inventa nem extrapola séries econômicas:
ausência de competência exigida em qualquer fase interrompe o cálculo com ValueError explícito.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path

try:
    from .official_indices import _competence_key
except ImportError:
    from official_indices import _competence_key

LEI_14905_BOUNDARY = date(2024, 8, 30)
EC_113_BOUNDARY = date(2021, 12, 9)
ADI_5090_BOUNDARY = date(2024, 6, 17)

SUPPORTED_REGIMES = {
    "civil_lei_14905",
    "fazenda_ec113",
    "tributario_selic",
    "fgts_adi5090",
    "custom",
}


def _dec(value: object, label: str = "valor") -> Decimal:
    """Converte string ou Decimal para Decimal finito, rejeitando float."""
    if isinstance(value, (float, bool)):
        raise ValueError(f"{label}: ponto flutuante/booleano não permitido; informe string decimal")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, str):
        cleaned = value.strip()
        if not cleaned or len(cleaned) > 50:
            raise ValueError(f"{label}: string decimal vazia ou excessiva")
        try:
            number = Decimal(cleaned)
        except InvalidOperation as error:
            raise ValueError(f"{label}: valor decimal inválido ({value!r})") from error
    else:
        raise ValueError(f"{label}: tipo inválido ({type(value).__name__})")
    if not number.is_finite() or abs(number.adjusted()) > 30:
        raise ValueError(f"{label}: valor não finito ou fora do limite operacional")
    return number


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _rate_str(value: Decimal, places: str = "0.000001") -> str:
    return str(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def _month_range(start_ym: str, end_ym: str) -> list[str]:
    sy, sm = (int(x) for x in start_ym.split("-"))
    ey, em = (int(x) for x in end_ym.split("-"))
    if (sy, sm) > (ey, em):
        return []
    months: list[str] = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def _prev_ym(ym: str) -> str:
    y, m = (int(x) for x in ym.split("-"))
    return f"{y - 1:04d}-12" if m == 1 else f"{y:04d}-{m - 1:02d}"


def _series_map(points: list[dict] | None, series_label: str) -> dict[str, Decimal]:
    if not points:
        return {}
    if not isinstance(points, list):
        raise ValueError(f"Série {series_label} deve ser lista de objetos {{'date', 'value'}}")
    mapped: dict[str, Decimal] = {}
    for item in points:
        if not isinstance(item, dict) or "date" not in item or "value" not in item:
            raise ValueError(f"Ponto inválido em {series_label}")
        comp = _competence_key(str(item["date"]))
        if comp in mapped:
            raise ValueError(f"Competência duplicada {comp} em {series_label}")
        raw_val = item["value"]
        if isinstance(raw_val, str):
            raw_val = raw_val.replace(",", ".")
        mapped[comp] = _dec(raw_val, f"{series_label}[{comp}]")
    return mapped


def _require_competences(series: dict[str, Decimal], competences: list[str], series_name: str, phase_name: str) -> None:
    missing = [c for c in competences if c not in series]
    if missing:
        raise ValueError(
            f"Série obrigatória '{series_name}' sem cobertura para a fase '{phase_name}' "
            f"nas competências: {', '.join(missing)}"
        )


def _build_preset_phases(spec: dict, start_d: date, end_d: date) -> tuple[list[dict], list[str]]:
    regime = spec.get("regime") or ("custom" if spec.get("phases") else None)
    if regime not in SUPPORTED_REGIMES:
        raise ValueError(f"Regime inválido ou ausente: {regime!r}. Opções: {sorted(SUPPORTED_REGIMES)}")
    warnings: list[str] = []
    start_ym = f"{start_d.year:04d}-{start_d.month:02d}"
    end_ym = f"{end_d.year:04d}-{end_d.month:02d}"

    if regime == "custom":
        raw_phases = spec.get("phases")
        if not isinstance(raw_phases, list) or not raw_phases:
            raise ValueError("Regime 'custom' exige lista não vazia em 'phases'")
        built = []
        for idx, ph in enumerate(raw_phases, 1):
            p_start = date.fromisoformat(ph["start_date"])
            p_end = date.fromisoformat(ph["end_date"])
            if p_start > p_end:
                raise ValueError(f"Fase {idx} com datas invertidas")
            p_sym = ph.get("start_competence") or f"{p_start.year:04d}-{p_start.month:02d}"
            p_eym = ph.get("end_competence") or f"{p_end.year:04d}-{p_end.month:02d}"
            built.append({
                "name": ph.get("name", f"phase_{idx}"),
                "mode": ph["mode"],
                "start_date": p_start.isoformat(),
                "end_date": p_end.isoformat(),
                "competences": _month_range(p_sym, p_eym),
                "fixed_monthly_interest_pct": ph.get("fixed_monthly_interest_pct", spec.get("fixed_monthly_interest_pct")),
                "index_points": ph.get("index_points"),
                "ipca_points": ph.get("ipca_points"),
                "selic_points": ph.get("selic_points"),
                "normative_basis": ph.get("normative_basis", "Título / parâmetros fornecidos"),
            })
        return built, warnings

    if regime == "civil_lei_14905":
        fixed_pre = spec.get("fixed_monthly_interest_pct")
        if fixed_pre is None and start_d < LEI_14905_BOUNDARY:
            fixed_pre = "1.0"
            warnings.append(
                "Fase pré-30/08/2024: adotado fixed_monthly_interest_pct='1.0' (% a.m., CC art. 406 c/c CTN art. 161 §1º); "
                "conferir tese da SELIC pré-vigência (STJ, Corte Especial, REsp 1.795.982 / Tema 1368)."
            )
        if end_d < LEI_14905_BOUNDARY:
            return [{
                "name": "pre_lei_14905",
                "mode": "index_plus_fixed_interest",
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
                "competences": _month_range(start_ym, end_ym),
                "fixed_monthly_interest_pct": fixed_pre,
                "normative_basis": "CC, arts. 389 e 406 (redação anterior à Lei 14.905/2024)",
            }], warnings
        if start_d >= LEI_14905_BOUNDARY:
            return [{
                "name": "post_lei_14905",
                "mode": "lei_14905",
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
                "competences": _month_range(start_ym, end_ym),
                "normative_basis": "CC, arts. 389, p.u. (IPCA) e 406, § 1º (SELIC - IPCA, piso zero) — Lei 14.905/2024; Res. CMN 5.171/2024",
            }], warnings
        pre_comps = _month_range(start_ym, "2024-08")
        post_comps = _month_range("2024-09", end_ym)
        warnings.append("Transição intertemporal automática aplicada em 2024-08-30 (entrada em vigor da Lei 14.905/2024).")
        return [
            {
                "name": "pre_lei_14905",
                "mode": "index_plus_fixed_interest",
                "start_date": start_d.isoformat(),
                "end_date": "2024-08-29",
                "competences": pre_comps,
                "fixed_monthly_interest_pct": fixed_pre,
                "normative_basis": "CC, arts. 389 e 406 (fatos/meses anteriores a 30/08/2024)",
            },
            {
                "name": "post_lei_14905",
                "mode": "lei_14905",
                "start_date": "2024-08-30",
                "end_date": end_d.isoformat(),
                "competences": post_comps,
                "normative_basis": "CC, arts. 389, p.u. e 406, § 1º (Lei 14.905/2024; Res. CMN 5.171/2024)",
            },
        ], warnings

    if regime == "fazenda_ec113":
        fixed_pre = spec.get("fixed_monthly_interest_pct")
        if fixed_pre is None and start_d < EC_113_BOUNDARY:
            fixed_pre = "0.5"
            warnings.append(
                "Fase pré-09/12/2021 (Fazenda Pública, não tributário): adotado fixed_monthly_interest_pct='0.5' "
                "(STF Tema 810 / Lei 9.494/1997 art. 1º-F); conferir remuneração exata da poupança quando SELIC <= 8,5% a.a."
            )
        if end_d < EC_113_BOUNDARY:
            return [{
                "name": "pre_ec113_tema810",
                "mode": "index_plus_fixed_interest",
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
                "competences": _month_range(start_ym, end_ym),
                "fixed_monthly_interest_pct": fixed_pre,
                "normative_basis": "STF, Tema 810 (RE 870.947) — IPCA-E + juros da caderneta de poupança",
            }], warnings
        if start_d >= EC_113_BOUNDARY:
            return [{
                "name": "post_ec113_selic",
                "mode": "selic_unica",
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
                "competences": _month_range(start_ym, end_ym),
                "normative_basis": "EC 113/2021, art. 3º — Taxa SELIC única (correção + mora, sem capitalização)",
            }], warnings
        warnings.append("Transição intertemporal automática aplicada em 2021-12-09 (EC 113/2021, art. 3º).")
        return [
            {
                "name": "pre_ec113_tema810",
                "mode": "index_plus_fixed_interest",
                "start_date": start_d.isoformat(),
                "end_date": "2021-12-08",
                "competences": _month_range(start_ym, "2021-11"),
                "fixed_monthly_interest_pct": fixed_pre,
                "normative_basis": "STF, Tema 810 (período anterior à EC 113/2021)",
            },
            {
                "name": "post_ec113_selic",
                "mode": "selic_unica",
                "start_date": "2021-12-09",
                "end_date": end_d.isoformat(),
                "competences": _month_range("2021-12", end_ym),
                "normative_basis": "EC 113/2021, art. 3º — Taxa SELIC única",
            },
        ], warnings

    if regime == "tributario_selic":
        return [{
            "name": "tributario_selic_unica",
            "mode": "selic_unica",
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "competences": _month_range(start_ym, end_ym),
            "normative_basis": "Lei 9.250/1995, art. 39, § 4º; CTN, art. 161, § 1º; STF Tema 1062 / STJ Tema 905",
        }], warnings

    # regime == "fgts_adi5090"
    jam_pct = spec.get("fixed_monthly_interest_pct", "0.25")
    if end_d < ADI_5090_BOUNDARY:
        return [{
            "name": "pre_adi5090_tr_jam",
            "mode": "index_plus_fixed_interest",
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "competences": _month_range(start_ym, end_ym),
            "fixed_monthly_interest_pct": jam_pct,
            "normative_basis": "Lei 8.036/1990, art. 13 (TR + 3% a.a.) — período pré-ADI 5090 (efeitos ex nunc)",
        }], warnings
    if start_d >= ADI_5090_BOUNDARY:
        return [{
            "name": "post_adi5090_piso_ipca",
            "mode": "fgts_adi5090_floor",
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "competences": _month_range(start_ym, end_ym),
            "fixed_monthly_interest_pct": jam_pct,
            "normative_basis": "STF, ADI 5090 (ata publicada em 17/06/2024, efeitos ex nunc) — remuneração mínima pelo IPCA",
        }], warnings
    warnings.append("Transição ex nunc da ADI 5090/STF aplicada a partir de junho/2024 (piso IPCA sobre TR + JAM).")
    return [
        {
            "name": "pre_adi5090_tr_jam",
            "mode": "index_plus_fixed_interest",
            "start_date": start_d.isoformat(),
            "end_date": "2024-06-16",
            "competences": _month_range(start_ym, _prev_ym("2024-06")),
            "fixed_monthly_interest_pct": jam_pct,
            "normative_basis": "Lei 8.036/1990, art. 13 (período anterior à ADI 5090)",
        },
        {
            "name": "post_adi5090_piso_ipca",
            "mode": "fgts_adi5090_floor",
            "start_date": "2024-06-17",
            "end_date": end_d.isoformat(),
            "competences": _month_range("2024-06", end_ym),
            "fixed_monthly_interest_pct": jam_pct,
            "normative_basis": "STF, ADI 5090 — piso mínimo equivalente ao IPCA",
        },
    ], warnings


def calculate_monetary_update(spec: dict) -> dict:
    """Atualiza crédito com fases temporais, imputação parcial (CC art. 354), CPC art. 523 e honorários."""
    if not isinstance(spec, dict):
        raise ValueError("Especificação do cálculo deve ser um dicionário JSON")
    principal_orig = _dec(spec.get("principal"), "principal")
    if principal_orig < Decimal("0"):
        raise ValueError("principal não pode ser negativo")
    start_d = date.fromisoformat(str(spec["start_date"]))
    end_d = date.fromisoformat(str(spec["end_date"]))
    if start_d > end_d:
        raise ValueError("start_date posterior a end_date")

    imputation = spec.get("imputation", "interest_first")
    if imputation not in {"interest_first", "principal_first"}:
        raise ValueError("imputation deve ser 'interest_first' (CC, art. 354) ou 'principal_first'")

    global_index = _series_map(spec.get("index_points"), "index_points")
    global_ipca = _series_map(spec.get("ipca_points"), "ipca_points")
    global_selic = _series_map(spec.get("selic_points"), "selic_points")

    payments_by_comp: dict[str, list[dict]] = {}
    for raw_pay in spec.get("partial_payments") or []:
        pay_d = date.fromisoformat(str(raw_pay["date"]))
        if pay_d < start_d or pay_d > end_d:
            raise ValueError(f"Pagamento parcial em {pay_d.isoformat()} fora do intervalo [{start_d}, {end_d}]")
        amt = _dec(raw_pay["amount"], "partial_payment.amount")
        if amt <= Decimal("0"):
            raise ValueError("Valor de pagamento parcial deve ser positivo")
        comp = f"{pay_d.year:04d}-{pay_d.month:02d}"
        payments_by_comp.setdefault(comp, []).append({
            "date": pay_d.isoformat(),
            "amount": amt,
            "imputation": raw_pay.get("imputation", imputation),
        })
    for comp_list in payments_by_comp.values():
        comp_list.sort(key=lambda item: item["date"])

    phases, warnings = _build_preset_phases(spec, start_d, end_d)

    monthly_ledger: list[dict] = []
    phase_summaries: list[dict] = []
    imputation_log: list[dict] = []

    with localcontext() as ctx:
        ctx.prec = 50
        corrected_principal = principal_orig
        accrued_interest = Decimal("0")
        overpayment_balance = Decimal("0")

        for phase in phases:
            p_name = phase["name"]
            p_mode = phase["mode"]
            comps = phase["competences"]
            p_index = _series_map(phase.get("index_points"), f"{p_name}.index_points") or global_index
            p_ipca = _series_map(phase.get("ipca_points"), f"{p_name}.ipca_points") or global_ipca or p_index
            p_selic = _series_map(phase.get("selic_points"), f"{p_name}.selic_points") or global_selic

            phase_corr_factor = Decimal("1")
            phase_simple_interest_pct = Decimal("0")

            if p_mode in {"index_plus_fixed_interest", "index_only"} and comps:
                _require_competences(p_index, comps, "index_points", p_name)
            elif p_mode == "lei_14905" and comps:
                _require_competences(p_ipca, comps, "ipca_points/index_points", p_name)
                _require_competences(p_selic, comps, "selic_points", p_name)
            elif p_mode == "selic_unica" and comps:
                _require_competences(p_selic, comps, "selic_points", p_name)
            elif p_mode == "fgts_adi5090_floor" and comps:
                _require_competences(p_index, comps, "index_points (TR)", p_name)
                _require_competences(p_ipca, comps, "ipca_points", p_name)
            elif p_mode not in {"index_plus_fixed_interest", "index_only", "lei_14905", "selic_unica", "fgts_adi5090_floor"}:
                raise ValueError(f"Modo de fase desconhecido: {p_mode!r}")

            fixed_rate_pct = (
                _dec(phase["fixed_monthly_interest_pct"], f"{p_name}.fixed_monthly_interest_pct")
                if phase.get("fixed_monthly_interest_pct") is not None
                else Decimal("0")
            )

            for comp in comps:
                if p_mode == "index_only":
                    corr_pct = p_index[comp]
                    int_pct = Decimal("0")
                elif p_mode == "index_plus_fixed_interest":
                    corr_pct = p_index[comp]
                    int_pct = fixed_rate_pct
                elif p_mode == "lei_14905":
                    corr_pct = p_ipca[comp]
                    raw_diff = p_selic[comp] - p_ipca[comp]
                    int_pct = raw_diff if raw_diff > Decimal("0") else Decimal("0")
                elif p_mode == "selic_unica":
                    corr_pct = Decimal("0")
                    int_pct = p_selic[comp]
                else:  # fgts_adi5090_floor
                    tr_pct = p_index[comp]
                    tr_jam_factor = (Decimal("1") + tr_pct / Decimal("100")) * (Decimal("1") + fixed_rate_pct / Decimal("100"))
                    tr_jam_pct = (tr_jam_factor - Decimal("1")) * Decimal("100")
                    corr_pct = p_ipca[comp] if p_ipca[comp] > tr_jam_pct else tr_jam_pct
                    int_pct = Decimal("0")

                corr_mult = Decimal("1") + (corr_pct / Decimal("100"))
                phase_corr_factor *= corr_mult
                phase_simple_interest_pct += int_pct

                # Atualiza o capital e a expressão monetária dos juros já vencidos pelo índice de inflação
                # (sem capitalizar juros sobre juros), acrescendo os juros simples do mês sobre o capital corrigido.
                if corr_pct != Decimal("0"):
                    corrected_principal *= corr_mult
                    accrued_interest *= corr_mult
                month_interest_added = corrected_principal * (int_pct / Decimal("100"))
                accrued_interest += month_interest_added

                for pay in payments_by_comp.get(comp, []):
                    amt = pay["amount"]
                    mode_imp = pay["imputation"]
                    if mode_imp == "interest_first":
                        to_int = min(amt, accrued_interest)
                        accrued_interest -= to_int
                        rem = amt - to_int
                        to_prin = min(rem, corrected_principal)
                        corrected_principal -= to_prin
                        extra = rem - to_prin
                    else:
                        to_prin = min(amt, corrected_principal)
                        corrected_principal -= to_prin
                        rem = amt - to_prin
                        to_int = min(rem, accrued_interest)
                        accrued_interest -= to_int
                        extra = rem - to_int
                    overpayment_balance += extra
                    imputation_log.append({
                        "date": pay["date"],
                        "competence": comp,
                        "amount": _money(amt),
                        "imputation_rule": "CC, art. 354 (juros primeiro, depois capital)" if mode_imp == "interest_first" else "Estipulação expressa (capital primeiro)",
                        "imputed_to_interest": _money(to_int),
                        "imputed_to_principal": _money(to_prin),
                        "excess_overpayment": _money(extra),
                        "remaining_principal": _money(corrected_principal),
                        "remaining_interest": _money(accrued_interest),
                    })

                monthly_ledger.append({
                    "competence": comp,
                    "phase": p_name,
                    "mode": p_mode,
                    "correction_pct": _rate_str(corr_pct),
                    "interest_pct": _rate_str(int_pct),
                    "corrected_principal": _money(corrected_principal),
                    "accrued_interest": _money(accrued_interest),
                    "subtotal": _money(corrected_principal + accrued_interest),
                })

            phase_summaries.append({
                "name": p_name,
                "mode": p_mode,
                "start_date": phase["start_date"],
                "end_date": phase["end_date"],
                "competences_count": len(comps),
                "first_competence": comps[0] if comps else None,
                "last_competence": comps[-1] if comps else None,
                "correction_factor": _rate_str(phase_corr_factor, "0.000000000001"),
                "simple_interest_pct": _rate_str(phase_simple_interest_pct),
                "normative_basis": phase["normative_basis"],
            })

        subtotal = corrected_principal + accrued_interest
        hon_pct = _dec(spec["honorarios_sucumbencia_pct"], "honorarios_sucumbencia_pct") if spec.get("honorarios_sucumbencia_pct") is not None else Decimal("0")
        if hon_pct < Decimal("0"):
            raise ValueError("honorarios_sucumbencia_pct não pode ser negativo")
        honorarios_sucumbencia = subtotal * (hon_pct / Decimal("100"))

        art523 = spec.get("art523_cpc") or {}
        base_523 = subtotal + honorarios_sucumbencia
        multa_523 = base_523 * Decimal("0.10") if art523.get("multa_10") else Decimal("0")
        hon_523 = base_523 * Decimal("0.10") if art523.get("honorarios_10") else Decimal("0")
        grand_total = base_523 + multa_523 + hon_523

    return {
        "regime": spec.get("regime") or "custom",
        "start_date": start_d.isoformat(),
        "end_date": end_d.isoformat(),
        "principal_original": _money(principal_orig),
        "corrected_principal": _money(corrected_principal),
        "moratory_interest": _money(accrued_interest),
        "updated_debt_subtotal": _money(subtotal),
        "honorarios_sucumbencia_pct": str(hon_pct),
        "honorarios_sucumbencia": _money(honorarios_sucumbencia),
        "art523_multa_10": _money(multa_523),
        "art523_honorarios_10": _money(hon_523),
        "overpayment_credit": _money(overpayment_balance),
        "grand_total": _money(grand_total),
        "phases_applied": phase_summaries,
        "partial_payments_imputed": imputation_log,
        "monthly_ledger": monthly_ledger,
        "warnings": warnings,
        "legal_status": "deterministic_calculation_from_supplied_parameters",
    }


def compare_bank_rate(
    contract_monthly_pct: str,
    bcb_market_monthly_pct: str,
    threshold_multiplier: str = "1.5",
) -> dict:
    """Compara taxa contratual mensal com a taxa média de mercado do BCB/SGS (STJ Temas 24–27)."""
    contract_m = _dec(contract_monthly_pct, "contract_monthly_pct")
    market_m = _dec(bcb_market_monthly_pct, "bcb_market_monthly_pct")
    threshold = _dec(threshold_multiplier, "threshold_multiplier")
    if contract_m < Decimal("0"):
        raise ValueError("contract_monthly_pct não pode ser negativa")
    if market_m <= Decimal("0"):
        raise ValueError("bcb_market_monthly_pct deve ser estritamente positiva")
    if threshold <= Decimal("0"):
        raise ValueError("threshold_multiplier deve ser estritamente positivo")

    with localcontext() as ctx:
        ctx.prec = 50
        ic = contract_m / Decimal("100")
        im = market_m / Decimal("100")
        contract_annual = ((Decimal("1") + ic) ** 12 - Decimal("1")) * Decimal("100")
        market_annual = ((Decimal("1") + im) ** 12 - Decimal("1")) * Decimal("100")
        ratio = contract_m / market_m
        spread_m = contract_m - market_m
        spread_y = contract_annual - market_annual
        threshold_rate_m = market_m * threshold
        exceeds = ratio > threshold

    return {
        "contract_monthly_pct": _rate_str(contract_m, "0.0001"),
        "contract_annual_effective_pct": _rate_str(contract_annual, "0.0001"),
        "bcb_market_monthly_pct": _rate_str(market_m, "0.0001"),
        "bcb_market_annual_effective_pct": _rate_str(market_annual, "0.0001"),
        "ratio_contract_over_market": _rate_str(ratio, "0.0001"),
        "spread_monthly_pp": _rate_str(spread_m, "0.0001"),
        "spread_annual_pp": _rate_str(spread_y, "0.0001"),
        "threshold_multiplier": _rate_str(threshold, "0.0001"),
        "threshold_monthly_pct": _rate_str(threshold_rate_m, "0.0001"),
        "exceeds_objective_threshold": exceeds,
        "normative_references": [
            "STJ, Tema 27 (REsp 1.061.530/RS)",
            "STJ, Súmula 382 (estipulação > 12% a.a., por si só, não indica abusividade)",
            "STJ, Súmula 530 (ausência do contrato impõe taxa média de mercado do BCB)",
        ],
        "note": (
            "A jurisprudência do STJ (Tema 27) exige demonstração concreta de discrepância substancial frente à "
            "taxa média de mercado da espécie e época da operação, considerado o risco do crédito; o multiplicador "
            "é referencial matemático objetivo de triagem pericial, não presunção legal absoluta."
        ),
        "legal_status": "mathematical_comparison_requires_case_subsumption_stj_tema_27",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Motor determinístico de atualização monetária, juros e revisional bancária")
    parser.add_argument("--input", type=Path, help="Arquivo JSON de especificação para calculate_monetary_update")
    parser.add_argument("--compare-bank-rate", nargs=2, metavar=("CONTRACT_PCT_AM", "BCB_PCT_AM"),
                        help="Compara taxa mensal contratual e taxa média mensal do BCB")
    parser.add_argument("--threshold", default="1.5", help="Multiplicador de referência para --compare-bank-rate (padrão: 1.5)")
    args = parser.parse_args(argv)
    try:
        if args.compare_bank_rate:
            result = compare_bank_rate(args.compare_bank_rate[0], args.compare_bank_rate[1], args.threshold)
        elif args.input:
            spec = json.loads(args.input.read_text(encoding="utf-8"))
            result = calculate_monetary_update(spec)
        elif not sys.stdin.isatty():
            spec = json.loads(sys.stdin.read())
            result = calculate_monetary_update(spec)
        else:
            parser.error("Informe --input ARQUIVO.json ou --compare-bank-rate CONTRATO BCB")
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
