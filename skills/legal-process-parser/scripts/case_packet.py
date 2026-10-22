"""Bounded, lossless reading packets and retrieval receipts; no model calls.

A receipt proves what the local exporter made available, not that a person or
model understood it. The host records substantive review separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .case_memory import atomic_json, identity, page_revision
except ImportError:
    from case_memory import atomic_json, identity, page_revision


def layer_text(page: dict, layer: str) -> str:
    if layer == "text":
        return page.get("text", "")
    vision = page.get("vision") or {}
    return "\n".join(str(vision.get(key) or "") for key in ("description", "transcription")).strip()


def segments(memory: dict, width: int):
    for doc in memory.get("documents", []):
        for page in doc.get("pages", []):
            for layer in ("text", "vision"):
                text = layer_text(page, layer)
                if not text and layer == "vision":
                    continue
                for start in range(0, max(1, len(text)), width):
                    end = min(start + width, len(text))
                    render = dict(page.get("render") or {})
                    if render.get("path") and doc.get("folder", ".") != ".":
                        render["path"] = (Path(doc["folder"]) / render["path"]).as_posix()
                    yield {"page_id": f"{doc['sha256']}:{page['pdf_page']}",
                           "document": doc["name"], "document_id": page["document_id"],
                           "content_revision": page_revision(page), "layer": layer,
                           "start": start, "end": end, "length": len(text),
                           "text": text[start:end], "render": render,
                           "court_page": page.get("court_page"), "piece": page.get("piece")}


def reading_packet(output: Path, *, offset: int = 0, max_chars: int = 12000) -> dict:
    if offset < 0 or not 512 <= max_chars <= 64000:
        raise ValueError("offset >= 0 e max_chars entre 512 e 64000")
    memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8-sig"))
    selected, consumed, next_offset = [], 0, None
    for index, segment in enumerate(segments(memory, max_chars // 2)):
        if index < offset:
            continue
        cost = max(1, len(segment["text"]))
        if selected and consumed + cost > max_chars:
            next_offset = index
            break
        selected.append(segment)
        consumed += cost
    if not selected:
        raise ValueError("Cursor fora do corpus; não representa lote lido")
    receipt = {"schema_version": "1.0", "corpus_revision": memory["corpus_revision"],
               "offset": offset, "max_chars": max_chars,
               "segments": [{k: v for k, v in item.items() if k in {
                   "page_id", "content_revision", "layer", "start", "end", "length"}} |
                   {"text_sha256": hashlib.sha256(item["text"].encode()).hexdigest()} for item in selected],
               "attestation": "local_export_only_not_semantic_reading"}
    receipt["receipt_id"] = identity(receipt)
    atomic_json(output / "reading_receipts" / (receipt["receipt_id"] + ".json"), receipt)
    try:
        from .artifact_tracking import track_artifacts
    except ImportError:
        from artifact_tracking import track_artifacts
    track_artifacts(output, ["reading_receipts/" + receipt["receipt_id"] + ".json"])
    return {"corpus_revision": memory["corpus_revision"], "offset": offset, "next_offset": next_offset,
            "cursor_rule": "Mantenha max_chars e corpus_revision constantes; alteração exige reiniciar offset=0.",
            "characters": consumed, "receipt_id": receipt["receipt_id"], "segments": selected,
            "meaning": "Conteúdo integral destes intervalos disponibilizado; o modelo deve examiná-lo antes de registrar revisão."}


def check_reading_coverage(review: dict, memory: dict, output: Path | None = None) -> list[str]:
    errors, seen = [], set()
    records = review.get("reading_coverage", [])
    pages = {f"{d['sha256']}:{p['pdf_page']}": p for d in memory.get("documents", []) for p in d.get("pages", [])}
    expected = {(pid, layer) for pid, p in pages.items() for layer in ("text", "vision")
                if layer == "text" or layer_text(p, layer)}
    if not isinstance(records, list):
        return ["reading_coverage: lista obrigatória"]
    for record in records:
        if not isinstance(record, dict):
            errors.append("reading_coverage: registro inválido")
            continue
        key = (record.get("page_id"), record.get("layer"))
        if key not in expected or key in seen:
            errors.append("reading_coverage: camada/página desconhecida ou duplicada")
            continue
        seen.add(key)
        page = pages[key[0]]
        text = layer_text(page, key[1])
        if record.get("content_revision") != page_revision(page):
            errors.append(f"{key[0]}: leitura vinculada a conteúdo desatualizado")
        spans = record.get("intervals", [])
        if not isinstance(spans, list):
            spans = []
        valid_spans = []
        for span in spans:
            if not isinstance(span, list) or len(span) != 2 or not all(type(n) is int for n in span) or not 0 <= span[0] <= span[1] <= len(text):
                errors.append(f"{key[0]}: intervalo de leitura inválido")
            else:
                valid_spans.append(span)
        position = 0
        for span in sorted(valid_spans):
            if span[0] > position:
                errors.append(f"{key[0]}: lacuna entre intervalos de leitura")
            position = max(position, span[1])
        if position != len(text) or not valid_spans:
            errors.append(f"{key[0]}: leitura integral da camada {key[1]} não registrada")
        if record.get("method") == "local_receipt":
            if output is None:
                continue  # The finalizer checks disk receipts; standalone checks are structural.
            exported = []
            for receipt_id in record.get("receipt_ids", []):
                if not isinstance(receipt_id, str) or len(receipt_id) != 64 or any(c not in "0123456789abcdef" for c in receipt_id):
                    errors.append(f"{key[0]}: ID de recibo inválido")
                    continue
                path = output / "reading_receipts" / (receipt_id + ".json")
                try:
                    receipt = json.loads(path.read_text(encoding="utf-8"))
                    if receipt.get("receipt_id") != receipt_id or identity({k:v for k,v in receipt.items() if k != "receipt_id"}) != receipt_id or receipt.get("corpus_revision") != memory["corpus_revision"]:
                        raise ValueError("recibo alterado/desatualizado")
                    for segment in receipt["segments"]:
                        if (segment["page_id"], segment["layer"]) == key:
                            start, end = segment["start"], segment["end"]
                            if not (type(start) is int and type(end) is int and 0 <= start <= end <= len(text)) or segment.get("length") != len(text):
                                raise ValueError("intervalo/quantidade inválida")
                            if segment["content_revision"] != page_revision(page) or hashlib.sha256(text[start:end].encode()).hexdigest() != segment["text_sha256"]:
                                raise ValueError("conteúdo diferente do exportado")
                            exported.append([start, end])
                except (OSError, ValueError, KeyError, TypeError):
                    errors.append(f"{key[0]}: recibo de leitura ausente, alterado ou obsoleto")
            for span in valid_spans:
                if span not in exported:
                    errors.append(f"{key[0]}: intervalo não consta dos recibos locais")
        elif record.get("method") != "host_observation" or not record.get("tool_reference"):
            errors.append(f"{key[0]}: indicar observação real da ferramenta ou recibo local")
    if seen != expected:
        errors.append("reading_coverage: páginas/camadas do corpus não examinadas")
    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta lote integral limitado por caracteres; avance next_offset até null.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args()
    try:
        print(json.dumps(reading_packet(args.output, offset=args.offset, max_chars=args.max_chars), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
