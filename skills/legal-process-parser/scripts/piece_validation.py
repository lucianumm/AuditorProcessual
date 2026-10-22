"""Traceability checks that depend on the requested procedural piece.

These checks operate on claims *recorded* by the reviewer. They cannot infer that
every allegation or independent ground in the underlying proceeding was found.
The host AI must read the case and decide which records are material.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict


RESPONSE_SECTIONS = {
    "inicial": {"fundamentos"},
    "contestacao": {"impugnacao", "fundamentos"},
    "replica": {"impugnacao", "fundamentos"},
    "recurso": {"impugnacao", "admissibilidade"},
    "pericia": {"analise_tecnica", "quesitos"},
    "cumprimento": {"titulo", "obrigacao", "demonstrativo", "fundamentos"},
    "manifestacao": {"objeto", "fundamentos"},
}

RESPONSE_LABELS = {
    "contested_claims": "alegação/pedido adverso",
    "defense_points": "defesa/documento novo",
    "decision_grounds": "fundamento da decisão",
}


def _fold(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFD", value.casefold())
        if unicodedata.category(character) != "Mn"
    )


def _unquoted_prose(value: str) -> str:
    """Remove marked literal quotations before linting the author's own voice."""
    text = re.sub(r"(?m)^\s*>.*$", " ", value)
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    for opening, closing in (("\"", "\""), ("“", "”"), ("«", "»"), ("‘", "’")):
        text = re.sub(re.escape(opening) + r"[^\n]*?" + re.escape(closing), " ", text)
    return text


def initial_voice_findings(paragraph: dict) -> list[str]:
    """Detect distancing at the start of an initial's factual assertion.

    An opposing party's allegation or a literal quote can legitimately contain
    the same words. This lint deliberately uses a narrow position and context.
    """
    if not isinstance(paragraph, dict) or paragraph.get("section") != "fatos":
        return []
    text = paragraph.get("text", "")
    if not isinstance(text, str):
        return []
    prose = _fold(_unquoted_prose(text))
    pattern = re.compile(
        r"(?:^|[.!?;]\s+|\n)\s*(?:[-*]\s*)?"
        r"(?:o autor|a autora|os autores|as autoras|a parte autora|"
        r"o requerente|a requerente|os requerentes|as requerentes)\s+"
        r"(?:alega(?:m)?|sustenta(?:m)?|afirma(?:m)?)\b"
    )
    return ["narrativa da própria parte com distanciamento"] if pattern.search(prose) else []


def _finding(
    code: str,
    description: str,
    target_ids: list[str],
    *,
    scope: str = "issue",
    effect: str = "blocks_issue",
    severity: str = "material",
    category: str = "procedural",
    action: str = "Revisar a peça e vincular a resposta aos elementos do processo.",
) -> dict:
    return {
        "code": code,
        "category": category,
        "severity": severity,
        "scope": scope,
        "target_ids": [target for target in target_ids if isinstance(target, str) and target],
        "description": description,
        "delivery_effect": effect,
        "required_action": action,
    }


def _records(review: dict, key: str, findings: list[dict]) -> list[dict]:
    records = review.get(key)
    if records is None:
        return []  # Older revisions have no inventory; absence proves nothing.
    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        findings.append(_finding(
            "PIECE_INVENTORY_INVALID", f"{key}: inventário deve ser lista de objetos.", [],
            scope="execution", effect="blocks_delivery", severity="blocking",
            action="Corrigir o formato do inventário da peça."
        ))
        return []
    return records


