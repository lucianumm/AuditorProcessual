"""Locate official candidates from captured indexes; selection remains authored."""
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

try:
    from .research_sources import capture
    from .source_records import official_url
    from .numeric_criteria import fold
except ImportError:
    from research_sources import capture
    from source_records import official_url
    from numeric_criteria import fold


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag == "a" and not self.hidden:
            self.current = {"href": dict(attrs).get("href", ""), "label": ""}

    def handle_data(self, data):
        if self.current is not None and not self.hidden:
            self.current["label"] += data

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def rank_links(html: str, base_url: str, question: str, *, limit: int = 20) -> list[dict]:
    if not question.strip() or not 1 <= limit <= 50 or not official_url(base_url):
        raise ValueError("Indicar questão, índice oficial e limite entre 1 e 50")
    parser = Links()
    parser.feed(html)
    words = {w for w in re.findall(r"[a-z0-9]+", fold(question)) if len(w) >= 4} - {"para", "como", "sobre", "trabalho", "direito", "qual", "quais"}
    found = {}
    for link in parser.links:
        url = urljoin(base_url, link["href"]).split("#", 1)[0]
        if not official_url(url) or url == base_url.split("#", 1)[0]:
            continue
        searchable = fold(link["label"] + " " + urlsplit(url).path)
        matched = sorted(w for w in words if w in searchable)
        if not matched:
            continue
        candidate = {"url": url, "label": " ".join(link["label"].split()), "matched_terms": matched,
                     "locator_score": len(matched), "status": "candidate_requires_full_text_selection"}
        if url not in found or found[url]["locator_score"] < candidate["locator_score"]:
            found[url] = candidate
    return sorted(found.values(), key=lambda r: (-r["locator_score"], r["url"]))[:limit]


def discover_candidates(output: Path, urls: list[str], question: str, *, limit: int = 20) -> dict:
    if not urls or len(urls) > 4 or any(not official_url(url) for url in urls):
        raise ValueError("Selecionar até quatro índices ou resultados de busca oficiais efetivamente localizados")
    if not question.strip() or not 1 <= limit <= 50:
        raise ValueError("Indicar questão e limite entre 1 e 50")
    indexes, candidates = [], {}
    for url in dict.fromkeys(urls):
        try:
            record = capture(url, output)
            if record["content_type"] not in {"text/html", "application/xhtml+xml"}:
                indexes.append({"url": url, "status": "not_html_index", "capture_id": record["capture_id"]})
                continue
            raw = (output / "research_sources" / (record["capture_id"] + ".source")).read_bytes().decode(record["encoding"])
            found = rank_links(raw, record["url"], question, limit=limit)
            indexes.append({"url": record["url"], "status": "captured", "capture_id": record["capture_id"], "candidates_found": len(found)})
            for item in found:
                item["index_capture_ids"] = sorted(set(candidates.get(item["url"], {}).get("index_capture_ids", []) + [record["capture_id"]]))
                candidates[item["url"]] = item
        except (OSError, ValueError, LookupError) as error:
            indexes.append({"url": url, "status": "unavailable", "reason": str(error)})
    return {"schema_version": "1.0", "question": question, "indexes": indexes,
            "candidates": sorted(candidates.values(), key=lambda r: (-r["locator_score"], r["url"]))[:limit],
            "status": "candidates_located" if candidates else "no_candidate_located",
            "next_step": "Examinar inteiro teor, redação por período e contrapontos; consultar a fonte escolhida na sessão da resposta e vincular dispositivo/cláusula/fundamento.",
            "scope": "Literal location and real HTTP capture; empty results do not prove absence; discovery does not satisfy per-response consultation."}
