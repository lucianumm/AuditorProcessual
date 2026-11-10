"""Decimal arithmetic for supplied labor parameters; no legal defaults or eval()."""
from __future__ import annotations

import argparse
import ast
import json
import hashlib
import re
from collections import deque
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_UP, ROUND_HALF_EVEN
from pathlib import Path

try:
    from .contracts import validate_contract
    from .case_memory import identity, atomic_json, atomic_text, atomic_bytes
except ImportError:
    from contracts import validate_contract
    from case_memory import identity, atomic_json, atomic_text, atomic_bytes

UNITS = {"money": {"BRL": 1}, "hours": {"hour": 1}, "days": {"day": 1}, "months": {"month": 1}, "percent": {"percent": 1}}
FUNCTIONS = {"min": min, "max": max}
ROUNDINGS = {"HALF_UP": ROUND_HALF_UP, "HALF_EVEN": ROUND_HALF_EVEN}


def decimal_value(value) -> Decimal:
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Valor deve ser string decimal curta, com ponto e sem separador de milhares")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Valor decimal inválido") from error
    if not number.is_finite() or abs(number.adjusted()) > 30:
        raise ValueError("Valor não finito ou fora do limite operacional")
    return number


def parse_expression(expression: str, bindings: dict) -> ast.Expression:
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError) as error:
        raise ValueError("Expressão aritmética inválida") from error
    nodes = list(ast.walk(tree))
    if len(nodes) > 100:
        raise ValueError("Expressão muito complexa; decompor em parcelas")
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Load, ast.Constant, ast.Call,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub)
    if any(not isinstance(node, allowed) for node in nodes):
        raise ValueError("Somente nomes vinculados, números, + - * / e min/max são permitidos")
    calls = [node for node in nodes if isinstance(node, ast.Call)]
    for call in calls:
        if not isinstance(call.func, ast.Name) or call.func.id not in FUNCTIONS or len(call.args) < 2 or call.keywords:
            raise ValueError("Somente min(a, b, ...) e max(a, b, ...) com dois ou mais termos são permitidos")
    function_names = {id(call.func) for call in calls}
    if set(bindings) & set(FUNCTIONS):
        raise ValueError("min e max são reservados; renomear o binding")
    names = {node.id for node in nodes if isinstance(node, ast.Name) and id(node) not in function_names}
    if names != set(bindings):
        raise ValueError("Bindings devem corresponder exatamente aos parâmetros utilizados")
    for node in nodes:
        if isinstance(node, ast.Constant):
            token = ast.get_source_segment(expression, node) or ""
            if type(node.value) not in {int, float} or any(c in token.lower() for c in "ej_"):
                raise ValueError("Constante aritmética inválida")
            if decimal_value(token) not in {Decimal(0), Decimal(1), Decimal(100)}:
                raise ValueError("Taxa, divisor ou quantidade deve ser parâmetro com fonte")
    return tree


def _evaluate(node, expression, bindings, values):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, expression, bindings, values)
    if isinstance(node, ast.Name):
        return values[bindings[node.id]]
    if isinstance(node, ast.Constant):
        return decimal_value(ast.get_source_segment(expression, node)), {}
    if isinstance(node, ast.UnaryOp):
        value, unit = _evaluate(node.operand, expression, bindings, values)
        return (-value if isinstance(node.op, ast.USub) else value), unit
    if isinstance(node, ast.Call):
        evaluated = [_evaluate(arg, expression, bindings, values) for arg in node.args]
        # A literal zero is a floor or ceiling in any unit (e.g. interest never below zero).
        units = [unit for arg, (value, unit) in zip(node.args, evaluated) if not (isinstance(arg, ast.Constant) and value == 0)]
        if not units or any(unit != units[0] for unit in units):
            raise ValueError(node.func.id + ": termos com unidades incompatíveis")
        return FUNCTIONS[node.func.id](value for value, _ in evaluated), units[0]
    left, left_unit = _evaluate(node.left, expression, bindings, values)
    right, right_unit = _evaluate(node.right, expression, bindings, values)
    if isinstance(node.op, (ast.Add, ast.Sub)):
        if left_unit != right_unit:
            raise ValueError("Soma/subtração entre unidades incompatíveis")
        return (left + right if isinstance(node.op, ast.Add) else left - right), left_unit
    if isinstance(node.op, ast.Div) and right == 0:
        raise ValueError("Divisão por zero")
    sign = -1 if isinstance(node.op, ast.Div) else 1
    unit = dict(left_unit)
    for key, exponent in right_unit.items():
        unit[key] = unit.get(key, 0) + exponent * sign
    # A percentage only becomes a fraction through an explicit division by 100.
    if sign == -1 and isinstance(node.right, ast.Constant) and right == 100 and unit.get("percent", 0) > 0:
        unit["percent"] -= 1
    unit = {key: exponent for key, exponent in unit.items() if exponent}
    return (left / right if sign == -1 else left * right), unit


