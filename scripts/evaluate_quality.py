"""Evaluate a case output against independently annotated synthetic expectations.

The evaluator measures observable omissions and traceability. Lexical matches and
source checks do not establish that a legal proposition is correct or persuasive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Objeto JSON esperado: {path}")
    return data


def _fold(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or "").casefold())
    return "".join(char for char in text if unicodedata.category(char) != "Mn")


def _fraction(found: int, total: int) -> float | None:
    return round(found / total, 4) if total else None


def _locator(source: dict[str, Any]) -> tuple[str, int] | None:
    try:
        return str(source["source_sha256"]), int(source["pdf_page"])
    except (KeyError, TypeError, ValueError):
        return None


def _candidate_text(item: dict[str, Any], kind: str) -> str:
    fields = {
        "fact": ("text",),
        "issue": ("question", "conclusion", "subsumption"),
        "request": ("text",),
    }[kind]
    return " ".join(str(item.get(field, "")) for field in fields)


def _match(gold: dict[str, Any], candidates: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    phrases = gold.get("text_any", [])
    for candidate in candidates:
        text = _fold(_candidate_text(candidate, kind))
        if any(_fold(phrase) in text for phrase in phrases):
            return candidate
    return None


def _gold_locator(source: dict[str, Any], source_hashes: dict[str, str]) -> tuple[str, int]:
    name = source["file"]
    if name not in source_hashes:
        raise ValueError(f"Fonte não declarada no caso: {name}")
    page = source["page"]
    if not isinstance(page, int) or page < 1:
        raise ValueError(f"Página inválida para {name}: {page}")
    return source_hashes[name], page


def _indexed_pages(memory: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    pages = {}
    for document in memory.get("documents", []):
        for page in document.get("pages", []):
            pages[(document.get("sha256"), page.get("pdf_page"))] = page
    return pages


def _quote_in_page(source: dict[str, Any], page: dict[str, Any] | None) -> bool:
    if not page or not source.get("quote"):
        return False
    visual = page.get("vision", {})
    content = " ".join((
        str(page.get("text", "")),
        str(visual.get("description", "")) if isinstance(visual, dict) else "",
        str(visual.get("transcription", "")) if isinstance(visual, dict) else "",
    ))
    return _fold(source["quote"]) in _fold(content)


def _recorded_conflicts(review: dict[str, Any]) -> list[set[tuple[str, int]]]:
    pairs = []
    for conflict in review.get("conflicts", []):
        if not isinstance(conflict, dict):
            continue
        sources = conflict.get("sources", [])
        if not sources and conflict.get("fact_ids"):
            fact_ids = set(conflict["fact_ids"])
            sources = [source for fact in review.get("facts", []) if fact.get("id") in fact_ids
                       for source in fact.get("sources", [])]
        pair = {_locator(source) for source in sources if isinstance(source, dict)}
        pair.discard(None)
        if len(pair) >= 2:
            pairs.append(pair)
    for finding in review.get("findings", []):
        if not isinstance(finding, dict) or "CONTRAD" not in _fold(finding.get("code", "")).upper():
            continue
        page_ids = finding.get("target_ids", []) if finding.get("scope") == "page" else []
        pair = set()
        for page_id in page_ids:
            try:
                sha, page = str(page_id).rsplit(":", 1)
                pair.add((sha, int(page)))
            except ValueError:
                continue
        if len(pair) >= 2:
            pairs.append(pair)
    return pairs


def _status_map(validation: dict[str, Any], gate: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    readiness = validation.get("readiness") or gate.get("readiness") or validation
    if not isinstance(readiness, dict):
        readiness = {}
    issues = readiness.get("issue_statuses", [])
    return {str(item.get("id")): str(item.get("analysis_status")) for item in issues if isinstance(item, dict)}, readiness


def _validate_gold(gold: dict[str, Any], case_path: Path) -> dict[str, str]:
    if gold.get("schema_version") != "1.0" or gold.get("synthetic") is not True:
        raise ValueError("Caso de avaliação deve ser sintético e usar schema_version 1.0")
    expected = gold.get("expected")
    if not isinstance(expected, dict) or not any(expected.get(k) for k in ("facts", "issues", "requests", "contradictions")):
        raise ValueError("Caso sem rótulos independentes")
    source_hashes = {}
    for source in gold.get("source_files", []):
        name = source.get("file")
        if not isinstance(name, str) or not name or name in source_hashes:
            raise ValueError("Fonte sintética ausente ou repetida")
        path = (case_path.parent / name).resolve()
        if not path.is_file() or not path.is_relative_to(case_path.parent.resolve()):
            raise ValueError(f"Fonte sintética indisponível: {name}")
        source_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not source_hashes:
        raise ValueError("Caso sem fonte sintética")
    labels = set()
    for kind in ("facts", "issues", "requests", "contradictions"):
        for item in expected.get(kind, []):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or item["id"] in labels:
                raise ValueError(f"Rótulo {kind} sem ID único")
            labels.add(item["id"])
            if kind != "contradictions" and not item.get("text_any"):
                raise ValueError(f"Rótulo {item['id']} sem expressão observável")
            for key in ("source", "source_a", "source_b"):
                if key in item:
                    _gold_locator(item[key], source_hashes)
    return source_hashes


def evaluate(case_path: Path, artifact_dir: Path, *, review_path: Path | None = None,
             elapsed_seconds: float | None = None, context_tokens: int | None = None) -> dict[str, Any]:
    gold = _read_json(case_path)
    source_hashes = _validate_gold(gold, case_path)
    expected = gold["expected"]
    review = _read_json(review_path or artifact_dir / "legal_review.json")
    memory = _read_json(artifact_dir / "case_memory.json")
    validation_path = artifact_dir / "legal_review_validation.json"
    validation = _read_json(validation_path) if validation_path.is_file() else {}
    gate_path = artifact_dir / "quality_gate.json"
    gate = _read_json(gate_path) if gate_path.is_file() else {}
    pages = _indexed_pages(memory)
    details: dict[str, list[dict[str, Any]]] = {key: [] for key in ("facts", "issues", "requests", "contradictions")}
    violations = []
    for name, sha in source_hashes.items():
        if not any(d.get("sha256") == sha for d in memory.get("documents", [])):
            violations.append(f"Fonte esperada ausente da memória: {name}")

    fact_matches = {}
    for label in expected.get("facts", []):
        candidate = _match(label, review.get("facts", []), "fact")
        found = candidate is not None
        expected_source = _gold_locator(label["source"], source_hashes) if label.get("source") else None
        cited = bool(candidate and expected_source and any(_locator(s) == expected_source and _quote_in_page(s, pages.get(expected_source))
                           for s in candidate.get("sources", []))) if expected_source else found
        details["facts"].append({"id": label["id"], "found": found, "correct_source": cited,
                                 "candidate_id": candidate.get("id") if candidate else None})
        if candidate:
            fact_matches[label["id"]] = candidate
        if not found:
            violations.append(f"Fato esperado omitido: {label['id']}")
        elif not cited:
            violations.append(f"Fato sem citação esperada válida: {label['id']}")

    issue_matches = {}
    status_by_id, readiness = _status_map(validation, gate)
    false_blocks = 0
    for label in expected.get("issues", []):
        candidate = _match(label, review.get("issues", []), "issue")
        found = candidate is not None
        candidate_id = candidate.get("id") if candidate else None
        observed = status_by_id.get(str(candidate_id)) or (candidate or {}).get("analysis_status")
        wanted = label.get("analysis_status")
        status_ok = not wanted or observed == wanted
        details["issues"].append({"id": label["id"], "found": found, "expected_status": wanted,
                                  "observed_status": observed, "status_correct": status_ok,
                                  "candidate_id": candidate_id})
        if candidate:
            issue_matches[label["id"]] = candidate
        if not found:
            violations.append(f"Questão esperada omitida: {label['id']}")
        elif not status_ok:
            violations.append(f"Estado da questão incorreto: {label['id']} ({observed}; esperado {wanted})")
            if wanted == "concluded" and observed in {"qualified", "undetermined"}:
                false_blocks += 1

    for label in expected.get("requests", []):
        candidate = _match(label, review.get("requests", []), "request")
        linked = bool(candidate) and all(issue_matches.get(i, {}).get("id") in candidate.get("issue_ids", [])
                                         for i in label.get("issue_ids", []))
        details["requests"].append({"id": label["id"], "found": candidate is not None,
                                    "issues_linked": linked, "candidate_id": candidate.get("id") if candidate else None})
        if not candidate:
            violations.append(f"Pedido esperado omitido: {label['id']}")
        elif not linked:
            violations.append(f"Pedido sem vínculo com questão esperada: {label['id']}")

    conflict_pairs = _recorded_conflicts(review)
    for label in expected.get("contradictions", []):
        pair = {_gold_locator(label["source_a"], source_hashes), _gold_locator(label["source_b"], source_hashes)}
        found = any(pair <= recorded for recorded in conflict_pairs)
        details["contradictions"].append({"id": label["id"], "found": found})
        if not found:
            violations.append(f"Contradição esperada não registrada: {label['id']}")

    citation_count = citation_valid = 0
    for fact in review.get("facts", []):
        for source in fact.get("sources", []):
            citation_count += 1
            locator = _locator(source)
            if locator and _quote_in_page(source, pages.get(locator)):
                citation_valid += 1
            else:
                violations.append(f"Citação sem trecho na página referida: {fact.get('id', '?')}")
    expected_status = expected.get("execution_status")
    observed_status = readiness.get("execution_status")
    if expected_status and observed_status != expected_status:
        violations.append(f"Execução {observed_status}; esperada {expected_status}")
        if expected_status == "completed" and observed_status in {"partial", "failed"}:
            false_blocks += 1
    expected_draft = expected.get("draft_status")
    observed_draft = readiness.get("draft_status")
    if expected_draft and observed_draft != expected_draft:
        violations.append(f"Minuta {observed_draft}; esperada {expected_draft}")
        if expected_draft == "ready_for_review" and observed_draft in {"partial", "blocked"}:
            false_blocks += 1
    if elapsed_seconds is not None and elapsed_seconds < 0:
        raise ValueError("Tempo observado deve ser não negativo")
    if context_tokens is not None and context_tokens < 0:
        raise ValueError("Tokens observados devem ser não negativos")
    budget = gold.get("limits", {}).get("max_elapsed_seconds")
    if budget is not None and elapsed_seconds is not None and elapsed_seconds > budget:
        violations.append(f"Tempo observado {elapsed_seconds}s supera limite do caso {budget}s")
    metrics = {
        "fact_recall": _fraction(sum(x["found"] for x in details["facts"]), len(details["facts"])),
        "issue_recall": _fraction(sum(x["found"] for x in details["issues"]), len(details["issues"])),
        "request_recall": _fraction(sum(x["found"] for x in details["requests"]), len(details["requests"])),
        "contradiction_recall": _fraction(sum(x["found"] for x in details["contradictions"]), len(details["contradictions"])),
        "citation_precision": _fraction(citation_valid, citation_count),
        "expected_fact_citation_recall": _fraction(sum(x["correct_source"] for x in details["facts"]),
                                                   sum("source" in x for x in expected.get("facts", []))),
        "false_block_count": false_blocks,
        "elapsed_seconds": elapsed_seconds,
        "context_tokens": context_tokens,
    }
    return {"schema_version": "1.0", "case_id": gold.get("case_id"), "synthetic": True,
            "passed_observable_checks": not violations, "metrics": metrics, "details": details,
            "expected_status": expected_status, "observed_status": observed_status,
            "violations": violations,
            "limitations": ["Comparação textual de rótulos sintéticos; não valida mérito jurídico ou equivalência semântica.",
                            "Tempo e tokens só são medidos quando fornecidos como observações da execução."]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Avalia resultados da skill contra casos sintéticos anotados independentemente")
    parser.add_argument("--case", required=True, type=Path, help="JSON com fontes e rótulos sintéticos")
    parser.add_argument("--artifact-dir", required=True, type=Path, help="Diretório de saída da execução avaliada")
    parser.add_argument("--review", type=Path, help="Revisão específica, inclusive uma revisão rejeitada")
    parser.add_argument("--output", type=Path, help="JSON de avaliação a gravar")
    parser.add_argument("--elapsed-seconds", type=float, help="Tempo observado externamente em segundos")
    parser.add_argument("--context-tokens", type=int, help="Tokens observados externamente")
    args = parser.parse_args()
    try:
        report = evaluate(args.case, args.artifact_dir, review_path=args.review,
                          elapsed_seconds=args.elapsed_seconds, context_tokens=args.context_tokens)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Avaliação inválida: {exc}\n")
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0 if report["passed_observable_checks"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
