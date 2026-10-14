"""Check factual quantities, official numeric criteria and actual arithmetic.

Numeric transformations are deterministic. Applicability and meaning of the
quoted criterion remain attributed legal interpretation, not machine proof.
"""
from __future__ import annotations

import argparse
import calendar
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

try:
    from .contracts import validate_contract
    from .labor_calculations import compute_calculations, decimal_value
except ImportError:
    from contracts import validate_contract
    from labor_calculations import compute_calculations, decimal_value


def transform(value: str, method: str) -> Decimal:
    amount = decimal_value(value)
    operations = {"identity": lambda n: n, "percent_to_fraction": lambda n: n / 100,
                  "percent_to_factor": lambda n: 1 + n / 100, "minutes_to_hours": lambda n: n / 60}
    if method not in operations:
        raise ValueError("Transformação numérica desconhecida")
    return operations[method](amount)


def numbers_in_excerpt(text: str) -> set[Decimal]:
    found = set()
    for match in re.findall(r"(?<!\w)-?\d+(?:[.,]\d+)*(?!\w)", text):
        normalized = match.replace(".", "").replace(",", ".") if "," in match else match.replace(".", "") if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", match) else match
        try:
            found.add(decimal_value(normalized))
        except ValueError:
            continue
    return found


def select_calculations(payload: dict, request_ids: set[str], checks: dict) -> dict:
    """Project the requested parcels and their dependency closure, not all claims."""
    items = {r["id"]: r for r in payload["items"]}
    inputs = {r["id"]: r for r in payload["inputs"]}
    rows = {r["input_id"]: r for r in checks.get("inputs", [])}
    selected = {iid for iid, row in items.items() if set(row["request_ids"]) & request_ids}
    needed = set(selected)
    queue = list(selected)
    while queue:
        key = queue.pop()
        row = items.get(key) or rows.get(key, {})
        for dependency in row.get("bindings", {}).values():
            if dependency not in items and dependency not in inputs:
                raise ValueError("Parcela/parâmetro dependente desconhecido: " + dependency)
            if dependency not in needed:
                needed.add(dependency)
                queue.append(dependency)
    return dict(payload, inputs=[r for r in payload["inputs"] if r["id"] in needed],
                items=[dict(r, include_in_total=r["include_in_total"] and r["id"] in selected)
                       for r in payload["items"] if r["id"] in needed])