def compute_calculations(payload: dict, *, facts: dict | None = None, norms: dict | None = None,
                         requests: dict | None = None) -> dict:
    errors = validate_contract(payload, "labor_calculation.schema.json")
    if errors:
        raise ValueError("; ".join(errors[:8]))
    inputs = {item["id"]: item for item in payload["inputs"]}
    items = {item["id"]: item for item in payload["items"]}
    if len(inputs) != len(payload["inputs"]) or len(items) != len(payload["items"]) or set(inputs) & set(items):
        raise ValueError("IDs de parâmetros e parcelas devem ser únicos e distintos")
    values = {key: (decimal_value(item["value"]), UNITS.get(item["unit"], {})) for key, item in inputs.items()}
    for input_record in inputs.values():
        for key, known in (("fact_ids", facts), ("norm_ids", norms)):
            if known is not None and not set(input_record[key]) <= set(known):
                raise ValueError(input_record["id"] + ": parâmetro sem fonte existente")
    dependencies, trees, downstream = {}, {}, {key: [] for key in items}
    seen_rows, used_payments, payment_inputs = set(), set(), set()
    for key, item in items.items():
        row_key = (item["relationship_id"], item["competence"], item["claim_type"], item["segment"], item["kind"])
        if row_key in seen_rows:
            raise ValueError("Parcela repetida na mesma relação, competência e segmento")
        seen_rows.add(row_key)
        date.fromisoformat(item["competence"] + "-01")
        if item.get("period_start"):
            start, end = date.fromisoformat(item["period_start"]), date.fromisoformat(item["period_end"])
            if start > end or start.strftime("%Y-%m") != item["competence"] or end.strftime("%Y-%m") != item["competence"]:
                raise ValueError(key + ": período fora da competência; decompor por mês")
        for field, known in (("norm_ids", norms), ("request_ids", requests), ("payment_fact_ids", facts)):
            if known is not None and not set(item.get(field, [])) <= set(known):
                raise ValueError(key + ": referência inexistente em " + field)
        if not item["norm_ids"]:
            raise ValueError(key + ": parcela trabalhista exige fundamento normativo vinculado")
        for payment in item.get("payment_fact_ids", []):
            if payment in used_payments:
                raise ValueError("Pagamento abatido em mais de uma parcela; registrar alocação comprovada como fatos distintos")
            used_payments.add(payment)
        for bound in item["bindings"].values():
            if inputs.get(bound, {}).get("role") == "payment":
                if bound in payment_inputs:
                    raise ValueError(bound + ": pagamento informado usado em mais de uma parcela; registrar alocações distintas")
                payment_inputs.add(bound)
        trees[key] = parse_expression(item["expression"], item["bindings"])
        bound = set(item["bindings"].values())
        if not bound <= set(inputs) | set(items):
            raise ValueError(key + ": parâmetro ou parcela referida inexistente")
        dependencies[key] = bound & set(items)
        for previous in dependencies[key]:
            downstream[previous].append(key)
    remaining = {key: len(deps) for key, deps in dependencies.items()}
    queue = deque(key for key, count in remaining.items() if count == 0)
    results = {}
    with localcontext() as context:
        context.prec = 50
        while queue:
            key = queue.popleft()
            item = items[key]
            raw, unit = _evaluate(trees[key], item["expression"], item["bindings"], values)
            if unit.get("percent"):
                raise ValueError(key + ": percentual usado como multiplicador; dividir por 100 ou informar fator")
            if unit != UNITS["money"] or not raw.is_finite() or raw.adjusted() > 18:
                raise ValueError(key + ": resultado deve ser valor monetário finito")
            rounded = raw.quantize(Decimal("0.01"), rounding=ROUNDINGS[item.get("rounding_mode", "HALF_UP")])
            if rounded != decimal_value(item["expected_result"]):
                raise ValueError(key + ": resultado informado diverge do cálculo decimal (" + str(rounded) + ")")
            if item["kind"] == "deduction" and rounded > 0:
                raise ValueError(key + ": abatimento deve ser negativo")
            values[key] = (rounded if payload["rounding"] == "per_item" else raw, UNITS["money"])
            numeric = re.sub(r"[A-Za-z_][A-Za-z0-9_]*",lambda match:match.group(0) if match.group(0) in FUNCTIONS else
                             "(" + str(values[item["bindings"][match.group(0)]][0]) + ")",item["expression"])
            source_facts, source_norms = set(), set(item["norm_ids"])
            for bound_id in item["bindings"].values():
                if bound_id in inputs:
                    source_facts.update(inputs[bound_id]["fact_ids"])
                    source_norms.update(inputs[bound_id]["norm_ids"])
                else:
                    source_facts.update(results[bound_id]["source_fact_ids"])
                    source_norms.update(results[bound_id]["source_norm_ids"])
            results[key] = {**item, "result":str(rounded), "unrounded_result":str(raw),
                            "numeric_expression":numeric,"depends_on":sorted(dependencies[key]),
                            "source_fact_ids":sorted(source_facts),"source_norm_ids":sorted(source_norms)}
            for later in downstream[key]:
                remaining[later] -= 1
                if remaining[later] == 0:
                    queue.append(later)
        if len(results) != len(items):
            raise ValueError("Dependência circular entre parcelas")
        total = sum((values[key][0] for key in results if items[key]["include_in_total"]), Decimal(0))
        modes = {items[key].get("rounding_mode", "HALF_UP") for key in results if items[key]["include_in_total"]}
        total_mode = modes.pop() if len(modes) == 1 else "HALF_UP"
        total = total.quantize(Decimal("0.01"), rounding=ROUNDINGS[total_mode])
        displayed_total = sum((decimal_value(results[key]["result"]) for key in results if items[key]["include_in_total"]),Decimal(0))
    return {"schema_version":"1.0", "corpus_revision":payload["corpus_revision"], "input_revision":identity(payload),
            "status":"computed_from_supplied_parameters", "purpose":payload["purpose"], "currency":"BRL",
            "rounding":payload["rounding"],"total_rounding_mode":total_mode,"inputs":payload["inputs"], "items":[results[key] for key in items], "total":str(total),
            "displayed_items_total":str(displayed_total),"rounding_difference":str(total-displayed_total),
            "legal_parameters_reason":payload["legal_parameters_reason"],
            "legal_parameters_status":"host_authored_requires_legal_review"}


