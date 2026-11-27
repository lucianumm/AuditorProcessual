"""Flag observable prose overreach; this is not a semantic certification."""
from __future__ import annotations

import re
from decimal import Decimal

try:
    from .numeric_criteria import quantities, fold
    from .prose_dates import find_dates, find_periods, harvest, date_supported
    from .review_integrity import atom_polarity_conflict, verb_stem
except ImportError:
    from numeric_criteria import quantities, fold
    from prose_dates import find_dates, find_periods, harvest, date_supported
    from review_integrity import atom_polarity_conflict, verb_stem

ROLES = {"ativo": r"\b(?:reclamante|autor[a]?|requerente|demandante|empregad[oa]|trabalhador[a]?|obreir[oa])\b",
         "passivo": r"\b(?:reclamad[oa]|re|reu|requerid[oa]|demandad[oa]|empregador[a]?|empresa)\b",
         "perito": r"\bperit[oa]\b", "juizo": r"\b(?:juizo|juiz[a]?|magistrad[oa]|tribunal)\b"}


def role_of(text: str) -> str | None:
    folded = fold(text or "")
    hits = [role for role, rx in ROLES.items() if re.search(rx, folded)]
    return hits[0] if len(hits) == 1 else None


def linked_sources(paragraph: dict, review: dict) -> list:
    """Structured records the paragraph declares as its support."""
    fids, nids = set(paragraph.get("fact_ids", [])), set(paragraph.get("norm_ids", []))
    facts = [f for f in review.get("facts", []) if f.get("id") in fids]
    cids = {f.get("client_record_id") for f in facts}
    labor = review.get("labor_review", {})
    return (facts + [a for a in review.get("assertion_reviews", []) if a.get("fact_id") in fids] +
            [n for n in review.get("norms", []) if n.get("id") in nids] +
            [m for m in review.get("normative_map", []) if m.get("norm_id") in nids or
             any(set(d.get("fact_ids", [])) & fids for d in m.get("relevant_dates", []))] +
            [c for c in review.get("client_records", []) if c.get("id") in cids] +
            [r for r in labor.get("contract_periods", []) + labor.get("relationships", []) if set(r.get("fact_ids", [])) & fids] +
            [p for p in review.get("periods", []) if isinstance(p, dict) and set(p.get("fact_ids", [])) & fids])


def date_errors(text: str, paragraph: dict, review: dict) -> list[str]:
    sources = linked_sources(paragraph, review)
    allowed = harvest(sources)
    errors = []
    for date in find_dates(text):
        reason = date_supported(date["value"], allowed)
        if reason:
            errors.append(reason + ": " + date["text"])
    bounds = [(a["atoms"].get("period_start"), a["atoms"].get("period_end")) for a in review.get("assertion_reviews", [])
              if a.get("fact_id") in paragraph.get("fact_ids", []) and a.get("atoms", {}).get("period_start")]
    for period in find_periods(text):
        start, end = period["start"]["value"], period["end"]["value"]
        if start[:len(end)] > end[:len(start)]:
            errors.append("período invertido na prosa: " + period["text"])
            continue
        if bounds:
            low = min(b[0] for b in bounds)
            high = max(b[1] or b[0] for b in bounds)
            if start[:len(low)] < low[:len(start)] or end[:len(high)] > high[:len(end)]:
                errors.append("período na prosa além do período apurado nos fatos vinculados: " + period["text"])
    return errors


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
    errors += date_errors(text, paragraph, review)
    for a in linked:
        if a.get("atoms") and atom_polarity_conflict(text, a["atoms"]):
            errors.append("polaridade da frase diverge do fato vinculado " + a.get("fact_id", "") + " (" + a["atoms"].get("action", "") + ")")
    return list(dict.fromkeys(errors))


def prose_warnings(paragraph: dict, review: dict) -> list[str]:
    """Heuristic signals for the author; they never block by themselves."""
    text = "\n".join(line for line in paragraph["text"].splitlines() if not line.lstrip().startswith(">"))
    warnings = []
    for a in review.get("assertion_reviews", []):
        if a.get("fact_id") not in paragraph.get("fact_ids", []):
            continue
        atoms = a.get("atoms", {})
        actor, action = role_of(atoms.get("actor", "")), fold(atoms.get("action", "")).split()
        if not actor or not action or len(action[0]) < 4:
            continue
        stem = verb_stem(action[0])
        for sentence in re.split(r"(?<=[.;!?])\s+", fold(text)):
            found = re.search(r"\b" + re.escape(stem), sentence)
            if not found:
                continue
            before = sentence[:found.start()]
            roles = [(m.start(), role) for role, rx in ROLES.items() for m in re.finditer(rx, before)]
            if roles and max(roles)[1] != actor:
                warnings.append("sujeito da frase (" + max(roles)[1] + ") difere do ator do fato " + a["fact_id"] + " (" + actor + ")")
    words = len(re.findall(r"\w+", text))
    if words > 220:
        warnings.append("parágrafo longo (" + str(words) + " palavras); considerar dividir")
    for sentence in re.split(r"(?<=[.;!?])\s+", text):
        if len(re.findall(r"\w+", sentence)) > 60:
            warnings.append("frase acima de 60 palavras")
            break
    quoted = sum(len(line) for line in paragraph["text"].splitlines() if line.lstrip().startswith(">"))
    if quoted > 1200:
        warnings.append("citação literal extensa (" + str(quoted) + " caracteres); transcrever só o trecho necessário")
    return list(dict.fromkeys(warnings))


def audit_prose(review: dict, paragraphs: list[dict] | None = None) -> dict:
    rows = [{"paragraph_id": p["id"], "errors": prose_errors(p, review), "warnings": prose_warnings(p, review)}
            for p in (paragraphs if paragraphs is not None else review.get("paragraphs", []))]
    return {"paragraphs": rows, "status": "requires_review" if any(r["errors"] for r in rows) else "no_observable_mismatch",
            "scope": "Literal quantities, calendar dates, periods, atom polarity and explicit overclaiming; "
                     "unregistered semantic claims still require full host review."}