def _record_responses(
    review: dict,
    inventory: str,
    allowed_dispositions: set[str],
    response_sections: set[str],
    facts: dict,
    issues: dict,
    paragraph_issue_sections: dict,
    findings: list[dict],
) -> None:
    records = _records(review, inventory, findings)
    ids = set()
    label = RESPONSE_LABELS[inventory]
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip() or record_id in ids:
            findings.append(_finding(
                "PIECE_INVENTORY_ID", f"{inventory}: ID ausente ou duplicado.", [],
                scope="execution", effect="blocks_delivery", severity="blocking",
                action="Atribuir ID único a cada item do inventário."
            ))
            continue
        ids.add(record_id)
        source_id = record.get("source_fact_id")
        if source_id not in facts:
            findings.append(_finding(
                "PIECE_SOURCE_MISSING", f"{label} {record_id}: fato fonte não resolvido.", [],
                scope="execution", effect="blocks_delivery", severity="blocking",
                action="Identificar a alegação, defesa ou decisão nos autos e ligá-la ao fato registrado."
            ))
            continue
        disposition = record.get("disposition", "answered" if record.get("response_issue_id") else "unanswered")
        if disposition not in allowed_dispositions:
            findings.append(_finding(
                "PIECE_DISPOSITION_INVALID", f"{label} {record_id}: tratamento inválido.", [],
                scope="execution", effect="blocks_delivery", severity="blocking",
                action="Registrar resposta, aceitação fundamentada ou razão de não impugnação."
            ))
            continue
        response_id = record.get("response_issue_id")
        needs_response = disposition in {"answered", "disputed", "partially_admitted", "challenged"}
        if needs_response and response_id not in issues:
            findings.append(_finding(
                "PIECE_RESPONSE_MISSING", f"{label} {record_id}: resposta jurídica não vinculada.", [],
                scope="execution", effect="blocks_delivery", severity="material",
                action="Relacionar o item à questão que o enfrenta ou registrar justificativa de aceitação."
            ))
            continue
        if needs_response and not (paragraph_issue_sections.get(response_id, set()) & response_sections):
            findings.append(_finding(
                "PIECE_RESPONSE_NOT_DRAFTED", f"{label} {record_id}: resposta ausente da redação pertinente.", [response_id],
                action="Incluir a resposta fundamentada na seção de impugnação ou fundamentação."
            ))
        if disposition in {"unanswered", "not_challenged"} and (
            disposition == "unanswered" or record.get("essential", True) or not str(record.get("reason", "")).strip()
        ):
            essential = record.get("essential", True)
            effect = "blocks_delivery" if essential else "qualifies_conclusion"
            findings.append(_finding(
                "PIECE_GROUND_UNANSWERED", f"{label} {record_id}: item registrado sem enfrentamento.",
                [] if essential else [source_id], scope="execution" if essential else "fact", effect=effect,
                action="Enfrentar o item ou fundamentar por que ele não afeta o objetivo da peça."
            ))
        elif not needs_response and not str(record.get("reason", "")).strip():
            findings.append(_finding(
                "PIECE_DISPOSITION_UNEXPLAINED", f"{label} {record_id}: aceitação/exclusão sem razão.",
                [response_id] if response_id in issues else [source_id],
                scope="issue" if response_id in issues else "fact",
                effect="qualifies_conclusion",
                action="Explicar a admissão, irrelevância ou delimitação do objeto."
            ))


