"""Structured consolidation of approved chapters into one pleading draft.

The text joins the authored chapters in the chosen order and derives from the
analysis only what is mechanical: numbering, the requests section with their
nature and condition, the claim value from executed calculation lines, the
evidence still to be produced and the list of documents referred to. Every
field the analysis cannot fill is marked [CONFIRMAR] or DEFINIR; nothing is
filed and the draft remains RASCUNHO — NÃO PROTOCOLAR.
"""
from __future__ import annotations

from decimal import Decimal

DRAFT = "RASCUNHO — NÃO PROTOCOLAR"
NATURE = {"principal": "pedido principal", "subsidiary": "pedido subsidiário", "alternative": "pedido alternativo"}


def brl(value: Decimal) -> str:
    whole, _, cents = f"{value.quantize(Decimal('0.01')):.2f}".partition(".")
    sign = "-" if whole.startswith("-") else ""
    return "R$ " + sign + f"{int(whole.lstrip('-')):,}".replace(",", ".") + "," + cents


def claim_value(review: dict, request_ids: list[str]) -> dict:
    """Sum of executed lines of the principal requests (subsidiary and alternative requests are not added)."""
    requests = {r["id"]: r for r in review.get("requests", [])}
    principal = [r for r in request_ids if requests.get(r, {}).get("priority", "principal") == "principal"]
    items = review.get("labor_review", {}).get("calculation_set", {}).get("items", [])
    per_request: dict[str, Decimal] = {}
    for item in items:
        if not item.get("include_in_total", True):
            continue
        owners = [r for r in item.get("request_ids", []) if r in principal]
        if owners:
            # A line shared by several principal requests is counted once, under the first.
            per_request[owners[0]] = per_request.get(owners[0], Decimal("0")) + Decimal(str(item["expected_result"]))
    estimated = {}
    for rid in principal:
        if rid not in per_request and requests.get(rid, {}).get("estimated_value") not in (None, ""):
            # Estimate recorded in the analysis (e.g. labor initial with value indicated by estimate).
            estimated[rid] = Decimal(str(requests[rid]["estimated_value"]))
    undefined = [r for r in principal if r not in per_request and r not in estimated]
    total = sum(per_request.values(), Decimal("0")) + sum(estimated.values(), Decimal("0"))
    return {"total": str(total), "per_request": {k: str(v) for k, v in per_request.items()},
            "estimated": {k: str(v) for k, v in estimated.items()}, "undefined_request_ids": undefined,
            "rule": "Soma das linhas executadas dos pedidos principais; subsidiários e alternativos não somados.",
            "status": "to_confirm"}


def labor_value_findings(review: dict, value: dict) -> list[str]:
    """Labor initial: requests must indicate a value (calculated or estimated); confirm the CLT wording in the response."""
    if not review.get("labor_review") or review.get("piece_type") != "inicial" or not value["undefined_request_ids"]:
        return []
    return ["Reclamação trabalhista com pedido sem indicação de valor (" + ", ".join(value["undefined_request_ids"]) +
            "): quantificar por motor determinístico ou registrar estimativa fundamentada (conferir a redação vigente "
            "do art. 840, § 1º, e do art. 852-B, I, da CLT)"]


def _page_label(source: dict, names: dict) -> str:
    name = names.get(source.get("source_sha256"), source.get("document_id", "documento"))
    label = f"{name}, p. {source.get('pdf_page')}"
    if source.get("court_page"):
        label += f" (fl. {source['court_page']})"
    return label