def review_parameters(payload: dict, checks: dict, review: dict, citations: list[dict], source_texts: dict) -> dict:
    errors = validate_contract(checks, "labor_parameters.schema.json")
    result = {"errors": errors, "arithmetic_status": "not_run", "legal_applicability": "host_authored_not_machine_certified"}
    if errors:
        return result
    if payload["corpus_revision"] != review["corpus_revision"]:
        errors.append("Parâmetros pertencem a outra revisão do caso")
    inputs = {r["id"]: r for r in payload["inputs"]}
    rows = {r["input_id"]: r for r in checks["inputs"]}
    if len(rows) != len(checks["inputs"]) or set(rows) != set(inputs):
        errors.append("Conferir cada parâmetro exatamente uma vez")
    atoms = {r["fact_id"]: r["atoms"] for r in review.get("assertion_reviews", [])}
    mappings = {r["norm_id"]: r for r in review.get("normative_map", [])}
    periods = {r["id"]: r for r in review.get("labor_review", {}).get("contract_periods", [])}
    dependencies = {iid: set(r["bindings"].values()) if r["basis"] == "derived" else set() for iid, r in rows.items()}
    settled = set()
    while True:
        progress = {iid for iid, deps in dependencies.items() if deps <= settled} - settled
        if not progress:
            break
        settled |= progress
    if settled != set(rows):
        errors.append("Derivação circular ou origem não conferida entre parâmetros")
    for iid, row in rows.items():
        parameter = inputs.get(iid)
        if not parameter:
            continue
        try:
            if transform(row["source_value"], row["transform"]) != decimal_value(parameter["value"]):
                errors.append(iid + ": valor diverge da origem e da transformação fornecidas")
            if row["basis"] == "fact":
                if not row["fact_id"] or row["fact_id"] not in parameter["fact_ids"]:
                    errors.append(iid + ": dado do caso sem fato correspondente")
                field = atoms.get(row["fact_id"], {}).get(row["fact_field"])
                if field is None or decimal_value(field) != decimal_value(row["source_value"]):
                    errors.append(iid + ": quantidade diverge do campo factual reconferido")
                if row["norm_id"] or row["source_record_id"]:
                    errors.append(iid + ": separar origem factual do critério normativo")
            elif row["basis"] == "legal_rule":
                matching = [c for c in citations if c["norm_id"] == row["norm_id"] and c["source_record_id"] == row["source_record_id"]]
                if row["norm_id"] not in parameter["norm_ids"] or not matching or row["quote"] not in source_texts.get(row["source_record_id"], ""):
                    errors.append(iid + ": critério numérico sem trecho oficial consultado para a resposta")
                if decimal_value(row["source_value"]) not in numbers_in_excerpt(row["quote"]):
                    errors.append(iid + ": número do critério ausente do trecho literal")
                if row["fact_id"] or row["fact_field"]:
                    errors.append(iid + ": critério normativo não pode fingir dado factual")
                mapping = mappings.get(row["norm_id"], {})
                if mapping.get("temporal_status") != "applicable" or not mapping.get("effective_from") or row["effective_from"] < mapping["effective_from"] or mapping.get("effective_until") and (not row["effective_until"] or row["effective_until"] > mapping["effective_until"]):
                    errors.append(iid + ": período ou aplicabilidade diverge do mapa normativo conferido")
            else:
                if not row["expression"] or not row["bindings"]:
                    errors.append(iid + ": parâmetro derivado exige expressão e origens identificadas")
                else:
                    try:
                        from .labor_calculations import parse_expression, _evaluate
                    except ImportError:
                        from labor_calculations import parse_expression, _evaluate
                    values = {r["id"]: (decimal_value(r["value"]), {}) for r in payload["inputs"] if r["id"] != iid}
                    if iid in row["bindings"].values() or not set(row["bindings"].values()) <= set(values):
                        errors.append(iid + ": derivação circular ou origem desconhecida")
                    else:
                        value, _ = _evaluate(parse_expression(row["expression"], row["bindings"]), row["expression"], row["bindings"], values)
                        if value != decimal_value(row["source_value"]):
                            errors.append(iid + ": valor derivado diverge da execução aritmética")
            if row["period_id"] not in periods:
                errors.append(iid + ": vincular relação e período contratual reais")
            period = periods.get(row["period_id"], {})
            if not row["effective_from"] or row["effective_until"] and row["effective_until"] < row["effective_from"]:
                errors.append(iid + ": período da conferência ausente ou invertido")
            for item in payload["items"]:
                if iid not in item["bindings"].values():
                    continue
                year, month = map(int, item["competence"].split("-"))
                start = item.get("period_start") or date(year, month, 1).isoformat()
                end = item.get("period_end") or date(year, month, calendar.monthrange(year, month)[1]).isoformat()
                if period.get("relationship_id") != item["relationship_id"] or row["effective_from"] > start or row["effective_until"] and row["effective_until"] < end:
                    errors.append(iid + ": critério não cobre a relação/competência; decompor por período")
        except (ValueError, TypeError, KeyError) as error:
            errors.append(iid + ": conferência numérica incompleta: " + str(error))
    if not errors:
        try:
            computed = compute_calculations(payload, facts={r["id"]: r for r in review["facts"]},
                                           norms={r["id"]: r for r in review["norms"]}, requests={r["id"]: r for r in review["requests"]})
            result.update(computed, arithmetic_status="executed")
        except (ValueError, KeyError, TypeError) as error:
            errors.append("Cálculo não conferido: " + str(error))
    result["errors"] = list(dict.fromkeys(errors))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Conferência por parâmetro; uso integrado à pesquisa de cada resposta")
    parser.add_argument("--transformation", choices=["identity", "percent_to_fraction", "percent_to_factor", "minutes_to_hours"])
    parser.add_argument("--value")
    parser.add_argument("--profile")
    args = parser.parse_args()
    try:
        if args.profile:
            profiles = json.loads((Path(__file__).resolve().parents[1] / "references/labor_parameter_profiles.json").read_text(encoding="utf-8"))["profiles"]
            selected = next((p for p in profiles if p["id"] == args.profile), None)
            if selected is None:
                raise ValueError("Perfil de cálculo desconhecido")
            print(json.dumps({"profile": selected, "status": "candidate_not_legal_rule"}, ensure_ascii=False, indent=2))
            return 0
        if not args.transformation or args.value is None:
            raise ValueError("Indicar transformação e valor com origem conferida; para conta completa usar response_research.py")
        print(json.dumps({"value": str(transform(args.value, args.transformation)), "scope": "arithmetic_only"}))
        return 0
    except ValueError as error:
        print(json.dumps({"error": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
