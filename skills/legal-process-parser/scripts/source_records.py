"""Inspect official-source records without mistaking a declaration for attestation.

HTTP receipts retain the downloaded bytes for integrity checks. Browser records
can preserve what a host agent saw, but a JSON file cannot prove the tool was
actually invoked; their evidence level is always explicitly unattested.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

try:
    from .case_memory import atomic_json, identity
except ImportError:
    from case_memory import atomic_json, identity


def official_url(url: str) -> bool:
    """Accept HTTPS URLs under Brazilian official host suffixes only."""
    if not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    return (
        parsed.scheme == "https"
        and port in {None, 443}
        and bool(host)
        and not parsed.username
        and not parsed.password
        and any(host.endswith(suffix) for suffix in (".gov.br", ".jus.br", ".leg.br", ".mp.br"))
    )


def _valid_date(value: object) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_id(record: dict, key: str) -> bool:
    identifier = record.get(key)
    return isinstance(identifier, str) and re.fullmatch(r"[0-9a-f]{64}", identifier) is not None and identity({k: v for k, v in record.items() if k != key}) == identifier


def record_browser_observation(
    output: Path,
    *,
    url: str,
    accessed_on: str,
    text: str,
    context: str,
    tool_reference: str,
    observed_by: str,
    coverage_scope: str = "excerpt",
    locator: str = "",
) -> dict:
    """Record a browser observation supplied by the host, without attesting it.

    This function does not browse. The caller must use the actual host tool and
    supply its real reference. An arbitrary string remains a claim, not proof.
    """
    record = {
        "method": "browser_observation",
        "evidence_level": "self_recorded_unverified",
        "url": url,
        "accessed_on": accessed_on,
        "text": text,
        "context": context,
        "tool_reference": tool_reference,
        "observed_by": observed_by,
        "coverage_scope": coverage_scope,
        "locator": locator,
    }
    errors = _browser_fields(record)
    if errors:
        raise ValueError("; ".join(errors))
    record["source_record_id"] = identity(record)
    atomic_json(Path(output) / "research_sources" / f"{record['source_record_id']}.json", record)
    return record


def record_unavailable_source(
    output: Path,
    *,
    url: str,
    accessed_on: str,
    reason: str,
    attempt_reference: str,
    issue_ids: list[str],
) -> dict:
    """Preserve a failed lookup as a limitation, never as a legal authority."""
    record = {
        "method": "source_unavailable",
        "status": "unavailable",
        "url": url,
        "accessed_on": accessed_on,
        "reason": reason,
        "attempt_reference": attempt_reference,
        "issue_ids": issue_ids,
    }
    if not official_url(url) or not _valid_date(accessed_on) or not isinstance(reason, str) or not reason.strip() or not isinstance(attempt_reference, str) or not attempt_reference.strip() or not isinstance(issue_ids, list) or not issue_ids or any(not isinstance(i, str) or not i for i in issue_ids):
        raise ValueError("Fonte inacessível: URL, data, motivo, tentativa e questões afetadas são necessários")
    record["source_record_id"] = identity(record)
    atomic_json(Path(output) / "research_sources" / f"{record['source_record_id']}.json", record)
    return record


def _browser_fields(record: dict) -> list[str]:
    errors = []
    if not official_url(record.get("url")):
        errors.append("URL oficial HTTPS necessária")
    if not _valid_date(record.get("accessed_on")):
        errors.append("data de acesso ISO inválida")
    for field in ("text", "context", "tool_reference", "observed_by"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} ausente")
    if record.get("coverage_scope") not in {"excerpt", "full_document"}:
        errors.append("coverage_scope inválido")
    if record.get("evidence_level") != "self_recorded_unverified":
        errors.append("observação de navegador não pode declarar atestado independente")
    return errors


def inspect_source_record(record: dict, output: Path, norm: dict | None = None) -> dict:
    """Return structural errors, honest evidence level and any caveats."""
    result = {"errors": [], "warnings": [], "evidence_level": "unavailable", "method": "unknown"}
    if not isinstance(record, dict):
        result["errors"].append("registro de fonte inválido")
        return result
    method = record.get("method")
    result["method"] = method if isinstance(method, str) else "unknown"
    if method == "official_http_capture":
        result["evidence_level"] = "verified_http"  # Byte integrity and recorded URL, not legal applicability.
        if not _record_id(record, "capture_id"):
            result["errors"].append("identidade da captura HTTP inválida")
        if not official_url(record.get("url")) or record.get("requested_url") and not official_url(record.get("requested_url")):
            result["errors"].append("URL oficial HTTPS inválida")
        if not _valid_date(record.get("accessed_on")):
            result["errors"].append("data da captura inválida")
        text = record.get("text")
        if not isinstance(text, str) or not text.strip() or record.get("text_hash") != _sha256(text.encode("utf-8")):
            result["errors"].append("texto ou hash da captura inválido")
        raw_hash = record.get("raw_content_hash")
        safe_id = record.get("capture_id") if _record_id(record, "capture_id") else None
        raw_path = Path(output) / "research_sources" / f"{safe_id}.source" if safe_id else None
        if not isinstance(raw_hash, str) or raw_path is None or not raw_path.is_file() or _sha256_file(raw_path) != raw_hash:
            result["errors"].append("resposta oficial bruta ausente ou alterada")
        if not result["errors"]:
            result["warnings"].append("Integridade e URL registradas; aplicabilidade jurídica depende da análise da questão.")
    elif method == "browser_observation":
        result["evidence_level"] = "self_recorded_unverified"
        result["errors"].extend(_browser_fields(record))
        if not _record_id(record, "source_record_id"):
            result["errors"].append("identidade da observação inválida")
        result["warnings"].append("Observação declarada pela IA; o arquivo não atesta uma chamada real ao navegador nem o texto integral da fonte.")
    elif method == "source_unavailable":
        result["evidence_level"] = "unavailable"
        if not _record_id(record, "source_record_id"):
            result["errors"].append("identidade da tentativa inválida")
        if not official_url(record.get("url")) or not _valid_date(record.get("accessed_on")) or not record.get("reason") or not record.get("attempt_reference") or not record.get("issue_ids"):
            result["errors"].append("tentativa de fonte inacessível incompleta")
        result["warnings"].append("Fonte inacessível; não pode sustentar norma como verificada.")
    else:
        result["errors"].append("método de registro de fonte desconhecido")
    if norm:
        if record.get("url") != norm.get("url") or record.get("accessed_on") != norm.get("accessed_on") or record.get("text") != norm.get("official_text"):
            result["errors"].append("fonte diverge da norma registrada")
        quote = norm.get("quote")
        if not isinstance(quote, str) or not quote.strip() or quote not in str(record.get("text", "")):
            result["errors"].append("citação normativa ausente do texto observado")
        if method == "source_unavailable":
            result["errors"].append("fonte inacessível não sustenta norma")
    if result["errors"]:
        result["evidence_level"] = "invalid"
    return result


def inspect_norm_source(norm: dict, output: Path) -> dict:
    """Inspect the source linked by one norm; never assume that a record proves use."""
    result = {"errors": [], "warnings": [], "evidence_level": "unavailable", "method": "unknown"}
    if norm.get("capture_id") and norm.get("source_record_id"):
        result["errors"].append("norma contém duas origens incompatíveis")
        return result
    identifier = norm.get("capture_id") or norm.get("source_record_id")
    if not isinstance(identifier, str) or len(identifier) != 64 or any(c not in "0123456789abcdef" for c in identifier):
        result["errors"].append("captura ou observação oficial ausente")
        return result
    path = Path(output) / "research_sources" / f"{identifier}.json"
    if not path.is_file():
        result["errors"].append("registro da fonte oficial não encontrado")
        return result
    try:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError):
        result["errors"].append("registro da fonte oficial ilegível")
        return result
    result = inspect_source_record(record, output, norm)
    expected_field = "capture_id" if result["method"] == "official_http_capture" else "source_record_id"
    if record.get(expected_field) != identifier or bool(norm.get("capture_id")) != (result["method"] == "official_http_capture"):
        result["errors"].append("identificador ou método da fonte diverge da norma")
        result["evidence_level"] = "invalid"
    return result
