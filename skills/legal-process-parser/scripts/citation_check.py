"""Locate cited provisions in official text and read their version markers.

The checks are structural: a located provision without a revocation marker is
not a statement that the norm governs the case. Portals that refuse automated
access must be observed by the host browser or supplied as an official file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

WS = re.compile(r"\s+")
ORD = r"(?:[ \t]?(?:º|°|ª|o)(?![A-Za-zÀ-ÿ]))?"
SUFFIX = r"(?:-([A-Z]{1,2})(?=[\s.\-–—:;,)]|$))?"
# Planalto headings vary: "Art. 66 -", " Art . 1º", "Art.\xa018.", "Art. .\n195 -", "Art.\n872 -".
ORD_HEAD = r"(?:[ \t\xa0]?(?:º|°|ª|o)(?![A-Za-zÀ-ÿ]))?"
ARTICLE_HEAD = re.compile(r"(?m)^[ \t\r\xa0]*(?:\[[^\]\n]*\][ \t\r\xa0]*)*Art[ \t\xa0]*\.[\s.]*(\d{1,4})" + ORD_HEAD + SUFFIX)
ARTICLE_INLINE = re.compile(r"(?<![\w])Art[ \xa0]*\.[ \xa0.]*(\d{1,4})" + ORD_HEAD + SUFFIX)
PARAGRAPH = re.compile(r"(?<![\w])§[ ]?(\d{1,3})" + ORD + SUFFIX + r"|Parágrafo único", re.IGNORECASE)
PARAGRAPH_HEAD = re.compile(r"(?m)^[ \t\r\xa0]*(?:\[[^\]\n]*\][ \t\xa0]*)*(?:§[ \t\xa0]?(\d{1,3})" + ORD.replace("[ \\t]", "[ \\t\\xa0]") + SUFFIX + r"|Parágrafo único)", re.IGNORECASE)
STRUCK = re.compile(r"\[REDAÇÃO ANTERIOR/RISCADA\](.*?)\[FIM DA REDAÇÃO ANTERIOR/RISCADA\]", re.S)
LAW = r"(?:Lei(?: Complementar)?|Decreto-Lei|Decreto|Medida Provisória|Emenda Constitucional)\s*(?:n[º°o.]*\s*)?([\d.]+(?:-\d+)?)(?:\s*,\s*de\s*([\d.]+\s*)?(?:de\s*\w+\s*de\s*)?(\d{4}))?"
MARKERS = (
    ("revoked", re.compile(r"\((?:Revogad[oa]s?|Revogado\(a\)) pel[oa] " + LAW, re.I)),
    ("revoked", re.compile(r"\((?:Revogad[oa]s?)\)", re.I)),
    ("vetoed", re.compile(r"\((?:VETADO|Vetado)\)")),
    ("amended", re.compile(r"\(Redação dada pel[oa] " + LAW, re.I)),
    ("included", re.compile(r"\(Inclu[íi]d[oa]s? pel[oa] " + LAW, re.I)),
    ("renumbered", re.compile(r"\(Renumerad[oa] pel[oa] " + LAW, re.I)),
    ("constitutional_challenge", re.compile(r"\(Vide (ADI|ADC|ADPF|ADO)\s*(?:n[º°o.]*\s*)?([\d.]+)", re.I)),
    ("effective_note", re.compile(r"\(Vig[êe]ncia\)", re.I)),
)
# Dates catalogued for common labor-law transitions; still confirmed per case.
KNOWN_EFFECTIVE_DATES = {"13467/2017": "2017-11-11", "14905/2024": "2024-08-30", "13874/2019": "2019-09-20",
                         "14442/2022": "2022-09-05", "14611/2023": "2023-07-04", "13103/2015": "2015-04-17",
                         # EC 141/2026: published 16/10/2026; weekly limits phase in (art. 6º) and rest days after 2 months.
                         "141/2026": "2026-10-16"}
PRECEDENT_STATUS = re.compile(r"cancelad|revogad|suspens|sobrestad|tese (?:firmada|fixada)|transitad|trânsito em julgado|"
                              r"m[ée]rito (?:julgado|pendente)|pendente|em julgamento|vigente|alterad|nova reda[çc][ãa]o|"
                              r"superad|modula|publicad|DEJT|DJe|Res\.|Resolu[çc][ãa]o|aprovad|editad|convertid|julgad", re.I)

CITATION_PATTERNS = (
    ("article", re.compile(r"(?<![\w])art(?:igo)?s?\.?[ ]?(\d{1,4})" + ORD.replace("[ \\t]?", "[ ]?") + r"(?:-([A-Z]{1,2}))?", re.I)),
    ("sumula", re.compile(r"(?<![\w])S[úu]mula(?:s)?(?: Vinculante)?(?: n[º°o.]*)?[ ]?(\d{1,4})", re.I)),
    ("sumula", re.compile(r"(?<![\w])SUM-(\d{1,4})")),
    ("oj", re.compile(r"(?<![\w])(?:OJ|Orienta[çc][ãa]o Jurisprudencial)(?:[ -](?:SDI|SBDI|SDC)-?\d?[ -]?)?(?: n[º°o.]*)?[ ]?(\d{1,4})", re.I)),
    ("pn", re.compile(r"(?<![\w])(?:PN|Precedente Normativo)(?: n[º°o.]*)?[ ]?(\d{1,4})", re.I)),
    ("tema", re.compile(r"(?<![\w])Tema(?:s)?(?: n[º°o.]*)?[ ]?(\d{1,5})", re.I)),
    ("control", re.compile(r"(?<![\w])(ADI|ADC|ADPF|ADO)(?: n[º°o.]*)?[ ]?([\d.]{1,7})")),
    ("nr", re.compile(r"(?<![\w])NR[- ]?(\d{1,2})(?!\d)")),
    ("instruction", re.compile(r"(?<![\w])(?:IN|Instru[çc][ãa]o Normativa)(?: n[º°o.]*)?[ ]?(\d{1,3})(?:/\d{4})?(?=[^\n]{0,20}TST)", re.I)),
    ("law", re.compile(r"(?<![\w])(?:Lei|Lei Complementar|LC|Decreto-Lei|Decreto)(?: n[º°o.]*)?[ ]?(\d{1,3}\.\d{3}|\d{1,6})(?!\d)(?:/(\d{2,4})|,? de (?:[\d.]+ de \w+ de )?(\d{4}))?", re.I)),
)


# Articles of a contract or internal rule are facts of the case, not legal authority.
PRIVATE_DOCUMENT = re.compile(r"^[^.;]{0,25}\b(?:do|deste|desse|daquele) (?:contrato|regulamento|estatuto|edital|regimento)", re.I)


def normalize(text: str) -> str:
    return WS.sub(" ", str(text).replace("\xa0", " ")).strip()


def contains(text: str, quote: str) -> bool:
    """Whitespace-insensitive inclusion; official HTML breaks lines inside sentences."""
    needle = normalize(quote)
    return bool(needle) and needle in normalize(text)


def quote_words(quote: str) -> int:
    return len(re.findall(r"\w+", str(quote)))


def parse_citations(text: str) -> list[dict]:
    """Structured legal citations written in prose or in a provision field."""
    found, seen = [], set()
    clean = normalize(text)
    for kind, pattern in CITATION_PATTERNS:
        for match in pattern.finditer(clean):
            if kind == "control":
                number = match.group(1).upper() + " " + match.group(2).replace(".", "")
            elif kind == "law":
                number = match.group(1).replace(".", "")
                year = match.group(2) or match.group(3)
                if year:
                    year = year if len(year) == 4 else ("19" + year if int(year) > 40 else "20" + year)
                    number += "/" + year
            else:
                number = match.group(1) + ("-" + match.group(2).upper() if match.lastindex and match.lastindex >= 2 and match.group(2) else "")
            item = {"kind": kind, "number": number, "label": match.group(0), "start": match.start()}
            if kind == "article":
                tail = clean[match.end():match.end() + 60]
                paragraph = re.match(r"\s*,?\s*(?:§[ ]?(\d{1,3})" + ORD.replace("[ \\t]?", "[ ]?") + r"|(par[áa]grafo [úu]nico)|(caput))", tail, re.I)
                if paragraph:
                    item["paragraph"] = "único" if paragraph.group(2) else "caput" if paragraph.group(3) else paragraph.group(1)
                inciso = re.match(r"\s*,?\s*(?:§[^,]*,\s*)?(?:inciso\s*)?([IVXLC]{1,7})(?![\w])", tail)
                if inciso:
                    item["inciso"] = inciso.group(1)
            key = (kind, number.split("/")[0] if kind == "law" else number)
            if (key, item.get("paragraph")) in seen:
                continue
            seen.add((key, item.get("paragraph")))
            item["key"] = list(key)
            found.append(item)
    return sorted(found, key=lambda row: row["start"])


def citation_keys(text: str) -> set[tuple[str, str]]:
    return {tuple(item["key"]) for item in parse_citations(text)}


def struck_spans(text: str) -> list[tuple[int, int]]:
    return [(m.start(1), m.end(1)) for m in STRUCK.finditer(text) if m.group(1).strip()]


def version_markers(segment: str) -> list[dict]:
    clean = normalize(segment)
    markers = []
    for marker, pattern in MARKERS:
        for match in pattern.finditer(clean):
            row = {"type": marker, "text": match.group(0)}
            if marker == "constitutional_challenge":
                row["action"] = match.group(1).upper() + " " + match.group(2).replace(".", "")
            elif match.lastindex:
                row["act_number"] = (match.group(1) or "").replace(".", "")
                row["year"] = match.group(match.lastindex) if match.lastindex >= 3 else None
                key = row["act_number"] + "/" + (row["year"] or "")
                if key in KNOWN_EFFECTIVE_DATES:
                    row["catalogued_effective_date"] = KNOWN_EFFECTIVE_DATES[key]
            if row not in markers:
                markers.append(row)
    return markers


def segment_articles(text: str) -> list[dict]:
    """Split legislation into article segments; struck headings are kept but flagged."""
    heads = list(ARTICLE_HEAD.finditer(text)) or list(ARTICLE_INLINE.finditer(text))
    spans = struck_spans(text)
    segments = []
    for index, match in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        number = match.group(1) + ("-" + match.group(2) if match.group(2) else "")
        segments.append({"number": number, "start": match.start(), "end": end,
                         "struck": any(a <= match.start(1) < b for a, b in spans)})
    return segments


def units(segment: str) -> list[tuple[str, str]]:
    """Caput and paragraphs of one article; headings at line start, inline only for one-line text."""
    marks = list(PARAGRAPH_HEAD.finditer(segment)) if "\n" in segment.strip() else list(PARAGRAPH.finditer(segment))
    rows = [("caput", segment[:marks[0].start()] if marks else segment)]
    for index, match in enumerate(marks):
        label = "único" if match.group(1) is None else match.group(1) + ("-" + match.group(2) if match.group(2) else "")
        end = marks[index + 1].start() if index + 1 < len(marks) else len(segment)
        rows.append((label, segment[match.start():end]))
    return [(label, normalize(body)) for label, body in rows]


def sub_segment(segment: str, paragraph: str | None, quote: str = "") -> str | None:
    """Return the cited unit; without a paragraph, the unit holding the quote or the caput."""
    rows = units(segment)
    if paragraph:
        return next((body for label, body in rows if label == paragraph), None)
    if quote:
        holder = next((body for _, body in rows if contains(_unstruck(body), quote)), None)
        if holder is not None:
            return holder
    return rows[0][1]


BOUNDARY = re.compile(r"\s(?:[IVXLC]{1,7}\s?[-–—]\s|[a-z]\)\s|§\s?\d|Parágrafo único|Art\.\s?\d)")


def narrow(unit: str, quote: str = "", inciso: str | None = None) -> str:
    """Text of the cited inciso or of the passage holding the quote, up to the next item.

    Markers such as "(Revogado)" follow the item they qualify; a revoked inciso must
    not mark the whole article as revoked.
    """
    start = None
    if quote:
        start = normalize(unit).find(normalize(quote))
        unit = normalize(unit)
    elif inciso:
        match = re.search(r"(?:^|\s)" + inciso + r"\s?[-–—]\s", unit)
        start = match.start() if match else None
    if start is None or start < 0:
        return unit
    following = BOUNDARY.search(unit, start + max(len(normalize(quote)) if quote else 2, 2))
    return unit[start:following.start() if following else len(unit)]


def _status(findings: list[dict]) -> str:
    if any(f["severity"] == "blocking" for f in findings):
        return "blocking"
    return "qualified" if any(f["severity"] == "qualifying" for f in findings) else "located_no_marker"


def _finding(code: str, severity: str, message: str, **extra) -> dict:
    return {"code": code, "severity": severity, "message": message, **extra}


def _temporal(markers: list[dict], fact_dates: list[str]) -> list[dict]:
    findings = []
    dates = sorted(d for d in fact_dates if isinstance(d, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d))
    for marker in markers:
        if marker["type"] in {"revoked"}:
            findings.append(_finding("provision_revoked", "qualifying",
                "Dispositivo com marca de revogação; usar somente para fatos anteriores à revogação, com análise intertemporal.", marker=marker["text"]))
        elif marker["type"] == "vetoed":
            findings.append(_finding("provision_vetoed", "qualifying", "Dispositivo vetado; confirmar se houve derrubada do veto.", marker=marker["text"]))
        elif marker["type"] == "constitutional_challenge":
            findings.append(_finding("constitutional_challenge_noted", "qualifying",
                "Texto oficial remete a controle de constitucionalidade; conferir a situação de " + marker["action"] + ".", marker=marker["text"]))
        elif marker["type"] in {"amended", "included"} and dates:
            effective = marker.get("catalogued_effective_date")
            earliest = dates[0]
            if effective and earliest < effective:
                code = "wording_changed_after_facts" if marker["type"] == "amended" else "provision_added_after_facts"
                findings.append(_finding(code, "qualifying",
                    "Fatos anteriores à vigência catalogada (" + effective + ") desta redação; aplicar a versão da época ou justificar a incidência.",
                    marker=marker["text"]))
            elif not effective and marker.get("year") and earliest[:4] <= marker["year"]:
                findings.append(_finding("wording_date_to_confirm", "qualifying",
                    "Redação alterada no mesmo ano ou depois dos fatos; conferir a data exata de vigência.", marker=marker["text"]))
    return findings


def _precedent(text: str, citation: dict, quote: str) -> dict:
    clean = normalize(text)
    number = citation["number"].split("-")[0]
    kind = citation["kind"]
    if kind == "control":
        action, digits = (citation["number"].split() + [""])[:2]
        label = re.escape(action) + r"(?: n[º°o.]*)?[ ]?" + r"\.?".join(digits) + r"(?!\d)"
    else:
        label = {
            "sumula": r"(?:S[úu]mula(?: Vinculante)?(?: n[º°o.]*)?[ ]?|SUM-)0*",
            "oj": r"(?:OJ|Orienta[çc][ãa]o Jurisprudencial)[^\d]{0,30}0*",
            "pn": r"(?:PN|Precedente Normativo)(?: n[º°o.]*)?[ ]?0*",
            "tema": r"Tema(?: n[º°o.]*)?[ ]?0*",
            "instruction": r"(?:IN|Instru[çc][ãa]o Normativa)(?: n[º°o.]*)?[ ]?0*",
            "nr": r"NR[- ]?0*",
        }[kind] + number + r"(?!\d)"
    pattern = re.compile(label, re.I)
    matches = list(pattern.finditer(clean))
    findings = []
    if not matches:
        findings.append(_finding("precedent_not_found", "blocking",
            "Identificador citado não aparece na fonte consultada; consultar a página própria do precedente."))
        return {"located": False, "findings": findings, "status_terms": []}
    windows = [clean[max(0, m.start() - 200):m.end() + 900] for m in matches]
    terms = sorted({t.group(0).lower() for w in windows for t in PRECEDENT_STATUS.finditer(w)})
    if quote and not any(contains(w, quote) for w in windows) and contains(clean, quote):
        findings.append(_finding("quote_far_from_identifier", "qualifying",
            "Trecho está na página, mas distante do identificador citado; confirmar que pertence ao precedente."))
    if any(t.startswith("cancelad") or t.startswith("revogad") for t in terms):
        findings.append(_finding("precedent_cancelled_or_revoked", "qualifying",
            "A fonte registra cancelamento/revogação próximo ao identificador; usar só com análise temporal."))
    if any(t.startswith("suspens") or t.startswith("sobrestad") for t in terms):
        findings.append(_finding("precedent_suspended", "qualifying", "A fonte registra suspensão/sobrestamento próximo ao identificador."))
    if citation["kind"] == "tema" and not terms:
        findings.append(_finding("tema_status_not_observed", "qualifying", "Situação do Tema não aparece no trecho consultado; consultar a página de andamento."))
    return {"located": True, "findings": findings, "status_terms": terms}


def check_citation(text: str, provision: str, quote: str = "", *, fact_dates: list[str] | None = None) -> dict:
    """Return located segment, markers and typed findings for one citation."""
    citations = [c for c in parse_citations(provision) if c["kind"] != "law"] or parse_citations(provision)
    result = {"provision": provision, "citation": citations[0] if citations else None, "located": False,
              "markers": [], "findings": [], "scope": "structural; legal applicability remains authored"}
    if quote and quote_words(quote) < 3:
        result["findings"].append(_finding("quote_too_short", "blocking", "Trecho com menos de três palavras não sustenta a citação."))
    if quote and not contains(text, quote):
        result["findings"].append(_finding("quote_not_in_source", "blocking", "Trecho ausente da fonte consultada."))
    citation = result["citation"]
    if citation is None:
        result["findings"].append(_finding("provision_unstructured", "info",
            "Dispositivo sem artigo, súmula, OJ, Tema ou ação identificável; conferência estrutural não executada."))
        result["status"] = _status(result["findings"])
        return result
    if citation["kind"] in {"sumula", "oj", "pn", "tema", "control", "instruction", "nr"}:
        precedent = _precedent(text, citation, quote)
        result.update(located=precedent["located"], status_terms=precedent["status_terms"])
        result["findings"] += precedent["findings"]
        result["status"] = _status(result["findings"])
        return result
    if citation["kind"] == "law":
        result["findings"].append(_finding("provision_without_article", "info",
            "Citação de lei sem artigo; conferir o dispositivo específico usado no fundamento."))
        result["status"] = _status(result["findings"])
        return result
    segments = segment_articles(text)
    if not segments:
        result["findings"].append(_finding("provision_not_isolated", "qualifying",
            "A fonte não traz cabeçalhos de artigo; não foi possível confirmar que o trecho pertence ao dispositivo citado."))
        result["status"] = _status(result["findings"])
        return result
    candidates = [s for s in segments if s["number"] == citation["number"]]
    if not candidates:
        result["findings"].append(_finding("provision_not_found", "blocking",
            "Artigo " + citation["number"] + " não localizado na fonte consultada; conferir URL, lei e numeração."))
        result["status"] = _status(result["findings"])
        return result
    pieces = []
    for candidate in candidates:
        body = text[candidate["start"]:candidate["end"]]
        piece = sub_segment(body, citation.get("paragraph"), quote)
        if piece is not None:
            pieces.append((candidate, piece))
    if not pieces:
        result["findings"].append(_finding("paragraph_not_found", "blocking",
            "Parágrafo " + str(citation.get("paragraph")) + " não localizado no artigo " + citation["number"] + "."))
        result["status"] = _status(result["findings"])
        return result
    current = [(c, p) for c, p in pieces if not c["struck"]] or pieces
    result["located"] = True
    result["segment"] = current[0][1][:4000]
    if quote and contains(text, quote):
        inside = [(c, p) for c, p in pieces if not c["struck"] and contains(_unstruck(p), quote)]
        if not contains(_unstruck(text), quote) or (not inside and any(contains(p, quote) for _, p in pieces)):
            result["findings"].append(_finding("quote_in_struck_text", "blocking",
                "Trecho pertence a redação riscada/anterior; citar a redação vigente ou tratar como versão histórica."))
        elif not inside:
            result["findings"].append(_finding("quote_outside_provision", "blocking",
                "Trecho existe na fonte, mas fora do dispositivo citado."))
        else:
            current = inside
            result["segment"] = inside[0][1][:4000]
    unit = _unstruck(current[0][1])
    narrowed = narrow(unit, quote if quote and contains(unit, quote) else "", citation.get("inciso"))
    heading = unit[:BOUNDARY.search(unit).start()] if BOUNDARY.search(unit) else unit
    result["markers"] = version_markers(narrowed) + [m for m in version_markers(heading)
                                                    if m["type"] in {"revoked", "vetoed"} and normalize(heading).strip(" -–—()").startswith(("Art", "§"))
                                                    and len(normalize(heading)) < 120]
    distinct = {tuple(sorted(m.items())) for m in result["markers"]}
    result["markers"] = [dict(m) for m in sorted(distinct)]
    if not quote and len([c for c, _ in pieces if not c["struck"]]) > 1:
        result["findings"].append(_finding("provision_ambiguous", "info",
            "O número do dispositivo aparece mais de uma vez na fonte (preâmbulo, ADCT ou lei transcrita); informar trecho para identificar o dispositivo."))
    result["findings"] += _temporal(result["markers"], fact_dates or [])
    result["status"] = _status(result["findings"])
    return result


def _unstruck(text: str) -> str:
    return STRUCK.sub(" ", text)


def check_record(record: dict, provision: str, quote: str = "", *, fact_dates: list[str] | None = None) -> dict:
    result = check_citation(str(record.get("text", "")), provision, quote, fact_dates=fact_dates)
    result["source_method"] = record.get("method")
    result["source_url"] = record.get("url")
    return result


def prose_citation_gaps(paragraph_text: str, norms: list[dict]) -> list[dict]:
    """Citations written in a paragraph that no linked norm covers."""
    covered = set()
    blob = []
    for norm in norms:
        covered |= citation_keys(" ".join(str(norm.get(k, "")) for k in ("title", "provision", "quote")))
        blob.append(str(norm.get("official_text", "")) + " " + str(norm.get("title", "")))
    joined = normalize(" ".join(blob))
    missing = []
    clean = normalize(paragraph_text)
    for item in parse_citations(paragraph_text):
        key = tuple(item["key"])
        if key in covered:
            continue
        following = clean[item["start"] + len(item["label"]):item["start"] + len(item["label"]) + 45]
        if item["kind"] == "article" and PRIVATE_DOCUMENT.search(following):
            continue
        if item["kind"] == "law" and norms and (item["number"].split("/")[0] in joined.replace(".", "")):
            continue
        missing.append(item)
    return missing


LIVE_CASES = (
    ("https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm", "Art. 384", "", "provision_revoked"),
    ("https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm", "art. 71, § 4º",
     "implica o pagamento, de natureza indenizatória, apenas do período suprimido", "wording_changed_after_facts"),
    ("https://www.tst.jus.br/sumulas", "Súmula 338", "", "blocked_by_portal"),
)


def live_smoke(output: Path) -> list[dict]:
    """Manual check against real portals; never part of offline CI."""
    try:
        from .research_sources import capture, SourceBlocked
    except ImportError:
        from research_sources import capture, SourceBlocked
    rows = []
    for url, provision, quote, expected in LIVE_CASES:
        try:
            record = capture(url, output)
            result = check_record(record, provision, quote, fact_dates=["2016-03-01"])
            codes = [f["code"] for f in result["findings"]]
        except SourceBlocked as error:
            codes, result = ["blocked_by_portal"], {"error": str(error)}
        except (OSError, ValueError) as error:
            codes, result = ["unavailable"], {"error": str(error)}
        rows.append({"url": url, "provision": provision, "expected": expected, "codes": codes, "passed": expected in codes})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Confere dispositivo, trecho e marcas de versão em fonte oficial capturada")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--record", type=Path, required=True, help="research_sources/<id>.json")
    check.add_argument("--provision", required=True)
    check.add_argument("--quote", default="")
    check.add_argument("--fact-date", action="append", default=[])
    parse = sub.add_parser("parse")
    parse.add_argument("--text", required=True)
    live = sub.add_parser("live")
    live.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "check":
        record = json.loads(args.record.read_text(encoding="utf-8"))
        result = check_record(record, args.provision, args.quote, fact_dates=args.fact_date)
    elif args.command == "parse":
        result = parse_citations(args.text)
    else:
        result = live_smoke(args.output.resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if all(r["passed"] for r in result) else 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if isinstance(result, dict) and result.get("status") == "blocking" else 0


if __name__ == "__main__":
    raise SystemExit(main())
