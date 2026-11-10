"""Keep generated-file manifests synchronized after incremental local updates."""
from __future__ import annotations

import json
from pathlib import Path


def track_artifacts(output: Path, names: list[str], *, status: str | None = None,
                    archived: list[dict] | None = None, bundle: bool = False) -> None:
    try:
        from .case_memory import atomic_json
        from .helpers import sha256_file, write_process_bundle
    except ImportError:
        from case_memory import atomic_json
        from helpers import sha256_file, write_process_bundle
    path = output / "manifest.json"
    if not path.is_file():
        return
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if status:
        manifest["authorial_deliverable_status"] = status
    if archived:
        manifest["superseded_deliverables"] = archived
        names = names + [item["path"] for item in archived]
    existing = manifest.get("generated_files", [])
    manifest["generated_files"] = list(dict.fromkeys(existing + [name for name in names if (output / name).is_file()]))
    hashes = manifest.setdefault("artifact_hashes", {})
    # Refresh named artifacts and stale banners; other hashes stay unchanged.
    for name in names + ["analise_juridica.md", "minuta_peca.md"]:
        candidate = (output / name).resolve()
        if not candidate.is_relative_to(output.resolve()):
            raise ValueError("Artefato fora do diretório de saída")
        if candidate.is_file() and name not in {"manifest.json", "processo_completo.zip"}:
            hashes[name] = sha256_file(candidate)
    atomic_json(path, manifest)
    if bundle:
        write_process_bundle(output)


def invalidate_legal_delivery(output: Path, revision: str, reason: str) -> list[dict]:
    """Preserve prior deliverables and make stale approval flags visibly unusable."""
    try:
        from .case_memory import atomic_json, atomic_text
        from .legal_review import mark_previous_deliverables_stale
    except ImportError:
        from case_memory import atomic_json, atomic_text
        from legal_review import mark_previous_deliverables_stale
    archived = mark_previous_deliverables_stale(output, revision, reason)
    for name in ("legal_review_validation.json", "quality_gate.json"):
        path = output / name
        if not path.is_file():
            continue
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        value["previous_status"] = value.get("status")
        value.update(status="review_required", can_issue_final_legal_conclusion=False,
                     stale_revision=revision, stale_reason=reason, technical_status="not_current")
        value["errors"] = list(dict.fromkeys(value.get("errors", []) + [reason]))
        if name == "quality_gate.json":
            value["blocking_gates"] = list(dict.fromkeys(value.get("blocking_gates", []) + ["stale_legal_review"]))
        atomic_json(path,value)
    if (output / "quality_gate.md").is_file():
        atomic_text(output / "quality_gate.md", "# REVISÃO ANTERIOR DESATUALIZADA\n\n" + reason + "\n")
    track_artifacts(output,["legal_review_validation.json","quality_gate.json","quality_gate.md"],
                    status="stale_requires_reassessment", archived=archived)
    return archived
