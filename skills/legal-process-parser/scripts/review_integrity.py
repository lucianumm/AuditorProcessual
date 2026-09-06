"""Conservative evidence checks. These checks do not prove semantic entailment."""
from __future__ import annotations

import re
import unicodedata

try:
    from .case_memory import page_revision
except ImportError:
    from case_memory import page_revision


def normalized(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn")


def opposite_polarity(left: str, right: str) -> bool:
    """Flag same words with negation added/removed; not general contradiction detection."""
    def tokens(text):
        return re.findall(r"\w+", normalized(text))
    a, b = tokens(left), tokens(right)
    negative = {"nao", "nunca", "jamais"}
    return bool(set(a) & negative) != bool(set(b) & negative) and [x for x in a if x not in negative] == [x for x in b if x not in negative]


def check_support(review: dict, memory: dict) -> list[str]:
    errors = []
    pages = {f"{d['sha256']}:{p['pdf_page']}": p for d in memory["documents"] for p in d["pages"]}
    ledger = review.get("page_reviews", [])
    if not isinstance(ledger, list):
        return ["page_reviews deve ser lista"]
    recorded = set()
    fact_ids = {f.get("id") for f in review.get("facts", [])}
    for entry in ledger:
        key = entry.get("page_id")
        page = pages.get(key)
        if not page or key in recorded:
            errors.append("Revisão por página desconhecida/duplicada")
            continue
        recorded.add(key)
        if entry.get("content_revision") != page_revision(page):
            errors.append(f"{key}: revisão de conteúdo desatualizada")
        if entry.get("relevance") not in {"relevant", "context", "technical", "blank"} or not entry.get("findings") or not entry.get("reviewed_by"):
            errors.append(f"{key}: registrar relevância, achados/contexto e revisor")
        if not isinstance(entry.get("fact_ids"), list) or not set(entry["fact_ids"]) <= fact_ids:
            errors.append(f"{key}: fatos da revisão não resolvidos")
        if entry.get("relevance") == "relevant" and not entry.get("fact_ids"):
            errors.append(f"{key}: página relevante sem proposições extraídas")
    if recorded != set(pages):
        errors.append("Revisão substantiva por página incompleta (page_reviews)")
    for fact in review.get("facts", []):
        support = fact.get("support", {})
        if not isinstance(support, dict) or support.get("assessment") not in {"direct", "inference", "client_account", "disputed"} or not support.get("reason") or not support.get("reviewed_by"):
            errors.append(f"{fact.get('id')}: avaliação de suporte ausente")
        for source in fact.get("sources", []):
            if opposite_polarity(fact.get("text", ""), source.get("quote", "")):
                errors.append(f"{fact.get('id')}: negação contradiz o trecho citado")
            left, right = normalized(fact.get("text", "")), normalized(source.get("quote", ""))
            pattern = r"\d+(?:[.,/]\d+)*"
            if re.sub(pattern, "<number>", left) == re.sub(pattern, "<number>", right) and re.findall(pattern, left) != re.findall(pattern, right):
                errors.append(f"{fact.get('id')}: valores/datas divergem do trecho citado")
    facts = {f["id"]: f for f in review.get("facts", [])}
    for paragraph in review.get("paragraphs", []):
        for fid in paragraph.get("fact_ids", []):
            if fid in facts and opposite_polarity(paragraph.get("text", ""), facts[fid].get("text", "")):
                errors.append(f"{paragraph.get('id')}: negação contradiz o fato vinculado")
    for issue in review.get("issues", []):
        for requirement in issue.get("requirements", []):
            if requirement.get("assessment") in {"missing", "disputed"} and not requirement.get("treatment"):
                errors.append(f"{issue.get('id')}: requisito faltante/controvertido sem estratégia explícita")
        research = issue.get("research", {})
        if not isinstance(research, dict) or not all(research.get(k) for k in ("material_law", "procedure", "temporal_scope", "jurisdiction", "contrary_authorities", "closure_reason")):
            errors.append(f"{issue.get('id')}: pesquisa por questão incompleta")
    for request in review.get("requests", []):
        kind = request.get("priority", "principal")
        if kind not in {"principal", "subsidiary", "alternative"}:
            errors.append(f"{request.get('id')}: prioridade de pedido inválida")
        if kind != "principal" and not request.get("condition"):
            errors.append(f"{request.get('id')}: pedido subsidiário/alternativo sem condição")
    return errors
