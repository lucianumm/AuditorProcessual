"""Capture an explicitly selected official HTML/text source; no process upload."""
from __future__ import annotations

import argparse
import hashlib
import json
import io
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.client import HTTPException
from pathlib import Path
from urllib.request import HTTPRedirectHandler, Request, build_opener

try:
    from .case_memory import atomic_json, atomic_bytes, identity
    from .source_records import official_url
except ImportError:
    from case_memory import atomic_json, atomic_bytes, identity
    from source_records import official_url


MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_PDF_PAGES = 1000
HTML_TYPES = {"text/html", "application/xhtml+xml"}
TEXT_TYPES = HTML_TYPES | {"text/plain", "application/json", "application/xml", "text/xml"}
SUPPORTED_TYPES = TEXT_TYPES | {"application/pdf"}
USER_AGENT = "Mozilla/5.0 (compatible; AuditorProcessual/0.21; +https://github.com/lucianumm/AuditorProcessual)"
# Anti-bot pages of official portals (WAF/captcha) are not legal sources.
BLOCK_SIGNATURES = ("verificação de segurança", "verificacao de seguranca", "captcha", "access denied",
                    "acesso negado", "just a moment", "attention required", "request unsuccessful",
                    "request rejected", "the requested url was rejected", "x-amzn-waf")


class SourceBlocked(ValueError):
    """The official portal answered with a challenge or empty body instead of the source."""


class OfficialRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not official_url(newurl):
            raise ValueError("Redirecionamento para fonte não oficial bloqueado")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
        self.marked_stack = []
        self.title = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag == "title":
            self.in_title = True
        attributes = dict(attrs)
        style = str(attributes.get("style", "")).replace(" ", "").lower()
        marker = "revoked" if tag in {"s", "del", "strike"} or "line-through" in style else (
            "added" if tag in {"ins"} else None
        )
        if marker:
            self.marked_stack.append((tag, marker))
            label = "REDAÇÃO ANTERIOR/RISCADA" if marker == "revoked" else "REDAÇÃO ACRESCENTADA"
            self.parts.append(f"\n[{label}] ")
        if tag in {"p", "br", "div", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag == "title":
            self.in_title = False
        for index in range(len(self.marked_stack) - 1, -1, -1):
            marked_tag, marker = self.marked_stack[index]
            if marked_tag != tag:
                continue
            self.marked_stack.pop(index)
            label = "ANTERIOR/RISCADA" if marker == "revoked" else "ACRESCENTADA"
            self.parts.append(f" [FIM DA REDAÇÃO {label}]\n")
            break

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if not self.hidden:
            self.parts.append(data)


def source_text(raw: bytes, content_type: str, encoding: str) -> str:
    """Derive the stored text from the preserved bytes; inspection repeats this."""
    if content_type == "application/pdf":
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(raw))
            if len(reader.pages) > MAX_PDF_PAGES:
                raise ValueError("PDF oficial extenso demais; selecionar seção específica")
            pages = [p.extract_text() or "" for p in reader.pages]
        except ValueError:
            raise
        except Exception as error:  # pypdf raises its own hierarchy for damaged files.
            raise ValueError("PDF oficial ilegível: " + type(error).__name__) from error
        if not any(text.strip() for text in pages):
            raise ValueError("PDF oficial sem texto: pesquisa pendente; obtenha fonte acessível ou revisão OCR/visual verificável")
        return "\n\n".join(f"[PDF p. {i}]\n{text}" for i, text in enumerate(pages, 1))
    decoded = raw.decode(encoding)
    if content_type in HTML_TYPES:
        parser = TextParser()
        parser.feed(decoded)
        return "".join(parser.parts)
    return decoded


def blocked_reason(status, headers, raw: bytes, text: str, content_type: str) -> str | None:
    """Return why a response is a portal block instead of an official text."""
    if isinstance(status, int) and status != 200:
        return f"HTTP {status} sem conteúdo integral da fonte"
    waf = headers.get("x-amzn-waf-action") if hasattr(headers, "get") else None
    if isinstance(waf, str) and waf:
        return "desafio anti-robô do portal (" + waf + ")"
    if not raw or not text.strip():
        return "resposta sem texto"
    if content_type in HTML_TYPES:
        parser = TextParser()
        parser.feed(raw.decode("utf-8", "replace"))
        title = " ".join("".join(parser.title).split()).lower()
        sample = " ".join(text.split()).lower()
        if any(s in title for s in BLOCK_SIGNATURES) or (len(sample) < 3000 and any(s in sample for s in BLOCK_SIGNATURES)):
            return "página de verificação/bloqueio do portal"
    return None


