"""CNJ single-number validation (Res. CNJ 65/2008), NUP parsing, and legal domain routing."""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence


LEGAL_PROFILE_PATH = Path(__file__).resolve().parent.parent / "references" / "legal_domain_profiles.json"

# Aceita a forma abreviada sem zeros à esquerda usada pelo TST ("RR-713-03.2010.5.04.0029").
CNJ_NUMBER_RE = re.compile(r"(?<!\d)(\d{1,7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})(?!\d)")
# Número Único de Protocolo administrativo federal/estadual (NNNNN.NNNNNN/AAAA-DD).
NUP_NUMBER_RE = re.compile(r"(?<!\d)(\d{5})\.(\d{6})/(\d{4})-(\d{2})(?!\d)")

# Segmento "J" do número único (Res. CNJ 65/2008).
CNJ_SEGMENTS = {
    "1": "Supremo Tribunal Federal",
    "2": "Conselho Nacional de Justiça",
    "3": "Superior Tribunal de Justiça",
    "4": "Justiça Federal",
    "5": "Justiça do Trabalho",
    "6": "Justiça Eleitoral",
    "7": "Justiça Militar da União",
    "8": "Justiça dos Estados e do Distrito Federal",
    "9": "Justiça Militar Estadual",
}

# Código "TR" da Justiça Estadual, Eleitoral e Militar Estadual: unidades da Federação em ordem alfabética.
CNJ_UF = {
    "01": "AC", "02": "AL", "03": "AP", "04": "AM", "05": "BA", "06": "CE", "07": "DF", "08": "ES", "09": "GO",
    "10": "MA", "11": "MT", "12": "MS", "13": "MG", "14": "PA", "15": "PB", "16": "PR", "17": "PE", "18": "PI",
    "19": "RJ", "20": "RN", "21": "RS", "22": "RO", "23": "RR", "24": "SC", "25": "SE", "26": "SP", "27": "TO",
}


def _normalise_spaces(value: str) -> str:
    value = value.replace("\x00", "")
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"[ \t]+", " ", value).strip()


def _fold_legal_text(value: str) -> str:
    value = unicodedata.normalize("NFD", value or "")
    return "".join(char for char in value if unicodedata.category(char) != "Mn").lower()