def compose(selected: list[dict], review: dict, request_owners: dict, memory: dict | None = None,
            declared_value: str | None = None) -> dict:
    names = {d.get("sha256"): d.get("name") for d in (memory or {}).get("documents", [])}
    requests = {r["id"]: r for r in review.get("requests", [])}
    facts = {f["id"]: f for f in review.get("facts", [])}
    assertions = {a["fact_id"]: a for a in review.get("assertion_reviews", [])}
    numbers = {c["id"]: str(index) for index, c in enumerate(selected, 1)}
    lines = ["# CONSOLIDAÇÃO DOS CAPÍTULOS SELECIONADOS", "", DRAFT, "",
             "[CONFIRMAR: endereçamento, qualificação completa das partes, representação e procuração]", ""]
    for chapter in selected:
        lines += ["## " + numbers[chapter["id"]] + ". " + chapter["title"].replace("\n", " "), ""]
        lines += ["\n\n".join(p["text"] for p in chapter["paragraphs"]), ""]
    n = len(selected)
    sections = {str(i) for i in range(1, n + 5)}
    lines += [f"## {n + 1}. Dos pedidos", "", "Ante o exposto, requer:", ""]
    ordered = [r for c in selected for r in c["request_ids"]]
    for index, rid in enumerate(ordered, 1):
        request = requests.get(rid, {"text": "DEFINIR"})
        nature = request.get("priority", "principal")
        prefix = {"subsidiary": "Subsidiariamente", "alternative": "Alternativamente"}.get(nature)
        condition = request.get("condition")
        text = request.get("text", "DEFINIR").rstrip(".")
        if prefix:
            text = prefix + (", " + condition.rstrip(".") if condition else ", [DEFINIR condição de apreciação]") + ": " + text[0].lower() + text[1:]
        lines.append(f"{index}. {text} (fundamentos no item {numbers[request_owners[rid]]}).")
    value = claim_value(review, ordered)
    lines += ["", f"## {n + 2}. Das provas", ""]
    proofs = []
    for chapter in selected:
        for fid in dict.fromkeys(f for p in chapter["paragraphs"] for f in p.get("fact_ids", [])):
            needed = facts.get(fid, {}).get("evidence_needed")
            if needed and assertions.get(fid, {}).get("evidence_status") != "supported" and needed not in proofs:
                proofs.append(needed)
    if proofs:
        lines += ["Requer a produção das provas a seguir, sem prejuízo de outras admitidas [CONFIRMAR]:", ""]
        lines += ["- " + proof for proof in proofs]
    else:
        lines.append("[CONFIRMAR: provas a produzir; os fatos vinculados têm apoio documental registrado]")
    lines += ["", f"## {n + 3}. Do valor da causa", ""]
    amount = Decimal(value["total"])
    statement = (f"[CONFIRMAR] Atribui-se à causa o valor de {brl(amount)}" if amount else "[CONFIRMAR] Valor da causa: DEFINIR")
    if value["estimated"]:
        statement += " (inclui estimativa registrada na análise para " + ", ".join(
            f"item {ordered.index(r) + 1}" for r in value["estimated"]) + ")"
    if value["undefined_request_ids"]:
        statement += "; pedidos sem quantificação a definir: " + ", ".join(
            f"item {ordered.index(r) + 1}" for r in value["undefined_request_ids"])
    lines.append(statement + ".")
    if declared_value is not None:
        declared = Decimal(str(declared_value))
        value["declared"] = str(declared)
        if declared != amount:
            value["divergence"] = str(declared - amount)
            lines.append(f"[CONFERIR: valor informado {brl(declared)} difere da soma calculada {brl(amount)}.]")
    lines += ["", f"## {n + 4}. Documentos referidos", ""]
    documents = []
    for chapter in selected:
        for fid in dict.fromkeys(f for p in chapter["paragraphs"] for f in p.get("fact_ids", [])):
            for source in facts.get(fid, {}).get("sources", []):
                label = _page_label(source, names)
                if label not in documents:
                    documents.append(label)
    lines += ["- " + d for d in documents] if documents else ["[CONFIRMAR: rol de documentos]"]
    lines += ["", DRAFT, ""]
    return {"text": "\n".join(lines), "sections": sections, "claim_value": value, "proofs": proofs,
            "documents": documents, "numbering": numbers}


def traceability_matrix(selected: list[dict], review: dict, cards: list[dict], numbers: dict, memory: dict | None = None) -> str:
    """Technical annex, outside the text addressed to the court."""
    names = {d.get("sha256"): d.get("name") for d in (memory or {}).get("documents", [])}
    facts = {f["id"]: f for f in review.get("facts", [])}
    norms = {n["id"]: n for n in review.get("norms", [])}
    owners = {r: c for c in selected for r in c["request_ids"]}
    state = {"supported": "sustentado", "conditioned": "condicionado", "decisive_gap": "lacuna decisiva"}
    lines = ["# MATRIZ DE RASTREABILIDADE (anexo técnico, não dirigido ao juízo)", "", DRAFT, "",
             "| Pedido | Item/§ | Fatos | Prova (doc/pág/fl.) | Norma conferida (data) | Estado |", "|---|---|---|---|---|---|"]
    for card in cards:
        chapter = owners.get(card["request_id"])
        if not chapter:
            continue
        paragraphs = [p for p in chapter["paragraphs"] if card["request_id"] in p.get("request_ids", [])]
        fids = sorted({f for p in chapter["paragraphs"] for f in p.get("fact_ids", [])})
        nids = sorted({n for p in chapter["paragraphs"] for n in p.get("norm_ids", [])})
        proof = "; ".join(_page_label(s, names) for f in fids for s in facts.get(f, {}).get("sources", [])) or "relato/prova a produzir"
        norm = "; ".join(f"{norms[n].get('provision', n)} ({norms[n].get('accessed_on', '?')})" for n in nids if n in norms) or "—"
        place = numbers[chapter["id"]] + " §" + ",".join(p["id"] for p in paragraphs)
        cell = lambda value: str(value).replace("|", "/").replace("\n", " ")
        lines.append("| " + " | ".join(cell(v) for v in (card["request_id"], place, ", ".join(fids) or "—", proof, norm,
                                                          state[card["status"]] + " — " + card["reason"])) + " |")
    return "\n".join(lines) + "\n"
