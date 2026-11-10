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
from decimal import Decimal, localcontext
from pathlib import Path

try:
    from .contracts import validate_contract
    from .labor_calculations import compute_calculations, decimal_value
    from .numeric_criteria import quantities, criterion_matches, same_value
    from .citation_check import contains
except ImportError:
    from contracts import validate_contract
    from labor_calculations import compute_calculations, decimal_value
    from numeric_criteria import quantities, criterion_matches, same_value
    from citation_check import contains


def transform(value: str, method: str) -> Decimal:
    amount = decimal_value(value)
    operations = {"identity": lambda n: n, "percent_to_fraction": lambda n: n / 100,
                  "percent_to_factor": lambda n: 1 + n / 100, "minutes_to_hours": lambda n: n / 60}
    if method not in operations:
        raise ValueError("Transformação numérica desconhecida")
    return operations[method](amount)


def numbers_in_excerpt(text: str) -> set[Decimal]:
    return {Decimal(q["value"]) for q in quantities(text)}


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
    result = {"errors": errors, "arithmetic_status": "not_run", "numeric_criteria": {}, "legal_applicability": "host_authored_not_machine_certified"}
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
    used_by_item = {}
    for item in payload["items"]:
        used = set(item["bindings"].values()) & set(inputs)
        queue = list(used)
        while queue:
            parent = queue.pop()
            for child in dependencies.get(parent, set()):
                if child in inputs and child not in used:
                    used.add(child)
                    queue.append(child)
        used_by_item[item["id"]] = used
    for iid, row in rows.items():
        parameter = inputs.get(iid)
        if not parameter:
            continue
        try:
            with localcontext() as context:
                context.prec = 50
                transformed = transform(row["source_value"], row["transform"])
            if not same_value(str(transformed), parameter["value"]):
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
                if row["norm_id"] not in parameter["norm_ids"] or not matching or not contains(source_texts.get(row["source_record_id"], ""), row["quote"]):
                    errors.append(iid + ": critério numérico sem trecho oficial consultado para a resposta")
                matches = criterion_matches(row, parameter)
                result["numeric_criteria"][iid] = matches
                if not matches:
                    errors.append(iid + ": número/unidade/limite do critério ausente ou incompatível com o trecho literal")
                if len({(q["unit"], q["relation"]) for q in matches}) > 1:
                    errors.append(iid + ": critérios concorrentes; delimitar unidade, limite e condição aplicável")
                if any(q["relation"] != "exact" for q in matches) and not row.get("conditions_analysis"):
                    errors.append(iid + ": limite numérico exige análise das condições de aplicação")
                if re.search(r"(?<![\w-])(?:desde que|salvo|exceto|quando|se)(?![\w-])", row["quote"], re.I) and not row.get("conditions_analysis"):
                    errors.append(iid + ": condição/exceção do trecho numérico exige análise específica")
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
                    try:
                        from .labor_calculations import UNITS
                    except ImportError:
                        from labor_calculations import UNITS
                    values = {r["id"]: (decimal_value(r["value"]), UNITS.get(r["unit"], {})) for r in payload["inputs"] if r["id"] != iid}
                    if iid in row["bindings"].values() or not set(row["bindings"].values()) <= set(values):
                        errors.append(iid + ": derivação circular ou origem desconhecida")
                    else:
                        with localcontext() as context:
                            context.prec = 50
                            value, unit = _evaluate(parse_expression(row["expression"], row["bindings"]), row["expression"], row["bindings"], values)
                        if not same_value(str(value), row["source_value"]):
                            errors.append(iid + ": valor derivado diverge da execução aritmética")
                        if unit != UNITS.get(parameter["unit"], {}):
                            errors.append(iid + ": unidade da derivação diverge da unidade do parâmetro")
            if row["period_id"] not in periods:
                errors.append(iid + ": vincular relação e período contratual reais")
            period = periods.get(row["period_id"], {})
            if not row["effective_from"] or row["effective_until"] and row["effective_until"] < row["effective_from"]:
                errors.append(iid + ": período da conferência ausente ou invertido")
            for item in payload["items"]:
                if iid not in used_by_item[item["id"]]:
                    continue
                year, month = map(int, item["competence"].split("-"))
                start = item.get("period_start") or date(year, month, 1).isoformat()
                end = item.get("period_end") or date(year, month, calendar.monthrange(year, month)[1]).isoformat()
                if period.get("relationship_id") != item["relationship_id"] or row["effective_from"] > start or row["effective_until"] and row["effective_until"] < end:
                    errors.append(iid + ": critério não cobre a relação/competência; decompor por período")
                if period.get("start") and start < period["start"] or period.get("end") and end > period["end"]:
                    errors.append(iid + ": parcela fora do período contratual vinculado")
        except (ValueError, TypeError, KeyError) as error:
            errors.append(iid + ": conferência numérica incompleta: " + str(error))
    if not errors:
        try:
            computed = compute_calculations(payload, facts={r["id"]: r for r in review["facts"]},
                                           norms={r["id"]: r for r in review["norms"]}, requests={r["id"]: r for r in review["requests"]})
            result.update(computed, arithmetic_status="executed")
            provisional = {cid for q in review.get("labor_review", {}).get("workflow", {}).get("material_questions", [])
                           if q["status"] == "open" and q.get("impact_scope") == "calculation_item" for cid in q.get("calculation_item_ids", [])}
            if provisional:
                result["provisional_item_ids"] = sorted(provisional & {i["id"] for i in payload["items"]})
                result["factual_status"] = "open_calculation_questions_require_review"
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
