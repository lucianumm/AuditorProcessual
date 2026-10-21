"""Flag observable prose overreach; this is not a semantic certification."""
from __future__ import annotations

import re
from decimal import Decimal

try:
    from .numeric_criteria import quantities, fold
except ImportError:
    from numeric_criteria import quantities, fold


def prose_errors(paragraph: dict, review: dict) -> list[str]:
    # Explicit block quotations are source text, not the author's assertions.
    text = "\n".join(line for line in paragraph["text"].splitlines() if not line.lstrip().startswith(">"))
    normalized = fold(text)
    facts = {f["id"]: f for f in review.get("facts", [])}
    assertions = {a["fact_id"]: a for a in review.get("assertion_reviews", [])}
    norms = {n["id"]: n for n in review.get("norms", [])}
    linked = [assertions.get(fid, {}) for fid in paragraph.get("fact_ids", [])]
    errors = []
    def asserted(pattern):
        return any(not re.search(r"\b(?:nao|nunca|sem)\b[^.;:!?]{0,25}$", normalized[max(0, m.start() - 30):m.start()])
                   for m in re.finditer(pattern, normalized))
    if asserted(r"\b(?:comprovad[oa]s?|demonstrad[oa]s? documentalmente)\b") and linked and any(
            a.get("evidence_status") != "supported" for a in linked):
        errors.append("afirmação de comprovação sem apoio conferido de todos os fatos vinculados")
    # Documentary support alone does not mean the opposing party admitted a fact.
    if asserted(r"\bincontrovers[oa]s?\b"):
        support = " ".join(facts.get(fid, {}).get("text", "") for fid in paragraph.get("fact_ids", []))
        if not re.search(r"\b(?:admit|incontrovers|confess)", fold(support)):
            errors.append("incontrovérsia sem admissão/confissão identificável nos fatos vinculados")
    sources = " ".join(facts.get(fid, {}).get("text", "") for fid in paragraph.get("fact_ids", []))
    sources += " " + " ".join(norms.get(nid, {}).get("quote", "") for nid in paragraph.get("norm_ids", []))
    allowed = {(Decimal(q["value"]), q["unit"]) for q in quantities(sources)}
    for a in linked:
        atoms = a.get("atoms", {})
        if atoms.get("amount") is not None:
            allowed.add((Decimal(str(atoms["amount"])), "money"))
    calculation = review.get("labor_review", {}).get("calculation_set", {})
    # Include only calculation lines belonging to this paragraph's requests.
    for item in calculation.get("items", []):
        if set(item["request_ids"]) & set(paragraph.get("request_ids", [])):
            allowed.add((Decimal(item["expected_result"]), "money"))
    for q in quantities(text):
        if q["unit"] == "number":
            continue
        if (Decimal(q["value"]), q["unit"]) not in allowed:
            errors.append("quantidade na prosa sem suporte vinculado: " + q["text"])
    return list(dict.fromkeys(errors))


def audit_prose(review: dict, paragraphs: list[dict] | None = None) -> dict:
    rows = [{"paragraph_id": p["id"], "errors": prose_errors(p, review)} for p in (paragraphs if paragraphs is not None else review.get("paragraphs", []))]
    return {"paragraphs": rows, "status": "requires_review" if any(r["errors"] for r in rows) else "no_observable_mismatch",
            "scope": "Literal quantities and explicit overclaiming; unregistered semantic claims still require full host review."}
