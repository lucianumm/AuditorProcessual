"""Reconcile attributed time-bank movements; no automatic finding of validity."""
from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

try:
    from .contracts import validate_contract
    from .labor_calculations import decimal_value
except ImportError:
    from contracts import validate_contract
    from labor_calculations import decimal_value


def reconcile_bank(payload: dict) -> dict:
    errors = validate_contract(payload, "time_bank.schema.json")
    if errors:
        raise ValueError("; ".join(errors))
    as_of = date.fromisoformat(payload["as_of"])
    rows = payload["movements"]
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Movimento duplicado")
    credits, used, findings = {}, {}, []
    for row in rows:
        amount = decimal_value(row["minutes"])
        if amount <= 0 or date.fromisoformat(row["date"]) > as_of:
            raise ValueError("Movimento precisa de quantidade positiva e data até o limite analisado")
        if row["kind"] == "credit":
            if row["allocations"] or row["expires_on"] and row["expires_on"] < row["date"]:
                raise ValueError("Crédito com alocação ou vencimento incoerente")
            credits[row["id"]], used[row["id"]] = row, Decimal(0)
        elif row["expires_on"] is not None:
            raise ValueError("Débito não define vencimento de crédito")
    for row in rows:
        if row["kind"] != "debit":
            continue
        total = Decimal(0)
        allocated = set()
        for allocation in row["allocations"]:
            cid = allocation["credit_id"]
            credit = credits.get(cid)
            if cid in allocated or not credit or credit["relationship_id"] != row["relationship_id"] or credit["date"] > row["date"]:
                raise ValueError("Alocação duplicada, inexistente, anterior ao crédito ou de outra relação")
            allocated.add(cid)
            amount = decimal_value(allocation["minutes"])
            if amount <= 0:
                raise ValueError("Alocação precisa de quantidade positiva")
            total += amount
            used[cid] += amount
            if used[cid] > decimal_value(credit["minutes"]):
                raise ValueError("Mesmo crédito consumido além do saldo")
            if credit["expires_on"] and row["date"] > credit["expires_on"]:
                findings.append({"debit_id": row["id"], "credit_id": cid, "cause": "allocation_after_supplied_expiry"})
        if total != decimal_value(row["minutes"]):
            raise ValueError("Débito precisa corresponder às alocações identificadas")
    balances = [{"credit_id": cid, "relationship_id": row["relationship_id"],
                 "remaining_minutes": str(decimal_value(row["minutes"]) - used[cid]),
                 "expired_under_supplied_date": bool(row["expires_on"] and row["expires_on"] < payload["as_of"]),
                 "fact_ids": row["fact_ids"], "norm_ids": row["norm_ids"]} for cid, row in credits.items()]
    return {"schema_version": "1.0", "as_of": payload["as_of"], "balances": balances, "findings": findings,
            "status": "requires_review" if findings else "reconciled_from_supplied_records",
            "legal_status": "validity_and_legal_consequences_require_case_analysis"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Concilia créditos e compensações efetivamente registrados")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(reconcile_bank(json.loads(args.input.read_text(encoding="utf-8-sig"))), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
