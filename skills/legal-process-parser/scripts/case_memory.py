"""Persistent corpus memory, content identities and atomic checkpoints."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

ENGINE_VERSION = "1.2.0"


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
    previous_pages = {f"{d['sha256']}:{p['pdf_page']}": page_revision(p)
                      for d in old.get("documents", []) for p in d.get("pages", [])}
    current_pages = {f"{d['sha256']}:{p['pdf_page']}": p["content_revision"]
                     for d in documents.values() for p in d["pages"]}
    changed = sorted(key for key, value in current_pages.items() if previous_pages.get(key) != value)
    removed = sorted(set(previous_pages) - set(current_pages))
    try:
        from .case_graph import affected_elements, build_case_graph
        from .case_search import rebuild_index
    except ImportError:
        from case_graph import affected_elements, build_case_graph
        from case_search import rebuild_index
    review_path = output / "legal_review.json"
    if not review_path.is_file():
        review_path = next((path.parent / "legal_review.json" for path in reversed(manifests[:-1])
                            if (path.parent / "legal_review.json").is_file()), review_path)
    try:
        previous_review = json.loads(review_path.read_text(encoding="utf-8-sig")) if review_path.is_file() else {}
    except (OSError, ValueError):
        previous_review = {}
    graph = build_case_graph(previous_review, review_path.relative_to(output).as_posix() if review_path.is_file() else "")
    impacted = affected_elements(graph, changed + removed)
    memory = {"schema_version": "2.0", "engine_version": ENGINE_VERSION,
              "corpus_revision": revision, "documents": list(documents.values()),
              "dependency_graph": graph,
              "update": {"added_documents": added, "changed_pages": changed, "removed_pages": removed,
                         "impacted_elements": impacted,
                         "requires_legal_reassessment": bool(old and old.get("corpus_revision") != revision),
                         "previous_revision": old.get("corpus_revision")}}
    atomic_json(old_path, memory)
    rebuild_index(output, memory["documents"], revision)
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
                  "Reavaliar fatos, teses, provas, decisões e minutas anteriores à luz dos novos arquivos." if memory["update"]["requires_legal_reassessment"] else "Sem alteração do conteúdo do corpus desde a geração anterior.", ""])
    if changed or removed:
        lines.append("Páginas novas ou alteradas: " + (", ".join(f"`{key}`" for key in changed) or "nenhuma") + ".")
        if removed:
            lines.append("Páginas não presentes na versão atual: " + ", ".join(f"`{key}`" for key in removed) + ".")
        lines.append("")
        for kind, title in (("fact", "Fatos"), ("issue", "Questões"), ("request", "Pedidos"), ("paragraph", "Parágrafos")):
            values = impacted[f"{kind}_ids"]
            if values:
                lines.append(f"- {title} dependentes declarados: " + ", ".join(f"`{value}`" for value in values) + ".")
        if impacted["unmapped_page_ids"]:
            lines.append("- Páginas sem vínculos declarados: " + ", ".join(f"`{value}`" for value in impacted["unmapped_page_ids"]) + ". Exigem comparação com o restante do corpus.")
        lines.append("")
    if previous_review:
        stale = graph["review_revision"] != revision
        lines.extend(["## Índice jurídico declarado", "",
                      "Revisão anterior: desatualizada após mudanças no corpus." if stale else "Revisão vinculada à revisão atual do corpus.", ""])
        for key, title, display in (("facts", "Fatos", "text"), ("issues", "Questões", "question"),
                                    ("requests", "Pedidos", "text")):
            items = previous_review.get(key, [])
            if isinstance(items, list) and items:
                lines.extend([f"### {title}", ""])
                for item in items:
                    if isinstance(item, dict):
                        lines.append(f"- `{item.get('id', '?')}` — {str(item.get(display, '')).replace(chr(10), ' ')[:240]}")
                lines.append("")
    atomic_text(output / "memoria_processual.md", "\n".join(lines))
    return memory


def query_memory(output: Path, query: str) -> list[dict]:
    """Compatibility API. New callers should use search_memory for real pagination."""
    try:
        from .case_search import search_memory
    except ImportError:
        from case_search import search_memory
    matches: list[dict] = []
    offset = 0
    while True:
        result = search_memory(output, query, offset=offset, limit=100, mode="substring", include_full_pages=True)
        matches.extend({key: value for key, value in page.items()
                        if key not in {"snippet", "page_id", "process_id", "content_revision"}}
                       for page in result["pages"])
        if result["next_offset"] is None:
            break
        offset = result["next_offset"]
    return matches


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Consulta paginada do corpus cumulativo sem carregar todo o JSON no contexto da IA")
    parser.add_argument("output", type=Path)
    parser.add_argument("--query", default="")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--mode", choices=("tokens", "substring"), default="tokens")
    parser.add_argument("--document", help="Parte do nome do arquivo")
    parser.add_argument("--document-id")
    parser.add_argument("--source-sha256")
    parser.add_argument("--piece", help="Tipo de peça")
    parser.add_argument("--person", help="Expressão ou nome mencionado na página")
    parser.add_argument("--date-from", help="Data ISO inicial mencionada")
    parser.add_argument("--date-to", help="Data ISO final mencionada")
    parser.add_argument("--amount", help="Valor mencionado")
    parser.add_argument("--full-pages", action="store_true", help="Inclui o JSON completo das páginas encontradas")
    args = parser.parse_args()
    if args.offset < 0 or not 1 <= args.limit <= 100:
        parser.error("offset >= 0 e limit entre 1 e 100")
    try:
        from .case_search import search_memory
    except ImportError:
        from case_search import search_memory
    matches = search_memory(args.output, args.query, offset=args.offset, limit=args.limit,
                            mode=args.mode, document=args.document, document_id=args.document_id,
                            source_sha256=args.source_sha256, piece=args.piece, person=args.person,
                            date_from=args.date_from, date_to=args.date_to, amount=args.amount,
                            include_full_pages=args.full_pages)
    print(json.dumps(matches, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
