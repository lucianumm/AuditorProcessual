"""Calculadora determinística de prazos processuais brasileiros (CPC, CLT, JEC/JEF, CPP/LEP, RJ e Eleitoral).

Inclui Páscoa gregoriana exata, feriados nacionais (inclusive 20/11 — Lei 14.759/2023 a partir de 2024),
recesso forense (CPC art. 220 / CLT art. 775-A), DJe, portal eletrônico (Lei 11.419/2006), citação no
Domicílio Judicial Eletrônico (Res. CNJ 455/2022 / art. 246 CPC), vedação da dobra em autos eletrônicos
(CPC art. 229 § 2º) e prorrogação por indisponibilidade do sistema (Lei 11.419 art. 10 § 2º / Lei 14.939/2024).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

WEEKDAY_NAMES_PT = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)

BUSINESS_DAY_RITOS = {"civel", "trabalhista", "jec", "jef"}
CALENDAR_DAY_RITOS = {"penal", "execucao_penal", "recuperacao_judicial", "eleitoral", "material_decadencial"}
SUPPORTED_RITOS = BUSINESS_DAY_RITOS | CALENDAR_DAY_RITOS
SUPPORTED_INTIMATION_MODES = {"dje", "portal_eletronico", "djen_citacao", "in_person_or_hearing", "juntada"}


def easter_sunday(year: int) -> date:
    """Algoritmo gregoriano anônimo (Meeus/Jones/Butcher) em aritmética inteira exata."""
    if not isinstance(year, int) or isinstance(year, bool) or year < 1583 or year > 9999:
        raise ValueError("Ano deve ser inteiro entre 1583 e 9999")
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def national_holidays(
    year: int,
    *,
    include_dia_da_justica: bool = False,
    include_quinta_feira_santa: bool = False,
    include_carnaval: bool = False,
    include_corpus_christi: bool = True,
) -> dict[date, str]:
    """Feriados nacionais brasileiros e pontos forenses opcionais para o ano indicado."""
    easter = easter_sunday(year)
    holidays: dict[date, str] = {
        date(year, 1, 1): "Confraternização Universal (Lei 662/1949)",
        easter - timedelta(days=2): "Sexta-Feira Santa / Paixão de Cristo (Lei 9.093/1995 / Lei 5.010/1966)",
        date(year, 4, 21): "Tiradentes (Lei 662/1949)",
        date(year, 5, 1): "Dia Mundial do Trabalho (Lei 662/1949)",
        date(year, 9, 7): "Independência do Brasil (Lei 662/1949)",
        date(year, 10, 12): "Nossa Senhora Aparecida (Lei 6.802/1980)",
        date(year, 11, 2): "Finados (Lei 662/1949)",
        date(year, 11, 15): "Proclamação da República (Lei 662/1949)",
        date(year, 12, 25): "Natal (Lei 662/1949)",
    }
    if include_corpus_christi:
        holidays[easter + timedelta(days=60)] = "Corpus Christi (calendário forense / ponto facultativo nacional)"
    if year >= 2024:
        holidays[date(year, 11, 20)] = "Dia Nacional de Zumbi e da Consciência Negra (Lei 14.759/2023)"
    if include_dia_da_justica:
        holidays[date(year, 12, 8)] = "Dia da Justiça (Decreto-Lei 8.292/1945 / Lei 5.010/1966, art. 62, IV)"
    if include_quinta_feira_santa:
        holidays[easter - timedelta(days=3)] = "Quinta-Feira Santa (Lei 5.010/1966, art. 62, II / calendário forense)"
    if include_carnaval:
        holidays[easter - timedelta(days=48)] = "Segunda-Feira de Carnaval (Lei 5.010/1966, art. 62, III / calendário forense)"
        holidays[easter - timedelta(days=47)] = "Terça-Feira de Carnaval (Lei 5.010/1966, art. 62, III / calendário forense)"
    return dict(sorted(holidays.items()))


def _is_recesso_date(day: date) -> bool:
    return (day.month == 12 and day.day >= 20) or (day.month == 1 and day.day <= 20)


def _is_forensic_recess_expediente_closed(day: date) -> bool:
    """Recesso estrito sem expediente forense (20/12 a 06/01 — Lei 5.010/1966, art. 62, I / Res. CNJ 244/2016)."""
    return (day.month == 12 and day.day >= 20) or (day.month == 1 and day.day <= 6)


def calculate_deadline(spec: dict) -> dict:
    """Calcula prazo processual com trilha diária auditável (audit_trail), dies a quo e dies ad quem."""
    if not isinstance(spec, dict):
        raise ValueError("Especificação de prazo deve ser um dicionário JSON")
    base_days = spec.get("days")
    if not isinstance(base_days, int) or isinstance(base_days, bool) or base_days < 1:
        raise ValueError("days deve ser inteiro positivo (>= 1)")

    base_date = date.fromisoformat(str(spec["base_date"]))
    rito = str(spec.get("rito", "civel")).lower().strip()
    if rito not in SUPPORTED_RITOS:
        raise ValueError(f"rito não suportado: {rito!r}. Opções: {sorted(SUPPORTED_RITOS)}")

    counting_mode = spec.get("counting_mode")
    if counting_mode is None:
        counting_mode = "business_days" if rito in BUSINESS_DAY_RITOS else "calendar_days"
    if counting_mode not in {"business_days", "calendar_days"}:
        raise ValueError("counting_mode deve ser 'business_days' ou 'calendar_days'")

    intimation_mode = str(spec.get("intimation_mode", "dje")).lower().strip()
    if intimation_mode not in SUPPORTED_INTIMATION_MODES:
        raise ValueError(f"intimation_mode inválido: {intimation_mode!r}. Opções: {sorted(SUPPORTED_INTIMATION_MODES)}")

    process_medium = str(spec.get("process_medium", "eletronico")).lower().strip()
    if process_medium not in {"eletronico", "fisico"}:
        raise ValueError("process_medium deve ser 'eletronico' ou 'fisico'")

    if spec.get("litisconsortes_dobra"):
        if process_medium == "eletronico":
            raise ValueError(
                "CPC, art. 229, § 2º: não se aplica a contagem em dobro para litisconsortes com diferentes "
                "procuradores quando o processo tramitar em autos eletrônicos."
            )

    multiplier = spec.get("multiplier", 1)
    if spec.get("litisconsortes_dobra") and process_medium == "fisico" and multiplier == 1:
        multiplier = 2
    prerogative = spec.get("prerogative")
    if prerogative in {"fazenda_publica", "ministerio_publico", "defensoria_publica"} and not spec.get("own_statutory_deadline"):
        multiplier = 2
    if multiplier not in {1, 2}:
        raise ValueError("multiplier deve ser 1 ou 2")
    effective_days = base_days * multiplier

    warnings: list[str] = []
    court_cal = spec.get("court_calendar") or {}
    inc_justica = bool(spec.get("include_dia_da_justica", court_cal.get("include_dia_da_justica", False)))
    inc_quinta = bool(spec.get("include_quinta_feira_santa", court_cal.get("include_quinta_feira_santa", False)))
    inc_carnaval = bool(spec.get("include_carnaval", court_cal.get("include_carnaval", False)))
    inc_corpus = bool(spec.get("include_corpus_christi", court_cal.get("include_corpus_christi", True)))

    recesso_suspends = spec.get("recesso_suspends")
    if recesso_suspends is None:
        recesso_suspends = rito in BUSINESS_DAY_RITOS
        if rito in {"penal", "execucao_penal"}:
            warnings.append(
                "Rito penal: recesso_suspends=False por padrão (CPP, art. 798, caput — réu preso/urgentes); "
                "para hipóteses abrangidas pelo art. 798-A do CPP (Lei 14.365/2022), defina recesso_suspends=True."
            )

    local_holidays_map: dict[date, str] = {}
    for item in spec.get("local_holidays") or []:
        if isinstance(item, str):
            local_holidays_map[date.fromisoformat(item)] = "Feriado local informado"
        elif isinstance(item, dict) and "date" in item:
            local_holidays_map[date.fromisoformat(str(item["date"]))] = str(item.get("name", "Feriado local informado"))
        else:
            raise ValueError("Item inválido em local_holidays")
    if local_holidays_map:
        warnings.append(
            "Feriado local considerado: nos termos do art. 1.003, § 6º, do CPC (redação dada pela Lei 14.939/2024), "
            "comprovar o feriado local no ato da interposição, cabendo intimação para suprir eventual omissão antes de "
            "reconhecer intempestividade."
        )

    suspensions_list: list[tuple[date, date, str]] = []
    for item in spec.get("suspensions") or []:
        s_start = date.fromisoformat(str(item["start"]))
        s_end = date.fromisoformat(str(item["end"]))
        if s_start > s_end:
            raise ValueError("Período de suspensão invertido")
        suspensions_list.append((s_start, s_end, str(item.get("reason", "Suspensão processual informada"))))

    outage_dates = {date.fromisoformat(str(d)) for d in (spec.get("system_outage_on_start_or_end") or [])}

    holiday_cache: dict[int, dict[date, str]] = {}

    def _holidays_for_year(yr: int) -> dict[date, str]:
        if yr not in holiday_cache:
            holiday_cache[yr] = national_holidays(
                yr,
                include_dia_da_justica=inc_justica,
                include_quinta_feira_santa=inc_quinta,
                include_carnaval=inc_carnaval,
                include_corpus_christi=inc_corpus,
            )
        return holiday_cache[yr]

    def _day_non_working_reason(day: date, *, check_recesso_suspension: bool = True) -> str | None:
        if day.weekday() >= 5:
            return f"Fim de semana ({WEEKDAY_NAMES_PT[day.weekday()]})"
        nat = _holidays_for_year(day.year).get(day)
        if nat:
            return f"Feriado nacional: {nat}"
        loc = local_holidays_map.get(day)
        if loc:
            return f"Feriado local: {loc}"
        for s_start, s_end, s_reason in suspensions_list:
            if s_start <= day <= s_end:
                return f"Suspensão: {s_reason}"
        if check_recesso_suspension and recesso_suspends and _is_recesso_date(day):
            return "Suspensão de prazos / recesso forense (20/12 a 20/01 — CPC, art. 220 / CLT, art. 775-A)"
        return None

    def _is_expediente_day(day: date) -> bool:
        """Dia útil forense para disponibilização/publicação/prorrogação de termo final."""
        if _day_non_working_reason(day, check_recesso_suspension=True) is not None:
            return False
        if not recesso_suspends and _is_forensic_recess_expediente_closed(day) and rito != "material_decadencial":
            return False
        return True

    def _next_business_day_after(day: date, *, check_outage: bool = False) -> date:
        cur = day + timedelta(days=1)
        while not _is_expediente_day(cur) or (check_outage and cur in outage_dates):
            cur += timedelta(days=1)
        return cur

    def _same_or_next_business_day(day: date, *, check_outage: bool = False) -> date:
        cur = day
        while not _is_expediente_day(cur) or (check_outage and cur in outage_dates):
            cur += timedelta(days=1)
        return cur

    publication_or_intimation: date | None = None
    dies_a_quo: date | None = None
    outage_applied = False

    if intimation_mode == "dje":
        # Lei 11.419/2006, art. 4º, §§ 3º e 4º: disponibilização -> publicação no 1º dia útil seguinte -> início no 1º dia útil seguinte.
        publication_or_intimation = _next_business_day_after(base_date, check_outage=False)
        raw_start = _next_business_day_after(publication_or_intimation, check_outage=False)
        dies_a_quo = _same_or_next_business_day(raw_start, check_outage=True)
        if dies_a_quo != raw_start:
            outage_applied = True

    elif intimation_mode == "portal_eletronico":
        # Lei 11.419/2006, art. 5º, §§ 1º a 3º: até 10 dias corridos da remessa, prorrogando se cair em dia não útil.
        tacit_raw = base_date + timedelta(days=10)
        tacit_date = _same_or_next_business_day(tacit_raw, check_outage=False)
        consult_raw = spec.get("consultation_date")
        if consult_raw:
            consult_d = date.fromisoformat(str(consult_raw))
            if consult_d < base_date:
                raise ValueError("consultation_date anterior à base_date")
            if consult_d <= tacit_date:
                publication_or_intimation = _same_or_next_business_day(consult_d, check_outage=False)
            else:
                publication_or_intimation = tacit_date
                warnings.append("Consulta posterior ao decêndio legal: considerada intimação tácita ao fim dos 10 dias corridos (Lei 11.419/2006, art. 5º, § 3º).")
        else:
            publication_or_intimation = tacit_date
        raw_start = _next_business_day_after(publication_or_intimation, check_outage=False)
        dies_a_quo = _same_or_next_business_day(raw_start, check_outage=True)
        if dies_a_quo != raw_start:
            outage_applied = True

    elif intimation_mode == "djen_citacao":
        # Res. CNJ 455/2022 (alt. Res. CNJ 569/2024) + CPC, arts. 231, IX e 246, §§ 1º-A a 1º-C.
        recipient_kind = str(spec.get("recipient_kind", "pj_privada")).lower().strip()
        confirm_raw = spec.get("confirmation_date") or spec.get("consultation_date")
        if recipient_kind in {"fazenda_publica", "direito_publico"}:
            tacit_window_end = _same_or_next_business_day(base_date + timedelta(days=10), check_outage=False)
            if confirm_raw:
                conf_d = date.fromisoformat(str(confirm_raw))
                if conf_d < base_date:
                    raise ValueError("confirmation_date anterior à base_date")
                publication_or_intimation = _same_or_next_business_day(conf_d, check_outage=False) if conf_d <= tacit_window_end else tacit_window_end
            else:
                publication_or_intimation = tacit_window_end
            raw_start = _next_business_day_after(publication_or_intimation, check_outage=False)
            dies_a_quo = _same_or_next_business_day(raw_start, check_outage=True)
            if dies_a_quo != raw_start:
                outage_applied = True
        elif recipient_kind == "pj_privada":
            # Janela de 3 dias úteis para confirmação expressa (CPC, art. 246, § 1º-A).
            conf_limit = base_date
            for _ in range(3):
                conf_limit = _next_business_day_after(conf_limit, check_outage=False)
            if confirm_raw:
                conf_d = date.fromisoformat(str(confirm_raw))
                if conf_d < base_date:
                    raise ValueError("confirmation_date anterior à base_date")
                if conf_d <= conf_limit:
                    publication_or_intimation = _same_or_next_business_day(conf_d, check_outage=False)
                    start_rule = spec.get("djen_confirmed_start_rule", "fifth_business_day_art231_ix")
                    if start_rule == "fifth_business_day_art231_ix":
                        cur_b = publication_or_intimation
                        for _ in range(5):
                            cur_b = _next_business_day_after(cur_b, check_outage=False)
                        raw_start = cur_b
                    elif start_rule == "next_business_day":
                        raw_start = _next_business_day_after(publication_or_intimation, check_outage=False)
                    else:
                        raise ValueError("djen_confirmed_start_rule deve ser 'fifth_business_day_art231_ix' ou 'next_business_day'")
                    dies_a_quo = _same_or_next_business_day(raw_start, check_outage=True)
                    if dies_a_quo != raw_start:
                        outage_applied = True
            if dies_a_quo is None:
                warnings.append(
                    f"Citação eletrônica (Domicílio Judicial Eletrônico) de PJ privada não confirmada em até 3 dias úteis "
                    f"(limite {conf_limit.isoformat()}): não há citação tácita para PJ privada (CPC, art. 246, § 1º-A e Res. CNJ 455/2022 / 569/2024); "
                    "necessária renovação da citação pelos meios ordinários e apresentação de justa causa na primeira oportunidade sob pena de multa de até 5% (art. 246, § 1º-C, CPC)."
                )
                return {
                    "base_date": base_date.isoformat(),
                    "rito": rito,
                    "counting_mode": counting_mode,
                    "intimation_mode": intimation_mode,
                    "recipient_kind": recipient_kind,
                    "process_medium": process_medium,
                    "base_days": base_days,
                    "multiplier": multiplier,
                    "effective_days": effective_days,
                    "confirmation_deadline": conf_limit.isoformat(),
                    "citation_confirmed": False,
                    "publication_or_effective_intimation_date": None,
                    "dies_a_quo": None,
                    "dies_ad_quem": None,
                    "audit_trail": [],
                    "warnings": warnings,
                    "legal_status": "awaiting_valid_citation_no_tacit_citation_pj_privada",
                }
        else:
            raise ValueError("recipient_kind em djen_citacao deve ser 'pj_privada' ou 'fazenda_publica'")

    else:  # in_person_or_hearing / juntada
        if rito == "material_decadencial" and not spec.get("prorrogate_start", False):
            publication_or_intimation = base_date
            dies_a_quo = base_date + timedelta(days=1)
        else:
            publication_or_intimation = _same_or_next_business_day(base_date, check_outage=False)
            raw_start = _next_business_day_after(publication_or_intimation, check_outage=False)
            dies_a_quo = _same_or_next_business_day(raw_start, check_outage=True)
            if dies_a_quo != raw_start:
                outage_applied = True

    assert dies_a_quo is not None
    counted = 0
    cur = dies_a_quo
    counting_days_map: dict[date, tuple[bool, int | None, str]] = {}

    if counting_mode == "business_days":
        while True:
            reason_non = _day_non_working_reason(cur, check_recesso_suspension=True)
            if reason_non is None:
                counted += 1
                if counted == effective_days and cur in outage_dates:
                    # O último dia útil teve indisponibilidade do sistema: conta o prazo, mas prorroga o vencimento.
                    counting_days_map[cur] = (True, counted, f"Dia útil #{counted} (indisponibilidade do sistema no termo final — prorroga)")
                    outage_applied = True
                    cur += timedelta(days=1)
                    while not _is_expediente_day(cur) or cur in outage_dates:
                        if cur in outage_dates:
                            outage_applied = True
                        r_pr = _day_non_working_reason(cur, check_recesso_suspension=True) or "Indisponibilidade do sistema eletrônico (Lei 11.419/2006, art. 10, § 2º)"
                        counting_days_map[cur] = (False, None, f"Prorrogação do vencimento: {r_pr}")
                        cur += timedelta(days=1)
                    dies_ad_quem = cur
                    counting_days_map[cur] = (False, effective_days, "Termo final prorrogado (Lei 11.419/2006, art. 10, § 2º)")
                    break
                counting_days_map[cur] = (True, counted, f"Dia útil #{counted}")
                if counted == effective_days:
                    dies_ad_quem = cur
                    break
            else:
                counting_days_map[cur] = (False, None, reason_non)
            cur += timedelta(days=1)
    else:
        # Prazo em dias corridos (CPP art. 798, Lei 11.101 art. 189 § 1º I, Eleitoral, Decadencial).
        while True:
            susp_reason = None
            for s_start, s_end, s_r in suspensions_list:
                if s_start <= cur <= s_end:
                    susp_reason = f"Suspensão: {s_r}"
                    break
            if susp_reason is None and recesso_suspends and _is_recesso_date(cur):
                susp_reason = "Suspensão de prazos no recesso forense (configuração explícita / CPP art. 798-A)"
            if susp_reason is not None:
                counting_days_map[cur] = (False, None, susp_reason)
            else:
                counted += 1
                counting_days_map[cur] = (True, counted, f"Dia corrido #{counted}")
                if counted == effective_days:
                    if not _is_expediente_day(cur) or cur in outage_dates:
                        if cur in outage_dates:
                            outage_applied = True
                        cur += timedelta(days=1)
                        while not _is_expediente_day(cur) or cur in outage_dates:
                            if cur in outage_dates:
                                outage_applied = True
                            r_pr = _day_non_working_reason(cur, check_recesso_suspension=recesso_suspends) or "Sem expediente forense / indisponibilidade do sistema"
                            counting_days_map[cur] = (False, None, f"Prorrogação do termo final: {r_pr}")
                            cur += timedelta(days=1)
                        dies_ad_quem = cur
                        counting_days_map[cur] = (False, effective_days, "Termo final prorrogado para o 1º dia útil seguinte (CPP art. 798 § 3º / CC art. 132 § 1º)")
                    else:
                        dies_ad_quem = cur
                    break
            cur += timedelta(days=1)

    if outage_applied:
        warnings.append(
            "Prorrogação por indisponibilidade do sistema eletrônico aplicada (Lei 11.419/2006, art. 10, § 2º e Res. CNJ 185/2013): "
            "juntar certidão oficial de indisponibilidade do tribunal no ato do protocolo; eventual ausência da certidão "
            "enseja intimação prévia para regularização nos termos do art. 1.003, § 6º, do CPC (Lei 14.939/2024)."
        )

    audit_trail: list[dict] = []
    step = base_date
    while step <= dies_ad_quem:
        is_bus = _is_expediente_day(step) and step not in outage_dates
        if step < dies_a_quo:
            if step == base_date and step == publication_or_intimation:
                reason = "Data-base / intimação efetiva (exclui-se o dia do começo — CPC, art. 224)"
            elif step == base_date:
                reason = f"Data-base ({intimation_mode})"
            elif step == publication_or_intimation:
                reason = "Data considerada como publicação / intimação efetiva"
            elif step in outage_dates:
                reason = "Indisponibilidade do sistema eletrônico no início do prazo (Lei 11.419/2006, art. 10, § 2º)"
            else:
                reason = _day_non_working_reason(step, check_recesso_suspension=True) or "Aguardando aperfeiçoamento da intimação / início do prazo"
            audit_trail.append({
                "date": step.isoformat(),
                "weekday": WEEKDAY_NAMES_PT[step.weekday()],
                "is_business_day": is_bus,
                "counted": False,
                "day_count": None,
                "reason": reason,
            })
        else:
            was_counted, d_num, d_reason = counting_days_map[step]
            audit_trail.append({
                "date": step.isoformat(),
                "weekday": WEEKDAY_NAMES_PT[step.weekday()],
                "is_business_day": is_bus,
                "counted": was_counted,
                "day_count": d_num,
                "reason": d_reason,
            })
        step += timedelta(days=1)

    return {
        "base_date": base_date.isoformat(),
        "rito": rito,
        "counting_mode": counting_mode,
        "intimation_mode": intimation_mode,
        "process_medium": process_medium,
        "base_days": base_days,
        "multiplier": multiplier,
        "effective_days": effective_days,
        "publication_or_effective_intimation_date": publication_or_intimation.isoformat() if publication_or_intimation else None,
        "dies_a_quo": dies_a_quo.isoformat(),
        "dies_ad_quem": dies_ad_quem.isoformat(),
        "audit_trail": audit_trail,
        "warnings": warnings,
        "legal_status": "deterministic_deadline_calculation_verify_local_court_calendar",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calculadora determinística de prazos processuais brasileiros")
    parser.add_argument("--input", type=Path, help="Arquivo JSON de especificação para calculate_deadline")
    parser.add_argument("--holidays-year", type=int, help="Lista os feriados nacionais calculados para o ano informado")
    args = parser.parse_args(argv)
    try:
        if args.holidays_year is not None:
            hols = {k.isoformat(): v for k, v in national_holidays(args.holidays_year).items()}
            print(json.dumps({"year": args.holidays_year, "easter_sunday": easter_sunday(args.holidays_year).isoformat(),
                              "holidays": hols}, ensure_ascii=False, indent=2))
            return 0
        if args.input:
            spec = json.loads(args.input.read_text(encoding="utf-8"))
        elif not sys.stdin.isatty():
            spec = json.loads(sys.stdin.read())
        else:
            parser.error("Informe --input ARQUIVO.json ou --holidays-year ANO")
            return 2
        result = calculate_deadline(spec)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
