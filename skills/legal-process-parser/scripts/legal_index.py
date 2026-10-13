"""Navigable legal index. Entries are attributed declarations, not new findings."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

try:
    from .case_memory import atomic_json, atomic_text
except ImportError:
    from case_memory import atomic_json, atomic_text


def anchor(kind: str, identifier: str) -> str:
    import hashlib
    return kind + "-" + hashlib.sha256(identifier.encode()).hexdigest()[:20]


def safe_text(value) -> str:
    return (str(value or "").replace("&", "&amp;").replace("\n", " ").replace("|", "\\|")
            .replace("<", "&lt;").replace(">", "&gt;").replace("[", "&#91;").replace("]", "&#93;"))


def build_legal_index(output: Path, memory: dict, review: dict | None = None) -> dict:
    documents = {doc["sha256"]: doc for doc in memory.get("documents", [])}
    entries = []
    lines = ["# ÍNDICE JURÍDICO E DE FONTES", "",
             "Localizador cumulativo; não substitui leitura integral nem certifica a interpretação.", "",
             f"Corpus: `{memory['corpus_revision']}`", ""]
    if review:
        current = review.get("corpus_revision") == memory["corpus_revision"]
        lines += ["Revisão jurídica: " + ("vinculada ao corpus" if current else "ANTERIOR — reavaliar") + ".", ""]
        try:
            from .research_memory import research_revision
        except ImportError:
            from research_memory import research_revision
        current_research = research_revision(output)
        if review.get("research_revision"):
            lines += ["Fontes consultadas: " + ("snapshot atual" if review["research_revision"] == current_research else "ANTERIOR — fonte consultada alterada; reavaliar") + ".", ""]
        else:
            lines += ["Fontes da revisão legada: snapshot de pesquisa não registrado.", ""]
    lines += ["## Arquivos e páginas", ""]
    accounts = (review or {}).get("client_records", []) or memory.get("client_records", [])
    if accounts:
        lines += ["## Relatos e referências de atendimento", ""]
        for account in accounts:
            aid = anchor("client", account["id"])
            label = safe_text(account["text"])
            entries.append({"kind": "client", "id": account["id"], "anchor": aid,
                            "label": account["text"], "conversation_reference": account["conversation_reference"]})
            lines += [f'<a id="{aid}"></a>', "### " + safe_text(account["id"]), "", label, "",
                      "Origem: " + safe_text(account["conversation_reference"]) + ". Relato do cliente.", ""]
    for digest, doc in documents.items():
        prefix = "" if doc.get("folder", ".") == "." else doc["folder"] + "/"
        target_markdown = output / prefix / "processo_completo.md"
        source_text = target_markdown.read_text(encoding="utf-8-sig") if target_markdown.is_file() else ""
        for page in doc.get("pages", []):
            pid = f"{digest}:{page['pdf_page']}"
            aid = anchor("page", pid)
            fragment = f"p{page['pdf_page']:04d}"
            if f'id="{fragment}"' not in source_text:
                fragment = f"página-pdf-{page['pdf_page']}"  # Legacy v1–v3 heading slug.
            link = quote(prefix + "processo_completo.md", safe="/") + "#" + quote(fragment)
            label = "PDF p." if doc.get("page_unit", "pdf_page") == "pdf_page" else "segmento lógico"
            display = f"{doc['name']} — {label} {page['pdf_page']} — {page.get('piece', '')}"
            entries.append({"kind":"page", "id":pid, "anchor":aid, "label":display, "source_link":link,
                            "document_id":page.get("document_id"), "dates":page.get("dates", []), "entities":page.get("entities", {})})
            lines += [f'<a id="{aid}"></a>', f"- [{safe_text(display)}]({link})", ""]
    for kind, field, title, display_key in (
        ("fact", "facts", "Fatos e provas", "text"), ("issue", "issues", "Questões jurídicas", "question"),
        ("norm", "norms", "Normas e precedentes", "title"), ("norm_application", "norm_applications", "Integração normativa", "basis_for_use"),
        ("thesis", "theses", "Teses", "proposition"), ("request", "requests", "Pedidos", "text"),
        ("paragraph", "paragraphs", "Redação", "text")):
        items = (review or {}).get(field, [])
        if not items:
            continue
        lines += [f"## {title}", ""]
        for item in items:
            aid = anchor(kind, item["id"])
            label = safe_text(item.get(display_key, ""))
            links = []
            for source in item.get("sources", []):
                pid = f"{source.get('source_sha256')}:{source.get('pdf_page')}"
                doc = documents.get(source.get("source_sha256"), {})
                text = safe_text(f"{doc.get('name', 'fonte não resolvida')} — página/segmento {source.get('pdf_page')}")
                links.append(f"[{text}](#{anchor('page', pid)})")
            for reference, other_kind in (("fact_ids", "fact"), ("norm_ids", "norm"), ("issue_ids", "issue"),
                                          ("request_ids", "request"), ("norm_application_ids", "norm_application")):
                links.extend(f"[{safe_text(identifier)}](#{anchor(other_kind, identifier)})" for identifier in item.get(reference, []))
            if item.get("issue_id"):
                links.append(f"[{safe_text(item['issue_id'])}](#{anchor('issue', item['issue_id'])})")
            if item.get("norm_id"):
                links.append(f"[{safe_text(item['norm_id'])}](#{anchor('norm', item['norm_id'])})")
            entries.append({"kind":kind, "id":item["id"], "anchor":aid, "label":item.get(display_key, ""), "links":links})
            lines += [f'<a id="{aid}"></a>', f"### {safe_text(item['id'])}", "", label, "", " · ".join(links), ""]
    if (review or {}).get("labor_review"):
        try:
            from .labor_analysis import labor_entries
        except ImportError:
            from labor_analysis import labor_entries
        lines += ["## Relações, períodos e verificações trabalhistas",""]
        for item in labor_entries(review):
            aid = anchor("labor",item["id"])
            links = []
            for field,kind in (("fact_ids","fact"),("norm_ids","norm"),("request_ids","request"),("issue_ids","issue")):
                links += [f"[{safe_text(identifier)}](#{anchor(kind,identifier)})" for identifier in item.get(field,[])]
            if item.get("norm_id"):
                links.append(f"[{safe_text(item['norm_id'])}](#{anchor('norm',item['norm_id'])})")
            if item.get("client_record_id"):
                links.append(f"[{safe_text(item['client_record_id'])}](#{anchor('client',item['client_record_id'])})")
            if item.get("issue_id"):
                links.append(f"[{safe_text(item['issue_id'])}](#{anchor('issue',item['issue_id'])})")
            entries.append({"kind":"labor","id":item["id"],"anchor":aid,"label":item["label"],"links":links})
            lines += [f'<a id="{aid}"></a>',"### " + safe_text(item["id"]),"",safe_text(item["label"]),""," · ".join(links),""]
    index = {"schema_version":"1.0", "corpus_revision":memory["corpus_revision"],
             "review_revision":(review or {}).get("corpus_revision"),
             "review_research_revision":(review or {}).get("research_revision"), "entries":entries}
    atomic_json(output / "indice_juridico.json", index)
    atomic_text(output / "indice_juridico.md", "\n".join(lines))
    return index
