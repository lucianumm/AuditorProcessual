"""Provider-neutral legal synthesis: validate references, then render authored work.

The host AI researches and interprets. This module checks its recorded evidence;
it cannot certify the truth of a fact or the correctness of a legal opinion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

try:
    from .case_memory import atomic_json, atomic_text, identity
except ImportError:
    from case_memory import atomic_json, atomic_text, identity

PROHIBITED = ("conforme documentação", "conforme documentos", "documento apresentado",
              "certidão analisada", "foi analisado", "a documentação demonstra",
              "a peça registra o seguinte", "a peça contém o seguinte")
PIECE_SECTIONS = {
    "inicial": ("enderecamento", "qualificacao", "fatos", "fundamentos", "pedidos", "provas", "valor_da_causa"),
    "contestacao": ("enderecamento", "qualificacao", "sintese", "impugnacao", "fundamentos", "pedidos"),
    "replica": ("enderecamento", "sintese", "impugnacao", "provas", "pedidos"),
    "pericia": ("enderecamento", "objeto", "analise_tecnica", "quesitos", "pedidos"),
    "recurso": ("enderecamento", "admissibilidade", "decisao_recorrida", "impugnacao", "pedidos"),
    "cumprimento": ("enderecamento", "titulo", "obrigacao", "demonstrativo", "pedidos"),
    "manifestacao": ("enderecamento", "objeto", "fundamentos", "pedidos"),
}


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn")


def style_findings(text: str, initial: bool = False) -> list[str]:
    # Exact source quotations are stored separately and never rewritten by lint.
    normalized = fold(text)
    findings = [phrase for phrase in PROHIBITED if fold(phrase) in normalized]
    if initial:
        for pattern in (r"\b(?:o autor|a autora|os autores|as autoras|a parte autora|a parte|o requerente|a requerente)\s+(?:alega[m]?|sustenta[m]?|afirma[m]?)\b", r"\bsegundo (?:o autor|a autora|os autores|a parte autora)\b"):
            if re.search(pattern, normalized):
                findings.append("narrativa da própria parte com distanciamento")
    return findings


def official_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError:
        return False
    return parsed.scheme == "https" and port in {None, 443} and not parsed.username and not parsed.password and any(
        host.endswith(suffix) for suffix in (".gov.br", ".jus.br", ".leg.br", ".mp.br"))


def date_valid(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def collection(review: dict, name: str, errors: list[str]) -> list[dict]:
    value = review.get(name)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        errors.append(f"{name}: exige lista de objetos")
        return []
    ids = [item.get("id") for item in value]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(str(i) for i in ids)):
        errors.append(f"{name}: IDs ausentes ou duplicados")
    return value


def validate_review(review: dict, memory: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(review, dict):
        return ["A revisão deve ser objeto JSON"]
    if review.get("corpus_revision") != memory.get("corpus_revision"):
        errors.append("Revisão desatualizada: corpus_revision difere dos uploads atuais")
    task = review.get("task")
    if task not in {"analyze", "petition", "audit"}:
        errors.append("task: analyze, petition ou audit obrigatório")
    strategy = review.get("strategy", {})
    if not isinstance(strategy, dict):
        return errors + ["strategy deve ser objeto"]
    for key in ("objective", "jurisdiction", "domain", "phase"):
        if not isinstance(strategy.get(key), str) or not strategy[key].strip():
            errors.append(f"strategy.{key}: ausente")
    if task == "petition" and not strategy.get("represented_party"):
        errors.append("Parte representada indispensável para a peça")
    facts = collection(review, "facts", errors)
    norms = collection(review, "norms", errors)
    issues = collection(review, "issues", errors)
    requests = collection(review, "requests", errors)
    paragraphs = collection(review, "paragraphs", errors)
    clients = collection(review, "client_records", errors)
    pages = {(d["sha256"], p["pdf_page"]): p for d in memory["documents"] for p in d["pages"]}
    expected_pages = {f"{sha}:{number}" for sha, number in pages}
    checked = review.get("reviewed_pages", [])
    if not isinstance(checked, list) or set(str(x) for x in checked) != expected_pages or len(checked) != len(expected_pages):
        errors.append("reviewed_pages não corresponde a todas as páginas do corpus")
    relations = review.get("related_processes_reason", "")
    process_ids = {d.get("process_id") for d in memory["documents"] if d.get("process_id") and re.fullmatch(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", d["process_id"])}
    if len(process_ids) > 1 and not relations:
        errors.append("Processos distintos exigem justificativa de relação")
    fact_ids = {f.get("id") for f in facts}
    norm_ids = {n.get("id") for n in norms}
    issue_ids = {i.get("id") for i in issues}
    request_ids = {r.get("id") for r in requests}
    client_map = {c.get("id"): c for c in clients}

    def refs(item: dict, field: str, known: set, required: bool = True) -> None:
        values = item.get(field, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or v not in known for v in values) or (required and not values):
            errors.append(f"{item.get('id')}: {field} ausentes ou não resolvidos")

    for fact in facts:
        if not fact.get("text") or fact.get("nature") not in {"fato", "alegacao", "prova", "decisao", "inferencia", "lacuna"}:
            errors.append(f"{fact.get('id')}: texto ou natureza inválidos")
        if fact.get("origin") == "client":
            client = client_map.get(fact.get("client_record_id"), {})
            if not client.get("text") or not client.get("conversation_reference") or not fact.get("evidence_needed"):
                errors.append(f"{fact.get('id')}: relato do cliente sem registro/prova necessária")
        elif fact.get("origin") == "document":
            sources = fact.get("sources", [])
            if not isinstance(sources, list) or not sources:
                errors.append(f"{fact.get('id')}: fontes ausentes")
                continue
            for source in sources:
                if not isinstance(source, dict):
                    errors.append(f"{fact.get('id')}: fonte inválida")
                    continue
                page = pages.get((source.get("source_sha256"), source.get("pdf_page")))
                quote = source.get("quote")
                if not page or source.get("document_id") != page.get("document_id"):
                    errors.append(f"{fact.get('id')}: arquivo/página/document_id não resolvido")
                    continue
                searchable = page["text"]
                if source.get("image_id"):
                    images = [v for v in page.get("visuals", []) if v.get("image_id") == source["image_id"]]
                    searchable = "\n".join(v.get("semantic_description", "") for v in images)
                elif source.get("layer") == "vision":
                    searchable = page.get("vision", {}).get("description", "") + "\n" + page.get("vision", {}).get("transcription", "")
                if not isinstance(quote, str) or not quote.strip() or quote not in searchable:
                    errors.append(f"{fact.get('id')}: trecho não encontrado na fonte indicada")
        else:
            errors.append(f"{fact.get('id')}: origin deve ser client ou document")
    for norm in norms:
        if not official_url(str(norm.get("url", ""))):
            errors.append(f"{norm.get('id')}: URL oficial HTTPS necessária")
        for field in ("title", "provision", "quote", "official_text", "temporal_analysis", "jurisdiction", "hierarchy", "case_fit", "reviewed_by"):
            if not isinstance(norm.get(field), str) or not norm[field].strip():
                errors.append(f"{norm.get('id')}: {field} ausente")
        if norm.get("quote") and norm["quote"] not in norm.get("official_text", ""):
            errors.append(f"{norm.get('id')}: citação não pertence ao texto oficial registrado")
        if not date_valid(norm.get("accessed_on")) or norm.get("status") != "verified":
            errors.append(f"{norm.get('id')}: conferência individual pendente")
        if norm.get("kind") == "precedent":
            for field in ("court", "case_number", "decision_date", "holding", "binding_status", "distinguishing", "current_status"):
                if not norm.get(field):
                    errors.append(f"{norm.get('id')}: precedente sem {field}")
    if not issues:
        errors.append("Nenhuma questão jurídica fundamentada")
    for issue in issues:
        refs(issue, "fact_ids", fact_ids)
        refs(issue, "norm_ids", norm_ids)
        refs(issue, "request_ids", request_ids, required=False)
        for field in ("question", "subsumption", "counterargument", "response", "conclusion", "evidence_assessment"):
            if not issue.get(field):
                errors.append(f"{issue.get('id')}: {field} ausente")
        requirements = issue.get("requirements", [])
        if not isinstance(requirements, list) or not requirements:
            errors.append(f"{issue.get('id')}: análise requisito por requisito ausente")
        else:
            for requirement in requirements:
                if not isinstance(requirement, dict) or not requirement.get("rule") or requirement.get("assessment") not in {"supported", "disputed", "missing"} or not requirement.get("reason"):
                    errors.append(f"{issue.get('id')}: requisito inválido")
                else:
                    refs(requirement, "fact_ids", fact_ids, required=requirement.get("assessment") != "missing")
    for request in requests:
        refs(request, "issue_ids", issue_ids)
        refs(request, "fact_ids", fact_ids)
        if request.get("origin") not in {"existing", "user", "proposed"} or not request.get("text") or not request.get("compatibility"):
            errors.append(f"{request.get('id')}: pedido sem origem, texto ou compatibilidade")
    if not facts or not paragraphs:
        errors.append("Fatos e redação substantiva são necessários")
    piece_type = review.get("piece_type")
    if task == "petition":
        if piece_type not in PIECE_SECTIONS:
            errors.append("piece_type inválido")
        else:
            sections = {p.get("section") for p in paragraphs}
            errors.extend(f"Seção obrigatória ausente: {s}" for s in PIECE_SECTIONS[piece_type] if s not in sections)
        if not requests:
            errors.append("Peça sem pedidos")
    for paragraph in paragraphs:
        text = paragraph.get("text", "")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{paragraph.get('id')}: parágrafo vazio")
            continue
        if style_findings(text, initial=piece_type == "inicial" and paragraph.get("section") == "fatos"):
            errors.append(f"{paragraph.get('id')}: formulação incompatível com a voz jurídica")
        refs(paragraph, "fact_ids", fact_ids, required=paragraph.get("section") == "fatos")
        refs(paragraph, "norm_ids", norm_ids, required=False)
        refs(paragraph, "issue_ids", issue_ids, required=False)
        refs(paragraph, "request_ids", request_ids, required=paragraph.get("section") == "pedidos")
        if paragraph.get("section") == "fundamentos" and not paragraph.get("issue_ids"):
            errors.append(f"{paragraph.get('id')}: fundamento sem questão jurídica")
    represented_requests = {r for p in paragraphs for r in p.get("request_ids", [])}
    if task == "petition" and not request_ids <= represented_requests:
        errors.append("Pedidos estruturados ausentes da redação")
    represented_issues = {i for p in paragraphs for i in p.get("issue_ids", [])}
    if not issue_ids <= represented_issues:
        errors.append("Questões estruturadas ausentes da redação")
    if piece_type == "recurso":
        grounds = review.get("decision_grounds", [])
        if not grounds or any(not isinstance(g, dict) or not g.get("source_fact_id") in fact_ids or not g.get("response_issue_id") in issue_ids for g in grounds):
            errors.append("Recurso sem correspondência entre fundamentos da decisão e impugnações")
    for conflict in review.get("conflicts", []):
        if not isinstance(conflict, dict) or not conflict.get("treatment"):
            errors.append("Conflito sem tratamento explícito")
        else:
            refs(conflict, "fact_ids", fact_ids)
    closure = review.get("research_closure", {})
    if not isinstance(closure, dict) or not closure.get("searched_topics") or not closure.get("stop_reason"):
        errors.append("Pesquisa sem tópicos examinados e critério de encerramento")
    if not isinstance(review.get("unresolved"), list) or review.get("unresolved"):
        errors.append("Pendências jurídicas impedem conclusão final")
    try:
        from .review_integrity import check_support
    except ImportError:
        from review_integrity import check_support
    return list(dict.fromkeys(errors + check_numbers(review) + check_support(review, memory)))


def check_numbers(review: dict) -> list[str]:
    errors = []
    for calculation in review.get("calculations", []):
        try:
            operands = calculation["operands"]
            if not operands or any(not x.get("source_fact_id") in {f["id"] for f in review["facts"]} for x in operands):
                raise ValueError("Operandos sem fonte")
            values = [Decimal(x["value"]) for x in operands]
            if not all(v.is_finite() for v in values):
                raise ValueError("Valor não finito")
            if calculation["operation"] == "sum":
                result = sum(values, Decimal(0))
            elif calculation["operation"] == "subtract" and len(values) == 2:
                result = values[0] - values[1]
            else:
                raise ValueError("Operação não suportada")
            if result != Decimal(calculation["result"]):
                errors.append(f"Cálculo divergente: {calculation.get('id')}")
        except (KeyError, TypeError, ValueError, InvalidOperation):
            errors.append("Cálculo sem premissas/operandos válidos; não executado")
    for period in review.get("periods", []):
        try:
            if not period.get("source_fact_ids") or not set(period["source_fact_ids"]) <= {f["id"] for f in review["facts"]}:
                raise ValueError("Período sem fonte")
            if date.fromisoformat(period["start"]) > date.fromisoformat(period["end"]):
                errors.append(f"Período invertido: {period.get('id')}")
        except (KeyError, TypeError, ValueError):
            errors.append("Período sem datas ISO ou fontes válidas")
    return errors


def render_review(review: dict) -> str:
    lines = ["# " + review.get("title", "Análise jurídica"), "", "RASCUNHO — NÃO PROTOCOLAR.", ""]
    facts = {f["id"]: f for f in review["facts"]}
    norms = {n["id"]: n for n in review["norms"]}
    section = None
    for paragraph in review["paragraphs"]:
        if paragraph.get("section") != section:
            section = paragraph.get("section")
            lines.extend(["## " + str(section).replace("_", " ").capitalize(), ""])
        lines.extend([paragraph["text"], ""])
        citations = []
        for fact_id in paragraph.get("fact_ids", []):
            fact = facts[fact_id]
            for source in fact.get("sources", []):
                label = f"{source.get('piece', 'Fonte')} — PDF p. {source['pdf_page']}"
                label += f" — arquivo {source.get('file', source.get('source_sha256', ''))} — SHA-256 {source.get('source_sha256', '')} — document_id {source.get('document_id', '')}"
                if source.get("court_page") is not None:
                    label += f" — fl. {source['court_page']}"
                if source.get("image_id"):
                    label += f" — imagem {source['image_id']}"
                citations.append(label)
        citations += [f"[{norms[n]['title']} — {norms[n]['provision']}]({norms[n]['url']})" for n in paragraph.get("norm_ids", [])]
        if citations:
            lines.extend(["Fontes: " + "; ".join(dict.fromkeys(citations)) + ".", ""])
    return "\n".join(lines)


def finalize(output: Path, review_path: Path) -> dict:
    memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8-sig"))
    try:
        review = json.loads(review_path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        return {"status": "review_required", "errors": [f"Revisão não carregada: {exc}"]}
    try:
        try:
            from .contracts import validate_contract
        except ImportError:
            from contracts import validate_contract
        errors = validate_contract(review, "legal_review.schema.json")
        if not errors:
            errors = validate_review(review, memory)
        for norm in review.get("norms", []) if isinstance(review, dict) else []:
            capture_id = norm.get("capture_id", "")
            if not isinstance(capture_id, str) or not re.fullmatch(r"[a-f0-9]{64}", capture_id):
                errors.append(f"{norm.get('id')}: captura oficial ausente")
                continue
            path = output / "research_sources" / f"{capture_id}.json"
            if not path.is_file():
                errors.append(f"{norm.get('id')}: captura oficial não encontrada")
                continue
            receipt = json.loads(path.read_text(encoding="utf-8-sig"))
            raw_path = path.with_suffix(".source")
            if not raw_path.is_file() or hashlib.sha256(raw_path.read_bytes()).hexdigest() != receipt.get("raw_content_hash"):
                errors.append(f"{norm.get('id')}: resposta oficial bruta ausente ou alterada")
            if receipt.get("method") != "official_http_capture" or identity({k: v for k, v in receipt.items() if k != "capture_id"}) != capture_id:
                errors.append(f"{norm.get('id')}: identidade/método da captura inválidos")
            expected_text_hash = hashlib.sha256(str(receipt.get("text", "")).encode("utf-8")).hexdigest()
            if receipt.get("url") != norm.get("url") or receipt.get("accessed_on") != norm.get("accessed_on") or receipt.get("text_hash") != expected_text_hash or norm.get("official_text") != receipt.get("text"):
                errors.append(f"{norm.get('id')}: fonte diverge da captura preservada")
    except (TypeError, KeyError, AttributeError, ValueError):
        errors = ["Estrutura de revisão inválida; confira o contrato antes de entregar"]
    full_coverage = bool(memory["documents"]) and all(d["coverage"].get("full_conversion_complete") for d in memory["documents"])
    if not full_coverage:
        errors.append("Corpus com cobertura incompleta: resolver camadas pendentes")
    report = {"status": "review_required" if errors else "ready_for_professional_review", "errors": errors,
              "corpus_revision": memory["corpus_revision"], "review_sha256": identity(review),
              "scope": "consistência estrutural e rastreabilidade; mérito depende da revisão jurídica"}
    report.update(technical_status="failed" if errors else "passed", substantive_status="professional_review_required",
                  can_issue_final_legal_conclusion=False)
    receipt_dir = output / "legal_reviews" / identity(review)
    atomic_json(receipt_dir / "review.json", review)
    atomic_json(receipt_dir / "validation.json", report)
    atomic_json(output / "legal_review_validation.json", report)
    # Never overwrite a deliverable with an invalid or stale review.
    if not errors:
        text = render_review(review)
        atomic_text(receipt_dir / "entrega.md", text)
        atomic_text(output / ("minuta_peca.md" if review["task"] == "petition" else "analise_juridica.md"), text)
        atomic_json(output / "ficha_estrategica.json", review["strategy"])
        atomic_json(output / "legal_review.json", review)
        base_path = output / "legal_basis.json"
        if base_path.exists():
            basis = json.loads(base_path.read_text(encoding="utf-8-sig"))
            basis["candidate_history"] = basis.get("candidate_history", []) + basis.get("legal_sources", [])
            basis["legal_sources"] = [{**n, "name": n["title"], "reference": n["provision"], "verification_status": "verified"} for n in review["norms"]]
            basis["verification"] = {"status": "verified", "review_sha256": report["review_sha256"]}
            atomic_json(base_path, basis)
        atomic_json(output / "quality_gate.json", {
            "schema_version": "1.1", "task": review["task"], "status": "passed", "blocking_gates": [],
            "can_describe_corpus": True, "can_issue_final_legal_conclusion": False,
            "rules": ["Validação técnica não certifica mérito; minuta exige revisão profissional."],
            "substantive_status": "professional_review_required",
            "scope": report["scope"], "review_sha256": report["review_sha256"],
            "gates": {name: {"status": "passed"} for name in ("coverage", "provenance", "legal_verification", "narrative_style", "issue_request_consistency")},
        })
        atomic_text(output / "quality_gate.md", "# VALIDAÇÃO DA ENTREGA\n\n" + report["scope"] + "\n\nReferências, capturas oficiais, cobertura, cálculos declarados e redação passaram nos controles automáticos. A avaliação de mérito é a registrada pela IA/revisor.\n")
        # Keep analytical reasoning separate from the court-facing deliverable.
        reasoning = ["# FUNDAMENTAÇÃO ESTRATÉGICA", ""]
        for issue in review["issues"]:
            reasoning.extend(["## " + issue["question"], "", issue["subsumption"], "",
                              "Contraponto: " + issue["counterargument"], "", "Resposta: " + issue["response"], "",
                              "Prova: " + issue["evidence_assessment"], "", issue["conclusion"], ""])
        atomic_text(output / "fundamentacao_estrategica.md", "\n".join(reasoning))
    else:
        atomic_json(output / "quality_gate.json", {"schema_version": "1.1", "task": review.get("task", "analyze") if isinstance(review, dict) else "analyze", "can_describe_corpus": full_coverage, "rules": ["Revisão reprovada; não usar entregas anteriores como atuais."], "status": "review_required", "blocking_gates": ["legal_review"],
                    "can_issue_final_legal_conclusion": False, "errors": errors, "gates": {"legal_verification": {"status": "review_required"}}})
        atomic_text(output / "quality_gate.md", "# REVISÃO PENDENTE\n\n" + "\n".join("- " + e for e in errors))
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        manifest["legal_review"] = report
        manifest["authorial_deliverable_status"] = "invalid_current_review" if errors else "draft_for_professional_review"
        manifest["quality_gate"] = json.loads((output / "quality_gate.json").read_text(encoding="utf-8"))
        generated = ["legal_review_validation.json", "legal_review.json", "ficha_estrategica.json", "fundamentacao_estrategica.md", "quality_gate.json", "quality_gate.md", "minuta_peca.md", "analise_juridica.md"]
        manifest["generated_files"] = list(dict.fromkeys(manifest.get("generated_files", []) + [n for n in generated if (output / n).is_file()]))
        try:
            from .helpers import sha256_file, write_process_bundle
        except ImportError:
            from helpers import sha256_file, write_process_bundle
        manifest["artifact_hashes"] = {name: sha256_file(output / name) for name in manifest["generated_files"] if name not in {"manifest.json", "processo_completo.zip"} and (output / name).is_file()}
        atomic_json(manifest_path, manifest)
        write_process_bundle(output)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Confere a síntese jurídica produzida pela IA e gera a entrega.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--review", type=Path, required=True)
    args = parser.parse_args()
    result = finalize(args.output.resolve(), args.review.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