def _request_findings(review: dict, piece_type: str, issue_ids: set, paragraphs: list[dict]) -> list[dict]:
    findings: list[dict] = []
    requests = [r for r in review.get("requests", []) if isinstance(r, dict)]
    request_ids = {r.get("id") for r in requests if isinstance(r.get("id"), str)}
    request_map = {r.get("id"): r for r in requests}
    drafted = {rid for paragraph in paragraphs if paragraph.get("section") == "pedidos"
               for rid in paragraph.get("request_ids", []) if isinstance(rid, str)}
    issue_sections = defaultdict(set)
    for paragraph in paragraphs:
        for issue_id in paragraph.get("issue_ids", []):
            issue_sections[issue_id].add(paragraph.get("section"))
    substantive_sections = RESPONSE_SECTIONS.get(piece_type, set())
    for request in requests:
        rid = request.get("id")
        if rid not in drafted:
            findings.append(_finding(
                "PIECE_REQUEST_NOT_DRAFTED", f"Pedido {rid}: ausente da seção de pedidos.", [rid],
                scope="request", effect="blocks_delivery",
                action="Redigir o pedido e conservar seu vínculo com os fundamentos."
            ))
        for issue_id in request.get("issue_ids", []):
            if issue_id in issue_ids and not (issue_sections[issue_id] & substantive_sections):
                findings.append(_finding(
                    "PIECE_REQUEST_NO_REASONING", f"Pedido {rid}: questão {issue_id} não fundamentada no corpo da peça.",
                    [issue_id],
                    action="Desenvolver a questão vinculada em seção substantiva da peça."
                ))
        related = request.get("related_request_id")
        if related is not None and (related == rid or related not in request_ids):
            findings.append(_finding(
                "PIECE_REQUEST_RELATION_INVALID", f"Pedido {rid}: relação com outro pedido não resolvida.", [rid],
                scope="request", effect="blocks_delivery",
                action="Indicar um pedido relacionado existente e diferente do atual."
            ))
        incompatible_ids = request.get("incompatible_with", [])
        if not isinstance(incompatible_ids, list):
            findings.append(_finding(
                "PIECE_REQUEST_INCOMPATIBLE_FORMAT", f"Pedido {rid}: incompatibilidades devem ser lista de IDs.", [rid],
                scope="request", effect="blocks_delivery",
                action="Registrar incompatibilidades como lista de pedidos existentes."
            ))
            continue
        for incompatible in incompatible_ids:
            if incompatible == rid or incompatible not in request_ids:
                findings.append(_finding(
                    "PIECE_REQUEST_INCOMPATIBLE_REF", f"Pedido {rid}: incompatibilidade refere pedido inexistente.", [rid],
                    scope="request", effect="blocks_delivery",
                    action="Corrigir as referências de incompatibilidade."
                ))
            elif (request.get("priority", "principal") == "principal"
                  and request_map[incompatible].get("priority", "principal") == "principal"):
                findings.append(_finding(
                    "PIECE_PRINCIPAL_CONFLICT", f"Pedidos {rid} e {incompatible}: ambos principais e declarados incompatíveis.",
                    [rid, incompatible], scope="request", effect="blocks_delivery",
                    action="Definir relação subsidiária/alternativa ou justificar compatibilidade jurídica."
                ))
    for request in requests:
        current = request.get("id")
        visited = set()
        while current in request_map and current not in visited:
            visited.add(current)
            current = request_map[current].get("related_request_id")
        if current in visited:
            findings.append(_finding(
                "PIECE_REQUEST_RELATION_CYCLE", f"Pedido {request.get('id')}: relação circular entre pedidos.",
                [request.get("id")], scope="request", effect="blocks_delivery",
                action="Corrigir a ordem de apreciação dos pedidos relacionados."
            ))
    return findings


def validate_piece(review: dict, memory: dict) -> list[dict]:
    """Return structured, scoped findings; do not certify legal completeness.

    `memory` is accepted for the common validator interface. Provenance and
    page-level completeness are checked by the corpus/review validators.
    """
    if not isinstance(review, dict) or review.get("task") != "petition":
        return []
    piece_type = review.get("piece_type")
    if piece_type not in RESPONSE_SECTIONS:
        return []  # Existing schema and core validator report an invalid type.
    findings: list[dict] = []
    facts = {f.get("id"): f for f in review.get("facts", []) if isinstance(f, dict)}
    issues = {i.get("id"): i for i in review.get("issues", []) if isinstance(i, dict)}
    paragraphs = [p for p in review.get("paragraphs", []) if isinstance(p, dict)]
    sections = defaultdict(set)
    for paragraph in paragraphs:
        for issue_id in paragraph.get("issue_ids", []):
            sections[issue_id].add(paragraph.get("section"))
    if piece_type == "inicial":
        for paragraph in paragraphs:
            if initial_voice_findings(paragraph):
                findings.append(_finding(
                    "INITIAL_DISTANCED_VOICE", f"Parágrafo {paragraph.get('id')}: narrativa inicial distanciada da parte.",
                    [paragraph.get("id")], scope="paragraph", effect="qualifies_conclusion", severity="advisory",
                    category="editorial", action="Redigir o fato afirmativamente, preservando sua fonte no registro técnico."
                ))
    if piece_type == "contestacao":
        _record_responses(review, "contested_claims",
                          {"answered", "disputed", "partially_admitted", "admitted", "outside_scope", "unanswered"},
                          RESPONSE_SECTIONS[piece_type], facts, issues, sections, findings)
    elif piece_type == "replica":
        _record_responses(review, "defense_points",
                          {"answered", "accepted", "irrelevant", "unanswered"},
                          RESPONSE_SECTIONS[piece_type], facts, issues, sections, findings)
    elif piece_type == "recurso":
        _record_responses(review, "decision_grounds",
                          {"challenged", "answered", "not_challenged", "accepted"},
                          {"impugnacao"}, facts, issues, sections, findings)
    findings.extend(_request_findings(review, piece_type, set(issues), paragraphs))
    return list({(f["code"], tuple(f["target_ids"]), f["description"]): f for f in findings}.values())
