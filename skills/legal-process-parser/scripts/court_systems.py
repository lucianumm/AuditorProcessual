"""Multi-system Brazilian electronic court and administrative record stamps.

Supports PJe (1st/2nd degrees and TST), eproc, e-SAJ, PROJUDI, and SEI/NUP
without executing external links or discarding the preserved page text.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Sequence


NUMBER_PROCESS_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
NUP_PROCESS_RE = re.compile(r"\b\d{5}\.\d{6}/\d{4}-\d{2}\b")
COURT_PAGE_RE = re.compile(r"(?:fl\.?|folha|p[\u00e1a]g(?:ina)?\s+dos\s+autos)\s*[:.]?\s*(\d{1,5})", re.I)

DEFAULT_PIECE_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("Peti\u00e7\u00e3o Inicial", ("peti\u00e7\u00e3o inicial", "inicial")),
    ("Emenda \u00e0 Inicial", ("emenda", "emenda \u00e0 inicial")),
    ("Contesta\u00e7\u00e3o", ("contesta\u00e7\u00e3o", "defesa")),
    ("Reconven\u00e7\u00e3o", ("reconven\u00e7\u00e3o",)),
    ("R\u00e9plica", ("r\u00e9plica", "impugna\u00e7\u00e3o \u00e0 contesta\u00e7\u00e3o")),
    ("Manifesta\u00e7\u00e3o", ("manifesta\u00e7\u00e3o",)),
    ("Raz\u00f5es Finais", ("raz\u00f5es finais", "alega\u00e7\u00f5es finais")),
    ("Contrarraz\u00f5es", ("contrarraz\u00f5es",)),
    ("Embargos de Declara\u00e7\u00e3o", ("embargos de declara\u00e7\u00e3o", "embargos declarat\u00f3rios")),
    ("Recurso", ("recurso", "raz\u00f5es recursais")),
    ("Senten\u00e7a", ("senten\u00e7a",)),
    ("Ac\u00f3rd\u00e3o", ("ac\u00f3rd\u00e3o",)),
    ("Decis\u00e3o", ("decis\u00e3o", "decis\u00e3o monocr\u00e1tica")),
    ("Despacho", ("despacho",)),
    ("Certid\u00e3o", ("certid\u00e3o",)),
    ("Laudo/Per\u00edcia", ("laudo", "per\u00edcia")),
    ("Contrato", ("contrato",)),
    ("Procura\u00e7\u00e3o", ("procura\u00e7\u00e3o",)),
    ("Documento Financeiro", ("extrato", "holerite", "comprovante", "nota fiscal", "pix")),
    ("Documento M\u00e9dico", ("atestado", "prontu\u00e1rio", "laudo m\u00e9dico", "aso")),
    ("Documento", ("documento",)),
]

# --- 1. PJe (1º e 2º graus e TST) ---
PJE_SIGNATURE_RE = re.compile(
    r"(?:[Dd]ocumento assinado eletronicamente por|[Aa]ssinado eletronicamente por:?)\s[\s\S]{0,240}?"
    r"\d{2}/\d{2}/\d{4}[\s\S]{0,60}?-\s*([0-9a-f]{7})(?![0-9A-Za-z])"
)
PJE_TST_SIGNATURE_RE = re.compile(
    r"Firmado por assinatura digital em \d{2}/\d{2}/\d{4} pelo sistema AssineJus[\s\S]{0,220}?"
    r"(?:c[óo]digo[\s:]+([0-9A-Za-z._-]+))?",
    re.I,
)
PJE_SIGNER_1ST_RE = re.compile(
    r"[Dd]ocumento assinado eletronicamente por\s+([^,\n]+?)(?:,\s*[^,\n]+?)*,\s*em\s+\d{2}/\d{2}/\d{4}"
)
PJE_SIGNER_2ND_RE = re.compile(
    r"[Aa]ssinado eletronicamente por:?\s*([^\n-]+?)\s*-\s*\d{2}/\d{2}/\d{4}"
)
PJE_PAGE_ID_RE = re.compile(r"\bID\.?\s*([0-9a-f]{7})\s*-\s*P[áa]g\.\s*(\d{1,5})\b")
PJE_FLS_RE = re.compile(r"(?<![\w.])Fls\.\s*:\s*(\d{1,5})\b")
PJE_PROCESS_RE = re.compile(r"N[úu]mero do processo:\s*(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})\b")
PJE_STAMP_LINE_RE = re.compile(
    r"^(?:[Dd]ocumento assinado eletronicamente.*|[Aa]ssinado eletronicamente por.*|https?://\S*pje\S*.*"
    r"|Firmado por assinatura digital.*AssineJus.*|https?://\S*tst\.jus\.br\S*.*"
    r"|N[úu]mero do (?:documento|processo):.*|[0-9a-f]{7}|\d{1,5})$",
    re.I,
)
PJE_RAPPORTEUR_RE = re.compile(r"(?m)^\s*relatora?\s*:")
PJE_CLAIM_RE = re.compile(r"(?<!\w)(?:reclama\u00e7\u00e3o|reclamat\u00f3ria|a\u00e7\u00e3o) trabalhista(?!\w)")
PJE_MIN_CONTENT_CHARS = 20

# --- 2. eproc ---
EPROC_EVENT_RE = re.compile(
    r"\bEvento\s+(\d+)\s*[,/-]\s*([A-Za-z]{2,12}\s*\d*)\s*[,/-]\s*P[áa]gina\s+(\d{1,5})\b",
    re.I,
)
EPROC_PROCESS_RE = re.compile(
    r"\bProcesso\s+N[ºo°]\s*:?\s*(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})\b",
    re.I,
)
EPROC_SIGNER_RE = re.compile(
    r"(?:[Dd]ocumento\s+)?[Aa]ssinado eletronicamente por:?\s+([^\n,;]+?)"
    r"(?:\s*,\s*(?:em|conforme|Cargo)|\s+-\s+\d{2}/\d{2}/\d{4}|\n|$)"
)
VERIFIER_CRC_RE = re.compile(
    r"[Cc][óo]digo\s+verificador\s*:?\s*([0-9A-Za-z]+)"
    r"(?:[\s\S]{0,40}?[Cc][óo]digo\s+CRC\s*:?\s*([0-9A-Fa-f]+))?"
)
EPROC_STAMP_LINE_RE = re.compile(
    r"^(?:.*Evento\s+\d+\s*[,/-]\s*[A-Za-z]{2,12}\s*\d*\s*[,/-]\s*P[áa]gina\s+\d+.*"
    r"|Processo\s+N[ºo°]\s*:?\s*\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}.*"
    r"|(?:[Dd]ocumento\s+)?[Aa]ssinado eletronicamente por.*"
    r"|.*[Cc][óo]digo\s+verificador\s*:?\s*[0-9A-Za-z]+.*[Cc][óo]digo\s+CRC.*"
    r"|.*https?://\S*eproc\S*.*|\d{1,5})$",
    re.I,
)

# --- 3. e-SAJ ---
ESAJ_CONF_RE = re.compile(
    r"Para conferir o original,\s*acesse o site[\s\S]{0,280}?"
    r"informe o processo\s+(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})"
    r"(?:\s+e\s+c[óo]digo\s+([0-9A-Za-z]+))?\.?",
    re.I,
)
ESAJ_COPY_RE = re.compile(
    r"Este documento [ée] c[óo]pia do original,\s*assinado digitalmente por\s+([^,\n]+?)"
    r"(?:,\s*(?:protocolado|liberado nos autos)\s+em\s+\d{2}/\d{2}/\d{4}"
    r"(?:\s+[àa]s\s+\d{2}:\d{2}(?::\d{2})?)?(?:,\s*sob o n[úu]mero\s+[0-9A-Za-z]+)?\.?|\n|$)",
    re.I,
)
ESAJ_PROTOCOL_ID_RE = re.compile(r"sob o n[úu]mero\s+([0-9A-Za-z]{6,})", re.I)
ESAJ_RELEASED_RE = re.compile(
    r"\bLiberado nos autos em\s+\d{2}/\d{2}/\d{4}(?:\s+[àa]s\s+\d{2}:\d{2}(?::\d{2})?)?",
    re.I,
)
ESAJ_FLS_RE = re.compile(r"\bfls\.\s*(\d{1,6})\b", re.I)
ESAJ_STAMP_LINE_RE = re.compile(
    r"^(?:fls\.\s*\d{1,6}|Este documento [ée] c[óo]pia do original.*"
    r"|Para conferir o original,\s*acesse o site.*|.*informe o processo\s+\d{7}-\d{2}.*c[óo]digo.*"
    r"|Liberado nos autos em\s+\d{2}/\d{2}/\d{4}.*|.*https?://\S*esaj\S*.*|\d{1,5})$",
    re.I,
)

# --- 4. PROJUDI ---
PROJUDI_MOV_RE = re.compile(r"\b(?:Ref\.\s*)?Mov\.\s*(\d+(?:\.\d+)?)\b", re.I)
PROJUDI_PROCESS_RE = re.compile(
    r"\bProcesso\s*:\s*(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})\b",
    re.I,
)
PROJUDI_SIGNER_RE = re.compile(
    r"\bAssinado digitalmente por:?\s+([^\n,;]+?)(?:\s*,\s*(?:em|protocolado)|\s+em\s+\d{2}/\d{2}/\d{4}|\n|$)",
    re.I,
)
PROJUDI_STAMP_LINE_RE = re.compile(
    r"^(?:(?:Ref\.\s*)?Mov\.\s*\d+(?:\.\d+)?.*|Processo\s*:\s*\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}.*"
    r"|Assinado digitalmente por.*|.*https?://\S*projudi\S*.*|\d{1,5})$",
    re.I,
)

# --- 5. SEI ---
SEI_SIG_RE = re.compile(
    r"[Dd]ocumento assinado eletronicamente por\s+([^,\n]+?)(?:,\s*[^,\n]+?)*,\s*em\s+\d{2}/\d{2}/\d{4}"
    r"[\s\S]{0,420}?c[óo]digo\s+verificador\s+([0-9A-Za-z]+)\s+e\s+(?:o\s+)?c[óo]digo\s+CRC\s+([0-9A-Fa-f]+)",
    re.I,
)
SEI_PROCESS_STAMP_RE = re.compile(
    r"(?:Processo(?:\s+SEI)?|SEI|NUP)\s*(?:n[ºo°.]?|:)\s*(\d{5}\.\d{6}/\d{4}-\d{2})\b",
    re.I,
)
SEI_STAMP_LINE_RE = re.compile(
    r"^(?:[Dd]ocumento assinado eletronicamente por.*|A autenticidade (?:do|deste) documento pode ser conferida.*"
    r"|.*c[óo]digo\s+verificador\s+[0-9A-Za-z]+.*c[óo]digo\s+CRC\s+[0-9A-Fa-f]+.*"
    r"|(?:Processo(?:\s+SEI)?|SEI|NUP)\s*(?:n[ºo°.]?|:)\s*\d{5}\.\d{6}/\d{4}-\d{2}.*"
    r"|.*https?://\S*/sei/\S*.*|\d{1,5})$",
    re.I,
)


def _normalise_spaces(value: str) -> str:
    value = value.replace("\x00", "")
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"[ \t]+", " ", value).strip()


def _clean_signer(raw: str | None) -> str | None:
    if not raw:
        return None
    cleaned = _normalise_spaces(raw).strip(" -:,.;")
    return cleaned or None


def _extract_pje_signer(text: str) -> str | None:
    match_1st = PJE_SIGNER_1ST_RE.search(text)
    if match_1st:
        return _clean_signer(match_1st.group(1))
    match_2nd = PJE_SIGNER_2ND_RE.search(text)
    if match_2nd:
        return _clean_signer(match_2nd.group(1))
    return None


def pje_footer(text: str) -> dict[str, Any]:
    """Read the PJe signature footer: document id, page within it and court folio."""
    signature = PJE_SIGNATURE_RE.search(text)
    page_ids = PJE_PAGE_ID_RE.findall(text)
    folios = PJE_FLS_RE.findall(text)
    document_id = signature.group(1) if signature else (page_ids[-1][0] if page_ids else None)
    return {
        "document_id": document_id,
        "document_page": int(page_ids[-1][1]) if page_ids else None,
        "court_page": int(folios[-1]) if folios else None,
    }


def strip_pje_footer(text: str) -> str:
    """Return the page text without the PJe stamp; other text is returned unchanged."""
    if not (PJE_SIGNATURE_RE.search(text) or PJE_PAGE_ID_RE.search(text) or PJE_TST_SIGNATURE_RE.search(text)):
        return text
    content = PJE_SIGNATURE_RE.sub("\n", text)
    content = PJE_TST_SIGNATURE_RE.sub("\n", content)
    content = PJE_PAGE_ID_RE.sub("\n", content)
    content = PJE_FLS_RE.sub("\n", content)
    lines = [line for line in content.split("\n") if not PJE_STAMP_LINE_RE.match(line.strip())]
    content = "\n".join(lines).strip()
    if len(re.sub(r"\s", "", content)) < PJE_MIN_CONTENT_CHARS:
        return ""
    return content


def extract_court_stamp(text: str) -> dict[str, Any]:
    """Extract normalized stamp metadata across PJe, eproc, e-SAJ, PROJUDI, and SEI."""
    if not text:
        return {
            "system": None,
            "document_id": None,
            "document_page": None,
            "court_page": None,
            "process_number": None,
            "signer": None,
        }

    # 1. PJe (1º/2º graus e TST)
    if (
        PJE_SIGNATURE_RE.search(text)
        or PJE_PAGE_ID_RE.search(text)
        or PJE_TST_SIGNATURE_RE.search(text)
        or re.search(r"https?://\S*pje\S*", text, re.I)
    ):
        footer = pje_footer(text)
        proc = PJE_PROCESS_RE.search(text)
        tst = PJE_TST_SIGNATURE_RE.search(text)
        doc_id = footer["document_id"] or (tst.group(1) if tst and tst.group(1) else None)
        return {
            "system": "pje",
            "document_id": doc_id,
            "document_page": footer["document_page"],
            "court_page": footer["court_page"],
            "process_number": proc.group(1) if proc else None,
            "signer": _extract_pje_signer(text),
        }

    # 2. e-SAJ
    if (
        ESAJ_CONF_RE.search(text)
        or ESAJ_COPY_RE.search(text)
        or ESAJ_RELEASED_RE.search(text)
        or re.search(r"https?://\S*esaj\S*", text, re.I)
    ):
        conf = ESAJ_CONF_RE.search(text)
        copy_match = ESAJ_COPY_RE.search(text)
        proto_match = ESAJ_PROTOCOL_ID_RE.search(text)
        fls = ESAJ_FLS_RE.findall(text)
        doc_id = (conf.group(2) if conf and conf.group(2) else None) or (proto_match.group(1) if proto_match else None)
        return {
            "system": "esaj",
            "document_id": doc_id,
            "document_page": None,
            "court_page": int(fls[-1]) if fls else None,
            "process_number": conf.group(1) if conf else None,
            "signer": _clean_signer(copy_match.group(1)) if copy_match else None,
        }

    # 3. eproc
    if (
        EPROC_EVENT_RE.search(text)
        or re.search(r"https?://\S*eproc\S*", text, re.I)
        or (EPROC_PROCESS_RE.search(text) and (EPROC_SIGNER_RE.search(text) or VERIFIER_CRC_RE.search(text)))
    ):
        ev = EPROC_EVENT_RE.search(text)
        proc = EPROC_PROCESS_RE.search(text)
        sig = EPROC_SIGNER_RE.search(text)
        crc = VERIFIER_CRC_RE.search(text)
        doc_id = (
            f"E{ev.group(1)}-{re.sub(r'\s+', '', ev.group(2)).upper()}"
            if ev
            else (crc.group(1) if crc else None)
        )
        return {
            "system": "eproc",
            "document_id": doc_id,
            "document_page": int(ev.group(3)) if ev else None,
            "court_page": None,
            "process_number": proc.group(1) if proc else None,
            "signer": _clean_signer(sig.group(1)) if sig else None,
        }

    # 4. PROJUDI
    if (
        PROJUDI_MOV_RE.search(text)
        or re.search(r"https?://\S*projudi\S*", text, re.I)
        or (PROJUDI_PROCESS_RE.search(text) and PROJUDI_SIGNER_RE.search(text))
    ):
        mov = PROJUDI_MOV_RE.search(text)
        proc = PROJUDI_PROCESS_RE.search(text)
        sig = PROJUDI_SIGNER_RE.search(text)
        return {
            "system": "projudi",
            "document_id": f"Mov.{mov.group(1)}" if mov else None,
            "document_page": None,
            "court_page": None,
            "process_number": proc.group(1) if proc else None,
            "signer": _clean_signer(sig.group(1)) if sig else None,
        }

    # 5. SEI (electronic administrative records)
    if (
        SEI_SIG_RE.search(text)
        or re.search(r"https?://\S*/sei/\S*", text, re.I)
        or (VERIFIER_CRC_RE.search(text) and NUP_PROCESS_RE.search(text))
    ):
        sei_sig = SEI_SIG_RE.search(text)
        crc = VERIFIER_CRC_RE.search(text)
        nup_stamp = SEI_PROCESS_STAMP_RE.search(text)
        nup_any = NUP_PROCESS_RE.search(text)
        return {
            "system": "sei",
            "document_id": sei_sig.group(2) if sei_sig else (crc.group(1) if crc else None),
            "document_page": None,
            "court_page": None,
            "process_number": nup_stamp.group(1) if nup_stamp else (nup_any.group(0) if nup_any else None),
            "signer": _clean_signer(sei_sig.group(1)) if sei_sig else None,
        }

    return {
        "system": None,
        "document_id": None,
        "document_page": None,
        "court_page": None,
        "process_number": None,
        "signer": None,
    }


def strip_court_stamps(text: str) -> str:
    """Strip PJe, eproc, e-SAJ, PROJUDI, or SEI signature/stamp boilerplate.

    Text without a detected court/administrative stamp is returned untouched.
    When a stamp was present and fewer than 20 non-whitespace characters remain,
    returns ``""`` so scanned pages carrying only native stamps trigger OCR/vision.
    """
    stamp = extract_court_stamp(text)
    system = stamp["system"]
    if system is None:
        return text
    if system == "pje":
        return strip_pje_footer(text)

    content = text
    if system == "esaj":
        content = ESAJ_CONF_RE.sub("\n", content)
        content = ESAJ_COPY_RE.sub("\n", content)
        content = ESAJ_RELEASED_RE.sub("\n", content)
        content = ESAJ_FLS_RE.sub("\n", content)
        line_re = ESAJ_STAMP_LINE_RE
    elif system == "eproc":
        content = EPROC_EVENT_RE.sub("\n", content)
        content = EPROC_PROCESS_RE.sub("\n", content)
        content = VERIFIER_CRC_RE.sub("\n", content)
        line_re = EPROC_STAMP_LINE_RE
    elif system == "projudi":
        content = PROJUDI_MOV_RE.sub("\n", content)
        content = PROJUDI_PROCESS_RE.sub("\n", content)
        line_re = PROJUDI_STAMP_LINE_RE
    else:  # sei
        content = SEI_SIG_RE.sub("\n", content)
        content = VERIFIER_CRC_RE.sub("\n", content)
        content = SEI_PROCESS_STAMP_RE.sub("\n", content)
        line_re = SEI_STAMP_LINE_RE

    lines = [line for line in content.split("\n") if not line_re.match(line.strip())]
    content = "\n".join(lines).strip()
    if len(re.sub(r"\s", "", content)) < PJE_MIN_CONTENT_CHARS:
        return ""
    return content


def _collect_other_stamped_numbers(text: str) -> dict[str, int]:
    """Collect process numbers explicitly anchored inside non-PJe court/SEI stamps."""
    stamped: dict[str, int] = {}

    def _add(num: str) -> None:
        stamped[num] = stamped.get(num, 0) + 1

    for match in ESAJ_CONF_RE.finditer(text):
        _add(match.group(1))
    if EPROC_EVENT_RE.search(text) or re.search(r"https?://\S*eproc\S*", text, re.I) or EPROC_SIGNER_RE.search(text) or VERIFIER_CRC_RE.search(text):
        for num in EPROC_PROCESS_RE.findall(text):
            _add(num)
    elif EPROC_PROCESS_RE.search(text):
        for num in EPROC_PROCESS_RE.findall(text):
            _add(num)
    if PROJUDI_MOV_RE.search(text) or re.search(r"https?://\S*projudi\S*", text, re.I) or PROJUDI_SIGNER_RE.search(text):
        for num in PROJUDI_PROCESS_RE.findall(text):
            _add(num)
    for num in SEI_PROCESS_STAMP_RE.findall(text):
        _add(num)
    if SEI_SIG_RE.search(text) or re.search(r"https?://\S*/sei/\S*", text, re.I):
        for num in NUP_PROCESS_RE.findall(text):
            _add(num)
    return stamped


def identify_process_number(text: str) -> dict[str, Any]:
    """Pick the case number of these records, not a precedent cited in them.

    Priority:
    1. PJe footer (``Número do processo: ...``) -> ``criterio="pje_rodape"``
    2. Other stamped system numbers (eproc, e-SAJ, PROJUDI, SEI) -> ``criterio="carimbo_sistema"``
    3. Most frequent CNJ number (or NUP if no CNJ) -> ``criterio="mais_frequente"``
    """
    cnj_counts: dict[str, int] = {}
    for number in NUMBER_PROCESS_RE.findall(text or ""):
        cnj_counts[number] = cnj_counts.get(number, 0) + 1

    nup_counts: dict[str, int] = {}
    for number in NUP_PROCESS_RE.findall(text or ""):
        nup_counts[number] = nup_counts.get(number, 0) + 1

    all_counts: dict[str, int] = {**cnj_counts}
    for number, count in nup_counts.items():
        all_counts[number] = count

    pje_stamped: dict[str, int] = {}
    for number in PJE_PROCESS_RE.findall(text or ""):
        pje_stamped[number] = pje_stamped.get(number, 0) + 1

    other_stamped = _collect_other_stamped_numbers(text or "")
    order_list = list(all_counts)

    def _rank_key(pool: dict[str, int], number: str) -> tuple[int, int]:
        idx = order_list.index(number) if number in order_list else len(order_list)
        return (pool[number], -idx)

    if pje_stamped:
        chosen = max(pje_stamped, key=lambda n: _rank_key(pje_stamped, n))
        criterion = "pje_rodape"
    elif other_stamped:
        chosen = max(other_stamped, key=lambda n: _rank_key(other_stamped, n))
        criterion = "carimbo_sistema"
    elif cnj_counts:
        cnj_order = list(cnj_counts)
        chosen = max(cnj_counts, key=lambda n: (cnj_counts[n], -cnj_order.index(n)))
        criterion = "mais_frequente"
    elif nup_counts:
        nup_order = list(nup_counts)
        chosen = max(nup_counts, key=lambda n: (nup_counts[n], -nup_order.index(n)))
        criterion = "mais_frequente"
    else:
        return {"numero": None, "criterio": None, "ocorrencias": 0, "citados": []}

    cited = [
        {"numero": number, "ocorrencias": count}
        for number, count in all_counts.items()
        if number != chosen
    ]
    return {
        "numero": chosen,
        "criterio": criterion,
        "ocorrencias": all_counts.get(chosen, 1),
        "citados": cited,
    }


def detect_piece_title(
    text: str,
    piece_patterns: Sequence[tuple[str, tuple[str, ...]]] | None = None,
) -> str:
    """Label an electronic document by the earliest whole-word piece name in its opening text."""
    patterns = list(piece_patterns) if piece_patterns is not None else DEFAULT_PIECE_PATTERNS
    sample = _normalise_spaces((text or "")[:1200]).lower()
    if not sample:
        return "N\u00e3o identificado"
    if PJE_RAPPORTEUR_RE.search(sample):
        return "Ac\u00f3rd\u00e3o"

    # Ensure "embargos de declaração" is always available even if caller passed a custom list without it.
    has_embargos = any("embargos" in term for _, terms in patterns for term in terms)
    effective_patterns = list(patterns)
    if not has_embargos:
        effective_patterns.insert(0, ("Embargos de Declara\u00e7\u00e3o", ("embargos de declara\u00e7\u00e3o", "embargos declarat\u00f3rios")))

    best: tuple[int, int, str] | None = None
    for order, (label, terms) in enumerate(effective_patterns):
        for term in terms:
            match = re.search(r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)", sample)
            if match and (best is None or (match.start(), order) < best[:2]):
                best = (match.start(), order, label)
    if best:
        return best[2]
    if PJE_CLAIM_RE.search(sample):
        return "Peti\u00e7\u00e3o Inicial"
    return "N\u00e3o identificado"
