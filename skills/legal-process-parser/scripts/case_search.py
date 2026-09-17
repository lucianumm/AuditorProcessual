"""Persistent, page-addressable corpus search; JSON is read only to rebuild the index."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

INDEX_NAME = "case_index.sqlite3"
DATE_PATTERN = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b")


def _dates(text: str) -> set[str]:
    result = set()
    for token in DATE_PATTERN.findall(text):
        try:
            parsed = date.fromisoformat(token) if "-" in token else datetime.strptime(token, "%d/%m/%Y").date()
            result.add(parsed.isoformat())
        except ValueError:
            continue
    return result


def _search_text(document: dict, page: dict) -> str:
    content = [document.get("name", ""), document.get("process_id") or "", page.get("piece") or "",
               page.get("text") or "", json.dumps(page.get("vision") or {}, ensure_ascii=False),
               json.dumps(page.get("visuals") or [], ensure_ascii=False)]
    return "\n".join(str(item) for item in content).casefold()


def rebuild_index(output: Path, documents: list[dict], corpus_revision: str) -> Path:
    """Build an independent SQLite file, then promote it after commit and close."""
    output.mkdir(parents=True, exist_ok=True)
    destination = output / INDEX_NAME
    memory_stat = (output / "case_memory.json").stat()
    descriptor, name = tempfile.mkstemp(prefix=".case-index-", suffix=".sqlite3", dir=output)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(name)) as connection:
            connection.executescript("""
                PRAGMA journal_mode=DELETE;
                PRAGMA synchronous=FULL;
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE pages (
                    id INTEGER PRIMARY KEY, document_order INTEGER NOT NULL,
                    source_sha256 TEXT NOT NULL, pdf_page INTEGER NOT NULL,
                    file TEXT NOT NULL, folder TEXT NOT NULL, process_id TEXT,
                    document_id TEXT, piece TEXT, court_page TEXT, status TEXT,
                    content_revision TEXT NOT NULL, search_text TEXT NOT NULL,
                    page_json TEXT NOT NULL,
                    UNIQUE(source_sha256, pdf_page)
                );
                CREATE INDEX pages_source ON pages(source_sha256, pdf_page);
                CREATE INDEX pages_document ON pages(document_id);
                CREATE INDEX pages_piece ON pages(piece);
                CREATE TABLE page_dates (page_id INTEGER NOT NULL, value TEXT NOT NULL,
                    PRIMARY KEY(page_id, value));
                CREATE INDEX page_dates_value ON page_dates(value, page_id);
            """)
            fts = True
            try:
                connection.execute("CREATE VIRTUAL TABLE page_fts USING fts5(search_text, content='pages', content_rowid='id', tokenize='unicode61 remove_diacritics 2')")
            except sqlite3.OperationalError:
                fts = False
            for order, document in enumerate(documents):
                for page in document.get("pages", []):
                    content = _search_text(document, page)
                    cursor = connection.execute("""INSERT INTO pages
                        (document_order, source_sha256, pdf_page, file, folder, process_id,
                         document_id, piece, court_page, status, content_revision, search_text, page_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (order, document["sha256"], page["pdf_page"], document.get("name", ""),
                         document.get("folder", "."), document.get("process_id"), page.get("document_id"),
                         page.get("piece"), str(page.get("court_page")) if page.get("court_page") is not None else None,
                         page.get("status"), page.get("content_revision", ""), content,
                         json.dumps(page, ensure_ascii=False)))
                    connection.executemany("INSERT INTO page_dates(page_id, value) VALUES (?, ?)",
                                           ((cursor.lastrowid, item) for item in _dates(content)))
            if fts:
                connection.execute("INSERT INTO page_fts(page_fts) VALUES ('rebuild')")
            connection.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", (
                ("corpus_revision", corpus_revision), ("memory_mtime_ns", str(memory_stat.st_mtime_ns)),
                ("memory_size", str(memory_stat.st_size)), ("fts_available", "1" if fts else "0")))
            connection.commit()
        os.replace(name, destination)
        return destination
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _ensure_index(output: Path) -> Path:
    path = output / INDEX_NAME
    memory = output / "case_memory.json"
    stat = memory.stat()
    if path.is_file():
        try:
            with closing(sqlite3.connect(path)) as connection:
                metadata = dict(connection.execute("SELECT key, value FROM metadata"))
                if (metadata.get("memory_mtime_ns") == str(stat.st_mtime_ns)
                        and metadata.get("memory_size") == str(stat.st_size)):
                    return path
        except sqlite3.DatabaseError:
            pass
    old = json.loads(memory.read_text(encoding="utf-8-sig"))
    return rebuild_index(output, old.get("documents", []), old.get("corpus_revision", ""))


