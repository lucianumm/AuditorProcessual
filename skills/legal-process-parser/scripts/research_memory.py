"""Version consulted authorities independently of uploaded case documents."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

try:
    from .case_memory import atomic_json, identity
    from .case_graph import affected_elements, build_case_graph
except ImportError:
    from case_memory import atomic_json, identity
    from case_graph import affected_elements, build_case_graph


def load_registry(output: Path) -> dict:
    path = output / "research_registry.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"schema_version":"1.0", "sources":{}, "events":[]}


def research_revision(output: Path) -> str:
    registry = load_registry(output)
    return identity(sorted((key, item["text_hash"]) for key, item in registry["sources"].items()))


def register_source_record(output: Path, record: dict) -> dict:
    if record.get("method") not in {"official_http_capture", "browser_observation"}:
        return {"changed":False}
    registry = load_registry(output)
    key = identity(record["method"], record["url"], record.get("locator", ""), record.get("coverage_scope", "full_http"))
    digest = hashlib.sha256(record.get("text", "").encode()).hexdigest()
    identifier = record.get("capture_id") or record.get("source_record_id")
    previous = registry["sources"].get(key)
    changed = bool(previous and previous["text_hash"] != digest)
    entry = {"url":record["url"], "method":record["method"], "text_hash":digest,
             "latest_record_id":identifier, "accessed_on":record["accessed_on"],
             "history":list(dict.fromkeys((previous or {}).get("history", []) + [identifier]))}
    registry["sources"][key] = entry
    if changed:
        registry["events"].append({"key":key, "previous_record_id":previous["latest_record_id"],
                                   "record_id":identifier, "accessed_on":record["accessed_on"],
                                   "meaning":"Texto consultado mudou; reavaliar contexto, vigência e incidência, não presumir mudança legislativa."})
    registry["research_revision"] = identity(sorted((k, v["text_hash"]) for k,v in registry["sources"].items()))
    atomic_json(output / "research_registry.json", registry)
    if changed and (output / "legal_review.json").is_file():
        review = json.loads((output / "legal_review.json").read_text(encoding="utf-8-sig"))
        norm_ids = [norm["id"] for norm in review.get("norms", [])
                    if (norm.get("capture_id") or norm.get("source_record_id")) in previous.get("history", [])]
        graph = build_case_graph(review)
        impact = affected_elements(graph, [], changed_norms=norm_ids)
        atomic_json(output / "legal_source_updates.json", {"research_revision":registry["research_revision"],
                    "changed_norm_ids":norm_ids, "impacted_elements":impact,
                    "requires_legal_reassessment":bool(norm_ids), "events":registry["events"]})
        if norm_ids:
            try:
                from .artifact_tracking import invalidate_legal_delivery
            except ImportError:
                from artifact_tracking import invalidate_legal_delivery
            archived = invalidate_legal_delivery(output, registry["research_revision"],
                "Uma fonte jurídica consultada mudou. Conferir legal_source_updates.json e reavaliar as conclusões dependentes.")
            atomic_json(output / "source_change_archives.json", archived)
            if (output / "case_memory.json").is_file():
                try:
                    from .legal_index import build_legal_index
                except ImportError:
                    from legal_index import build_legal_index
                memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8-sig"))
                build_legal_index(output, memory, review)
            try:
                from .artifact_tracking import track_artifacts
            except ImportError:
                from artifact_tracking import track_artifacts
            track_artifacts(output, ["research_registry.json", "legal_source_updates.json", "source_change_archives.json", "indice_juridico.json", "indice_juridico.md"],
                            status="stale_authority_change", archived=archived, bundle=True)
    try:
        from .artifact_tracking import track_artifacts
    except ImportError:
        from artifact_tracking import track_artifacts
    track_artifacts(output, ["research_registry.json", f"research_sources/{identifier}.json", f"research_sources/{identifier}.source"])
    return {"changed":changed, "research_revision":registry["research_revision"]}


def changed_authorities(review: dict, output: Path) -> list[str]:
    registry = load_registry(output)
    result = []
    for norm in review.get("norms", []):
        identifier = norm.get("capture_id") or norm.get("source_record_id")
        for item in registry["sources"].values():
            if identifier in item["history"]:
                path = output / "research_sources" / (str(identifier) + ".json")
                if path.is_file():
                    old = json.loads(path.read_text(encoding="utf-8"))
                    if hashlib.sha256(old.get("text", "").encode()).hexdigest() != item["text_hash"]:
                        result.append(norm["id"])
    return sorted(set(result))
