"""Capture an explicitly selected official HTML/text source; no process upload."""
from __future__ import annotations

import argparse
import hashlib
import json
import io
from datetime import datetime, timezone
from html.parser import HTMLParser
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

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "br", "div", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def capture(url: str, output: Path) -> dict:
    if not official_url(url):
        raise ValueError("Use URL HTTPS oficial brasileira, sem credenciais")
    opener = build_opener(OfficialRedirect())
    with opener.open(Request(url, headers={"User-Agent": "AuditorProcessual/1.0 source-research"}), timeout=30) as response:
        final_url = response.geturl()
        if not official_url(final_url):
            raise ValueError("Origem final não oficial")
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "text/plain", "application/xhtml+xml", "application/pdf"}:
            raise ValueError("Formato oficial não suportado: use HTML, TXT ou PDF")
        raw = response.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise ValueError("Fonte maior que 8 MiB; selecionar seção oficial específica")
        encoding = response.headers.get_content_charset() or "utf-8"
        if content_type == "application/pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            if len(reader.pages) > MAX_PDF_PAGES:
                raise ValueError("PDF oficial extenso demais; selecionar seção específica")
            pages = [p.extract_text() or "" for p in reader.pages]
            decoded = "\n\n".join(f"[PDF p. {i}]\n{text}" for i, text in enumerate(pages, 1))
            if len(decoded.encode("utf-8")) > MAX_SOURCE_BYTES:
                raise ValueError("Texto extraído da fonte excede 8 MiB; selecionar seção específica")
            if not any(text.strip() for text in pages):
                raise ValueError("PDF oficial sem texto: pesquisa pendente; obtenha fonte acessível ou revisão OCR/visual verificável")
            encoding = "pdf-text/utf-8"
        else:
            try:
                decoded = raw.decode(encoding)
            except UnicodeDecodeError:
                encoding = "cp1252"
                decoded = raw.decode(encoding)
    parser = TextParser()
    parser.feed(decoded)
    text = "".join(parser.parts) if content_type in {"text/html", "application/xhtml+xml"} else decoded
    if len(text.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("Texto da fonte excede 8 MiB; selecionar seção específica")
    receipt = {"requested_url": url, "url": final_url, "accessed_on": datetime.now(timezone.utc).date().isoformat(),
               "text": text, "raw_content_hash": hashlib.sha256(raw).hexdigest(),
               "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
               "content_type": content_type, "encoding": encoding, "method": "official_http_capture"}
    receipt["capture_id"] = identity(receipt)
    atomic_bytes(output / "research_sources" / (receipt["capture_id"] + ".source"), raw)
    atomic_json(output / "research_sources" / (receipt["capture_id"] + ".json"), receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Captura fonte oficial selecionada pela IA; não envia autos.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    receipt = capture(args.url, args.output.resolve())
    print(json.dumps({k: v for k, v in receipt.items() if k != "text"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
