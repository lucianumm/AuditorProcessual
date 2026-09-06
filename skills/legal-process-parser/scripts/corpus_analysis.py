"""Lossless passage inventory. Heuristics identify review candidates, not truth."""
from __future__ import annotations

import re
from typing import Sequence, Any

try:
    from .case_memory import identity
except ImportError:
    from case_memory import identity


def passages(pages: Sequence[Any]) -> list[dict]:
    result = []
    for page in pages:
        source = {"source_sha256": getattr(page, "source_sha256", ""), "pdf_page": page.pdf_page,
                  "document_id": page.document_id, "piece": page.piece, "court_page": page.court_page}
        # Blank-line blocks preserve sentences, tables and exact offsets without
        # truncating a long page.  Build spans explicitly because a lookahead
        # based regex would skip the block after a blank-line separator.
        spans: list[tuple[int, int]] = []
        start = 0
        for separator in re.finditer(r"\n\s*\n", page.text):
            end = separator.start()
            while start < end and page.text[start].isspace():
                start += 1
            if page.text[start:end].strip():
                spans.append((start, end))
            start = separator.end()
        end = len(page.text)
        while start < end and page.text[start].isspace():
            start += 1
        if page.text[start:end].strip():
            spans.append((start, end))
        if not spans:
            result.append({"id": identity(source, "empty")[:24], "text": "", "source": source,
                           "source_excerpt": "", "start": 0, "end": 0,
                           "start_offset": 0, "end_offset": 0,
                           "nature": "lacuna", "status": "review_required"})
        for block_start, block_end in spans:
            text = page.text[block_start:block_end]
            nature = "alegacao" if page.piece in {"Petição Inicial", "Contestação", "Réplica", "Recurso"} else "fato_documentado"
            if re.search(r"\b(alega|afirma|sustenta|segundo)\b", text, re.I):
                nature = "alegacao"
            elif page.piece in {"Sentença", "Acórdão", "Decisão", "Despacho"}:
                nature = "decisao" if re.search(r"\b(julgo|determino|defiro|indefiro|condeno|dispositivo)\b", text, re.I) else "prova_registrada"
            result.append({"id": identity(source, block_start, text)[:24], "content_id": identity(text),
                           "text": text, "source_excerpt": text, "source": source,
                           "start": block_start, "end": block_end,
                           "start_offset": block_start, "end_offset": block_end,
                           "nature": nature, "status": "candidate_requires_semantic_review"})
    for index, item in enumerate(result):
        item["previous_id"] = result[index - 1]["id"] if index else None
        item["next_id"] = result[index + 1]["id"] if index + 1 < len(result) else None
    return result


def coverage_errors(pages: Sequence[Any], records: list[dict]) -> list[str]:
    errors = []
    by_page = {}
    for record in records:
        by_page.setdefault(record["source"]["document_id"], []).append(record)
    for page in pages:
        covered = set()
        for record in by_page.get(page.document_id, []):
            if record["source"]["document_id"] == page.document_id:
                start, end = record["start"], record["end"]
                if page.text[start:end] != record["text"]:
                    errors.append(f"PDF p. {page.pdf_page}: trecho divergente")
                covered.update(range(start, end))
        if any(not c.isspace() and index not in covered for index, c in enumerate(page.text)):
            errors.append(f"PDF p. {page.pdf_page}: conteúdo não representado")
    return errors
