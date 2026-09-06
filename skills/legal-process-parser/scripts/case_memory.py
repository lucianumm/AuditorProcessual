"""Persistent corpus memory, content identities and atomic checkpoints."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

ENGINE_VERSION = "1.1.0"


def page_revision(page: dict) -> str:
    """Content identity, independent of output paths and processing timestamps."""
    return identity(page.get("text", ""), page.get("vision"), page.get("ocr"),
                    page.get("visuals"), (page.get("render") or {}).get("sha256"))


def identity(*values: Any) -> str:
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def atomic_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def atomic_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def engine_fingerprint() -> str:
    root = Path(__file__).resolve().parent.parent
    files = sorted(p for directory in ("scripts", "references", "schemas")
                   for p in (root / directory).rglob("*") if p.suffix in {".py", ".json", ".md"})
    return identity(ENGINE_VERSION, [(p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])


def checkpoint(cache: Path, stage: str, key: str, operation: Callable[[], Any]) -> Any:
    """Only successful operations are committed; corrupt checkpoints are retried."""
    path = cache / stage / f"{identity(key)}.json"
    if path.is_file():
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            if envelope["checksum"] == identity(envelope["value"]):
                return envelope["value"]
        except (OSError, ValueError, KeyError, TypeError):
            pass
    value = operation()
    atomic_json(path, {"checksum": identity(value), "value": value})
    return value


def update_memory(output: Path) -> dict:
    """Rebuild from preserved runs; one document entry per full source digest."""
    manifests = sorted((output / "versions").glob("*/manifest.json"),
                       key=lambda p: (json.loads(p.read_text(encoding="utf-8-sig")).get("processed_at", ""), p.stat().st_mtime_ns))
    manifests.append(output / "manifest.json")
    documents: dict[str, dict] = {}
    for path in manifests:
        if not path.is_file():
            continue
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
        digest = manifest["source"]["sha256"]
        folder = path.parent.relative_to(output).as_posix()
        pages_path = path.parent / "pages.jsonl"
        pages = [json.loads(line) for line in pages_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()] if pages_path.exists() else []
        entry = documents.setdefault(digest, {"sha256": digest, "versions": []})
        entry.update({"name": manifest["source"]["name"], "folder": folder,
                      "process_id": manifest.get("process_id"), "classification": manifest.get("classification", {}),
                      "coverage": manifest.get("coverage", {}), "pages": pages})
        entry["versions"].append({"folder": folder, "task": manifest.get("task"), "processed_at": manifest.get("processed_at")})
    for document in documents.values():
        for page in document["pages"]:
            page["content_revision"] = page_revision(page)
    revision = identity([(sha, [(p["pdf_page"], p["content_revision"]) for p in documents[sha]["pages"]]) for sha in sorted(documents)])
    old_path = output / "case_memory.json"
    old = json.loads(old_path.read_text(encoding="utf-8-sig")) if old_path.exists() else {}
    added = sorted(set(documents) - {d["sha256"] for d in old.get("documents", [])})
    previous_pages = {f"{d['sha256']}:{p['pdf_page']}": page_revision(p) for d in old.get("documents", []) for p in d["pages"]}
    changed = [f"{d['sha256']}:{p['pdf_page']}" for d in documents.values() for p in d["pages"]
               if previous_pages.get(f"{d['sha256']}:{p['pdf_page']}") != p["content_revision"]]
    memory = {"schema_version": "1.0", "engine_version": ENGINE_VERSION,
              "corpus_revision": revision, "documents": list(documents.values()),
              "update": {"added_documents": added, "changed_pages": changed, "requires_legal_reassessment": bool(old and old.get("corpus_revision") != revision),
                         "previous_revision": old.get("corpus_revision")}}
    atomic_json(old_path, memory)
    lines = ["# MEMÓRIA PROCESSUAL", "", f"Revisão do corpus: `{revision}`", "",
             "Cada fonte conserva seu arquivo e página. Processos com números diferentes devem ser relacionados explicitamente antes da análise conjunta.", ""]
    for document in documents.values():
        folder = document["folder"]
        prefix = "" if folder == "." else folder + "/"
        lines.extend([f"## {document['name']}", "", f"Processo: {document['process_id']}", "",
                      f"[Texto integral]({prefix}processo_completo.md) · [Manifesto]({prefix}manifest.json)", ""])
        for page in document["pages"]:
            lines.append(f"- PDF p. {page['pdf_page']} — {page.get('piece')} — `{page['document_id']}` — {page.get('status')}")
        lines.append("")
    lines.extend(["## Impacto dos novos envios", "",
                  "Reavaliar fatos, teses, provas, decisões e minutas anteriores à luz dos novos arquivos." if memory["update"]["requires_legal_reassessment"] else "Sem nova inclusão que exija reavaliação automática.", ""])
    atomic_text(output / "memoria_processual.md", "\n".join(lines))
    return memory


def query_memory(output: Path, query: str) -> list[dict]:
    memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8-sig"))
    terms = query.casefold().split()
    matches = []
    for document in memory["documents"]:
        for page in document["pages"]:
            haystack = (page["text"] + " " + json.dumps([page.get("visuals", []), page.get("vision", {})], ensure_ascii=False)).casefold()
            if all(term in haystack for term in terms):
                matches.append({"file": document["name"], "folder": document["folder"], "source_sha256": document["sha256"], **page})
    return matches


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Consulta paginada do corpus cumulativo sem carregar todo o JSON no contexto da IA")
    parser.add_argument("output", type=Path)
    parser.add_argument("--query", default="")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.offset < 0 or not 1 <= args.limit <= 100:
        parser.error("offset >= 0 e limit entre 1 e 100")
    matches = query_memory(args.output, args.query)
    print(json.dumps({"total": len(matches), "offset": args.offset,
                      "next_offset": args.offset + args.limit if args.offset + args.limit < len(matches) else None,
                      "pages": matches[args.offset:args.offset + args.limit]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
