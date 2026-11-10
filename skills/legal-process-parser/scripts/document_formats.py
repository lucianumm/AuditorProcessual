"""Extract supported text/OOXML without executing Office code or hiding loss.

Office units are logical segments, not physical PDF pages. Embedded media stays
an explicit visual limitation until the original is rendered and reviewed.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT_FORMATS = {".txt", ".md", ".csv", ".tsv", ".json", ".jsonl", ".xml", ".html", ".htm", ".log"}
OFFICE_FORMATS = {".docx", ".xlsx"}
MAX_EXPANDED_BYTES = 64 * 1024 * 1024
MAX_ENTRIES = 10000
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


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
    if suffix not in TEXT_FORMATS:
        raise ValueError(f"Formato {suffix or 'sem extensão'} não suportado no extrator local; preserve o original e converta para PDF/texto, ou use visão da IA para imagens. Nunca decodifique binário como texto.")
    with path.open("rb") as source:
        head = source.read(8192)
    unicode_bom = head.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff"))
    if (b"\x00" in head and not unicode_bom) or head.startswith((b"PK\x03\x04", b"\x89PNG", b"\xff\xd8", b"%PDF-", b"\xd0\xcf\x11\xe0")):
        raise ValueError("Conteúdo binário com extensão de texto; formato real precisa ser convertido")
    return "text"


def _xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    data = archive.read(name)
    xml_probe = data.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in xml_probe or b"<!ENTITY" in xml_probe:
        raise ValueError("XML Office com declaração de entidades não permitido")
    return ET.fromstring(data)


def _check_archive(archive: zipfile.ZipFile) -> list[str]:
    entries = archive.infolist()
    if len(entries) > MAX_ENTRIES or sum(i.file_size for i in entries) > MAX_EXPANDED_BYTES:
        raise ValueError("Office excede limite seguro de expansão; dividir/converter sem truncar")
    if any(i.flag_bits & 1 for i in entries):
        raise ValueError("Office criptografado: obtenha uma cópia acessível autorizada")
    names = [i.filename for i in entries]
    if len(set(names)) != len(names):
        raise ValueError("Office com nomes duplicados: não escolher silenciosamente uma versão")
    if any(n.lower().endswith("vbaproject.bin") for n in names):
        raise ValueError("Contêiner Office com macros não permitido")
    return names


def _word_text(element: ET.Element) -> str:
    values = []
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


def extract_office(path: Path) -> tuple[list[str], list[str]]:
    kind = inspect_format(path)
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
            def collect(container):
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
                    if cell.attrib.get("t") == "s":
                        try:
                            index = int(text)
                            if not 0 <= index < len(shared):
                                raise ValueError("índice fora da lista")
                            text = shared[index]
                        except (ValueError,IndexError) as error:
                            raise ValueError("Texto compartilhado de célula não resolvido") from error
                    elif cell.attrib.get("t") == "inlineStr":
                        text = "".join(n.text or "" for n in cell.iter(S + "t"))
                    formula = cell.find(S + "f")
                    if formula is not None:
                        lines.append(f"{cell.attrib.get('r')} = fórmula {formula.text}; valor armazenado: {text or '[AUSENTE]'}")
                        warnings.append("Fórmulas não executadas; valores armazenados podem estar desatualizados. Validar cálculos e formatação de datas/unidades.")
                    else:
                        lines.append(f"{cell.attrib.get('r')} = {text}")
            segments.append("\n".join(lines))
        return segments, list(dict.fromkeys(warnings))