def capture(url: str, output: Path, *, response_id: str | None = None) -> dict:
    if not official_url(url):
        raise ValueError("Use URL HTTPS oficial brasileira, sem credenciais")
    opener = build_opener(OfficialRedirect())
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9",
               "Accept": "text/html,application/xhtml+xml,application/pdf,application/json,text/plain;q=0.9,*/*;q=0.1"}
    try:
        with opener.open(Request(url, headers=headers), timeout=30) as response:
            final_url = response.geturl()
            if not official_url(final_url):
                raise ValueError("Origem final não oficial")
            content_type = response.headers.get_content_type()
            if content_type not in SUPPORTED_TYPES:
                raise ValueError("Formato oficial não suportado: use HTML, TXT, JSON, XML ou PDF")
            raw = response.read(MAX_SOURCE_BYTES + 1)
            if len(raw) > MAX_SOURCE_BYTES:
                raise ValueError("Fonte maior que 8 MiB; selecionar seção oficial específica")
            status = getattr(response, "status", None)
            response_headers = response.headers
            encoding = response.headers.get_content_charset() or "utf-8"
    except HTTPException as error:
        raise ValueError("Resposta HTTP incompleta: " + type(error).__name__) from error
    if content_type == "application/pdf":
        encoding = "pdf-text/utf-8"
        text = source_text(raw, content_type, encoding)
    else:
        try:
            text = source_text(raw, content_type, encoding)
        except (UnicodeDecodeError, LookupError):
            encoding = "cp1252"
            text = source_text(raw, content_type, encoding)
    reason = blocked_reason(status, response_headers, raw, text, content_type)
    if reason:
        raise SourceBlocked("Portal oficial não entregou a fonte (" + reason + "); usar navegador da IA ou arquivo oficial enviado e registrar a tentativa")
    if len(text.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("Texto da fonte excede 8 MiB; selecionar seção específica")
    captured_at = datetime.now(timezone.utc)
    receipt = {"requested_url": url, "url": final_url, "accessed_on": captured_at.date().isoformat(),
               "text": text, "raw_content_hash": hashlib.sha256(raw).hexdigest(),
               "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
               "content_type": content_type, "encoding": encoding, "method": "official_http_capture"}
    receipt["captured_at"] = captured_at.isoformat()
    if response_id is not None:
        receipt["response_id"] = response_id
    receipt["capture_id"] = identity(receipt)
    atomic_bytes(output / "research_sources" / (receipt["capture_id"] + ".source"), raw)
    atomic_json(output / "research_sources" / (receipt["capture_id"] + ".json"), receipt)
    try:
        from .research_memory import register_source_record
    except ImportError:
        from research_memory import register_source_record
    register_source_record(output, receipt)
    return receipt


def reconfirm(record: dict, output: Path) -> dict:
    """Fetch the same official URL again and compare bytes; never rewrites the old record."""
    if record.get("method") != "official_http_capture":
        raise ValueError("Reconfirmação aplica-se a captura HTTP oficial")
    fresh = capture(record.get("requested_url") or record["url"], output, response_id=record.get("response_id"))
    return {"capture_id": record.get("capture_id"), "fresh_capture_id": fresh["capture_id"],
            "same_raw_content": fresh["raw_content_hash"] == record.get("raw_content_hash"),
            "same_text": fresh["text_hash"] == record.get("text_hash"), "reconfirmed_at": fresh["captured_at"]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Captura fonte oficial selecionada pela IA; não envia autos.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    try:
        receipt = capture(args.url, args.output.resolve())
    except (OSError, ValueError, ImportError) as error:
        print(json.dumps({"error": str(error), "blocked_by_portal": isinstance(error, SourceBlocked)}, ensure_ascii=False))
        return 1
    print(json.dumps({k: v for k, v in receipt.items() if k != "text"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