@lru_cache(maxsize=1)
def load_legal_domain_profiles() -> dict[str, Any]:
    try:
        payload = json.loads(LEGAL_PROFILE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        payload = {"schema_version": "fallback", "default_domain": "processual", "domains": []}
    domains = payload.get("domains") if isinstance(payload, dict) else None
    payload["domains"] = domains if isinstance(domains, list) else []
    payload["by_key"] = {
        item.get("key"): item
        for item in payload["domains"]
        if isinstance(item, dict) and item.get("key")
    }
    return payload


def _domain_source_text(pages: Sequence[Any]) -> str:
    chunks: list[str] = []
    for page in pages:
        chunks.append(getattr(page, "text", "") or "")
        for visual in getattr(page, "visuals", None) or []:
            chunks.extend([
                str(visual.get("semantic_description", "")),
                str(visual.get("visible_text", "")),
                str(visual.get("ocr_text", "")),
            ])
    return "\n".join(chunks)


def cnj_check_digits(sequence: str, year: str, segment: str, court: str, origin: str) -> str:
    """Dígitos verificadores pelo módulo 97 (ISO 7064), como no Anexo VIII da Res. CNJ 65/2008."""
    remainder = int(sequence) % 97
    remainder = int(f"{remainder}{year}{segment}{court}") % 97
    remainder = int(f"{remainder}{origin}00") % 97
    return f"{98 - remainder:02d}"


def _cnj_court(segment: str, court: str) -> str:
    if segment in {"1", "2", "3"}:
        return CNJ_SEGMENTS[segment]
    if court == "00":
        return {
            "4": "Conselho da Justiça Federal",
            "5": "Tribunal Superior do Trabalho",
            "6": "Tribunal Superior Eleitoral",
            "7": "Superior Tribunal Militar",
        }.get(segment, "Tribunal não identificado")
    if segment == "4":
        return f"Tribunal Regional Federal da {int(court)}ª Região"
    if segment == "5":
        return f"Tribunal Regional do Trabalho da {int(court)}ª Região"
    if segment == "6" and court in CNJ_UF:
        return f"Tribunal Regional Eleitoral ({CNJ_UF[court]})"
    if segment == "8" and court in CNJ_UF:
        return f"Tribunal de Justiça ({CNJ_UF[court]})"
    if segment == "9" and court in CNJ_UF:
        return f"Tribunal de Justiça Militar ({CNJ_UF[court]})"
    if segment == "7":
        return f"Justiça Militar da União — {int(court)}ª Circunscrição"
    return "Tribunal não identificado"


def parse_cnj_numbers(text: str) -> list[dict[str, Any]]:
    """Números únicos CNJ no texto, com segmento, tribunal e conferência do dígito verificador."""
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in CNJ_NUMBER_RE.finditer(text or ""):
        sequence, digits, year, segment, court, origin = match.groups()
        sequence = sequence.zfill(7)
        number = f"{sequence}-{digits}.{year}.{segment}.{court}.{origin}"
        if number in seen:
            continue
        seen.add(number)
        found.append({
            "number": number,
            "segment": segment,
            "justice": CNJ_SEGMENTS.get(segment, "Segmento desconhecido"),
            "court_code": court,
            "court": _cnj_court(segment, court),
            "origin": origin,
            "year": year,
            "check_digits_valid": cnj_check_digits(sequence, year, segment, court, origin) == digits,
        })
    return found


def nup_check_digits(unit_code: str, sequence: str, year: str) -> str:
    """Dígitos verificadores módulo 11 do NUP federal (Portaria Interministerial nº 1.677/2015)."""
    base = f"{unit_code.zfill(5)}{sequence.zfill(6)}{year.zfill(4)}"
    total1 = sum(int(ch) * weight for ch, weight in zip(base, range(16, 1, -1)))
    rem1 = 11 - (total1 % 11)
    dv1 = rem1 - 10 if rem1 >= 10 else rem1
    base2 = f"{base}{dv1}"
    total2 = sum(int(ch) * weight for ch, weight in zip(base2, range(17, 1, -1)))
    rem2 = 11 - (total2 % 11)
    dv2 = rem2 - 10 if rem2 >= 10 else rem2
    return f"{dv1}{dv2}"


def parse_nup_numbers(text: str) -> list[dict[str, Any]]:
    """Números Únicos de Protocolo (SEI / processos administrativos) localizados no texto."""
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in NUP_NUMBER_RE.finditer(text or ""):
        unit_code, sequence, year, digits = match.groups()
        number = f"{unit_code}.{sequence}/{year}-{digits}"
        if number in seen:
            continue
        seen.add(number)
        found.append({
            "number": number,
            "unit_code": unit_code,
            "sequence": sequence,
            "year": year,
            "check_digits": digits,
            "check_digits_valid": nup_check_digits(unit_code, sequence, year) == digits,
        })
    return found


@lru_cache(maxsize=4096)
def _term_pattern(term: str) -> re.Pattern[str]:
    """Termo dobrado com limite de palavra: 'adi' não casa com 'adicional', nem 'reu' com 'reunião'."""
    body = r"\s+".join(re.escape(part) for part in _fold_legal_text(term).split())
    return re.compile(r"(?<![a-z0-9])" + body + r"(?![a-z0-9])")


def _strip_noise(folded: str, profiles: dict[str, Any]) -> str:
    """Remove qualificação e endereço (estado civil, município de residência) antes da contagem."""
    for pattern in profiles.get("noise_patterns", []):
        try:
            folded = re.sub(pattern, " ", folded)
        except re.error:
            continue
    return folded


def classify_legal_domain(pages: Sequence[Any]) -> dict[str, Any]:
    profiles = load_legal_domain_profiles()
    source_text = _domain_source_text(pages)
    folded = _strip_noise(_fold_legal_text(source_text), profiles)
    page_folded = [(page, _strip_noise(_fold_legal_text(page.text), profiles)) for page in pages]
    cnj_numbers = parse_cnj_numbers(source_text)
    nup_numbers = parse_nup_numbers(source_text)
    segment_rules = profiles.get("justice_segments", {})
    scores: list[dict[str, Any]] = []
    for profile in profiles.get("domains", []):
        key = profile.get("key")
        if not key:
            continue
        score = 0
        evidence: list[dict[str, Any]] = []
        for pattern in profile.get("patterns", []):
            weight = int(pattern.get("weight", 1))
            for term in pattern.get("terms", []):
                regex = _term_pattern(str(term))
                occurrences = len(regex.findall(folded)) if str(term).strip() else 0
                if not occurrences:
                    continue
                score += weight * min(occurrences, 3)
                for page, folded_page in page_folded:
                    if not regex.search(folded_page):
                        continue
                    snippet = _normalise_spaces(page.text).replace("|", "\\|")[:260]
                    evidence.append({
                        "term": term,
                        "weight": weight,
                        "occurrences": occurrences,
                        "source": {"pdf_page": page.pdf_page, "document_id": page.document_id, "snippet": snippet},
                    })
                    break
        # O segmento do número único é sinal forte, mas não substitui a leitura do objeto do pedido.
        for item in cnj_numbers:
            rule = segment_rules.get(item["segment"])
            if rule and rule.get("domain") == key:
                weight = int(rule.get("weight", 0)) if item["check_digits_valid"] else int(rule.get("weight", 0)) // 2
                score += weight
                holder = next(
                    (page for page in pages if any(found["number"] == item["number"] for found in parse_cnj_numbers(page.text))),
                    None,
                )
                source = {
                    "pdf_page": holder.pdf_page if holder else None,
                    "document_id": holder.document_id if holder else "",
                    "snippet": item["justice"] + " — " + item["court"] + ("" if item["check_digits_valid"] else " (dígito verificador divergente)"),
                    "cnj": item,
                }
                evidence.insert(0, {"term": "número CNJ " + item["number"], "weight": weight, "occurrences": 1, "source": source})
                break
        scores.append({
            "key": key,
            "label": profile.get("label", key),
            "score": score,
            "evidence": evidence[:12],
        })

    specialized = [item for item in scores if item["key"] != profiles.get("default_domain")]
    specialized.sort(key=lambda item: (-item["score"], item["label"]))
    fallback = next(
        (item for item in scores if item["key"] == profiles.get("default_domain")),
        {"key": "processual", "label": "Direito Processual (área a confirmar)", "score": 0, "evidence": []},
    )
    if specialized and specialized[0]["score"] >= 4:
        top = specialized[0]
        competitors = specialized[1:]
    elif fallback["score"] >= 4:
        top = fallback
        competitors = specialized
    else:
        top = specialized[0] if specialized else fallback
        competitors = specialized[1:] if specialized else []
    second_score = competitors[0]["score"] if competitors else 0
    margin = top["score"] - second_score
    identified = top["score"] >= 4
    if top["key"] == "processual" and top["score"] < 4:
        identified = False
    confidence = "high" if identified and top["score"] >= 12 and margin >= 4 else ("medium" if identified else "low")
    label = top["label"] if identified else "Não identificado nos autos"
    candidates = [item for item in ([top] + competitors) if item["score"] > 0][:5]
    if top["score"] == 0 and fallback["score"] > 0:
        candidates = [fallback]
    profile = profiles.get("by_key", {}).get(top["key"], profiles.get("by_key", {}).get("processual", {}))
    return {
        "primary_key": top["key"] if identified else None,
        "label": label,
        "confidence": confidence,
        "score": top["score"],
        "margin_to_next": margin,
        "ambiguous": identified and margin < 2,
        "candidates": candidates,
        "profile": profile,
        "source_policy": profiles.get("verification_policy", {}),
        "pages_considered": len(pages),
        "cnj_numbers": cnj_numbers,
        "nup_numbers": nup_numbers,
    }
