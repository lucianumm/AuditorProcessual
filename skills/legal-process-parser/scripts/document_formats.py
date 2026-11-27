"""Extract supported text, OOXML, ODF, RTF, EML, ZIP, ICP-Brasil (.p7s), and media manifests safely.

Non-PDF units are logical segments, not physical PDF pages. Embedded or standalone
media stays an explicit visual/audio limitation until reviewed. Never executes
macros, formulas, external relationships, XXE entities, or binary payloads.
"""
from __future__ import annotations

import email
import email.policy
import hashlib
import html
import math
import re
import struct
import tempfile
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

TEXT_FORMATS = {".txt", ".md", ".csv", ".tsv", ".json", ".jsonl", ".xml", ".html", ".htm", ".log"}
OFFICE_FORMATS = {".docx", ".xlsx"}
ODF_FORMATS = {".odt", ".ods"}
IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".bmp"}
MEDIA_FORMATS = {".mp3", ".ogg", ".opus", ".wav", ".mp4", ".webm"}
SAFE_ZIP_INNER_FORMATS = {
    ".txt", ".md", ".csv", ".tsv", ".json", ".xml", ".html", ".htm",
    ".docx", ".xlsx", ".odt", ".ods", ".rtf", ".eml",
}

MAX_EXPANDED_BYTES = 64 * 1024 * 1024
MAX_ENTRIES = 10000

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

ODF_OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
ODF_TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
ODF_TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"

EXCEL_BUILTIN_DATE_FMTS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 27, 30, 36, 45, 46, 47, 50, 57}
EXCEL_PURE_TIME_FMTS = {18, 19, 20, 21, 45, 46, 47}

