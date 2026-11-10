"""Count supplied clock intervals and calendars; the host selects legal rules."""
from __future__ import annotations

import argparse
import json
import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

LEAP_POLICIES = {"last_valid_day", "next_day", "strict"}


def parse_datetime(value: str) -> datetime:
    """ISO timestamp; a trailing Z is accepted on every supported Python version."""
    if not isinstance(value, str):
        raise ValueError("Marcação deve ser texto ISO com offset")
    return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)


def count_date_window(record: dict) -> dict:
    """Calendar operation for a supplied limitation rule, not a legal classification."""
    anchor = date.fromisoformat(record["anchor_date"])
    quantity = record["quantity"]
    if type(quantity) is not int or not 1 <= quantity <= 10000 or record["direction"] not in {"forward", "backward"}:
        raise ValueError("Janela exige quantidade e direção explícitas")
    sign = 1 if record["direction"] == "forward" else -1
    if record["leap_policy"] not in LEAP_POLICIES:
        raise ValueError("Definir tratamento de dia inexistente no mês/ano de destino (last_valid_day, next_day ou strict)")
    if record["unit"] == "days":
        result = anchor + timedelta(days=sign * quantity)
    elif record["unit"] in {"months", "years"}:
        months = quantity * (12 if record["unit"] == "years" else 1)
        absolute = anchor.year * 12 + anchor.month - 1 + sign * months
        year, month0 = divmod(absolute, 12)
        month = month0 + 1
        last = calendar.monthrange(year, month)[1]
        if anchor.day > last and record["leap_policy"] == "strict":
            raise ValueError("Dia inexistente no destino; confirmar regra aplicável")
        if anchor.day > last and record["leap_policy"] == "next_day":
            # Civil-law month/year counting: without an equal day, the term ends on the following day.
            result = date(year, month, last) + timedelta(days=1)
        else:
            result = date(year, month, min(anchor.day, last))
    else:
        raise ValueError("Unidade de janela desconhecida")
    for adjustment in record.get("adjustments", []):
        if type(adjustment.get("days")) is not int or abs(adjustment["days"]) > 100000 or not adjustment.get("fact_ids") or not adjustment.get("norm_ids") or not adjustment.get("reason"):
            raise ValueError("Ajuste exige dias, fatos, normas e fundamento específicos")
        result += timedelta(days=adjustment["days"])
    if record.get("expected_date") and record["expected_date"] != result.isoformat():
        raise ValueError("Marco informado diverge da janela e ajustes fornecidos")
    return {"date": result.isoformat(), "anchor_date": anchor.isoformat(),
            "status": "counted_from_supplied_rule_not_prescription_judgment"}


def working_day(record: dict) -> dict:
    start = parse_datetime(record["clock_in"])
    end = parse_datetime(record["clock_out"])
    if start.utcoffset() is None or end.utcoffset() is None:
        raise ValueError("Marcações exigem data, hora e offset; não presumir fuso ou mudança de dia")
    delta = end.astimezone(timezone.utc) - start.astimezone(timezone.utc)
    seconds = Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / 1000000
    rest = record["break_minutes"]
    if type(rest) is not int or rest < 0 or seconds <= 0 or rest * 60 > seconds:
        raise ValueError("Marcações/intervalos incompatíveis; conferir o original")
    if not record.get("fact_ids"):
        raise ValueError("Marcações devem apontar para fatos e fontes")
    minutes = (seconds / 60 - rest).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if record.get("expected_minutes") is not None and Decimal(str(record["expected_minutes"])).quantize(Decimal("0.0001")) != minutes:
        raise ValueError("Minutos informados divergem das marcações")
    show = lambda value: format(value, "f").rstrip("0").rstrip(".") if "." in format(value, "f") else format(value, "f")
    return {"worked_minutes":show(minutes),"worked_hours":show((minutes / 60).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "calendar_start":start.date().isoformat(),"calendar_end":end.date().isoformat(),
            "status":"elapsed_time_only","fact_ids":record["fact_ids"],
            "legal_counting_note":"Hora reduzida, tolerância, tempo à disposição e adicionais dependem do enquadramento registrado."}


def count_deadline(record: dict) -> dict:
    event = date.fromisoformat(record["event_date"])
    days = record["days"]
    if type(days) is not int or not 1 <= days <= 10000 or type(record["include_event_day"]) is not bool:
        raise ValueError("Quantidade de dias e inclusão/exclusão do marco devem ser explícitas")
    if record["mode"] not in {"business", "calendar"} or not record.get("trigger_fact_id") or not record.get("norm_id"):
        raise ValueError("Prazo exige regra, fato desencadeador e modo de contagem")
    if not record.get("jurisdiction"):
        raise ValueError("Identificar o órgão/território do calendário")
    if record["mode"] == "business" and not record.get("calendar_norm_ids"):
        raise ValueError("Contagem em dias úteis exige calendário oficial vinculado")
    holidays = {date.fromisoformat(value) for value in record.get("holidays", [])}
    suspensions = []
    for item in record.get("suspensions", []):
        start, end = date.fromisoformat(item["start"]), date.fromisoformat(item["end"])
        if start > end or not item.get("norm_id"):
            raise ValueError("Suspensão sem intervalo/regra válidos")
        suspensions.append((start,end))
    current = event if record["include_event_day"] else event + timedelta(days=1)
    counted, skipped = [], []
    for _ in range(73000):
        reason = ""
        if any(start <= current <= end for start,end in suspensions):
            reason = "suspension"
        elif record["mode"] == "business" and current.weekday() >= 5:
            reason = "weekend"
        elif record["mode"] == "business" and current in holidays:
            reason = "holiday"
        if reason:
            skipped.append({"date":current.isoformat(),"reason":reason})
        else:
            counted.append(current.isoformat())
            if len(counted) == days:
                break
        current += timedelta(days=1)
    else:
        raise ValueError("Calendário excessivo; conferir suspensões e quantidade")
    due, shifted_from = counted[-1], None
    if record.get("shift_to_business_day"):
        # Calendar-day terms ending on a non-business day move only under a supplied rule and calendar.
        if record["mode"] != "calendar" or not record.get("calendar_norm_ids"):
            raise ValueError("Prorrogação do vencimento exige contagem corrida e calendário oficial vinculado")
        current = date.fromisoformat(due)
        for _ in range(366):
            if current.weekday() < 5 and current not in holidays and not any(a <= current <= b for a, b in suspensions):
                break
            current += timedelta(days=1)
        else:
            raise ValueError("Calendário sem dia útil em um ano; conferir suspensões")
        if current.isoformat() != due:
            shifted_from, due = due, current.isoformat()
    if record.get("expected_due_date") and record["expected_due_date"] != due:
        raise ValueError("Vencimento informado diverge do calendário fornecido")
    return {"due_date":due,"shifted_from":shifted_from,"counted_days":counted,"skipped_days":skipped,
            "status":"counted_from_supplied_calendar","jurisdiction":record["jurisdiction"],
            "trigger_fact_id":record["trigger_fact_id"],"norm_id":record["norm_id"],
            "calendar_norm_ids":record.get("calendar_norm_ids",[])}


def main() -> int:
    parser = argparse.ArgumentParser(description="Confere duração e calendário a partir de fontes/parâmetros informados")
    parser.add_argument("mode",choices=["workday","deadline","window"])
    parser.add_argument("input",type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = {"workday": working_day, "deadline": count_deadline, "window": count_date_window}[args.mode](record)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,OverflowError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
