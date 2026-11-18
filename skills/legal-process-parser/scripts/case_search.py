"""Persistent, page-addressable corpus search; JSON is read only to rebuild the index."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
import unicodedata
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

INDEX_NAME = "case_index.sqlite3"
INDEX_SCHEMA_VERSION = "2.1"
DATE_PATTERN = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b")

ENTITY_PATTERNS: dict[str, re.Pattern[str]] = {
    "money": re.compile(r"R\$\s*(?:\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)", re.IGNORECASE),
    "date": DATE_PATTERN,
    "cnj": re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b"),
    "cpf_cnpj": re.compile(r"\b(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b"),
    "citation": re.compile(
        r"(?<![\wÀ-ÿ])(?:"
        r"art(?:igo)?s?\.?\s*\d{1,3}(?:\.\d{3})*(?:[º°ª]|-[A-Za-z]{1,2})?"
        r"(?:\s*,?\s*(?:§\s*\d+[º°ª]?|par[áa]grafo\s+[úu]nico|caput|inciso\s+[IVXLCDM]+))*"
        r"|s[úu]mula(?:\s+vinculante)?\s*(?:n[º°o.]*\s*)?\d{1,4}"
        r"|tema\s*(?:n[º°o.]*\s*)?\d{1,5}"
        r"|lei(?:\s+complementar)?\s*(?:n[º°o.]*\s*)?\d{1,3}(?:\.\d{3})*(?:/\d{2,4})?"
        r")",
        re.IGNORECASE,
    ),
}
VALID_ENTITY_TYPES = frozenset((*ENTITY_PATTERNS.keys(), "all"))


def fold_accents(text: str) -> str:
    """Casefold + remoção de diacríticos para busca insensível a acentos e falhas de OCR."""
    plain = "".join(ch for ch in unicodedata.normalize("NFKD", str(text)) if not unicodedata.combining(ch))
    return plain.casefold()


def _dates(text: str) -> set[str]:
    result = set()
    for token in DATE_PATTERN.findall(text):
        try:
            parsed = date.fromisoformat(token) if "-" in token else datetime.strptime(token, "%d/%m/%Y").date()
            result.add(parsed.isoformat())
        except ValueError:
            continue
    return result


def _raw_page_text(document: dict, page: dict) -> str:
    vision = page.get("vision") or {}
    vision_parts = [str(vision.get(k) or "") for k in ("description", "transcription")] if isinstance(vision, dict) else [json.dumps(vision, ensure_ascii=False)]
    content = [
        document.get("name", ""),
        document.get("process_id") or "",
        page.get("piece") or "",
        page.get("text") or "",
        "\n".join(p for p in vision_parts if p),
        json.dumps(page.get("visuals") or [], ensure_ascii=False),
    ]
    return "\n".join(str(item) for item in content if item)


def _search_text(document: dict, page: dict) -> str:
    content = [document.get("name", ""), document.get("process_id") or "", page.get("piece") or "",
               page.get("text") or "", json.dumps(page.get("vision") or {}, ensure_ascii=False),
               json.dumps(page.get("visuals") or [], ensure_ascii=False)]
    return "\n".join(str(item) for item in content).casefold()


def extract_entities(text: str, entity_type: str | None = None) -> dict[str, list[str]]:
    """Extrai valores monetários, datas, números CNJ, CPF/CNPJ e citações normativas/jurisprudenciais."""
    if entity_type is not None and entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(f"entity_type inválido: {entity_type!r}; use um de {sorted(VALID_ENTITY_TYPES)}")
    kinds = tuple(ENTITY_PATTERNS.keys()) if entity_type in (None, "all") else (entity_type,)
    extracted: dict[str, list[str]] = {}
    for kind in kinds:
        pattern = ENTITY_PATTERNS[kind]
        seen: dict[str, None] = {}
        for match in pattern.finditer(text):
            cleaned = re.sub(r"\s+", " ", match.group(0)).strip()
            if kind == "date":
                try:
                    if "-" in cleaned:
                        date.fromisoformat(cleaned)
                    else:
                        datetime.strptime(cleaned, "%d/%m/%Y")
                except ValueError:
                    continue
            if cleaned:
                seen.setdefault(cleaned, None)
        if seen:
            extracted[kind] = list(seen.keys())
    return extracted


def rebuild_index(output: Path, documents: list[dict], corpus_revision: str, accounts: list[dict] | None = None) -> Path:
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
                    document_id TEXT, piece TEXT, folded_piece TEXT,
                    court_page TEXT, status TEXT,
                    content_revision TEXT NOT NULL, search_text TEXT NOT NULL,
                    folded_text TEXT NOT NULL, raw_text TEXT NOT NULL,
                    page_json TEXT NOT NULL,
                    UNIQUE(source_sha256, pdf_page)
                );
                CREATE INDEX pages_source ON pages(source_sha256, pdf_page);
                CREATE INDEX pages_document ON pages(document_id);
                CREATE INDEX pages_piece ON pages(piece);
                CREATE INDEX pages_folded_piece ON pages(folded_piece);
                CREATE TABLE page_dates (page_id INTEGER NOT NULL, value TEXT NOT NULL,
                    PRIMARY KEY(page_id, value));
                CREATE INDEX page_dates_value ON page_dates(value, page_id);
                CREATE TABLE page_entities (
                    page_id INTEGER NOT NULL, kind TEXT NOT NULL, value TEXT NOT NULL,
                    ord INTEGER NOT NULL,
                    PRIMARY KEY(page_id, kind, value)
                );
                CREATE INDEX page_entities_kind ON page_entities(kind, page_id);
                CREATE TABLE client_accounts (
                    id TEXT PRIMARY KEY, received_order INTEGER NOT NULL,
                    text TEXT NOT NULL, conversation_reference TEXT NOT NULL,
                    supersedes TEXT, source_revision TEXT NOT NULL,
                    search_text TEXT NOT NULL, folded_text TEXT NOT NULL
                );
            """)
            fts = True
            try:
                connection.execute(
                    "CREATE VIRTUAL TABLE page_fts USING fts5(folded_text, content='pages', content_rowid='id', tokenize='unicode61 remove_diacritics 2')"
                )
            except sqlite3.OperationalError:
                fts = False
            for order, document in enumerate(documents):
                for page in document.get("pages", []):
                    raw_text = _raw_page_text(document, page)
                    content = _search_text(document, page)
                    folded = fold_accents(content)
                    piece_val = page.get("piece")
                    folded_piece = fold_accents(piece_val) if piece_val else ""
                    cursor = connection.execute("""INSERT INTO pages
                        (document_order, source_sha256, pdf_page, file, folder, process_id,
                         document_id, piece, folded_piece, court_page, status, content_revision,
                         search_text, folded_text, raw_text, page_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (order, document["sha256"], page["pdf_page"], document.get("name", ""),
                         document.get("folder", "."), document.get("process_id"), page.get("document_id"),
                         piece_val, folded_piece,
                         str(page.get("court_page")) if page.get("court_page") is not None else None,
                         page.get("status"), page.get("content_revision", ""), content, folded, raw_text,
                         json.dumps(page, ensure_ascii=False)))
                    page_id = cursor.lastrowid
                    connection.executemany(
                        "INSERT INTO page_dates(page_id, value) VALUES (?, ?)",
                        ((page_id, item) for item in _dates(content)),
                    )
                    entities = extract_entities(raw_text)
                    entity_rows = [
                        (page_id, kind, val, idx)
                        for kind, values in entities.items()
                        for idx, val in enumerate(values)
                    ]
                    if entity_rows:
                        connection.executemany(
                            "INSERT INTO page_entities(page_id, kind, value, ord) VALUES (?, ?, ?, ?)",
                            entity_rows,
                        )
            if fts:
                connection.execute("INSERT INTO page_fts(page_fts) VALUES ('rebuild')")
            for order, account in enumerate(accounts or []):
                acc_search = (account["text"] + "\n" + account["conversation_reference"]).casefold()
                connection.execute(
                    "INSERT INTO client_accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (account["id"], order, account["text"], account["conversation_reference"],
                     account.get("supersedes"), account["sha256"],
                     acc_search, fold_accents(acc_search)),
                )
            connection.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", (
                ("corpus_revision", corpus_revision),
                ("memory_mtime_ns", str(memory_stat.st_mtime_ns)),
                ("memory_size", str(memory_stat.st_size)),
                ("fts_available", "1" if fts else "0"),
                ("index_schema_version", INDEX_SCHEMA_VERSION),
            ))
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
                        and metadata.get("memory_size") == str(stat.st_size)
                        and metadata.get("index_schema_version") == INDEX_SCHEMA_VERSION):
                    return path
        except sqlite3.DatabaseError:
            pass
    old = json.loads(memory.read_text(encoding="utf-8-sig"))
    return rebuild_index(output, old.get("documents", []), old.get("corpus_revision", ""), old.get("client_records", []))


def search_client_records(output: Path, query: str = "", *, offset: int = 0, limit: int = 20) -> dict:
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError("offset >= 0 e limit entre 1 e 100")
    path = _ensure_index(output)
    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        tokens = fold_accents(query).split()
        where = " WHERE " + " AND ".join("instr(folded_text, ?) > 0" for _ in tokens) if tokens else ""
        total = connection.execute("SELECT count(*) FROM client_accounts" + where, tokens).fetchone()[0]
        rows = connection.execute(
            "SELECT id, text, conversation_reference, supersedes, source_revision FROM client_accounts"
            + where + " ORDER BY received_order LIMIT ? OFFSET ?",
            [*tokens, limit, offset],
        ).fetchall()
    return {
        "total": total,
        "offset": offset,
        "next_offset": offset + limit if offset + limit < total else None,
        "records": [{**dict(row), "source_kind": "client_account"} for row in rows],
        "meaning": "Relatos recebidos; nenhuma página/documento fictício.",
    }


def _snippet(text: str, query: str, width: int) -> str:
    if not query:
        return text[:width]
    folded_chars: list[str] = []
    index_map: list[int] = []
    for orig_idx, ch in enumerate(text):
        for fch in unicodedata.normalize("NFKD", ch):
            if not unicodedata.combining(fch):
                folded_chars.append(fch.casefold())
                index_map.append(orig_idx)
    folded = "".join(folded_chars)
    tokens = [token for token in re.findall(r"\w+", fold_accents(query)) if token]
    positions = [folded.find(token) for token in tokens]
    folded_pos = min((item for item in positions if item >= 0), default=-1)
    position = index_map[folded_pos] if 0 <= folded_pos < len(index_map) else 0
    start = max(0, position - width // 3)
    end = min(len(text), start + width)
    return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")


def search_memory(output: Path, query: str = "", *, offset: int = 0, limit: int = 20,
                  mode: str = "tokens", source_sha256: str | None = None,
                  document_id: str | None = None, document: str | None = None,
                  piece: str | None = None, person: str | None = None,
                  date_from: str | None = None, date_to: str | None = None,
                  amount: str | None = None, entity_type: str | None = None,
                  include_full_pages: bool = False, context_chars: int = 500,
                  context_window: int = 0) -> dict:
    """Return one search page; exact whole-page reading is opt-in.

    Snippets are for navigation only and are never evidence of complete reading.
    """
    if offset < 0 or not 1 <= limit <= 100 or mode not in {"tokens", "substring"}:
        raise ValueError("offset >= 0, limit entre 1 e 100, mode tokens ou substring")
    if not 80 <= context_chars <= 4000:
        raise ValueError("context_chars deve estar entre 80 e 4000")
    if not 0 <= context_window <= 5:
        raise ValueError("context_window deve estar entre 0 e 5")
    if entity_type is not None and entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(f"entity_type inválido: {entity_type!r}; use um de {sorted(VALID_ENTITY_TYPES)}")
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
        folded_query = fold_accents(query)
        tokens = [token for token in re.findall(r"\w+", folded_query) if token]
        use_fts = bool(tokens and mode == "tokens" and metadata.get("fts_available") == "1")
        relation = "pages AS p JOIN page_fts ON page_fts.rowid = p.id" if use_fts else "pages AS p"
        conditions: list[str] = []
        params: list[object] = []

        if use_fts:
            conditions.append("page_fts MATCH ?")
            params.append(" AND ".join('"' + token.replace('"', '""') + '"*' for token in tokens))
        elif folded_query.strip():
            for token in folded_query.split():
                conditions.append("instr(p.folded_text, ?) > 0")
                params.append(token)

        for field, value in (("source_sha256", source_sha256), ("document_id", document_id)):
            if value:
                conditions.append(f"p.{field} = ?")
                params.append(value)

        if piece:
            conditions.append("instr(COALESCE(p.folded_piece, ''), ?) > 0")
            params.append(fold_accents(piece))

        if document:
            conditions.append("instr(lower(p.file), ?) > 0")
            params.append(document.casefold())

        for value in (person, amount):
            if value:
                conditions.append("instr(p.folded_text, ?) > 0")
                params.append(fold_accents(value))

        if date_from or date_to:
            conditions.append("EXISTS (SELECT 1 FROM page_dates AS d WHERE d.page_id = p.id AND d.value >= ? AND d.value <= ?)")
            params.extend((date_from or "0001-01-01", date_to or "9999-12-31"))

        if entity_type is not None:
            if entity_type == "all":
                conditions.append("EXISTS (SELECT 1 FROM page_entities AS e WHERE e.page_id = p.id)")
            else:
                conditions.append("EXISTS (SELECT 1 FROM page_entities AS e WHERE e.page_id = p.id AND e.kind = ?)")
                params.append(entity_type)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        total = connection.execute(f"SELECT count(*) FROM {relation}{where}", params).fetchone()[0]
        rows = connection.execute(
            f"""SELECT p.id, p.source_sha256, p.pdf_page, p.file, p.folder,
                  p.process_id, p.document_id, p.piece, p.court_page, p.status,
                  p.content_revision, p.search_text, p.raw_text, p.page_json
                  FROM {relation}{where} ORDER BY p.document_order, p.pdf_page LIMIT ? OFFSET ?""",
            [*params, limit, offset],
        ).fetchall()

        pages = []
        for row in rows:
            page = dict(row)
            db_page_id = page.pop("id")
            raw_text = page.pop("raw_text")
            search_text = page.pop("search_text")
            payload = json.loads(page.pop("page_json"))
            display_source = payload.get("text") or raw_text or search_text
            page["snippet"] = _snippet(display_source, query, context_chars)
            page["page_id"] = f"{page['source_sha256']}:{page['pdf_page']}"

            # Entidades estruturadas extraídas da página
            if entity_type is not None and entity_type != "all":
                ent_rows = connection.execute(
                    "SELECT kind, value FROM page_entities WHERE page_id = ? AND kind = ? ORDER BY ord",
                    (db_page_id, entity_type),
                ).fetchall()
            else:
                ent_rows = connection.execute(
                    "SELECT kind, value FROM page_entities WHERE page_id = ? ORDER BY kind, ord",
                    (db_page_id,),
                ).fetchall()
            entities_map: dict[str, list[str]] = {}
            for erow in ent_rows:
                entities_map.setdefault(erow["kind"], []).append(erow["value"])
            if entity_type is not None or entities_map:
                page["extracted_entities"] = entities_map

            if context_window > 0:
                adj_rows = connection.execute(
                    """SELECT pdf_page, piece, court_page, raw_text, page_json
                       FROM pages
                       WHERE source_sha256 = ? AND pdf_page BETWEEN ? AND ? AND pdf_page != ?
                       ORDER BY pdf_page""",
                    (page["source_sha256"], page["pdf_page"] - context_window, page["pdf_page"] + context_window, page["pdf_page"]),
                ).fetchall()
                adjacent = []
                for adj in adj_rows:
                    adj_payload = json.loads(adj["page_json"])
                    adj_text = adj_payload.get("text") or adj["raw_text"] or ""
                    adjacent.append({
                        "pdf_page": adj["pdf_page"],
                        "page_id": f"{page['source_sha256']}:{adj['pdf_page']}",
                        "piece": adj["piece"],
                        "court_page": adj["court_page"],
                        "snippet": adj_text[: min(context_chars, 300)],
                    })
                page["context_window"] = adjacent

            if include_full_pages:
                page.update(payload)
            pages.append(page)

    return {
        "total": total,
        "offset": offset,
        "next_offset": offset + limit if offset + limit < total else None,
        "pages": pages,
        "corpus_revision": metadata.get("corpus_revision"),
        "search_mode": "fts5" if use_fts else "substring",
    }
