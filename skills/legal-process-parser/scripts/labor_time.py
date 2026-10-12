"""Count supplied clock intervals and calendars; the host selects legal rules."""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path


def working_day(record: dict) -> dict:
    start = datetime.fromisoformat(record["clock_in"])
    end = datetime.fromisoformat(record["clock_out"])
    if start.utcoffset() is None or end.utcoffset() is None:
        raise ValueError("Marcações exigem data, hora e offset; não presumir fuso ou mudança de dia")
    delta = end.astimezone(timezone.utc) - start.astimezone(timezone.utc)
    seconds = Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / 1000000
    rest = record["break_minutes"]
    if type(rest) is not int or rest < 0 or seconds <= 0 or rest * 60 > seconds:
        raise ValueError("Marcações/intervalos incompatíveis; conferir o original")
    if not record.get("fact_ids"):
        raise ValueError("Marcações devem apontar para fatos e fontes")
    minutes = seconds / 60 - rest
    if record.get("expected_minutes") is not None and Decimal(str(record["expected_minutes"])) != minutes:
        raise ValueError("Minutos informados divergem das marcações")
    return {"worked_minutes":str(minutes),"worked_hours":str(minutes / 60),
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
    if record.get("expected_due_date") and record["expected_due_date"] != counted[-1]:
        raise ValueError("Vencimento informado diverge do calendário fornecido")
    return {"due_date":counted[-1],"counted_days":counted,"skipped_days":skipped,
            "status":"counted_from_supplied_calendar","jurisdiction":record["jurisdiction"],
            "trigger_fact_id":record["trigger_fact_id"],"norm_id":record["norm_id"],
            "calendar_norm_ids":record.get("calendar_norm_ids",[])}


def main() -> int:
    parser = argparse.ArgumentParser(description="Confere duração e calendário a partir de fontes/parâmetros informados")
    parser.add_argument("mode",choices=["workday","deadline"])
    parser.add_argument("input",type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = working_day(record) if args.mode == "workday" else count_deadline(record)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,OverflowError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
