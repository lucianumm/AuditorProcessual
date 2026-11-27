"""Exportador forense determinístico de Markdown para OOXML (.docx) usando apenas biblioteca padrão.

Gera contêiner Office Open XML íntegro (sem macros, sem DTD/XXE, compatível com Word, LibreOffice e
`document_formats.extract_office`), formatado segundo o padrão forense brasileiro (A4, margens 3cm/3cm/2cm/2cm,
Times New Roman 12pt, espaçamento 1,5, recuo de citação longa de 4cm em 10pt simples, tabelas com bordas,
numeração de páginas no rodapé e aviso obrigatório de rascunho assistido por IA conforme Res. CNJ 332/2020 e 615/2025).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

SAFETY_NOTICE = (
    "RASCUNHO GERADO COM APOIO DE IA — NÃO PROTOCOLAR SEM REVISÃO ADVOCATÍCIA "
    "(RES. CNJ 332/2020 E 615/2025)"
)

PAGE_BREAK = "<!-- quebra-de-pagina -->"

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

ET.register_namespace("w", NS_W)
ET.register_namespace("r", NS_R)
ET.register_namespace("cp", NS_CP)
ET.register_namespace("dc", NS_DC)
ET.register_namespace("dcterms", NS_DCTERMS)
ET.register_namespace("xsi", NS_XSI)

# Medidas forenses brasileiras em twips (1 cm ≈ 566,93 twips; 1 pt = 20 twips)
A4_WIDTH_TWIPS = "11906"   # 21,0 cm
A4_HEIGHT_TWIPS = "16838"  # 29,7 cm
MARGIN_TOP_TWIPS = "1701"     # 3,0 cm
MARGIN_LEFT_TWIPS = "1701"    # 3,0 cm
MARGIN_BOTTOM_TWIPS = "1134"  # 2,0 cm
MARGIN_RIGHT_TWIPS = "1134"   # 2,0 cm
HEADER_DIST_TWIPS = "709"     # 1,25 cm
FOOTER_DIST_TWIPS = "709"     # 1,25 cm
FIRST_LINE_TWIPS = "709"      # 1,25 cm recuo de parágrafo
QUOTE_INDENT_TWIPS = "2268"   # 4,0 cm recuo de citação direta longa (ABNT/forense)

_XML_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_NUMBERED_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
_HR_RE = re.compile(r"^\s*(?:---+|\*\*\*+|___+)\s*$")
_TABLE_SEP_CELL_RE = re.compile(r"^:?-{2,}:?$")
_INLINE_TOKEN_RE = re.compile(
    r"(`[^`\n]+`"
    r"|\*\*\*[^*\n]+\*\*\*"
    r"|___[^_\n]+___"
    r"|\*\*[^*\n]+\*\*"
    r"|__[^_\n]+__"
    r"|\*[^*\n]+\*"
    r"|(?<!\w)_[^_\n]+_(?!\w)"
    r"|\[[^\]]+\]\([^)]+\))"
)


def _clean_xml_text(value: str) -> str:
    return _XML_CTRL_RE.sub("", html.unescape(value) if "&nbsp;" in value else value)


def _w(tag: str) -> str:
    return f"{{{NS_W}}}{tag}"


def _xml_bytes(element: ET.Element) -> bytes:
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def _set_run_props(
    r: ET.Element,
    *,
    bold: bool = False,
    italic: bool = False,
    code: bool = False,
    size_half_pts: str | None = None,
    color: str | None = None,
) -> None:
    if not (bold or italic or code or size_half_pts or color):
        return
    rpr = ET.SubElement(r, _w("rPr"))
    if code:
        ET.SubElement(
            rpr,
            _w("rFonts"),
            {_w("ascii"): "Courier New", _w("hAnsi"): "Courier New", _w("cs"): "Courier New"},
        )
        ET.SubElement(rpr, _w("shd"), {_w("val"): "clear", _w("color"): "auto", _w("fill"): "F4F4F4"})
    if bold:
        ET.SubElement(rpr, _w("b"))
        ET.SubElement(rpr, _w("bCs"))
    if italic:
        ET.SubElement(rpr, _w("i"))
        ET.SubElement(rpr, _w("iCs"))
    if color:
        ET.SubElement(rpr, _w("color"), {_w("val"): color})
    effective_sz = size_half_pts or ("20" if code else None)
    if effective_sz:
        ET.SubElement(rpr, _w("sz"), {_w("val"): effective_sz})
        ET.SubElement(rpr, _w("szCs"), {_w("val"): effective_sz})


def _append_text_run(
    p: ET.Element,
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    code: bool = False,
    size_half_pts: str | None = None,
    color: str | None = None,
) -> None:
    clean = _clean_xml_text(text)
    if not clean:
        return
    r = ET.SubElement(p, _w("r"))
    _set_run_props(r, bold=bold, italic=italic, code=code, size_half_pts=size_half_pts, color=color)
    t = ET.SubElement(r, _w("t"))
    if clean[0].isspace() or clean[-1].isspace() or "  " in clean:
        t.set(XML_SPACE, "preserve")
    t.text = clean


def _append_inline_runs(
    p: ET.Element,
    text: str,
    *,
    base_bold: bool = False,
    base_italic: bool = False,
    size_half_pts: str | None = None,
    color: str | None = None,
) -> None:
    pos = 0
    for match in _INLINE_TOKEN_RE.finditer(text):
        if match.start() > pos:
            _append_text_run(
                p,
                text[pos : match.start()],
                bold=base_bold,
                italic=base_italic,
                size_half_pts=size_half_pts,
                color=color,
            )
        token = match.group(0)
        if token.startswith("`") and token.endswith("`"):
            _append_text_run(p, token[1:-1], bold=base_bold, italic=base_italic, code=True, size_half_pts=size_half_pts, color=color)
        elif (token.startswith("***") and token.endswith("***")) or (token.startswith("___") and token.endswith("___")):
            _append_text_run(p, token[3:-3], bold=True, italic=True, size_half_pts=size_half_pts, color=color)
        elif (token.startswith("**") and token.endswith("**")) or (token.startswith("__") and token.endswith("__")):
            _append_text_run(p, token[2:-2], bold=True, italic=base_italic, size_half_pts=size_half_pts, color=color)
        elif (token.startswith("*") and token.endswith("*")) or (token.startswith("_") and token.endswith("_")):
            _append_text_run(p, token[1:-1], bold=base_bold, italic=True, size_half_pts=size_half_pts, color=color)
        elif token.startswith("[") and "](" in token and token.endswith(")"):
            bracket_end = token.index("](")
            label = token[1:bracket_end]
            url = token[bracket_end + 2 : -1].strip()
            rendered = f"{label} ({url})" if url.startswith(("http://", "https://")) and url not in label else label
            _append_text_run(p, rendered, bold=base_bold, italic=base_italic, size_half_pts=size_half_pts, color=color)
        pos = match.end()
    if pos < len(text):
        _append_text_run(p, text[pos:], bold=base_bold, italic=base_italic, size_half_pts=size_half_pts, color=color)


def _split_pipe_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped)]


def _is_table_separator(line: str) -> bool:
    if "|" not in line:
        return False
    cells = _split_pipe_row(line)
    return bool(cells) and all(_TABLE_SEP_CELL_RE.match(c) for c in cells if c != "") and any(cells)


def _looks_like_table_start(lines: list[str], idx: int) -> bool:
    if idx + 1 >= len(lines):
        return False
    first = lines[idx].strip()
    if "|" not in first or first.startswith(">"):
        return False
    return _is_table_separator(lines[idx + 1])


def _build_table_element(rows: list[list[str]], has_header: bool) -> ET.Element:
    tbl = ET.Element(_w("tbl"))
    tbl_pr = ET.SubElement(tbl, _w("tblPr"))
    ET.SubElement(tbl_pr, _w("tblW"), {_w("w"): "5000", _w("type"): "pct"})
    borders = ET.SubElement(tbl_pr, _w("tblBorders"))
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        ET.SubElement(borders, _w(edge), {_w("val"): "single", _w("sz"): "4", _w("space"): "0", _w("color"): "666666"})

    col_count = max((len(r) for r in rows), default=1)
    grid = ET.SubElement(tbl, _w("tblGrid"))
    col_width = str(max(900, 9070 // max(1, col_count)))
    for _ in range(col_count):
        ET.SubElement(grid, _w("gridCol"), {_w("w"): col_width})

    for row_idx, row_cells in enumerate(rows):
        tr = ET.SubElement(tbl, _w("tr"))
        is_header = has_header and row_idx == 0
        if is_header:
            tr_pr = ET.SubElement(tr, _w("trPr"))
            ET.SubElement(tr_pr, _w("tblHeader"))
        padded = row_cells + [""] * (col_count - len(row_cells))
        for cell_text in padded:
            tc = ET.SubElement(tr, _w("tc"))
            tc_pr = ET.SubElement(tc, _w("tcPr"))
            ET.SubElement(tc_pr, _w("tcW"), {_w("w"): col_width, _w("type"): "dxa"})
            if is_header:
                ET.SubElement(tc_pr, _w("shd"), {_w("val"): "clear", _w("color"): "auto", _w("fill"): "EAEAEA"})
            margins = ET.SubElement(tc_pr, _w("tcMar"))
            for side, val in (("top", "80"), ("bottom", "80"), ("left", "120"), ("right", "120")):
                ET.SubElement(margins, _w(side), {_w("w"): val, _w("type"): "dxa"})
            p = ET.SubElement(tc, _w("p"))
            ppr = ET.SubElement(p, _w("pPr"))
            ET.SubElement(ppr, _w("spacing"), {_w("before"): "40", _w("after"): "40", _w("line"): "240", _w("lineRule"): "auto"})
            ET.SubElement(ppr, _w("jc"), {_w("val"): "left"})
            if cell_text:
                _append_inline_runs(p, cell_text, base_bold=is_header, size_half_pts="21")
            else:
                ET.SubElement(p, _w("r"))
    return tbl


def _build_content_types() -> bytes:
    types = ET.Element(f"{{{NS_CT}}}Types")
    ET.SubElement(types, f"{{{NS_CT}}}Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    ET.SubElement(types, f"{{{NS_CT}}}Default", {"Extension": "xml", "ContentType": "application/xml"})
    overrides = (
        ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
        ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
        ("/word/header1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"),
        ("/word/footer1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"),
        ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
    )
    for part, ctype in overrides:
        ET.SubElement(types, f"{{{NS_CT}}}Override", {"PartName": part, "ContentType": ctype})
    return _xml_bytes(types)


def _build_root_rels() -> bytes:
    rels = ET.Element(f"{{{NS_PKG_REL}}}Relationships")
    ET.SubElement(rels, f"{{{NS_PKG_REL}}}Relationship", {
        "Id": "rId1",
        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        "Target": "word/document.xml",
    })
    ET.SubElement(rels, f"{{{NS_PKG_REL}}}Relationship", {
        "Id": "rId2",
        "Type": "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
        "Target": "docProps/core.xml",
    })
    return _xml_bytes(rels)


def _build_document_rels() -> bytes:
    rels = ET.Element(f"{{{NS_PKG_REL}}}Relationships")
    ET.SubElement(rels, f"{{{NS_PKG_REL}}}Relationship", {
        "Id": "rId1",
        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
        "Target": "styles.xml",
    })
    ET.SubElement(rels, f"{{{NS_PKG_REL}}}Relationship", {
        "Id": "rId2",
        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header",
        "Target": "header1.xml",
    })
    ET.SubElement(rels, f"{{{NS_PKG_REL}}}Relationship", {
        "Id": "rId3",
        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer",
        "Target": "footer1.xml",
    })
    return _xml_bytes(rels)


def _build_styles() -> bytes:
    styles = ET.Element(_w("styles"))
    defaults = ET.SubElement(styles, _w("docDefaults"))
    rpr_def = ET.SubElement(ET.SubElement(defaults, _w("rPrDefault")), _w("rPr"))
    ET.SubElement(rpr_def, _w("rFonts"), {
        _w("ascii"): "Times New Roman",
        _w("hAnsi"): "Times New Roman",
        _w("cs"): "Times New Roman",
    })
    ET.SubElement(rpr_def, _w("sz"), {_w("val"): "24"})
    ET.SubElement(rpr_def, _w("szCs"), {_w("val"): "24"})
    ET.SubElement(rpr_def, _w("lang"), {_w("val"): "pt-BR"})
    ppr_def = ET.SubElement(ET.SubElement(defaults, _w("pPrDefault")), _w("pPr"))
    ET.SubElement(ppr_def, _w("spacing"), {_w("after"): "120", _w("line"): "360", _w("lineRule"): "auto"})
    ET.SubElement(ppr_def, _w("jc"), {_w("val"): "both"})

    def add_style(style_id: str, name: str, *, sz: str = "24", bold: bool = False, italic: bool = False,
                  before: str = "0", after: str = "120", line: str = "360", jc: str = "both",
                  left: str | None = None, first_line: str | None = None, hanging: str | None = None,
                  keep_next: bool = False) -> None:
        st = ET.SubElement(styles, _w("style"), {_w("type"): "paragraph", _w("styleId"): style_id})
        if style_id == "Normal":
            st.set(_w("default"), "1")
        ET.SubElement(st, _w("name"), {_w("val"): name})
        ppr = ET.SubElement(st, _w("pPr"))
        if keep_next:
            ET.SubElement(ppr, _w("keepNext"))
        ET.SubElement(ppr, _w("spacing"), {_w("before"): before, _w("after"): after, _w("line"): line, _w("lineRule"): "auto"})
        if left or first_line or hanging:
            ind_attrs = {}
            if left:
                ind_attrs[_w("left")] = left
            if first_line:
                ind_attrs[_w("firstLine")] = first_line
            if hanging:
                ind_attrs[_w("hanging")] = hanging
            ET.SubElement(ppr, _w("ind"), ind_attrs)
        ET.SubElement(ppr, _w("jc"), {_w("val"): jc})
        rpr = ET.SubElement(st, _w("rPr"))
        if bold:
            ET.SubElement(rpr, _w("b"))
            ET.SubElement(rpr, _w("bCs"))
        if italic:
            ET.SubElement(rpr, _w("i"))
            ET.SubElement(rpr, _w("iCs"))
        ET.SubElement(rpr, _w("sz"), {_w("val"): sz})
        ET.SubElement(rpr, _w("szCs"), {_w("val"): sz})

    add_style("Normal", "Normal", sz="24", first_line=FIRST_LINE_TWIPS)
    add_style("Heading1", "heading 1", sz="28", bold=True, before="240", after="120", line="280", jc="left", keep_next=True)
    add_style("Heading2", "heading 2", sz="24", bold=True, before="200", after="100", line="280", jc="left", keep_next=True)
    add_style("Heading3", "heading 3", sz="24", bold=True, italic=True, before="160", after="80", line="280", jc="left", keep_next=True)
    add_style("ForensicQuote", "Forensic Quote", sz="20", before="120", after="120", line="240", jc="both", left=QUOTE_INDENT_TWIPS)
    add_style("ListBullet", "List Bullet", sz="24", before="40", after="80", line="300", jc="both", left="720", hanging="360")
    add_style("ListNumber", "List Number", sz="24", before="40", after="80", line="300", jc="both", left="720", hanging="360")
    add_style("Header", "header", sz="18", before="0", after="40", line="240", jc="center")
    add_style("Footer", "footer", sz="18", before="0", after="0", line="240", jc="right")
    return _xml_bytes(styles)


def _build_header(title: str, draft_banner: bool) -> bytes:
    hdr = ET.Element(_w("hdr"))
    p = ET.SubElement(hdr, _w("p"))
    ppr = ET.SubElement(p, _w("pPr"))
    ET.SubElement(ppr, _w("pStyle"), {_w("val"): "Header"})
    ET.SubElement(ppr, _w("jc"), {_w("val"): "center"})
    p_bdr = ET.SubElement(ppr, _w("pBdr"))
    ET.SubElement(p_bdr, _w("bottom"), {_w("val"): "single", _w("sz"): "6", _w("space"): "4", _w("color"): "990000" if draft_banner else "888888"})
    text = SAFETY_NOTICE if draft_banner else _clean_xml_text(title)
    _append_text_run(p, text, bold=draft_banner, size_half_pts="17", color="8B0000" if draft_banner else "555555")
    return _xml_bytes(hdr)


def _append_field_code(p: ET.Element, field_name: str, placeholder: str = "1") -> None:
    r_begin = ET.SubElement(p, _w("r"))
    _set_run_props(r_begin, size_half_pts="18", color="444444")
    ET.SubElement(r_begin, _w("fldChar"), {_w("fldCharType"): "begin"})

    r_instr = ET.SubElement(p, _w("r"))
    _set_run_props(r_instr, size_half_pts="18", color="444444")
    instr = ET.SubElement(r_instr, _w("instrText"))
    instr.set(XML_SPACE, "preserve")
    instr.text = f" {field_name} "

    r_sep = ET.SubElement(p, _w("r"))
    _set_run_props(r_sep, size_half_pts="18", color="444444")
    ET.SubElement(r_sep, _w("fldChar"), {_w("fldCharType"): "separate"})

    _append_text_run(p, placeholder, size_half_pts="18", color="444444")

    r_end = ET.SubElement(p, _w("r"))
    _set_run_props(r_end, size_half_pts="18", color="444444")
    ET.SubElement(r_end, _w("fldChar"), {_w("fldCharType"): "end"})


def _build_footer() -> bytes:
    ftr = ET.Element(_w("ftr"))
    p = ET.SubElement(ftr, _w("p"))
    ppr = ET.SubElement(p, _w("pPr"))
    ET.SubElement(ppr, _w("pStyle"), {_w("val"): "Footer"})
    ET.SubElement(ppr, _w("jc"), {_w("val"): "right"})
    _append_text_run(p, "Página ", size_half_pts="18", color="444444")
    _append_field_code(p, "PAGE", "1")
    _append_text_run(p, " de ", size_half_pts="18", color="444444")
    _append_field_code(p, "NUMPAGES", "1")
    return _xml_bytes(ftr)


def _build_core_props(title: str, metadata: dict | None) -> bytes:
    meta = metadata or {}
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = ET.Element(f"{{{NS_CP}}}coreProperties")
    dc_title = ET.SubElement(core, f"{{{NS_DC}}}title")
    dc_title.text = _clean_xml_text(str(meta.get("title") or title))
    dc_creator = ET.SubElement(core, f"{{{NS_DC}}}creator")
    dc_creator.text = _clean_xml_text(str(meta.get("creator") or "AuditorProcessual (Rascunho Assistido por IA)"))
    dc_desc = ET.SubElement(core, f"{{{NS_DC}}}description")
    dc_desc.text = _clean_xml_text(str(meta.get("description") or SAFETY_NOTICE))
    for tag in ("created", "modified"):
        el = ET.SubElement(core, f"{{{NS_DCTERMS}}}{tag}", {f"{{{NS_XSI}}}type": "dcterms:W3CDTF"})
        el.text = str(meta.get(tag) or now_iso)
    return _xml_bytes(core)


def _resolve_markdown_source(markdown_path_or_text: str | Path) -> str:
    if isinstance(markdown_path_or_text, Path):
        if not markdown_path_or_text.is_file():
            raise FileNotFoundError(f"Arquivo Markdown não encontrado: {markdown_path_or_text}")
        return markdown_path_or_text.read_text(encoding="utf-8-sig")
    if not isinstance(markdown_path_or_text, str):
        raise TypeError("markdown_path_or_text deve ser str ou Path")
    if "\n" not in markdown_path_or_text and len(markdown_path_or_text) <= 1024:
        candidate = Path(markdown_path_or_text)
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8-sig")
    return markdown_path_or_text


def export_markdown_to_docx(
    markdown_path_or_text: str | Path,
    output_docx: Path | str,
    *,
    title: str = "Minuta Jurídica",
    draft_banner: bool = True,
    metadata: dict | None = None,
    toc: bool = False,
    annex: str | Path | None = None,
) -> dict:
    """Converte Markdown forense em arquivo OOXML `.docx` válido e retorna recibo estruturado.

    `toc` insere campo de sumário (atualizado pelo editor); `annex` acrescenta, em nova página,
    um anexo técnico em Markdown (ex.: matriz de rastreabilidade da consolidação).
    """
    markdown_text = _resolve_markdown_source(markdown_path_or_text)
    if annex is not None:
        markdown_text = markdown_text.rstrip() + "\n\n" + PAGE_BREAK + "\n\n" + _resolve_markdown_source(annex)
    destination = Path(output_docx).resolve()
    if destination.suffix.lower() != ".docx":
        raise ValueError("O arquivo de destino deve ter extensão .docx")
    destination.parent.mkdir(parents=True, exist_ok=True)

    doc = ET.Element(_w("document"))
    body = ET.SubElement(doc, _w("body"))

    paragraph_count = 0
    table_count = 0
    heading_count = 0
    blockquote_count = 0

    if draft_banner:
        banner_p = ET.SubElement(body, _w("p"))
        ppr = ET.SubElement(banner_p, _w("pPr"))
        ET.SubElement(ppr, _w("spacing"), {_w("before"): "0", _w("after"): "180", _w("line"): "240", _w("lineRule"): "auto"})
        ET.SubElement(ppr, _w("jc"), {_w("val"): "center"})
        pbdr = ET.SubElement(ppr, _w("pBdr"))
        for side in ("top", "left", "bottom", "right"):
            ET.SubElement(pbdr, _w(side), {_w("val"): "single", _w("sz"): "6", _w("space"): "6", _w("color"): "990000"})
        ET.SubElement(ppr, _w("shd"), {_w("val"): "clear", _w("color"): "auto", _w("fill"): "FFF5F5"})
        _append_text_run(banner_p, SAFETY_NOTICE, bold=True, size_half_pts="18", color="8B0000")
        paragraph_count += 1

    if toc:
        toc_title = ET.SubElement(body, _w("p"))
        _append_text_run(toc_title, "Sumário", bold=True)
        toc_p = ET.SubElement(body, _w("p"))
        _append_field_code(toc_p, 'TOC \\o "1-3" \\h \\z \\u', "Atualize o sumário no editor (campo TOC).")
        paragraph_count += 2

    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    idx = 0
    n = len(lines)

    while idx < n:
        line = lines[idx]
        stripped = line.strip()

        if not stripped:
            idx += 1
            continue

        if stripped == PAGE_BREAK:
            ET.SubElement(ET.SubElement(ET.SubElement(body, _w("p")), _w("r")), _w("br"), {_w("type"): "page"})
            idx += 1
            continue

        # Bloco de código cercado ```
        if stripped.startswith("```"):
            idx += 1
            code_lines = []
            while idx < n and not lines[idx].strip().startswith("```"):
                code_lines.append(lines[idx])
                idx += 1
            if idx < n:
                idx += 1
            code_p = ET.SubElement(body, _w("p"))
            ppr = ET.SubElement(code_p, _w("pPr"))
            ET.SubElement(ppr, _w("ind"), {_w("left"): "720", _w("right"): "360"})
            ET.SubElement(ppr, _w("spacing"), {_w("before"): "80", _w("after"): "120", _w("line"): "240", _w("lineRule"): "auto"})
            ET.SubElement(ppr, _w("jc"), {_w("val"): "left"})
            ET.SubElement(ppr, _w("shd"), {_w("val"): "clear", _w("color"): "auto", _w("fill"): "F4F4F4"})
            for c_idx, cline in enumerate(code_lines):
                if c_idx > 0:
                    ET.SubElement(ET.SubElement(code_p, _w("r")), _w("br"))
                _append_text_run(code_p, cline, code=True, size_half_pts="20")
            paragraph_count += 1
            continue

        # Linha horizontal
        if _HR_RE.match(line):
            hr_p = ET.SubElement(body, _w("p"))
            ppr = ET.SubElement(hr_p, _w("pPr"))
            pbdr = ET.SubElement(ppr, _w("pBdr"))
            ET.SubElement(pbdr, _w("bottom"), {_w("val"): "single", _w("sz"): "6", _w("space"): "1", _w("color"): "AAAAAA"})
            paragraph_count += 1
            idx += 1
            continue

        # Títulos #, ##, ###
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            level = min(3, len(heading_match.group(1)))
            h_text = heading_match.group(2).strip()
            hp = ET.SubElement(body, _w("p"))
            ppr = ET.SubElement(hp, _w("pPr"))
            ET.SubElement(ppr, _w("pStyle"), {_w("val"): f"Heading{level}"})
            ET.SubElement(ppr, _w("keepNext"))
            ET.SubElement(ppr, _w("jc"), {_w("val"): "left"})
            sz = "28" if level == 1 else "24"
            _append_inline_runs(hp, h_text, base_bold=True, base_italic=(level == 3), size_half_pts=sz)
            paragraph_count += 1
            heading_count += 1
            idx += 1
            continue

        # Tabela Markdown | col | col |
        if _looks_like_table_start(lines, idx):
            header_cells = _split_pipe_row(lines[idx])
            idx += 2  # pula cabeçalho e linha separadora |---|---|
            table_rows = [header_cells]
            while idx < n and "|" in lines[idx] and lines[idx].strip() and not lines[idx].strip().startswith(">"):
                if _is_table_separator(lines[idx]):
                    idx += 1
                    continue
                table_rows.append(_split_pipe_row(lines[idx]))
                idx += 1
            body.append(_build_table_element(table_rows, has_header=True))
            table_count += 1
            continue

        # Citação direta longa (> blockquote): recuo 4cm (2268 twips), 10pt, espaçamento simples
        if stripped.startswith(">"):
            quote_parts: list[str] = []
            while idx < n and lines[idx].strip().startswith(">"):
                qline = re.sub(r"^\s*>+\s?", "", lines[idx]).strip()
                if not qline:
                    idx += 1
                    break
                quote_parts.append(qline)
                idx += 1
            if quote_parts:
                qp = ET.SubElement(body, _w("p"))
                ppr = ET.SubElement(qp, _w("pPr"))
                ET.SubElement(ppr, _w("pStyle"), {_w("val"): "ForensicQuote"})
                ET.SubElement(ppr, _w("ind"), {_w("left"): QUOTE_INDENT_TWIPS})
                ET.SubElement(ppr, _w("spacing"), {_w("before"): "120", _w("after"): "120", _w("line"): "240", _w("lineRule"): "auto"})
                ET.SubElement(ppr, _w("jc"), {_w("val"): "both"})
                _append_inline_runs(qp, " ".join(quote_parts), size_half_pts="20")
                paragraph_count += 1
                blockquote_count += 1
            continue

        # Lista com marcadores (- / * / +)
        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            lp = ET.SubElement(body, _w("p"))
            ppr = ET.SubElement(lp, _w("pPr"))
            ET.SubElement(ppr, _w("pStyle"), {_w("val"): "ListBullet"})
            ET.SubElement(ppr, _w("ind"), {_w("left"): "720", _w("hanging"): "360"})
            ET.SubElement(ppr, _w("spacing"), {_w("before"): "40", _w("after"): "80", _w("line"): "300", _w("lineRule"): "auto"})
            ET.SubElement(ppr, _w("jc"), {_w("val"): "both"})
            _append_text_run(lp, "• ", bold=True)
            _append_inline_runs(lp, bullet_match.group(1).strip())
            paragraph_count += 1
            idx += 1
            continue

        # Lista numerada (1. / 1))
        numbered_match = _NUMBERED_RE.match(line)
        if numbered_match:
            np = ET.SubElement(body, _w("p"))
            ppr = ET.SubElement(np, _w("pPr"))
            ET.SubElement(ppr, _w("pStyle"), {_w("val"): "ListNumber"})
            ET.SubElement(ppr, _w("ind"), {_w("left"): "720", _w("hanging"): "360"})
            ET.SubElement(ppr, _w("spacing"), {_w("before"): "40", _w("after"): "80", _w("line"): "300", _w("lineRule"): "auto"})
            ET.SubElement(ppr, _w("jc"), {_w("val"): "both"})
            _append_text_run(np, f"{numbered_match.group(1)}. ", bold=True)
            _append_inline_runs(np, numbered_match.group(2).strip())
            paragraph_count += 1
            idx += 1
            continue

        # Parágrafo comum (une linhas contíguas do mesmo parágrafo)
        para_lines = [stripped]
        idx += 1
        while idx < n:
            nxt = lines[idx]
            nxt_stripped = nxt.strip()
            if (
                not nxt_stripped
                or nxt_stripped.startswith(("```", ">", "#"))
                or _HR_RE.match(nxt)
                or _BULLET_RE.match(nxt)
                or _NUMBERED_RE.match(nxt)
                or _looks_like_table_start(lines, idx)
            ):
                break
            para_lines.append(nxt_stripped)
            idx += 1

        pp = ET.SubElement(body, _w("p"))
        ppr = ET.SubElement(pp, _w("pPr"))
        ET.SubElement(ppr, _w("pStyle"), {_w("val"): "Normal"})
        ET.SubElement(ppr, _w("ind"), {_w("firstLine"): FIRST_LINE_TWIPS})
        ET.SubElement(ppr, _w("spacing"), {_w("before"): "0", _w("after"): "120", _w("line"): "360", _w("lineRule"): "auto"})
        ET.SubElement(ppr, _w("jc"), {_w("val"): "both"})
        _append_inline_runs(pp, " ".join(para_lines))
        paragraph_count += 1

    if paragraph_count == 0 and table_count == 0:
        empty_p = ET.SubElement(body, _w("p"))
        ET.SubElement(empty_p, _w("r"))
        paragraph_count = 1

    # Configuração forense A4 (210x297mm) e margens ABNT/forenses (3cm sup/esq, 2cm inf/dir)
    sect_pr = ET.SubElement(body, _w("sectPr"))
    ET.SubElement(sect_pr, _w("headerReference"), {_w("type"): "default", f"{{{NS_R}}}id": "rId2"})
    ET.SubElement(sect_pr, _w("footerReference"), {_w("type"): "default", f"{{{NS_R}}}id": "rId3"})
    ET.SubElement(sect_pr, _w("pgSz"), {_w("w"): A4_WIDTH_TWIPS, _w("h"): A4_HEIGHT_TWIPS})
    ET.SubElement(sect_pr, _w("pgMar"), {
        _w("top"): MARGIN_TOP_TWIPS,
        _w("right"): MARGIN_RIGHT_TWIPS,
        _w("bottom"): MARGIN_BOTTOM_TWIPS,
        _w("left"): MARGIN_LEFT_TWIPS,
        _w("header"): HEADER_DIST_TWIPS,
        _w("footer"): FOOTER_DIST_TWIPS,
        _w("gutter"): "0",
    })

    parts: tuple[tuple[str, bytes], ...] = (
        ("[Content_Types].xml", _build_content_types()),
        ("_rels/.rels", _build_root_rels()),
        ("word/document.xml", _xml_bytes(doc)),
        ("word/_rels/document.xml.rels", _build_document_rels()),
        ("word/styles.xml", _build_styles()),
        ("word/header1.xml", _build_header(title, draft_banner)),
        ("word/footer1.xml", _build_footer()),
        ("docProps/core.xml", _build_core_props(title, metadata)),
    )

    fd, tmp_name = tempfile.mkstemp(prefix=".docx-", suffix=".docx", dir=destination.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for arcname, payload in parts:
                info = zipfile.ZipInfo(arcname, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, payload)
        os.replace(tmp_name, destination)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {
        "output_path": str(destination),
        "sha256": digest,
        "size_bytes": destination.stat().st_size,
        "title": title,
        "paragraphs": paragraph_count,
        "tables": table_count,
        "headings": heading_count,
        "blockquotes": blockquote_count,
        "draft_watermark": bool(draft_banner),
        "safety_notice": SAFETY_NOTICE if draft_banner else None,
        "page_layout": {
            "paper": "A4",
            "width_twips": int(A4_WIDTH_TWIPS),
            "height_twips": int(A4_HEIGHT_TWIPS),
            "margins_twips": {
                "top": int(MARGIN_TOP_TWIPS),
                "left": int(MARGIN_LEFT_TWIPS),
                "bottom": int(MARGIN_BOTTOM_TWIPS),
                "right": int(MARGIN_RIGHT_TWIPS),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exporta minuta ou relatório Markdown para .docx forense (A4, margens 3/3/2/2cm, aviso CNJ 332/2020 e 615/2025)"
    )
    parser.add_argument("input", type=Path, help="Arquivo Markdown de entrada (.md)")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Caminho de saída (.docx)")
    parser.add_argument("--title", default="Minuta Jurídica", help="Título nos metadados do documento")
    parser.add_argument("--no-draft-banner", action="store_true", help="Suprime a tarja visual adicional no corpo (mantendo cabeçalho de título)")
    parser.add_argument("--toc", action="store_true", help="Insere sumário (campo TOC atualizado pelo editor)")
    parser.add_argument("--annex", type=Path, help="Anexo técnico em Markdown, em nova página (ex.: matriz de rastreabilidade)")
    args = parser.parse_args()
    try:
        if not args.input.is_file():
            raise FileNotFoundError(f"Arquivo de entrada não encontrado: {args.input}")
        receipt = export_markdown_to_docx(
            args.input,
            args.output,
            title=args.title,
            draft_banner=not args.no_draft_banner,
            toc=args.toc,
            annex=args.annex,
        )
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
