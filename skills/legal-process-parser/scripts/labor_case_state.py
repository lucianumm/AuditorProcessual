"""Derive a navigable contract, proof strategy and precise change impact.

Only attributed records are projected. No document is treated as read by running
this module, and no missing date or contractual state is silently filled in.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .case_memory import identity
    from .prose_review import audit_prose
except ImportError:
    from case_memory import identity
    from prose_review import audit_prose


def record_changes(before: list[dict], after: list[dict]) -> list[dict]:
    left, right = ({r["id"]: r for r in rows} for rows in (before, after))
    return [{"id": key, "kind": "added" if key not in left else "removed" if key not in right else "changed",
             "fields": sorted(k for k in set(left.get(key, {})) | set(right.get(key, {})) if left.get(key, {}).get(k) != right.get(key, {}).get(k))}
            for key in sorted(set(left) | set(right)) if left.get(key) != right.get(key)]


def impact(review: dict, fact_ids=(), norm_ids=(), period_ids=(), issue_ids=()) -> dict:
    fids, nids, pids = set(fact_ids), set(norm_ids), set(period_ids)
    labor = review.get("labor_review", {})
    issues = set(issue_ids) | {i["id"] for i in review.get("issues", []) if set(i.get("fact_ids", [])) & fids or set(i.get("norm_ids", [])) & nids}
    issues |= {i["issue_id"] for i in labor.get("topic_assessments", []) if set(i["period_ids"]) & pids or set(i["fact_ids"]) & fids or set(i["norm_ids"]) & nids}
    # Instrument scope and vigency changes affect every issue that selected it.
    instruments = {i["id"] for i in labor.get("collective_instruments", []) if i["norm_id"] in nids}
    issues |= {i["issue_id"] for i in labor.get("topic_assessments", []) if any(c["instrument_id"] in instruments for c in i["collective_checks"])}
    request_ids = {r["id"] for r in review.get("requests", []) if set(r["issue_ids"]) & issues or set(r.get("fact_ids", [])) & fids}
    paragraphs = {p["id"] for p in review.get("paragraphs", []) if set(p.get("issue_ids", [])) & issues or set(p.get("fact_ids", [])) & fids or set(p.get("norm_ids", [])) & nids}
    calculation = labor.get("calculation_set", {})
    inputs = {p["id"] for p in calculation.get("inputs", []) if set(p["fact_ids"]) & fids or set(p["norm_ids"]) & nids}
    items = set()
    while True:
        additional = {p["id"] for p in calculation.get("items", []) if set(p["bindings"].values()) & (inputs | items) or set(p["norm_ids"]) & nids or set(p["request_ids"]) & request_ids} - items
        if not additional:
            break
        items |= additional
    return {"issue_ids": sorted(issues), "request_ids": sorted(request_ids), "paragraph_ids": sorted(paragraphs),
            "calculation_input_ids": sorted(inputs), "calculation_item_ids": sorted(items)}


def compare_reviews(before: dict, after: dict) -> dict:
    changes = []
    for field in ("facts", "norms"):
        for row in record_changes(before.get(field, []), after.get(field, [])):
            changes.append(dict(row, field=field, **{"fact_ids" if field == "facts" else "norm_ids": [row["id"]]}))
    for field in ("contract_periods", "relationships", "collective_instruments"):
        old = before.get("labor_review", {}).get(field, [])
        new = after.get("labor_review", {}).get(field, [])
        for row in record_changes(old, new):
            records = [r for r in old + new if r["id"] == row["id"]]
            if field == "collective_instruments":
                row["clause_changes"] = record_changes(next((r["clauses"] for r in old if r["id"] == row["id"]), []),
                                                       next((r["clauses"] for r in new if r["id"] == row["id"]), []))
            changes.append(dict(row, field=field, fact_ids=sorted({f for r in records for f in r.get("fact_ids", [])}),
                                norm_ids=sorted({n for r in records for n in r.get("norm_ids", [])} | {r["norm_id"] for r in records if r.get("norm_id")}),
                                period_ids=[row["id"]] if field == "contract_periods" else [p["id"] for v in (before, after)
                                    for p in v.get("labor_review", {}).get("contract_periods", []) if p["relationship_id"] == row["id"]] if field == "relationships" else []))
    # Atomic fields and contrary evidence can change without changing fact prose.
    for field, key in (("assertion_reviews", "fact_id"), ("normative_map", "norm_id")):
        old = [{**r, "id": r[key]} for r in before.get(field, [])]
        new = [{**r, "id": r[key]} for r in after.get(field, [])]
        for row in record_changes(old, new):
            changes.append(dict(row, field=field, **{"fact_ids" if key == "fact_id" else "norm_ids": [row["id"]]}))
    for field in ("issues", "requests", "theses", "norm_applications"):
        old, new = before.get(field, []), after.get(field, [])
        for row in record_changes(old, new):
            records = [r for r in old + new if r["id"] == row["id"]]
            changes.append(dict(row, field=field, issue_ids=sorted({i for r in records for i in r.get("issue_ids", [])}
                | {r["issue_id"] for r in records if r.get("issue_id")} | ({row["id"]} if field == "issues" else set()))))
    workflows = [v.get("labor_review", {}).get("workflow", {}) for v in (before, after)]
    for field in sorted(set(workflows[0]) | set(workflows[1])):
        old, new = (w.get(field, []) for w in workflows)
        if not isinstance(old, list) or not isinstance(new, list) or any(not isinstance(r, dict) or "id" not in r for r in old + new):
            continue
        for row in record_changes(old, new):
            records = [r for r in old + new if r["id"] == row["id"]]
            iids = {i for r in records for i in r.get("issue_ids", [])} | {r["issue_id"] for r in records if r.get("issue_id")}
            iids |= {claim["issue_id"] for w in workflows for claim in w.get("claim_reviews", [])
                     if claim["id"] in {r.get("claim_review_id") for r in records}}
            changes.append(dict(row, field="workflow." + field, issue_ids=sorted(iids),
                fact_ids=sorted({fid for r in records for fid in r.get("fact_ids", []) + r.get("answer_fact_ids", [])}
                                | {r[k] for r in records for k in ("act_fact_id", "left_fact_id", "right_fact_id") if r.get(k)}),
                norm_ids=sorted({nid for r in records for nid in r.get("norm_ids", [])}), period_ids=sorted({pid for r in records for pid in r.get("period_ids", [])})))
    for row in changes:
        affected = [impact(v, row.get("fact_ids", []), row.get("norm_ids", []), row.get("period_ids", []), row.get("issue_ids", [])) for v in (before, after)]
        row["impact"] = {key: sorted({x for a in affected for x in a[key]}) for key in affected[0]}
    return {"before_revision": identity(before), "after_revision": identity(after), "changes": changes,
            "scope": "Declared dependencies; prose and omitted links require host review."}


def case_state(review: dict, *, previous: dict | None = None, events: dict | None = None) -> dict:
    if events is not None and events.get("revision") != identity(events.get("events", [])):
        raise ValueError("Cronologia de relatos sem revisão íntegra; usar intake_events.json preservado")
    labor = review.get("labor_review", {})
    workflow = labor.get("workflow", {})
    facts = {f["id"]: f for f in review.get("facts", [])}
    assertions = {a["fact_id"]: a for a in review.get("assertion_reviews", [])}
    evidence_types = {}
    for check in labor.get("evidence_checks", []):
        for source in check["sources"]:
            evidence_types.setdefault(source["fact_id"], set()).add(check["document_type"])
    timeline = []
    for period in labor.get("contract_periods", []):
        timeline.append({"kind": "contract_period", **period, "precision": "as_recorded",
                         "impact": impact(review, period["fact_ids"], period["norm_ids"], [period["id"]])})
    for fid, fact in facts.items():
        atoms = assertions.get(fid, {}).get("atoms", {})
        timeline.append({"kind": "fact_observation", "id": fid, "text": fact["text"], "date": atoms.get("date"),
                         "start": atoms.get("period_start"), "end": atoms.get("period_end"), "atoms": atoms,
                         "origin": fact.get("origin"), "source_types": sorted(evidence_types.get(fid, [])),
                         "sources": fact.get("sources", []), "client_record_id": fact.get("client_record_id"),
                         "evidence_status": assertions.get(fid, {}).get("evidence_status", "not_reviewed"),
                         "impact": impact(review, [fid])})
    for event in (events or {}).get("events", []):
        timeline.append({"kind": "client_event", **event})
    timeline.sort(key=lambda row: (row.get("date") or row.get("start") or row.get("bounds", {}).get("earliest") or "9999", row["id"]))
    proof = {p["id"]: p for p in workflow.get("proof_plan", [])}
    strategies = []
    for claim in workflow.get("claim_reviews", []):
        for requirement in claim["requirements"]:
            strategies.append({"claim_review_id": claim["id"], "issue_id": claim["issue_id"], **requirement,
                               "proof_actions": [proof[pid] for pid in requirement["proof_plan_ids"] if pid in proof],
                               "drafting_basis": claim["drafting_basis"], "merit_status": claim["merit_status"]})
    conflicts = [{**r, "impact": impact(review, [r["left_fact_id"], r["right_fact_id"]], period_ids=r["period_ids"])}
                 for r in workflow.get("reconciliations", []) if r["status"] != "agrees"]
    return {"schema_version": "1.0", "corpus_revision": review.get("corpus_revision"), "review_revision": identity(review),
            "timeline": timeline, "conflicts": conflicts, "proof_strategy": strategies,
            "material_questions": workflow.get("material_questions", []), "instruction_questions": workflow.get("instruction_questions", []),
            "changes": compare_reviews(previous, review) if previous is not None else None, "collective_candidates": collective_candidates(review),
            "prose_review": audit_prose(review),
            "scope": "Attributed timeline; unknown dates, competing versions and future proof remain explicit."}


def collective_candidates(review: dict) -> list[dict]:
    try:
        from .labor_analysis import scope_matches
    except ImportError:
        from labor_analysis import scope_matches
    labor = review.get("labor_review", {})
    relations = {r["id"]: r for r in labor.get("relationships", [])}
    rows = []
    for period in labor.get("contract_periods", []):
        relation = relations.get(period["relationship_id"], {})
        for instrument in labor.get("collective_instruments", []):
            reasons = []
            if not scope_matches(relation.get("category", ""), instrument["category_scope"]):
                reasons.append("category_not_matched")
            if not scope_matches(relation.get("territory", ""), instrument["territory_scope"], hierarchy=True):
                reasons.append("territory_not_matched")
            if not relation.get("employers") or not all(scope_matches(e, instrument["employer_scope"]) for e in relation.get("employers", [])):
                reasons.append("employer_scope_not_matched")
            if period.get("end") and period["end"] < instrument["effective_from"] or period.get("start") and period["start"] > instrument["effective_until"]:
                reasons.append("outside_vigency")
            incomplete = not period.get("start") or not period.get("end")
            overlap_start = max(period.get("start") or instrument["effective_from"], instrument["effective_from"])
            overlap_end = min(period.get("end") or instrument["effective_until"], instrument["effective_until"])
            rows.append({"period_id": period["id"], "instrument_id": instrument["id"], "norm_id": instrument["norm_id"],
                         "status": "scope_mismatch" if reasons else "pending_period" if incomplete else "candidate_requires_legal_selection",
                         "reasons": reasons, "overlap_start": overlap_start if overlap_start <= overlap_end else None,
                         "overlap_end": overlap_end if overlap_start <= overlap_end else None,
                         "scope_analysis": "Recorded scope only; category/CNAE, instrument competition and negotiated limits require authored justification."})
    return rows


def state_markdown(state: dict) -> str:
    try:
        from .legal_index import safe_text, anchor
    except ImportError:
        from legal_index import safe_text, anchor
    lines = ["# CONTRATO, PROVA E IMPACTOS", "", state["scope"], ""]
    for row in state["timeline"]:
        lines += ["- " + safe_text(row["id"]) + " · " + row["kind"] + " · " + safe_text(str(row.get("date") or row.get("start") or row.get("bounds", {}))) + " · " + safe_text(str(row.get("atoms") or row.get("job") or row.get("description", "")))]
        if row["kind"] == "fact_observation":
            lines += ["  - [Fonte e contexto de " + safe_text(row["id"]) + "](indice_juridico.md#" + anchor("fact", row["id"]) + ") · " + row["evidence_status"] + "."]
            for source in row["sources"]:
                lines += ["  - " + safe_text(source.get("document_id", source.get("source_sha256", ""))) + " · página PDF " + str(source.get("pdf_page", "não registrada")) + "."]
    lines += ["", "## Estratégia por requisito", ""]
    for row in state["proof_strategy"]:
        lines += ["- " + safe_text(row["claim_review_id"] + "/" + row["requirement_id"]) + ": " + row["status"] + "."]
        for action in row["proof_actions"]:
            lines += ["  - " + safe_text(action["description"]) + " · detentor " + action["holder"] + " · meio " + action["method"] + " · fase " + safe_text(action["stage"]) + " · " + action["status"]
                      + ". Alternativa: " + safe_text(action["alternatives"]) + "."]
    lines += ["", "## Divergências e mudanças", ""]
    for row in state["conflicts"] + (state["changes"] or {}).get("changes", []):
        lines += ["- " + safe_text(row["id"]) + ": " + safe_text(row.get("reason") or ", ".join(row.get("fields", []))) + ". Impacto: " + safe_text(json.dumps(row["impact"], ensure_ascii=False))]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Linha do tempo e impacto de mudanças em fatos, cláusulas, pedidos e cálculos")
    parser.add_argument("review", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--events", type=Path)
    args = parser.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8-sig")) if p else None
    try:
        print(json.dumps(case_state(read(args.review), previous=read(args.previous), events=read(args.events)), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
