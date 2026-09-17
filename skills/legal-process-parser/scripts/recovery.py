"""Record extraction gaps and bounded, observable recovery work.

This module schedules actions for the host agent. It never claims that OCR, visual
inspection, or legal analysis happened merely because an action was queued.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Sequence

try:
    from .helpers import Page, now_utc
except ImportError:  # direct execution
    from helpers import Page, now_utc


MAX_DISTINCT_ATTEMPTS = 3


def _attempt(page: Page, action: str, outcome: str, evidence: str) -> dict[str, Any]:
    return {
        "id": f"ATT-{page.pdf_page:05d}-{action.upper()}",
        "target_ids": [f"{page.source_sha256}:{page.pdf_page}"],
        "source_sha256": page.source_sha256,
        "pdf_page": page.pdf_page,
        "action": action,
        "outcome": outcome,
        "evidence": evidence,
    }


def _finding(page: Page, code: str, description: str, impact: str, action: str,
             attempt_ids: list[str], *, severity: str = "material",
             effect: str = "qualifies_conclusion") -> dict[str, Any]:
    return {
        "id": f"EXT-{page.pdf_page:05d}-{code}",
        "code": code,
        "category": "coverage",
        "severity": severity,
        "status": "open",
        "scope": "page",
        "target_ids": [f"{page.source_sha256}:{page.pdf_page}"],
        "description": description,
        "impact": impact,
        "delivery_effect": effect,
        "required_action": action,
        "attempt_ids": attempt_ids,
        "resolution": None,
        "source_sha256": page.source_sha256,
        "pdf_page": page.pdf_page,
    }


def build_recovery_report(pages: Sequence[Page], source_sha256: str,
                          extraction_warnings: Sequence[str] = (),
                          render_warnings: Sequence[str] = ()) -> dict[str, Any]:
    """Build an issue-scoped queue from observed states, without retrying by guesswork."""
    findings: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    queue: list[dict[str, Any]] = []
    for page in pages:
        text = page.text.strip()
        render = page.render or {}
        vision = page.vision or {}
        ocr = page.ocr or {}
        page_attempts = [_attempt(page, "extract_text", "text_observed" if text else "no_text_observed",
                                  "pages.jsonl: text/source/quality")]
        if ocr.get("used"):
            page_attempts.append(_attempt(page, "ocr", "text_observed", "pages.jsonl: ocr.used=true"))
        if render.get("validated"):
            page_attempts.append(_attempt(page, "render_page", "render_validated", str(render.get("sha256") or render.get("relative_path") or "pages.jsonl: render.validated=true")))
        if vision.get("semantic_checked"):
            page_attempts.append(_attempt(page, "review_page_vision", "review_recorded", str(vision.get("render_sha256") or "pages.jsonl: vision.semantic_checked=true")))
        attempts.extend(page_attempts)
        attempt_ids = [item["id"] for item in page_attempts]
        page_findings: list[tuple[dict[str, Any], str, str]] = []
        outcome = vision.get("outcome")
        confirmed_nontext = page.status == "COMPLETE" and outcome in {"blank", "image_only"}

        if not text and not confirmed_nontext:
            if outcome == "unreadable":
                finding = _finding(page, "PAGE_UNREADABLE", "A página foi marcada como ilegível após revisão visual.",
                                   "Seu conteúdo não pode sustentar ou afastar fatos com segurança.",
                                   "Rever a imagem em maior resolução e registrar a limitação que permanecer.",
                                   attempt_ids, effect="blocks_delivery")
                page_findings.append((finding, "inspect_page_crop", "vision"))
            else:
                finding = _finding(page, "PAGE_CONTENT_UNKNOWN", "Nenhum texto útil ou conteúdo não textual confirmado foi registrado.",
                                   "A cobertura integral do documento ainda não é demonstrável.",
                                   "Aplicar OCR se disponível; depois inspecionar a página renderizada inteira.",
                                   attempt_ids, effect="blocks_delivery")
                page_findings.append((finding, "ocr_or_inspect_page", "ocr_or_vision"))
        if render.get("required") and not render.get("validated"):
            finding = _finding(page, "PAGE_RENDER_MISSING", "A renderização da página não foi validada.",
                               "Elementos visuais podem não estar representados.",
                               "Renderizar esta página com uma ferramenta disponível e conferir o arquivo gerado.",
                               attempt_ids, effect="blocks_delivery")
            page_findings.append((finding, "render_page", "pdf_render"))
        if vision.get("required") and not vision.get("semantic_checked"):
            finding = _finding(page, "PAGE_VISION_PENDING", "Não há revisão semântica da página inteira.",
                               "A leitura visual necessária à cobertura integral permanece pendente.",
                               "Inspecionar a página renderizada e registrar descrição vinculada à fonte e à renderização.",
                               attempt_ids, effect="blocks_delivery")
            page_findings.append((finding, "inspect_full_page", "vision"))
        if page.status == "COMPLETE_WITH_LIMITATION":
            finding = _finding(page, "PAGE_VISUAL_LIMITATION", "A revisão visual registrou uma limitação.",
                               "Conclusões dependentes desta página devem considerar a limitação descrita.",
                               "Examinar o trecho afetado ou justificar a limitação remanescente.",
                               attempt_ids)
            page_findings.append((finding, "inspect_page_crop", "vision"))
        for finding, action, capability in page_findings:
            findings.append(finding)
            queue.append({
                "finding_id": finding["id"],
                "action": action,
                "requires_capability": capability,
                "source_sha256": source_sha256,
                "pdf_page": page.pdf_page,
                "document_id": page.document_id,
                "status": "pending",
            })

    for warning in [*extraction_warnings, *render_warnings]:
        findings.append({
            "id": f"EXT-WARN-{len(findings) + 1:04d}",
            "code": "PROCESSING_WARNING",
            "category": "technical",
            "severity": "material",
            "status": "open",
            "scope": "document",
            "target_ids": [source_sha256],
            "description": warning,
            "impact": "Conferir as páginas afetadas antes de declarar cobertura integral.",
            "delivery_effect": "qualifies_conclusion",
            "required_action": "Verificar a falha técnica e as páginas correspondentes.",
            "attempt_ids": [],
            "resolution": None,
            "source_sha256": source_sha256,
        })
    return {
        "schema_version": "1.0",
        "source_sha256": source_sha256,
        "generated_at": now_utc(),
        "status": "partial" if findings else "completed",
        "max_distinct_attempts_per_finding": MAX_DISTINCT_ATTEMPTS,
        "findings": findings,
        "attempts": attempts,
        "queue": queue,
    }


def record_attempt(report: dict[str, Any], finding_id: str, action: str,
                   input_fingerprint: str, outcome: str, evidence: str) -> dict[str, Any]:
    """Record a completed host action once; cap distinct retries per finding."""
    result = deepcopy(report)
    finding = next((item for item in result.get("findings", []) if item.get("id") == finding_id), None)
    if finding is None:
        raise ValueError(f"Pendência não encontrada: {finding_id}")
    if finding.get("status") == "resolved":
        raise ValueError("Pendência resolvida não admite novas tentativas")
    prior = [item for item in result.get("attempts", []) if item.get("finding_id") == finding_id]
    if any(item.get("action") == action and item.get("input_fingerprint") == input_fingerprint for item in prior):
        raise ValueError("A mesma ação com a mesma entrada já foi registrada")
    if len(prior) >= int(result.get("max_distinct_attempts_per_finding", MAX_DISTINCT_ATTEMPTS)):
        raise ValueError("Limite de tentativas distintas atingido; registrar a limitação remanescente")
    if not action.strip() or not input_fingerprint.strip() or not outcome.strip() or not evidence.strip():
        raise ValueError("Ação, entrada, resultado observado e evidência são obrigatórios")
    attempt_id = f"ATT-REC-{finding_id}-{len(prior) + 1}"
    result.setdefault("attempts", []).append({
        "id": attempt_id,
        "finding_id": finding_id,
        "target_ids": finding.get("target_ids", []),
        "action": action,
        "input_fingerprint": input_fingerprint,
        "outcome": outcome,
        "evidence": evidence,
        "recorded_at": now_utc(),
    })
    finding.setdefault("attempt_ids", []).append(attempt_id)
    return result