EML_HEADER_RE = re.compile(
    rb"(?im)^(?:from|to|subject|date|mime-version|message-id|content-type|received|return-path)\s*:"
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_image_magic(suffix: str, head: bytes) -> bool:
    if suffix == ".png":
        return len(head) >= 8 and head.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix in {".jpg", ".jpeg"}:
        return len(head) >= 3 and head.startswith(b"\xff\xd8\xff")
    if suffix == ".webp":
        return len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if suffix in {".tiff", ".tif"}:
        return len(head) >= 4 and head[:4] in (b"II*\x00", b"MM\x00*")
    if suffix == ".bmp":
        return len(head) >= 26 and head[:2] == b"BM"
    return False


def _validate_media_magic(suffix: str, head: bytes) -> bool:
    if suffix == ".mp3":
        return (len(head) >= 3 and head[:3] == b"ID3") or (
            len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0
        )
    if suffix in {".ogg", ".opus"}:
        return len(head) >= 4 and head[:4] == b"OggS"
    if suffix == ".wav":
        return len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    if suffix == ".mp4":
        return len(head) >= 12 and head[4:8] == b"ftyp"
    if suffix == ".webm":
        return len(head) >= 4 and head[:4] == b"\x1a\x45\xdf\xa3"
    return False


def inspect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with path.open("rb") as source:
            head = source.read(1024)
        if not head.lstrip().startswith(b"%PDF-"):
            raise ValueError("Arquivo .pdf não contém cabeçalho PDF válido")
        return "pdf"
    if suffix in OFFICE_FORMATS:
        if not zipfile.is_zipfile(path):
            raise ValueError("Arquivo Office não é um contêiner OOXML válido")
        return suffix[1:]
    if suffix in ODF_FORMATS:
        if not zipfile.is_zipfile(path):
            raise ValueError("Arquivo OpenDocument não é um contêiner ODF válido")
        return suffix[1:]
    if suffix == ".rtf":
        with path.open("rb") as source:
            head = source.read(256)
        if not head.lstrip().startswith(b"{\\rtf"):
            raise ValueError("Arquivo .rtf não contém cabeçalho RTF válido")
        return "rtf"
    if suffix == ".eml":
        with path.open("rb") as source:
            head = source.read(8192)
        if b"\x00" in head or head.startswith((b"PK\x03\x04", b"\x89PNG", b"\xff\xd8", b"%PDF-", b"\xd0\xcf\x11\xe0")):
            raise ValueError("Arquivo .eml contém carga binária inválida no cabeçalho")
        if not EML_HEADER_RE.search(head):
            raise ValueError("Arquivo .eml sem cabeçalhos RFC 5322 reconhecíveis")
        return "eml"
    if suffix == ".zip":
        if not zipfile.is_zipfile(path):
            raise ValueError("Arquivo .zip não é um contêiner ZIP válido")
        return "zip"
    if suffix == ".p7s":
        with path.open("rb") as source:
            raw_probe = source.read(65536)
        stripped = raw_probe.lstrip()
        if not stripped or not (
            raw_probe.startswith(b"\x30")
            or stripped.startswith(b"-----BEGIN")
            or b"%PDF-" in raw_probe
        ):
            raise ValueError("Arquivo .p7s não contém envelope CMS/PKCS#7 válido")
        return "p7s"
    if suffix in IMAGE_FORMATS:
        with path.open("rb") as source:
            head = source.read(64)
        if not _validate_image_magic(suffix, head):
            raise ValueError(f"Arquivo {suffix} não contém cabeçalho de imagem válido")
        return "image"
    if suffix in MEDIA_FORMATS:
        with path.open("rb") as source:
            head = source.read(64)
        if not _validate_media_magic(suffix, head):
            raise ValueError(f"Arquivo {suffix} não contém cabeçalho de áudio/vídeo válido")
        return "audio_video"
    if suffix not in TEXT_FORMATS:
        raise ValueError(
            f"Formato {suffix or 'sem extensão'} não suportado no extrator local; preserve o original e "
            "converta para PDF/texto, ou use visão da IA para imagens. Nunca decodifique binário como texto."
        )
    with path.open("rb") as source:
        head = source.read(8192)
    unicode_bom = head.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff"))
    if (b"\x00" in head and not unicode_bom) or head.startswith((b"PK\x03\x04", b"\x89PNG", b"\xff\xd8", b"%PDF-", b"\xd0\xcf\x11\xe0")):
        raise ValueError("Conteúdo binário com extensão de texto; formato real precisa ser convertido")
    return "text"


def _xml_bytes(data: bytes) -> ET.Element:
    xml_probe = data.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in xml_probe or b"<!ENTITY" in xml_probe:
        raise ValueError("XML Office/ODF com declaração de entidades não permitido")
    return ET.fromstring(data)


def _xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    return _xml_bytes(archive.read(name))


def _check_archive(archive: zipfile.ZipFile, *, check_macros: bool = True) -> list[str]:
    entries = archive.infolist()
    if len(entries) > MAX_ENTRIES or sum(i.file_size for i in entries) > MAX_EXPANDED_BYTES:
        raise ValueError("Contêiner excede limite seguro de expansão; dividir/converter sem truncar")
    if any(i.flag_bits & 1 for i in entries):
        raise ValueError("Contêiner criptografado: obtenha uma cópia acessível autorizada")
    names = [i.filename for i in entries]
    if len(set(names)) != len(names):
        raise ValueError("Contêiner com nomes duplicados: não escolher silenciosamente uma versão")
    for info in entries:
        entry_name = info.filename
        if entry_name.startswith(("/", "\\")) or ".." in Path(entry_name.replace("\\", "/")).parts or ":" in entry_name.split("/")[0]:
            raise ValueError("Caminho inseguro detectado no contêiner (path traversal)")
        if ((info.external_attr >> 16) & 0o170000) == 0o120000:
            raise ValueError("Link simbólico não permitido no contêiner")
    if check_macros and any(
        n.lower().endswith("vbaproject.bin") or n.lower().startswith(("basic/", "scripts/"))
        for n in names
    ):
        raise ValueError("Contêiner Office com macros não permitido")
    return names


def _word_text(element: ET.Element) -> str:
    values: list[str] = []
    for node in element.iter():
        if node.tag == W + "p" and values:
            values.append("\n")
        elif node.tag in {W + "t", W + "delText"}:
            values.append(node.text or "")
        elif node.tag == W + "tab":
            values.append("\t")
        elif node.tag == W + "br":
            values.append("\n")
    return "".join(values)


def _odf_text(element: ET.Element) -> str:
    parts: list[str] = []

    def walk(node: ET.Element) -> None:
        if node.text:
            parts.append(node.text)
        for child in node:
            if child.tag == ODF_TEXT + "s":
                count = int(child.attrib.get(ODF_TEXT + "c", "1") or "1")
                parts.append(" " * min(max(count, 1), 64))
            elif child.tag == ODF_TEXT + "tab":
                parts.append("\t")
            elif child.tag == ODF_TEXT + "line-break":
                parts.append("\n")
            elif child.tag in {ODF_TEXT + "p", ODF_TEXT + "h"} and parts and not parts[-1].endswith("\n"):
                parts.append("\n")
                walk(child)
            else:
                walk(child)
            if child.tail:
                parts.append(child.tail)

    walk(element)
    return "".join(parts).strip()


def _parse_xlsx_styles(archive: zipfile.ZipFile, names: list[str]) -> tuple[dict[int, str], list[int]]:
    if "xl/styles.xml" not in names:
        return {}, []
    root = _xml(archive, "xl/styles.xml")
    custom_fmts: dict[int, str] = {}
    num_fmts_el = root.find(S + "numFmts")
    if num_fmts_el is not None:
        for fmt in num_fmts_el.findall(S + "numFmt"):
            try:
                fmt_id = int(fmt.attrib["numFmtId"])
                custom_fmts[fmt_id] = fmt.attrib.get("formatCode", "")
            except (KeyError, ValueError):
                continue
    xf_fmt_ids: list[int] = []
    cell_xfs_el = root.find(S + "cellXfs")
    if cell_xfs_el is not None:
        for xf in cell_xfs_el.findall(S + "xf"):
            try:
                xf_fmt_ids.append(int(xf.attrib.get("numFmtId", "0")))
            except ValueError:
                xf_fmt_ids.append(0)
    return custom_fmts, xf_fmt_ids


def _is_excel_date_format(num_fmt_id: int, custom_fmts: dict[int, str]) -> bool:
    if num_fmt_id in EXCEL_BUILTIN_DATE_FMTS:
        return True
    code = custom_fmts.get(num_fmt_id, "")
    if not code:
        return False
    primary = code.split(";")[0]
    cleaned = re.sub(r'"[^"]*"', "", primary)
    cleaned = re.sub(r"\\.", "", cleaned)
    cleaned = re.sub(r"\[[^\]]*\]", "", cleaned)
    cleaned = re.sub(r"[_*].", "", cleaned)
    lower = cleaned.lower()
    if any(ch in lower for ch in ("#", "?")):
        return False
    return bool(re.search(r"[yd]", lower))


def _format_excel_serial_date(raw_text: str, num_fmt_id: int) -> str:
    try:
        serial = float(raw_text)
    except ValueError:
        return raw_text
    if not math.isfinite(serial) or serial < 0 or serial >= 2958466:
        return raw_text
    day_part = int(math.floor(serial))
    frac = serial - day_part
    total_seconds = int(round(frac * 86400))
    if total_seconds >= 86400:
        day_part += 1
        total_seconds -= 86400
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    if day_part == 0 and num_fmt_id in EXCEL_PURE_TIME_FMTS:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if day_part == 0:
        return raw_text

    # Excel 1900 date system with Lotus 1-2-3 phantom 1900-02-29 (serial 60) handled.
    if day_part == 60:
        date_str = "1900-02-29"
    elif day_part < 60:
        dt = date(1899, 12, 31) + timedelta(days=day_part)
        date_str = dt.isoformat()
    else:
        dt = date(1899, 12, 30) + timedelta(days=day_part)
        date_str = dt.isoformat()

    if total_seconds > 0:
        return f"{date_str} {hours:02d}:{minutes:02d}:{seconds:02d}"
    return date_str


def extract_opendocument(path: Path) -> tuple[list[str], list[str]]:
    """Extract LibreOffice/OpenDocument .odt and .ods safely."""
    kind = inspect_format(path)
    if kind not in {"odt", "ods"}:
        raise ValueError(f"Formato {kind} não é OpenDocument (.odt/.ods)")
    warnings = [
        "Unidades OpenDocument são segmentos lógicos, não páginas físicas; converter a PDF para conferir layout/paginação."
    ]
    with zipfile.ZipFile(path) as archive:
        names = _check_archive(archive)
        media = [n for n in names if n.startswith(("Pictures/", "ObjectReplacements/", "media/")) and not n.endswith("/")]
        if media:
            warnings.append(
                f"VISUAL_REVIEW_REQUIRED: {len(media)} recursos visuais incorporados preservados no original; "
                "não foram semanticamente examinados. Converter a PDF e vincular a versão."
            )
        if "content.xml" not in names:
            raise ValueError("Arquivo OpenDocument sem content.xml")
        root = _xml(archive, "content.xml")
        body = root.find(ODF_OFFICE + "body")
        if body is None:
            raise ValueError("Arquivo OpenDocument sem office:body")

        if kind == "odt":
            text_body = body.find(ODF_OFFICE + "text")
            if text_body is None:
                raise ValueError("ODT sem corpo textual")
            lines: list[str] = []
            para_idx = 0
            table_idx = 0
            for node in text_body:
                if node.tag in {ODF_TEXT + "p", ODF_TEXT + "h"}:
                    para_idx += 1
                    lines.append(f"[Parágrafo {para_idx}] {_odf_text(node)}")
                elif node.tag == ODF_TABLE + "table":
                    table_idx += 1
                    for row_idx, row in enumerate(node.findall(ODF_TABLE + "table-row"), 1):
                        cells = [_odf_text(cell).replace("\n", " ") for cell in row.findall(ODF_TABLE + "table-cell")]
                        lines.append(f"[Tabela {table_idx}, linha {row_idx}] " + " | ".join(cells))
            return ["\n".join(lines)], list(dict.fromkeys(warnings))

        spreadsheet = body.find(ODF_OFFICE + "spreadsheet")
        if spreadsheet is None:
            raise ValueError("ODS sem corpo de planilha")
        segments: list[str] = []
        for sheet_idx, table in enumerate(spreadsheet.findall(ODF_TABLE + "table"), 1):
            sheet_name = table.attrib.get(ODF_TABLE + "name", f"Planilha{sheet_idx}")
            lines = [f"[Planilha: {sheet_name}]"]
            for row_idx, row in enumerate(table.findall(ODF_TABLE + "table-row"), 1):
                cells: list[str] = []
                for cell in row.findall(ODF_TABLE + "table-cell"):
                    cell_text = _odf_text(cell).replace("\n", " ")
                    formula = cell.attrib.get(ODF_TABLE + "formula")
                    repeat = int(cell.attrib.get(ODF_TABLE + "number-columns-repeated", "1") or "1")
                    if formula:
                        warnings.append(
                            "Fórmulas não executadas; valores armazenados podem estar desatualizados. Validar cálculos e formatação de datas/unidades."
                        )
                        rendered = f"fórmula {formula}; valor armazenado: {cell_text or '[AUSENTE]'}"
                    else:
                        rendered = cell_text
                    if rendered:
                        cells.extend([rendered] * min(max(repeat, 1), 32))
                    elif repeat <= 16:
                        cells.extend([""] * repeat)
                while cells and cells[-1] == "":
                    cells.pop()
                if cells:
                    lines.append(f"[Tabela {sheet_idx}, linha {row_idx}] " + " | ".join(cells))
            segments.append("\n".join(lines))
        return segments or ["[Planilha vazia]"], list(dict.fromkeys(warnings))


def extract_office(path: Path) -> tuple[list[str], list[str]]:
    kind = inspect_format(path)
    if kind in {"odt", "ods"}:
        return extract_opendocument(path)
    if kind not in {"docx", "xlsx"}:
        raise ValueError(f"Formato {kind} não é um contêiner Office (.docx/.xlsx/.odt/.ods)")
    warnings = ["Unidades Office são segmentos lógicos, não páginas físicas; converter a PDF para conferir layout/paginação."]
    with zipfile.ZipFile(path) as archive:
        names = _check_archive(archive)
        media = [n for n in names if n.startswith(("word/media/", "word/embeddings/", "word/charts/", "xl/media/", "xl/charts/", "xl/embeddings/"))]
        if media:
            warnings.append(f"VISUAL_REVIEW_REQUIRED: {len(media)} recursos visuais incorporados preservados no original; não foram semanticamente examinados. Converter a PDF e vincular a versão.")
        if kind == "docx":
            body = _xml(archive, "word/document.xml").find(W + "body")
            if body is None:
                raise ValueError("DOCX sem corpo de documento")
            lines = []
            nodes = []

            def collect(container: ET.Element) -> None:
                for node in container:
                    if node.tag in {W + "p", W + "tbl"}:
                        nodes.append(node)
                    else:
                        collect(node)

            collect(body)
            for position, node in enumerate(nodes, 1):
                if node.tag == W + "p":
                    lines.append(f"[Parágrafo {position}] " + _word_text(node))
                elif node.tag == W + "tbl":
                    for row_number, row in enumerate(node.findall(W + "tr"), 1):
                        cells = [_word_text(cell).replace("\n", " ") for cell in row.findall(W + "tc")]
                        lines.append(f"[Tabela {position}, linha {row_number}] " + " | ".join(cells))
            for name in names:
                if name.startswith("word/") and name.endswith(".xml") and Path(name).name.startswith(("header", "footer", "footnotes", "endnotes", "comments")):
                    lines.append(f"[Parte {name}] " + _word_text(_xml(archive, name)))
            if any(n.tag in {W + "ins", W + "del"} for n in body.iter()):
                warnings.append("Revisões controladas presentes: texto inserido/excluído permanece na extração; conferir visualmente antes de escolher uma redação.")
            return ["\n".join(lines)], warnings

        shared = []
        if "xl/sharedStrings.xml" in names:
            shared = ["".join(n.text or "" for n in item.iter(S + "t")) for item in _xml(archive, "xl/sharedStrings.xml")]
        custom_fmts, xf_fmt_ids = _parse_xlsx_styles(archive, names)
        workbook = _xml(archive, "xl/workbook.xml")
        rels = {r.attrib["Id"]: r.attrib for r in _xml(archive, "xl/_rels/workbook.xml.rels")}
        segments = []
        for sheet in workbook.findall(f"{S}sheets/{S}sheet"):
            relation = rels.get(sheet.attrib.get(R + "id"), {})
            if relation.get("TargetMode") == "External":
                raise ValueError("Planilha com origem externa: não buscar conteúdo automaticamente")
            target = relation.get("Target", "")
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            if ".." in Path(target).parts or target not in names:
                raise ValueError("Relacionamento de planilha não resolvido")
            lines = [f"[Planilha: {sheet.attrib.get('name')}; estado: {sheet.attrib.get('state', 'visible')}]"]
            for row in _xml(archive, target).iter(S + "row"):
                for cell in row.findall(S + "c"):
                    value = cell.find(S + "v")
                    text = value.text if value is not None and value.text is not None else ""
                    cell_type = cell.attrib.get("t")
                    if cell_type == "s":
                        try:
                            index = int(text)
                            if not 0 <= index < len(shared):
                                raise ValueError("índice fora da lista")
                            text = shared[index]
                        except (ValueError, IndexError) as error:
                            raise ValueError("Texto compartilhado de célula não resolvido") from error
                    elif cell_type == "inlineStr":
                        text = "".join(n.text or "" for n in cell.iter(S + "t"))
                    elif cell_type in {None, "", "n"} and text:
                        style_attr = cell.attrib.get("s")
                        if style_attr is not None:
                            try:
                                style_idx = int(style_attr)
                                if 0 <= style_idx < len(xf_fmt_ids):
                                    num_fmt_id = xf_fmt_ids[style_idx]
                                    if _is_excel_date_format(num_fmt_id, custom_fmts):
                                        text = _format_excel_serial_date(text, num_fmt_id)
                            except ValueError:
                                pass
                    formula = cell.find(S + "f")
                    if formula is not None:
                        lines.append(f"{cell.attrib.get('r')} = fórmula {formula.text}; valor armazenado: {text or '[AUSENTE]'}")
                        warnings.append("Fórmulas não executadas; valores armazenados podem estar desatualizados. Validar cálculos e formatação de datas/unidades.")
                    else:
                        lines.append(f"{cell.attrib.get('r')} = {text}")
            segments.append("\n".join(lines))
        return segments, list(dict.fromkeys(warnings))


_RTF_SKIP_DESTINATIONS = {
    "fonttbl", "colortbl", "stylesheet", "info", "pict", "object", "objdata",
    "generator", "themedata", "colorschememapping", "latentstyles", "datastore",
    "rsidtbl", "listtable", "listoverridetable", "revtbl", "pnseclvl",
}


def extract_rtf(path: Path) -> tuple[list[str], list[str]]:
    """Safe pure-stdlib RTF text extractor without executing embedded OLE objects."""
    inspect_format(path)
    raw = path.read_bytes()
    if len(raw) > MAX_EXPANDED_BYTES:
        raise ValueError("Arquivo RTF excede limite seguro de tamanho")
    src = raw.decode("latin-1")
    out: list[str] = []
    warnings: list[str] = ["Unidades RTF são segmentos lógicos, não páginas físicas."]
    visual_warned = False

    stack: list[tuple[int, bool]] = []
    uc_count = 1
    skip_group = False
    group_start = False

    idx = 0
    length = len(src)
    while idx < length:
        ch = src[idx]
        if ch == "{":
            stack.append((uc_count, skip_group))
            group_start = True
            idx += 1
            continue
        if ch == "}":
            if stack:
                uc_count, skip_group = stack.pop()
            group_start = False
            idx += 1
            continue
        if ch in "\r\n":
            idx += 1
            continue
        if ch != "\\":
            group_start = False
            if not skip_group:
                out.append(ch)
            idx += 1
            continue

        idx += 1
        if idx >= length:
            break
        nxt = src[idx]
        if nxt in "\\{}":
            group_start = False
            if not skip_group:
                out.append(nxt)
            idx += 1
            continue
        if nxt == "*":
            if group_start:
                skip_group = True
            idx += 1
            continue
        if nxt == "~":
            group_start = False
            if not skip_group:
                out.append(" ")
            idx += 1
            continue
        if nxt == "_":
            group_start = False
            if not skip_group:
                out.append("-")
            idx += 1
            continue
        if nxt == "-":
            group_start = False
            idx += 1
            continue
        if nxt == "\n" or nxt == "\r":
            group_start = False
            if not skip_group:
                out.append("\n")
            idx += 1
            continue
        if nxt == "'":
            group_start = False
            hex_digits = src[idx + 1 : idx + 3]
            if len(hex_digits) == 2 and all(c in "0123456789abcdefABCDEF" for c in hex_digits):
                if not skip_group:
                    out.append(bytes.fromhex(hex_digits).decode("cp1252", errors="replace"))
                idx += 3
            else:
                idx += 1
            continue

        word_match = re.match(r"([A-Za-z]+)(-?\d+)?", src[idx:])
        if not word_match:
            group_start = False
            idx += 1
            continue
        word, param_str = word_match.groups()
        idx += word_match.end()
        had_space_delim = False
        if idx < length and src[idx] == " ":
            had_space_delim = True
            idx += 1

        if word in _RTF_SKIP_DESTINATIONS:
            if word in {"pict", "object", "objdata"} and not visual_warned:
                warnings.append(
                    "VISUAL_REVIEW_REQUIRED: objeto/imagem incorporado em RTF preservado no original, sem renderização ou execução local."
                )
                visual_warned = True
            skip_group = True
            group_start = False
            continue
        group_start = False
        if skip_group:
            continue

        if word in {"par", "line", "row"}:
            out.append("\n")
        elif word == "tab":
            out.append("\t")
        elif word == "cell":
            out.append(" | ")
        elif word == "uc" and param_str is not None:
            try:
                uc_count = max(0, int(param_str))
            except ValueError:
                pass
        elif word == "u" and param_str is not None:
            try:
                codepoint = int(param_str)
                if codepoint < 0:
                    codepoint += 65536
                out.append(chr(codepoint))
            except (ValueError, OverflowError):
                pass
            # Skip `uc_count` fallback characters/hex escapes (`?` or `\'hh`).
            # Note: if `had_space_delim` was False, we are right at the fallback char;
            # if `had_space_delim` was True, the space acted as control-word delimiter.
            _ = had_space_delim
            skipped = 0
            while skipped < uc_count and idx < length:
                if src[idx : idx + 2] == "\\'" and idx + 4 <= length:
                    idx += 4
                elif src[idx] in "{}":
                    break
                else:
                    idx += 1
                skipped += 1

    text = "".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return [text], list(dict.fromkeys(warnings))


def _strip_html_safely(raw_html: str) -> str:
    cleaned = re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", raw_html)
    cleaned = re.sub(r"(?i)<br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"(?i)</(p|div|tr|li|h[1-6])>", "\n", cleaned)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_eml(path: Path) -> tuple[list[str], list[str]]:
    """Extract RFC 5322 .eml headers, body, and attachment manifest without executing payloads."""
    inspect_format(path)
    raw = path.read_bytes()
    if len(raw) > MAX_EXPANDED_BYTES:
        raise ValueError("Arquivo .eml excede limite seguro de tamanho")
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    warnings: list[str] = ["Mensagem de e-mail (.eml) extraída como segmento lógico; anexos não executados."]

    header_lines = [
        f"De: {msg.get('From', 'Não informado')}",
        f"Para: {msg.get('To', 'Não informado')}",
    ]
    if msg.get("Cc"):
        header_lines.append(f"Cc: {msg.get('Cc')}")
    header_lines.extend([
        f"Data: {msg.get('Date', 'Não informada')}",
        f"Assunto: {msg.get('Subject', 'Sem assunto')}",
    ])

    plain_bodies: list[str] = []
    html_bodies: list[str] = []
    attachments: list[dict[str, Any]] = []

    parts = list(msg.walk()) if msg.is_multipart() else [msg]
    for part in parts:
        if part.is_multipart():
            continue
        content_type = part.get_content_type()
        filename = part.get_filename()
        is_attachment = part.is_attachment() or bool(filename)
        payload = part.get_payload(decode=True) or b""

        if not is_attachment and content_type == "text/plain":
            charset = part.get_content_charset() or "utf-8"
            try:
                plain_bodies.append(payload.decode(charset, errors="replace").strip())
            except LookupError:
                plain_bodies.append(payload.decode("utf-8", errors="replace").strip())
        elif not is_attachment and content_type == "text/html":
            charset = part.get_content_charset() or "utf-8"
            try:
                raw_html = payload.decode(charset, errors="replace")
            except LookupError:
                raw_html = payload.decode("utf-8", errors="replace")
            html_bodies.append(_strip_html_safely(raw_html))
        else:
            att_name = filename or f"anexo-{len(attachments) + 1}.bin"
            attachments.append({
                "filename": att_name,
                "mime_type": content_type,
                "size_bytes": len(payload),
                "sha256": _sha256_bytes(payload),
            })

    body_text = "\n\n".join(b for b in plain_bodies if b) or "\n\n".join(b for b in html_bodies if b) or "[Sem corpo textual]"
    lines = ["[Mensagem Eletrônica (.eml)]", *header_lines, "", "[Corpo da mensagem]", body_text]
    if attachments:
        lines.extend(["", f"[Anexos inventariados: {len(attachments)}]"])
        for att in attachments:
            lines.append(
                f"- {att['filename']} | MIME: {att['mime_type']} | Tamanho: {att['size_bytes']} bytes | SHA-256: {att['sha256']}"
            )
        if any(att["mime_type"].startswith(("image/", "application/pdf", "video/", "audio/")) for att in attachments):
            warnings.append(
                "VISUAL_REVIEW_REQUIRED: e-mail contém anexo(s) binário(s)/visuais inventariados por hash, sem inspeção semântica automática."
            )
    return ["\n".join(lines)], list(dict.fromkeys(warnings))


def extract_bundle(path: Path) -> tuple[list[str], list[str]]:
    """Inspect and safely extract supported inner documents from a .zip bundle."""
    inspect_format(path)
    warnings: list[str] = ["Pacote .zip inspecionado com extração restrita a formatos seguros e verificação de limites."]
    segments: list[str] = []
    with zipfile.ZipFile(path) as archive:
        _check_archive(archive, check_macros=False)
        file_infos = [info for info in archive.infolist() if not info.is_dir()]
        summary_lines = [
            f"[Pacote ZIP: {path.name} | Entradas: {len(file_infos)}]",
        ]
        extracted_segments: list[str] = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            for index, info in enumerate(file_infos, 1):
                data = archive.read(info.filename)
                entry_sha = _sha256_bytes(data)
                suffix = Path(info.filename).suffix.lower()
                summary_lines.append(
                    f"- {info.filename} | {len(data)} bytes | SHA-256: {entry_sha}"
                )
                if suffix in SAFE_ZIP_INNER_FORMATS:
                    safe_target = tmp_root / f"entry_{index}{suffix}"
                    safe_target.write_bytes(data)
                    try:
                        inner_kind = inspect_format(safe_target)
                        if inner_kind in {"docx", "xlsx", "odt", "ods"}:
                            inner_texts, inner_warnings = extract_office(safe_target)
                        elif inner_kind == "rtf":
                            inner_texts, inner_warnings = extract_rtf(safe_target)
                        elif inner_kind == "eml":
                            inner_texts, inner_warnings = extract_eml(safe_target)
                        else:
                            inner_texts = [safe_target.read_text(encoding="utf-8", errors="replace")]
                            inner_warnings = []
                        warnings.extend(inner_warnings)
                        joined = "\n\n".join(t for t in inner_texts if t.strip())
                        extracted_segments.append(
                            f"[Entrada ZIP: {info.filename} | SHA-256: {entry_sha[:16]}]\n{joined or '[Vazio]'}"
                        )
                    except ValueError as exc:
                        warnings.append(f"Entrada ZIP '{info.filename}' não extraída como texto: {exc}")
                elif suffix in IMAGE_FORMATS or suffix == ".pdf":
                    warnings.append(
                        f"VISUAL_REVIEW_REQUIRED: entrada '{info.filename}' no pacote ZIP requer extração/visão individual."
                    )
                elif suffix in MEDIA_FORMATS:
                    warnings.append(
                        f"AUDIO_TRANSCRIPTION_REQUIRED: mídia '{info.filename}' no pacote ZIP requer transcrição humana/auditável."
                    )
        segments.append("\n".join(summary_lines))
        segments.extend(extracted_segments)
    return segments, list(dict.fromkeys(warnings))


def _extract_pdf_bytes(pdf_bytes: bytes) -> list[str] | None:
    reader_cls = None
    try:
        from pypdf import PdfReader  # type: ignore

        reader_cls = PdfReader
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore

            reader_cls = PdfReader
        except Exception:
            return None
    try:
        from io import BytesIO

        reader = reader_cls(BytesIO(pdf_bytes))
        return [(page.extract_text() or "") for page in reader.pages]
    except Exception:
        return None


def extract_p7s(path: Path) -> tuple[list[str], list[str]]:
    """Inspect ICP-Brasil CMS/PKCS#7 (.p7s) wrapper and extract embedded PDF text if present."""
    inspect_format(path)
    raw = path.read_bytes()
    if len(raw) > MAX_EXPANDED_BYTES:
        raise ValueError("Arquivo .p7s excede limite seguro de tamanho")
    digest = _sha256_bytes(raw)
    warnings: list[str] = [
        "Assinatura ICP-Brasil (.p7s) preservada mas não verificada criptograficamente localmente"
    ]
    pdf_start = raw.find(b"%PDF-")
    if pdf_start >= 0:
        eof_pos = raw.rfind(b"%%EOF")
        pdf_slice = raw[pdf_start : (eof_pos + 5 if eof_pos > pdf_start else len(raw))]
        extracted_pages = _extract_pdf_bytes(pdf_slice)
        if extracted_pages and any(page.strip() for page in extracted_pages):
            return extracted_pages, warnings
        warnings.append(
            "VISUAL_REVIEW_REQUIRED: PDF incorporado em envelope .p7s sem camada textual extraível localmente; requer visão/OCR."
        )
        return [
            f"[Envelope ICP-Brasil (.p7s): {path.name}]\n"
            f"Tamanho: {len(raw)} bytes\n"
            f"SHA-256: {digest}\n"
            "PDF incorporado localizado, porém sem camada textual nativa extraída localmente."
        ], warnings

    warnings.append(
        "VISUAL_REVIEW_REQUIRED: assinatura destacada ou conteúdo binário encapsulado em .p7s sem PDF embutido legível."
    )
    return [
        f"[Envelope ICP-Brasil (.p7s): {path.name}]\n"
        f"Tamanho: {len(raw)} bytes\n"
        f"SHA-256: {digest}\n"
        "Envelope CMS/PKCS#7 sem documento PDF embutido; preservar junto ao documento principal."
    ], warnings


def parse_image_dimensions(data: bytes, suffix: str = "") -> tuple[int | None, int | None]:
    """Read image width and height using Pillow if available, or pure-stdlib header parsing."""
    try:
        from io import BytesIO
        from PIL import Image  # type: ignore

        with Image.open(BytesIO(data)) as image:
            return int(image.width), int(image.height)
    except Exception:
        pass

    # Pure-stdlib binary header fallback
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        width, height = struct.unpack(">II", data[16:24])
        return int(width), int(height)
    if len(data) >= 26 and data[:2] == b"BM":
        width, height = struct.unpack("<ii", data[18:26])
        return abs(int(width)), abs(int(height))
    if len(data) >= 4 and data[:3] == b"\xff\xd8\xff":
        pos = 2
        size = len(data)
        while pos + 9 < size:
            if data[pos] != 0xFF:
                pos += 1
                continue
            while pos < size and data[pos] == 0xFF:
                pos += 1
            if pos >= size:
                break
            marker = data[pos]
            pos += 1
            if marker in {0xD8, 0xD9} or (0xD0 <= marker <= 0xD7):
                continue
            if pos + 2 > size:
                break
            seg_len = struct.unpack(">H", data[pos : pos + 2])[0]
            if seg_len < 2 or pos + seg_len > size:
                break
            if 0xC0 <= marker <= 0xCF and marker not in {0xC4, 0xC8, 0xCC} and pos + 7 <= size:
                height, width = struct.unpack(">HH", data[pos + 3 : pos + 7])
                return int(width), int(height)
            pos += seg_len
    if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk_type = data[12:16]
        if chunk_type == b"VP8X" and len(data) >= 30:
            w = 1 + int.from_bytes(data[24:27], "little")
            h = 1 + int.from_bytes(data[27:30], "little")
            return w, h
        if chunk_type == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk_type == b"VP8 " and len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
    if len(data) >= 8 and data[:4] in (b"II*\x00", b"MM\x00*"):
        endian = "<" if data[:2] == b"II" else ">"
        ifd_offset = struct.unpack(endian + "I", data[4:8])[0]
        if ifd_offset + 2 <= len(data):
            count = struct.unpack(endian + "H", data[ifd_offset : ifd_offset + 2])[0]
            width = height = None
            for i in range(min(count, 64)):
                entry_pos = ifd_offset + 2 + i * 12
                if entry_pos + 12 > len(data):
                    break
                tag, field_type, _, value_bytes = struct.unpack(endian + "HHII", data[entry_pos : entry_pos + 12])
                raw_val = data[entry_pos + 8 : entry_pos + 12]
                val = struct.unpack(endian + "H", raw_val[:2])[0] if field_type == 3 else value_bytes
                if tag == 256:
                    width = int(val)
                elif tag == 257:
                    height = int(val)
            if width and height:
                return width, height
    _ = suffix
    return None, None


def extract_media_manifest(path: Path) -> tuple[list[str], list[str]]:
    """Build a traceable logical segment for standalone image or audio/video evidence files."""
    kind = inspect_format(path)
    suffix = path.suffix.lower().lstrip(".")
    size_bytes = path.stat().st_size
    digest = _sha256_path(path)
    if kind == "image":
        head_bytes = path.read_bytes() if size_bytes <= 16 * 1024 * 1024 else path.open("rb").read(262144)
        width, height = parse_image_dimensions(head_bytes, path.suffix.lower())
        dim_str = f"{width}x{height} px" if width and height else "não determinadas sem decodificador gráfico"
        segment = (
            f"[Evidência de imagem: {path.name}]\n"
            f"Formato: {suffix.upper()}\n"
            f"Dimensões: {dim_str}\n"
            f"Tamanho: {size_bytes} bytes\n"
            f"SHA-256: {digest}\n"
            "Arquivo de imagem preservado integralmente; inspeção visual multimodal ou humana obrigatória."
        )
        warnings = [
            f"VISUAL_REVIEW_REQUIRED: arquivo de imagem ({path.name}) preservado no original; conteúdo visual requer visão da IA ou conferência humana."
        ]
        return [segment], warnings
    if kind == "audio_video":
        segment = (
            f"[Evidência de áudio/vídeo: {path.name}]\n"
            f"Formato: {suffix.upper()}\n"
            f"Tamanho: {size_bytes} bytes\n"
            f"SHA-256: {digest}\n"
            "Arquivo audiovisual preservado integralmente; transcrição auditável e conferência humana obrigatórias."
        )
        warnings = [
            f"AUDIO_TRANSCRIPTION_REQUIRED: arquivo de mídia ({path.name}) preservado no original; requer transcrição e conferência humana."
        ]
        return [segment], warnings
    raise ValueError(f"Arquivo {path.name} não é mídia autônoma suportada")
