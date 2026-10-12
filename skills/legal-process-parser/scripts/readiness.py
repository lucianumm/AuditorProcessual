"""Scope pending findings to the legal conclusions and prose they can affect.

This module evaluates recorded dependencies, not legal merit. A finding marked as
accepted limitation continues to constrain the dependent conclusion.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict


CATEGORIES = {"technical", "coverage", "evidence", "legal", "procedural", "editorial"}
SEVERITIES = {"blocking", "material", "advisory"}
STATES = {"open", "in_progress", "resolved", "accepted_limitation"}
SCOPES = {"execution", "document", "page", "fact", "norm", "issue", "request", "paragraph"}
EFFECTS = {"none", "qualifies_conclusion", "blocks_assertion", "blocks_issue", "blocks_delivery"}


def _identifier(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]}"


def normalize_findings(review: dict, derived: list[dict] | None = None) -> list[dict]:
    """Convert legacy unscoped notes without assuming that they are harmless."""
    result = []
    for index, note in enumerate(review.get("unresolved", []) if isinstance(review.get("unresolved"), list) else []):
        if not isinstance(note, str):
            continue
        result.append({
            "id": _identifier("LEGACY", f"{index}:{note}"), "code": "LEGACY_UNSCOPED",
            "category": "legal", "severity": "blocking", "status": "open",
            "scope": "execution", "target_ids": [], "description": note,
            "impact": "Escopo e dependências não identificados; exige classificação antes da entrega.",
            "delivery_effect": "blocks_delivery",
            "required_action": "Relacionar a pendência às questões afetadas e registrar sua resolução.",
            "attempt_ids": [], "resolution": None,
        })
    for index, raw in enumerate(list(review.get("findings", []) or []) + list(derived or [])):
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        item.setdefault("id", _identifier("FIND", f"{index}:{item.get('code')}:{item.get('target_ids')}"))
        item.setdefault("status", "open")
        item.setdefault("impact", item.get("description", "Pendência exige avaliação de impacto."))
        item.setdefault("attempt_ids", [])
        item.setdefault("resolution", None)
        result.append(item)
    return result


def validate_findings(findings: list[dict], review: dict, memory: dict) -> list[str]:
    errors = []
    known = {
        "document": {d.get("sha256") for d in memory.get("documents", [])},
        "page": {f"{d.get('sha256')}:{p.get('pdf_page')}" for d in memory.get("documents", []) for p in d.get("pages", [])},
        "fact": {x.get("id") for x in review.get("facts", [])},
        "norm": {x.get("id") for x in review.get("norms", [])},
        "issue": {x.get("id") for x in review.get("issues", [])},
        "request": {x.get("id") for x in review.get("requests", [])},
        "paragraph": {x.get("id") for x in review.get("paragraphs", [])},
    }
    seen = set()
    for finding in findings:
        fid = finding.get("id")
        if not isinstance(fid, str) or not fid or fid in seen:
            errors.append("Achado sem ID ou com ID duplicado")
        seen.add(fid)
        for field in ("code", "description", "impact", "required_action"):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                errors.append(f"{fid}: {field} ausente")
        for field, choices in (("category", CATEGORIES), ("severity", SEVERITIES),
                               ("status", STATES), ("scope", SCOPES), ("delivery_effect", EFFECTS)):
            if finding.get(field) not in choices:
                errors.append(f"{fid}: {field} inválido")
        targets = finding.get("target_ids")
        scope = finding.get("scope")
        if not isinstance(targets, list) or any(not isinstance(t, str) for t in targets):
            errors.append(f"{fid}: target_ids inválidos")
        elif scope == "execution" and targets:
            errors.append(f"{fid}: achado global não aceita target_ids")
        elif scope in known and (not targets or not set(targets) <= known[scope]):
            errors.append(f"{fid}: target_ids ausentes ou não resolvidos")
        if not isinstance(finding.get("attempt_ids"), list):
            errors.append(f"{fid}: attempt_ids inválidos")
        if finding.get("status") == "resolved" and not finding.get("resolution"):
            errors.append(f"{fid}: resolução ausente")
        if finding.get("severity") == "blocking" and finding.get("delivery_effect") == "none":
            errors.append(f"{fid}: bloqueio sem efeito declarado")
    return errors


def _affected_issues(finding: dict, review: dict, memory: dict) -> set[str]:
    """Resolve recorded dependencies. Unknown/global scope conservatively affects all."""
    issues = review.get("issues", [])
    all_ids = {issue["id"] for issue in issues}
    scope, targets = finding.get("scope"), set(finding.get("target_ids", []))
    if scope == "execution":
        return all_ids
    if scope == "issue":
        return targets
    facts = review.get("facts", [])
    fact_ids: set[str] = set()
    if scope == "fact":
        fact_ids = targets
    elif scope == "norm":
        return {i["id"] for i in issues if targets.intersection(i.get("norm_ids", []))}
    elif scope == "request":
        return {i["id"] for i in issues if targets.intersection(i.get("request_ids", [])) or any(
            r.get("id") in targets and i["id"] in r.get("issue_ids", []) for r in review.get("requests", []))}
    elif scope == "paragraph":
        paragraphs = [p for p in review.get("paragraphs", []) if p.get("id") in targets]
        return {iid for p in paragraphs for iid in p.get("issue_ids", [])} | {
            i["id"] for i in issues for p in paragraphs if set(p.get("fact_ids", [])) & set(i.get("fact_ids", []))}
    elif scope in {"page", "document"}:
        for fact in facts:
            for source in fact.get("sources", []):
                sha = source.get("source_sha256")
                page = f"{sha}:{source.get('pdf_page')}"
                if (scope == "document" and sha in targets) or (scope == "page" and page in targets):
                    fact_ids.add(fact["id"])
        # A source with no extracted fact has unknown impact, so do not release any issue.
        if not fact_ids:
            return all_ids
    affected = {i["id"] for i in issues if fact_ids.intersection(i.get("fact_ids", []))}
    return affected or all_ids


def evaluate_readiness(review: dict, memory: dict, findings: list[dict]) -> dict:
    active = [f for f in findings if f.get("status") != "resolved"]
    effects: dict[str, set[str]] = defaultdict(set)
    attached: dict[str, list[str]] = defaultdict(list)
    global_block = False
    blocked_paragraphs: set[str] = set()
    for finding in active:
        effect = finding.get("delivery_effect")
        if effect == "none":
            continue
        affected = _affected_issues(finding, review, memory)
        if effect == "blocks_delivery":
            global_block = True
        if effect == "blocks_assertion" and finding.get("scope") == "paragraph":
            blocked_paragraphs.update(finding.get("target_ids", []))
        for issue_id in affected:
            effects[issue_id].add(effect)
            attached[issue_id].append(finding["id"])
    issue_statuses = []
    for issue in review.get("issues", []):
        iid = issue["id"]
        declared = issue.get("analysis_status", "concluded")
        state = "undetermined" if "blocks_issue" in effects[iid] or "blocks_delivery" in effects[iid] else (
            "qualified" if effects[iid] & {"qualifies_conclusion", "blocks_assertion"} else "concluded")
        if declared == "undetermined":
            state = "undetermined"
        elif declared == "qualified" and state == "concluded":
            state = "qualified"
        issue_statuses.append({"id": iid, "analysis_status": state, "finding_ids": list(dict.fromkeys(attached[iid]))})
    states = [i["analysis_status"] for i in issue_statuses]
    if global_block or (states and all(s == "undetermined" for s in states)):
        analysis_status = "undetermined"
    elif any(s != "concluded" for s in states):
        analysis_status = "qualified"
    else:
        analysis_status = "concluded"
    draft_status = "not_requested"
    if review.get("task") == "petition":
        draft_status = "blocked" if global_block or (states and all(s == "undetermined" for s in states)) else (
            "partial" if analysis_status != "concluded" or blocked_paragraphs else "ready_for_review")
    permitted = {i["id"] for i in issue_statuses if i["analysis_status"] != "undetermined"}
    visible = []
    for paragraph in review.get("paragraphs", []):
        ids = set(paragraph.get("issue_ids", []))
        if paragraph.get("id") in blocked_paragraphs or (ids and not ids <= permitted):
            continue
        # Unlinked prose can contain a blocked proposition: keep only layout, not substance.
        if not ids and paragraph.get("section") not in {"enderecamento", "qualificacao", "valor_da_causa"} and analysis_status != "concluded":
            continue
        visible.append(paragraph.get("id"))
    return {
        "issue_statuses": issue_statuses, "analysis_status": analysis_status,
        "draft_status": draft_status, "execution_status": "partial" if analysis_status != "concluded" or blocked_paragraphs else "completed",
        "professional_review_status": "not_recorded", "global_block": global_block,
        "visible_paragraph_ids": visible, "active_finding_ids": [f["id"] for f in active],
    }