def compare_reference(result: dict, reference: dict, source_file: Path | None = None) -> dict:
    required = {"input_revision", "source_file_sha256", "tool", "tool_version", "table_revision", "reviewer", "items"}
    if not required <= set(reference) or any(not isinstance(reference[key], str) or not reference[key].strip() for key in required - {"items"}):
        raise ValueError("Referência exige revisão dos dados, arquivo, ferramenta/versão, tabelas e responsável")
    if reference["input_revision"] != result["input_revision"]:
        raise ValueError("Referência corresponde a outros parâmetros")
    detailed = reference.get("schema_version") == "2.0"
    if detailed and source_file is None:
        raise ValueError("Comparação detalhada exige bytes reais do arquivo externo, versão e tabelas")
    if len(reference["source_file_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in reference["source_file_sha256"]):
        raise ValueError("Hash do arquivo de referência inválido")
    if source_file is not None:
        digest = hashlib.sha256()
        with source_file.open("rb") as source:
            for chunk in iter(lambda:source.read(1024 * 1024),b""):
                digest.update(chunk)
        if digest.hexdigest() != reference["source_file_sha256"]:
            raise ValueError("Arquivo de referência diverge do hash registrado")
    expected = {item["id"]:decimal_value(item["result"]) for item in reference["items"]}
    actual = {item["id"]:decimal_value(item["result"]) for item in result["items"]}
    if len(expected) != len(reference["items"]) or set(expected) != set(actual):
        raise ValueError("Referência deve comparar cada parcela exatamente uma vez")
    mismatches = [{"id":key,"computed":str(actual[key]),"reference":str(expected[key])} for key in actual if actual[key] != expected[key]]
    compared_fields = ["result"]
    if detailed:
        fields = ("relationship_id", "competence", "claim_type", "kind", "segment", "expression", "bindings", "include_in_total")
        expected_rows = {r["id"]: r for r in reference["items"]}
        for item in result["items"]:
            recorded = expected_rows[item["id"]]
            if any(field not in recorded for field in fields) or not recorded.get("external_locator"):
                raise ValueError("Referência detalhada exige parcela/competência/natureza/base/abatimento e localizador externo")
            for field in fields:
                if item[field] != recorded[field]:
                    mismatches.append({"id": item["id"], "field": field, "computed": item[field], "reference": recorded[field]})
            if not recorded.get("rounding_mode"):
                raise ValueError("Referência detalhada exige arredondamento de cada parcela")
            if item.get("rounding_mode", "HALF_UP") != recorded["rounding_mode"]:
                mismatches.append({"id": item["id"], "field": "rounding_mode", "computed": item.get("rounding_mode", "HALF_UP"), "reference": recorded["rounding_mode"]})
        if not isinstance(reference.get("inputs"), list) or not isinstance(reference.get("rounding"), str):
            raise ValueError("Referência detalhada exige parâmetros/unidades e arredondamento externos")
        params = {p["id"]: p for p in reference["inputs"]}
        if len(params) != len(reference["inputs"]) or set(params) != {p["id"] for p in result["inputs"]}:
            raise ValueError("Comparar cada base, taxa, divisor e unidade exatamente uma vez")
        for item in result["inputs"]:
            other = params[item["id"]]
            if not other.get("external_locator") or "value" not in other or "unit" not in other:
                raise ValueError("Parâmetro externo sem valor, unidade ou localizador")
            if decimal_value(item["value"]) != decimal_value(other["value"]) or item["unit"] != other["unit"]:
                mismatches.append({"id": item["id"], "field": "input_value_or_unit", "computed": item, "reference": other})
        if reference["rounding"] != result["rounding"]:
            mismatches.append({"field": "rounding", "computed": result["rounding"], "reference": reference["rounding"]})
        if "total" not in reference:
            raise ValueError("Referência detalhada exige total externo")
        if decimal_value(reference["total"]) != decimal_value(result["total"]):
            mismatches.append({"field": "total", "computed": result["total"], "reference": reference["total"]})
        compared_fields += list(fields) + ["input_values", "input_units", "rounding", "rounding_mode", "total"]
    return {"status":"matched" if not mismatches else "divergent", "mismatches":mismatches,
            "compared_fields": compared_fields,
            "record_status":"external_reference_not_independently_attested", "tool":reference["tool"],
            "source_integrity_status":"verified_bytes" if source_file is not None else "not_checked",
            "tool_version":reference["tool_version"], "table_revision":reference["table_revision"]}


def calculation_markdown(result: dict) -> str:
    try:
        from .legal_index import safe_text
    except ImportError:
        from legal_index import safe_text
    lines = ["# MEMÓRIA DE CÁLCULO TRABALHISTA", "", "Valores calculados com os parâmetros registrados; conferir sua incidência jurídica.",
             "", "Corpus: " + result["corpus_revision"], "", "Parâmetros: " + result["input_revision"], "",
             "Arredondamento: " + result["rounding"], "",
             "| Parcela | Relação | Competência | Fórmula numérica | Valor (R$) |", "|---|---|---|---|---:|"]
    for item in result["items"]:
        lines.append("| " + " | ".join(safe_text(item[key]) for key in ("id","relationship_id","competence","numeric_expression","result")) + " |")
    lines += ["", "Total das parcelas marcadas para soma: R$ " + result["total"], "", safe_text(result["legal_parameters_reason"]), "", "## Premissas e vínculos", ""]
    if decimal_value(result["rounding_difference"]) != 0:
        lines += ["Diferença entre soma das linhas exibidas e total arredondado ao final: R$ " + result["rounding_difference"] + ".", ""]
    lines += ["| Parâmetro | Valor | Unidade | Fatos | Normas |","|---|---:|---|---|---|"]
    for parameter in result["inputs"]:
        lines.append("| " + " | ".join(safe_text(value) for value in (parameter["id"],parameter["value"],parameter["unit"],
                                                                      ", ".join(parameter["fact_ids"]),", ".join(parameter["norm_ids"]))) + " |")
    lines.append("")
    for item in result["items"]:
        lines += [safe_text(item["id"]) + ": " + safe_text(item["reason"]) + ".",
                  "Normas: " + ", ".join(safe_text(n) for n in item["norm_ids"]) + ". Pedidos: " + ", ".join(safe_text(r) for r in item["request_ids"]) + ".", ""]
    return "\n".join(lines)


def store_calculation(output: Path, result: dict) -> list[str]:
    output.mkdir(parents=True,exist_ok=True)
    names = ["calculo_trabalhista.json","memoria_calculo_trabalhista.md"]
    preserved = []
    for name in names:
        path = output / name
        if path.is_file():
            raw = path.read_bytes()
            archive = "calculation_history/" + hashlib.sha256(raw).hexdigest() + "/" + name
            if not (output / archive).exists():
                atomic_bytes(output / archive,raw)
            preserved.append(archive)
    atomic_json(output / names[0],result)
    atomic_text(output / names[1],calculation_markdown(result))
    if (output / "manifest.json").is_file():
        try:
            from .artifact_tracking import track_artifacts
        except ImportError:
            from artifact_tracking import track_artifacts
        track_artifacts(output,names + preserved,status="labor_calculation_recorded")
    return names + preserved


def main() -> int:
    parser = argparse.ArgumentParser(description="Calcula parcelas com Decimal, fontes e parâmetros explícitos")
    parser.add_argument("input",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--reference",type=Path,help="Transcrição conferida do resultado externo, vinculada aos mesmos parâmetros")
    parser.add_argument("--reference-source",type=Path,help="Arquivo real do resultado externo para conferir o hash")
    parser.add_argument("--case-output",type=Path,help="Confere a revisão dos dados contra case_memory.json")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if args.case_output:
            memory = json.loads((args.case_output / "case_memory.json").read_text(encoding="utf-8-sig"))
            if payload.get("corpus_revision") != memory["corpus_revision"]:
                raise ValueError("Parâmetros vinculados a corpus anterior")
        result = compute_calculations(payload)
        if args.reference:
            result["reference_comparison"] = compare_reference(result,json.loads(args.reference.read_text(encoding="utf-8-sig")),args.reference_source)
        elif args.reference_source:
            raise ValueError("--reference-source exige o registro --reference")
        if args.output:
            destinations = [(args.output / name).resolve() for name in ("calculo_trabalhista.json","memoria_calculo_trabalhista.md")]
            if args.input.resolve() in destinations or args.reference and args.reference.resolve() in destinations or args.reference_source and args.reference_source.resolve() in destinations:
                raise ValueError("Saída sobrescreveria arquivo de entrada; escolha diretório distinto")
            store_calculation(args.output,result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 1 if result.get("reference_comparison",{}).get("status") == "divergent" else 0
    except (OSError, ValueError, TypeError, KeyError, InvalidOperation, OverflowError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
