"""Trace a changed source page through a structured legal review.

The graph records declared dependencies, not an automatic legal assessment. New
sources without declared edges still require a corpus-wide contradiction check.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


KINDS = ("fact", "norm", "issue", "request", "paragraph")


def _items(review: dict, key: str) -> list[dict]:
    value = review.get(key, [])
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _ids(item: dict, key: str) -> list[str]:
    value = item.get(key, [])
    return [identifier for identifier in value if isinstance(identifier, str) and identifier] if isinstance(value, list) else []


def _node(kind: str, identifier: Any) -> str | None:
    return f"{kind}:{identifier}" if isinstance(identifier, str) and identifier else None


def build_case_graph(review: dict, source: str = "") -> dict:
    """Build source-to-draft edges from identifiers actually declared by the AI."""
    if not isinstance(review, dict):
        review = {}
    edges: set[tuple[str, str]] = set()

    def connect(upstream: str | None, downstream: str | None) -> None:
        if upstream and downstream:
            edges.add((upstream, downstream))

    for fact in _items(review, "facts"):
        fact_node = _node("fact", fact.get("id"))
        for location in _items(fact, "sources"):
            sha, number = location.get("source_sha256"), location.get("pdf_page")
            if isinstance(sha, str) and isinstance(number, int) and number > 0:
                connect(_node("page", f"{sha}:{number}"), fact_node)
    for page_review in _items(review, "page_reviews"):
        page_node = _node("page", page_review.get("page_id"))
        for fact_id in _ids(page_review, "fact_ids"):
            connect(page_node, _node("fact", fact_id))
    for issue in _items(review, "issues"):
        issue_node = _node("issue", issue.get("id"))
        for kind, key in (("fact", "fact_ids"), ("norm", "norm_ids")):
            for identifier in _ids(issue, key):
                connect(_node(kind, identifier), issue_node)
    for request in _items(review, "requests"):
        request_node = _node("request", request.get("id"))
        for kind, key in (("fact", "fact_ids"), ("issue", "issue_ids")):
            for identifier in _ids(request, key):
                connect(_node(kind, identifier), request_node)
    for paragraph in _items(review, "paragraphs"):
        paragraph_node = _node("paragraph", paragraph.get("id"))
        for kind, key in (("fact", "fact_ids"), ("norm", "norm_ids"), ("issue", "issue_ids"), ("request", "request_ids")):
            for identifier in _ids(paragraph, key):
                connect(_node(kind, identifier), paragraph_node)
    return {"schema_version": "1.0", "review_revision": review.get("corpus_revision"),
            "source": source, "edges": [{"from": left, "to": right} for left, right in sorted(edges)]}


def affected_elements(graph: dict, changed_pages: list[str]) -> dict:
    """Return the transitive impact of known links and pages needing fresh review."""
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in graph.get("edges", []):
        if isinstance(edge, dict) and isinstance(edge.get("from"), str) and isinstance(edge.get("to"), str):
            adjacency[edge["from"]].add(edge["to"])
    starts = {f"page:{page}" for page in changed_pages}
    seen = set(starts)
    queue = deque(sorted(starts))
    while queue:
        for next_node in adjacency.get(queue.popleft(), ()):
            if next_node not in seen:
                seen.add(next_node)
                queue.append(next_node)
    result = {f"{kind}_ids": sorted(node[len(kind) + 1:] for node in seen if node.startswith(f"{kind}:"))
              for kind in KINDS}
    result["source_page_ids"] = sorted(changed_pages)
    result["unmapped_page_ids"] = sorted(page for page in changed_pages if not adjacency.get(f"page:{page}"))
    return result