def _snippet(text: str, query: str, width: int) -> str:
    if not query:
        return text[:width]
    folded = text.casefold()
    tokens = [token for token in re.findall(r"\w+", query.casefold()) if token]
    positions = [folded.find(token) for token in tokens]
    position = min((item for item in positions if item >= 0), default=0)
    start = max(0, position - width // 3)
    end = min(len(text), start + width)
    return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")


def search_memory(output: Path, query: str = "", *, offset: int = 0, limit: int = 20,
                  mode: str = "tokens", source_sha256: str | None = None,
                  document_id: str | None = None, document: str | None = None,
                  piece: str | None = None, person: str | None = None,
                  date_from: str | None = None, date_to: str | None = None,
                  amount: str | None = None, include_full_pages: bool = False,
                  context_chars: int = 500) -> dict:
    """Return one SQL page. ``tokens`` uses FTS5 if present; ``substring`` keeps old semantics."""
    if offset < 0 or not 1 <= limit <= 100 or mode not in {"tokens", "substring"}:
        raise ValueError("offset >= 0, limit entre 1 e 100, mode tokens ou substring")
    if not 80 <= context_chars <= 4000:
        raise ValueError("context_chars deve estar entre 80 e 4000")
    if date_from:
        date.fromisoformat(date_from)
    if date_to:
        date.fromisoformat(date_to)
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from posterior a date_to")
    path = _ensure_index(output)
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        tokens = [token for token in re.findall(r"\w+", query.casefold()) if token]
        use_fts = bool(tokens and mode == "tokens" and metadata.get("fts_available") == "1")
        relation = "pages AS p JOIN page_fts ON page_fts.rowid = p.id" if use_fts else "pages AS p"
        conditions: list[str] = []
        params: list[object] = []
        if use_fts:
            conditions.append("page_fts MATCH ?")
            params.append(" AND ".join('"' + token.replace('"', '""') + '"*' for token in tokens))
        elif query.strip():
            for token in query.casefold().split():
                conditions.append("instr(p.search_text, ?) > 0")
                params.append(token)
        for field, value in (("source_sha256", source_sha256), ("document_id", document_id), ("piece", piece)):
            if value:
                conditions.append(f"p.{field} = ?")
                params.append(value)
        if document:
            conditions.append("instr(lower(p.file), ?) > 0")
            params.append(document.casefold())
        for value in (person, amount):
            if value:
                conditions.append("instr(p.search_text, ?) > 0")
                params.append(value.casefold())
        if date_from or date_to:
            conditions.append("EXISTS (SELECT 1 FROM page_dates AS d WHERE d.page_id = p.id AND d.value >= ? AND d.value <= ?)")
            params.extend((date_from or "0001-01-01", date_to or "9999-12-31"))
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        total = connection.execute(f"SELECT count(*) FROM {relation}{where}", params).fetchone()[0]
        rows = connection.execute(f"""SELECT p.source_sha256, p.pdf_page, p.file, p.folder,
                  p.process_id, p.document_id, p.piece, p.court_page, p.status,
                  p.content_revision, p.search_text, p.page_json
                  FROM {relation}{where} ORDER BY p.document_order, p.pdf_page LIMIT ? OFFSET ?""",
                  [*params, limit, offset]).fetchall()
        pages = []
        for row in rows:
            page = dict(row)
            payload = json.loads(page.pop("page_json"))
            page["snippet"] = _snippet(page.pop("search_text"), query, context_chars)
            page["page_id"] = f"{page['source_sha256']}:{page['pdf_page']}"
            if include_full_pages:
                page.update(payload)
            pages.append(page)
    return {"total": total, "offset": offset,
            "next_offset": offset + limit if offset + limit < total else None,
            "pages": pages, "corpus_revision": metadata.get("corpus_revision"),
            "search_mode": "fts5" if use_fts else "substring"}
