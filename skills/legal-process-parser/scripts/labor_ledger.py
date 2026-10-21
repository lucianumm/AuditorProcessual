"""Reconcile attributed daily marks and payroll; rules are supplied, never inferred."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

try:
    from .contracts import validate_contract
    from .labor_calculations import decimal_value
    from .labor_time import parse_datetime
except ImportError:
    from contracts import validate_contract
    from labor_calculations import decimal_value
    from labor_time import parse_datetime


MINUTE_STEP = Decimal("0.0001")


def minutes(delta: timedelta) -> Decimal:
    return (Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / 1000000) / 60


def q(value: Decimal) -> Decimal:
    """Minutes kept to 1/10000; avoids residues such as 1E-25 in weekly sums."""
    return value.quantize(MINUTE_STEP, rounding=ROUND_HALF_UP)


def fmt(value: Decimal | None) -> str | None:
    if value is None:
        return None
    text = format(q(value), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def workplace_zone(rule: dict | None):
    offset = (rule or {}).get("workplace_utc_offset")
    if not offset:
        return None
    sign = 1 if offset[0] == "+" else -1
    hours, mins = int(offset[1:3]), int(offset[4:6])
    return timezone(sign * timedelta(hours=hours, minutes=mins))


def night_minutes(start: datetime, end: datetime, window: dict | None) -> Decimal:
    if not window:
        return Decimal(0)
    if start.utcoffset() != end.utcoffset():
        raise ValueError("Contagem noturna com mudança de offset exige intervalos separados no marco")
    lower, upper = time.fromisoformat(window["start"]), time.fromisoformat(window["end"])
    if lower == upper:
        raise ValueError("Janela noturna não pode ter início igual ao fim")
    total = Decimal(0)
    current = start.date() - timedelta(days=1)
    # The caller caps individual intervals; no unbounded expansion.
    while current <= end.date():
        left = datetime.combine(current, lower, tzinfo=start.tzinfo)
        right = datetime.combine(current + timedelta(days=upper < lower), upper, tzinfo=start.tzinfo)
        overlap = min(end, right) - max(start, left)
        if overlap > timedelta(0):
            total += minutes(overlap)
        # Supplied extension rule: whole window worked and continued in the same interval.
        if window.get("extension") == "after_full_window" and start <= left and end > right:
            total += minutes(end - right)
        current += timedelta(days=1)
    return total


def reconcile_payroll(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    payment_ids = {}
    seen_ids = set()
    for row in rows:
        if row["id"] in seen_ids:
            raise ValueError("ID de rubrica duplicado")
        seen_ids.add(row["id"])
        date.fromisoformat(row["competence"] + "-01")
        amount = decimal_value(row["amount"])
        if amount < 0:
            raise ValueError("Valor de folha não pode ser negativo")
        key = (row["relationship_id"], row["competence"], row["rubric"])
        if row["kind"] in {"payment", "payment_confirmation"} and not row.get("payment_id"):
            raise ValueError("Pagamento precisa de identificador para evitar abatimento repetido")
        if row["kind"] == "payment":
            pid = (row["relationship_id"], row["payment_id"])
            if pid in payment_ids:
                raise ValueError("Mesmo pagamento contado em mais de uma rubrica; registrar alocações distintas comprovadas")
            payment_ids[pid] = row
        groups[key].append(row)
    results = []
    for key, items in sorted(groups.items()):
        due = [r for r in items if r["kind"] == "due"]
        paid = [r for r in items if r["kind"] == "payment"]
        salaries = [r for r in items if r["kind"] == "salary_parameter"]
        earned = sum((decimal_value(r["amount"]) for r in due), Decimal(0))
        payments = sum((decimal_value(r["amount"]) for r in paid), Decimal(0))
        confirmations = []
        for row in items:
            if row["kind"] != "payment_confirmation":
                continue
            target = payment_ids.get((row["relationship_id"], row["payment_id"]))
            agrees = bool(target and target["competence"] == row["competence"] and target["rubric"] == row["rubric"]
                          and decimal_value(target["amount"]) == decimal_value(row["amount"]))
            confirmations.append({"id": row["id"], "status": "agrees" if agrees else "unmatched_or_conflicting",
                                  "counted_again": False})
        results.append({"relationship_id": key[0], "competence": key[1], "rubric": key[2],
                        "due_recorded": str(earned) if due else None, "payments_recorded": str(payments) if paid else None,
                        "difference_recorded": str(earned - payments) if due and paid else None,
                        "salary_values": sorted({str(decimal_value(r["amount"])) for r in salaries}),
                        "salary_conflict": len({decimal_value(r["amount"]) for r in salaries}) > 1,
                        "payment_confirmations": confirmations,
                        "fact_ids": sorted({f for r in items for f in r["fact_ids"]}),
                        "origin": "client_estimate" if any(r["origin"] == "client" for r in items) else "document_records",
                        "status": "arithmetic_comparison_only"})
    return results


def apportion_workdays(payload: dict) -> dict:
    errors = validate_contract(payload, "labor_ledger.schema.json")
    if errors:
        raise ValueError("; ".join(errors))
    rules, days = payload["rules"], payload["days"]
    if len({r["id"] for r in rules}) != len(rules):
        raise ValueError("Regra de jornada duplicada")
    for rule in rules:
        if rule["period_start"] > rule["period_end"]:
            raise ValueError("Vigência da regra invertida")
        if decimal_value(rule["daily_limit_minutes"]) <= 0 or decimal_value(rule["weekly_limit_minutes"]) <= 0:
            raise ValueError("Limites de jornada devem ser positivos")
        if rule["night_reduction"] and (not rule["night_window"] or decimal_value(rule["night_window"]["unit_minutes"]) <= 0):
            raise ValueError("Redução noturna exige janela e unidade positivas fornecidas")
        if rule.get("intrajornada") and (decimal_value(rule["intrajornada"]["threshold_minutes"]) <= 0
                                         or decimal_value(rule["intrajornada"]["min_break_minutes"]) <= 0):
            raise ValueError("Parâmetros de intervalo intrajornada devem ser positivos e fundamentados")
        if rule.get("interjornada_min_minutes") and decimal_value(rule["interjornada_min_minutes"]) <= 0:
            raise ValueError("Intervalo interjornada mínimo deve ser positivo")
    known, seen_ids, intervals_by_relation = set(), set(), defaultdict(list)
    observed, weekly = [], defaultdict(list)
    last_end = {}
    for row in days:
        key = (row["relationship_id"], row["date"])
        if row["id"] in seen_ids or key in known:
            raise ValueError("Dia duplicado para a mesma relação")
        known.add(key); seen_ids.add(row["id"])
        work_date = date.fromisoformat(row["date"])
        applicable = [r for r in rules if r["relationship_id"] == row["relationship_id"]
                      and r["period_start"] <= row["date"] <= r["period_end"]]
        if len(applicable) > 1:
            raise ValueError("Regras de jornada concorrentes; selecionar critério fundamentado por período")
        worked_status = row["day_status"] in {"worked", "rest_day_worked"}
        if not worked_status and row["intervals"]:
            raise ValueError("Descanso/afastamento/desconhecido não pode ter trabalho declarado sem resolver conflito")
        if worked_status and not row["intervals"]:
            raise ValueError("Dia trabalhado sem intervalos; esclarecer marcações ou relato específico")
        physical, night = Decimal(0), Decimal(0)
        spans = []
        rule = applicable[0] if applicable else None
        zone = workplace_zone(rule)
        for interval in row["intervals"]:
            start, end = parse_datetime(interval["start"]), parse_datetime(interval["end"])
            if start.utcoffset() is None or end.utcoffset() is None:
                raise ValueError("Marcações exigem offsets explícitos")
            if zone is not None:
                # Night window and shift date follow the workplace clock, not the offset typed in the record.
                start, end = start.astimezone(zone), end.astimezone(zone)
            left, right = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
            if right <= left or right - left > timedelta(days=2):
                raise ValueError("Intervalo invertido ou excessivo")
            if start.date() < work_date or start.date() > work_date + timedelta(days=1):
                raise ValueError("Marcação fora da data atribuída ao turno")
            spans.append((left, right))
            physical += minutes(right - left)
            night += night_minutes(start, end, rule["night_window"] if rule else None)
        physical, night = q(physical), q(night)
        ordered = sorted(spans)
        break_minutes = q(sum((minutes(b[0] - a[1]) for a, b in zip(ordered, ordered[1:])), Decimal(0))) if ordered else None
        for left, right in spans:
            if any(left < previous_right and previous_left < right for previous_left, previous_right in intervals_by_relation[row["relationship_id"]]):
                raise ValueError("Intervalos sobrepostos para a mesma relação")
            intervals_by_relation[row["relationship_id"]].append((left, right))
        legal = physical
        if rule and rule["night_reduction"]:
            legal = q(physical - night + night * 60 / decimal_value(rule["night_window"]["unit_minutes"]))
        usable = rule is not None and row["day_status"] != "unknown"
        rest_work = row["day_status"] == "rest_day_worked"
        basis = (legal if rule and rule["limit_basis"] == "legal" else physical)
        daily = max(Decimal(0), basis - decimal_value(rule["daily_limit_minutes"])) if usable and not rest_work else None
        if usable and rest_work:
            daily = Decimal(0)
        result = {"id": row["id"], "relationship_id": row["relationship_id"], "date": row["date"],
                  "physical_minutes": fmt(physical) if row["day_status"] != "unknown" else None,
                  "night_minutes": fmt(night) if usable else None, "legal_minutes": fmt(legal) if usable else None,
                  "daily_excess_minutes": fmt(daily) if daily is not None else None,
                  "rule_id": rule["id"] if rule else None, "fact_ids": row["fact_ids"],
                  "origin": row["origin"], "status": "computed_from_supplied_rule" if usable else "pending_rule_or_day"}
        if rest_work:
            # Work on a weekly rest day or holiday is a separate rubric; it never enters the weekly limit here.
            result["rest_day_work_minutes"] = fmt(basis) if usable else None
        if break_minutes is not None and worked_status:
            result["break_minutes"] = fmt(break_minutes)
            intra = (rule or {}).get("intrajornada")
            if intra and usable:
                due = decimal_value(intra["min_break_minutes"]) if physical > decimal_value(intra["threshold_minutes"]) else Decimal(0)
                result["intrajornada_shortfall_minutes"] = fmt(max(Decimal(0), due - break_minutes))
        if worked_status and spans:
            last_end[(row["relationship_id"], row["date"])] = (min(s[0] for s in spans), max(s[1] for s in spans), result, rule)
        observed.append(result)
        if usable and not rest_work:
            week_start = work_date - timedelta(days=(work_date.weekday() - rule["week_start"]) % 7)
            weekly[(row["relationship_id"], week_start.isoformat(), rule["id"])].append((result, basis, daily))
    by_relation = defaultdict(list)
    for (relation, _), value in last_end.items():
        by_relation[relation].append(value)
    for shifts in by_relation.values():
        shifts.sort(key=lambda item: item[0])
        for previous, current in zip(shifts, shifts[1:]):
            gap = minutes(current[0] - previous[1])
            if gap <= 0 or gap > 48 * 60:
                continue
            current[2]["interjornada_gap_minutes"] = fmt(gap)
            minimum = (current[3] or {}).get("interjornada_min_minutes")
            if minimum:
                current[2]["interjornada_shortfall_minutes"] = fmt(max(Decimal(0), decimal_value(minimum) - gap))
    weeks = []
    for (relation, start, rule_id), rows in sorted(weekly.items()):
        rule = next(r for r in rules if r["id"] == rule_id)
        subtotal = sum((r[1] for r in rows), Decimal(0))
        daily_total = sum((r[2] for r in rows), Decimal(0))
        extra = max(Decimal(0), subtotal - decimal_value(rule["weekly_limit_minutes"]) - daily_total)
        dates = {r[0]["date"] for r in rows}
        expected = {(date.fromisoformat(start) + timedelta(days=day)).isoformat() for day in range(7)}
        weeks.append({"relationship_id": relation, "week_start": start, "rule_id": rule_id,
                      "daily_excess_minutes": fmt(daily_total), "additional_weekly_minutes": fmt(extra),
                      "total_excess_without_double_count": fmt(daily_total + extra),
                      "coverage": "complete" if dates == expected else "partial",
                      "unrepresented_dates": sorted(expected - dates),
                      "meaning": "Critério diário seguido do semanal, conforme parâmetros fornecidos; semana parcial não comprova ausência de outras horas."})
    week_rules = defaultdict(set)
    for week in weeks:
        week_rules[(week["relationship_id"], week["week_start"])].add(week["rule_id"])
    for week in weeks:
        if len(week_rules[(week["relationship_id"], week["week_start"])]) > 1:
            week.update(additional_weekly_minutes=None, total_excess_without_double_count=None,
                        coverage="mixed_rules_requires_review",
                        meaning="Mudança de regra na mesma semana: selecionar o critério semanal global; não reiniciar automaticamente o limite por segmento.")
    criteria = payload.get("weekly_criteria", [])
    if len({c["id"] for c in criteria}) != len(criteria) or len({(c["relationship_id"], c["week_start"]) for c in criteria}) != len(criteria):
        raise ValueError("Critério semanal global duplicado")
    for criterion in criteria:
        relation, start = criterion["relationship_id"], criterion["week_start"]
        date.fromisoformat(start)
        members = [w for w in weeks if w["relationship_id"] == relation and w["week_start"] == start]
        rule_ids = {w["rule_id"] for w in members}
        selected_rules = [r for r in rules if r["id"] in rule_ids]
        if not members or rule_ids != set(criterion["rule_ids"]):
            raise ValueError("Critério global precisa selecionar exatamente as regras da semana")
        if any(r["week_start"] != date.fromisoformat(start).weekday() or r["limit_basis"] != criterion["limit_basis"] for r in selected_rules):
            raise ValueError("Semana global exige mesmo início e base; resolver a transição antes de calcular")
        # A shifted week boundary must not include the same day in another week.
        end = (date.fromisoformat(start) + timedelta(days=6)).isoformat()
        affected = [d for d in observed if d["relationship_id"] == relation and start <= d["date"] <= end]
        if any(d["rule_id"] not in rule_ids for d in affected if d["status"] == "computed_from_supplied_rule"):
            raise ValueError("Semana com limites de início concorrentes; conferir critério antes de somar")
        rows = [d for d in affected if d["status"] == "computed_from_supplied_rule" and "rest_day_work_minutes" not in d]
        limit = decimal_value(criterion["weekly_limit_minutes"])
        if limit <= 0:
            raise ValueError("Limite semanal global deve ser positivo")
        subtotal = sum((decimal_value(d[criterion["limit_basis"] + "_minutes"]) for d in rows), Decimal(0))
        daily_total = sum((decimal_value(d["daily_excess_minutes"]) for d in rows), Decimal(0))
        extra = max(Decimal(0), subtotal - limit - daily_total)
        expected = {(date.fromisoformat(start) + timedelta(days=i)).isoformat() for i in range(7)}
        dates = {d["date"] for d in rows}
        weeks = [w for w in weeks if w not in members]
        weeks.append({"relationship_id": relation, "week_start": start, "rule_id": None, "rule_ids": sorted(rule_ids),
                      "criterion_id": criterion["id"], "norm_ids": criterion["norm_ids"], "reason": criterion["reason"],
                      "daily_excess_minutes": fmt(daily_total), "additional_weekly_minutes": fmt(extra),
                      "total_excess_without_double_count": fmt(daily_total + extra),
                      "coverage": "complete" if dates == expected else "partial", "unrepresented_dates": sorted(expected - dates),
                      "meaning": "Limite global fornecido; excessos diários deduzidos uma vez e preservados por regra de origem."})
    weeks.sort(key=lambda w: (w["relationship_id"], w["week_start"], w.get("rule_id") or ""))
    return {"schema_version": "1.0", "days": observed, "weeks": weeks,
            "payroll": reconcile_payroll(payload["payroll"]),
            "status": "partial" if any(r["status"].startswith("pending") for r in observed) or any(w["coverage"] != "complete" for w in weeks) else "computed",
            "legal_status": "supplied_rules_not_legal_certification"}


def ledger_markdown(result: dict) -> str:
    try:
        from .legal_index import safe_text
    except ImportError:
        from legal_index import safe_text
    lines = ["# CONCILIAÇÃO DE JORNADA E FOLHA", "", "Parâmetros e origens declarados; enquadramento depende das fontes do caso.", ""]
    for day in result["days"]:
        lines += [f"- {safe_text(day['relationship_id'])} · {day['date']}: {day['physical_minutes']} minutos físicos; excesso diário {day['daily_excess_minutes']}; origem {day['origin']}; {day['status']}. Fontes: " + ", ".join(safe_text(f) for f in day["fact_ids"])]
    for week in result["weeks"]:
        lines += ["", f"Semana {week['week_start']} · {safe_text(week['relationship_id'])}: {week['total_excess_without_double_count']} minutos de excesso pelo critério fornecido; cobertura {week['coverage']}."]
    for row in result["payroll"]:
        lines += ["", f"{safe_text(row['relationship_id'])} · {row['competence']} · {safe_text(row['rubric'])}: devido registrado {row['due_recorded']}; pagamento registrado {row['payments_recorded']}; diferença comparável {row['difference_recorded']}. Origem: {row['origin']}."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apura marcações e concilia folha com regras atribuídas; sem taxas universais")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(apportion_workdays(json.loads(args.input.read_text(encoding="utf-8-sig"))), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
