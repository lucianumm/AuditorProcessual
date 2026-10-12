"""Validate v4 reasoning records, not legal truth or model comprehension.

Source interpretation and atom extraction are authored by the host. This module
checks their consistency, completeness and exact links; human legal evaluation
remains separate, including when every technical check passes.
"""
from __future__ import annotations

import unicodedata
from datetime import date
from pathlib import Path

try:
    from .case_packet import check_reading_coverage
    from .research_memory import research_revision, changed_authorities
except ImportError:
    from case_packet import check_reading_coverage
    from research_memory import research_revision, changed_authorities

ATOM_FIELDS = ("actor", "action", "object", "polarity", "scope", "date", "period_start", "period_end", "amount", "currency")


def folded(value) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(value).casefold()) if unicodedata.category(c) != "Mn").strip()


def _map(review: dict, field: str, errors: list[str], identifier: str = "id") -> dict:
    values = review.get(field, [])
    result = {}
    if not isinstance(values, list):
        errors.append(f"{field}: lista obrigatória")
        return result
    for item in values:
        if not isinstance(item, dict) or not item.get(identifier) or item[identifier] in result:
            errors.append(f"{field}: registro inválido ou duplicado")
            continue
        result[item[identifier]] = item
    return result


def validate_precision(review: dict, memory: dict, output: Path | None = None) -> list[str]:
    if review.get("schema_version") != "4.0":
        return []
    errors = check_reading_coverage(review, memory, output)
    try:
        from .procedural_catalog import validate_catalog_selection
    except ImportError:
        from procedural_catalog import validate_catalog_selection
    errors.extend(validate_catalog_selection(review))
    facts = _map(review, "facts", errors)
    issues = _map(review, "issues", errors)
    norms = _map(review, "norms", errors)
    theses = _map(review, "theses", errors)
    assertions = _map(review, "assertion_reviews", errors, "fact_id")
    norm_map = _map(review, "normative_map", errors, "norm_id")
    thesis_reviews = _map(review, "thesis_reviews", errors, "thesis_id")
    precedents = _map(review, "precedent_comparisons", errors, "norm_id")
    context = review.get("execution_context", {})
    mode = context.get("mode")
    if mode not in {"local", "host_chat"}:
        errors.append("execution_context: modo local ou host_chat obrigatório")
    for key in ("vision", "browsing", "code_execution", "persistence"):
        record = context.get("capabilities", {}).get(key, {})
        if record.get("status") not in {"available", "unavailable", "not_tested"}:
            errors.append(f"execution_context: capacidade {key} não registrada")
        elif record.get("status") == "available" and not record.get("observed_reference"):
            errors.append(f"execution_context: capacidade {key} não observada nesta sessão")
    if mode == "host_chat" and any(item.get("method") == "local_receipt" for item in review.get("reading_coverage", [])):
        errors.append("host_chat não pode simular recibos de execução local")
    if output is not None and review.get("research_revision") != research_revision(output):
        errors.append("research_revision desatualizada: revisar fontes oficiais, mesmo sem novo upload")
    if set(assertions) != set(facts):
        errors.append("assertion_reviews: conferir cada fato exatamente uma vez")
    for fid, assertion in assertions.items():
        if fid not in facts:
            continue
        fact = facts[fid]
        linked = {iid for iid, issue in issues.items() if fid in issue.get("fact_ids", [])}
        if set(assertion.get("issue_ids", [])) != linked:
            errors.append(f"{fid}: questões da afirmação divergem dos vínculos do fato")
        atoms = assertion.get("atoms", {})
        if any(not str(atoms.get(key, "")).strip() for key in ("actor", "action", "object", "polarity", "scope")):
            errors.append(f"{fid}: sujeito, ação, objeto, polaridade e alcance precisam ser explicitados")
        support, contradiction = False, False
        sources = fact.get("sources", [])
        for evidence in assertion.get("evidence", []):
            index = evidence.get("source_index")
            if type(index) is not int or not 0 <= index < len(sources):
                errors.append(f"{fid}: evidência não resolve fonte exata do fato")
                continue
            source = sources[index]
            relation = evidence.get("relation")
            source_atoms = evidence.get("source_atoms", {})
            if relation == "supports":
                support = True
                for key in ATOM_FIELDS:
                    if atoms.get(key) is not None and (source_atoms.get(key) is None or folded(atoms[key]) != folded(source_atoms[key])):
                        errors.append(f"{fid}: suporte declarado contradiz {key} da fonte; registrar inferência, contexto ou divergência")
            elif relation == "contradicts":
                contradiction = True
            elif relation != "context":
                errors.append(f"{fid}: relação probatória inválida")
            if not evidence.get("context"):
                errors.append(f"{fid}: falta contexto do trecho citado")
            if source.get("image_id") and not source.get("region"):
                errors.append(f"{fid}: fonte visual decisiva exige região identificável")
        state = assertion.get("evidence_status")
        if state == "inferred" and fact.get("support", {}).get("assessment") != "inference":
            errors.append(f"{fid}: inferência não pode manter suporte declarado direto")
        if state == "supported" and (not support or contradiction):
            errors.append(f"{fid}: prova ausente/contrária não pode ser declarada sustentação incontroversa")
        if contradiction and state not in {"disputed", "contradicted"}:
            errors.append(f"{fid}: prova contrária exige estado controvertido ou contradito")
        if state == "contradicted" and fact.get("nature") == "fato":
            errors.append(f"{fid}: proposição contradita não pode permanecer como fato afirmado sem tratamento")
        if state in {"unproven", "disputed", "contradicted", "client_account"} and not assertion.get("treatment"):
            errors.append(f"{fid}: limite probatório sem tratamento explícito")
        if fact.get("origin") == "client" and state == "supported" and not sources:
            errors.append(f"{fid}: relato do cliente não equivale a confirmação documental")
        required_critical = {field for field in ("date", "period_start", "period_end", "amount") if atoms.get(field) is not None}
        checks = assertion.get("critical_checks", [])
        covered = set()
        for check in checks:
            field = check.get("field")
            covered.add(field)
            index = check.get("source_index")
            client_check = check.get("method") == "client_record" and fact.get("origin") == "client" and index is None
            if not client_check and (type(index) is not int or not 0 <= index < len(sources)):
                errors.append(f"{fid}: conferência crítica sem fonte")
            if client_check and (state != "client_account" or check.get("result") == "confirmed"):
                errors.append(f"{fid}: relato sem documento não confirma dado crítico")
            if check.get("result") not in {"confirmed", "disputed", "unreadable"} or not check.get("basis"):
                errors.append(f"{fid}: conferência crítica sem resultado/fundamento")
            if check.get("method") in {"render", "crop", "ocr_crosscheck"} and not check.get("region"):
                errors.append(f"{fid}: conferência visual sem região/crop")
            if check.get("method") in {"render", "crop", "ocr_crosscheck"} and context.get("capabilities", {}).get("vision", {}).get("status") != "available":
                errors.append(f"{fid}: conferência visual declarada sem capacidade observada")
            if check.get("result") != "confirmed" and state == "supported":
                errors.append(f"{fid}: dado crítico pendente incompatível com suporte integral")
        if not required_critical <= covered:
            errors.append(f"{fid}: reconferência de datas, períodos ou valores críticos ausente")
    if set(norm_map) != set(norms):
        errors.append("normative_map: registrar contexto e temporalidade de cada norma")
    for nid, mapping in norm_map.items():
        if nid not in norms:
            continue
        linked = {iid for iid, issue in issues.items() if nid in issue.get("norm_ids", [])}
        if set(mapping.get("issue_ids", [])) != linked:
            errors.append(f"{nid}: mapa normativo diverge das questões vinculadas")
        for applicable in mapping.get("relevant_dates", []):
            when = applicable.get("date")
            try:
                date.fromisoformat(when)
                if not set(applicable.get("fact_ids", [])) <= set(facts):
                    errors.append(f"{nid}: marco temporal sem fatos existentes")
                outside = bool(mapping.get("effective_from") and when < mapping["effective_from"] or
                               mapping.get("effective_until") and when > mapping["effective_until"])
                if outside and mapping.get("temporal_status") == "applicable" and not mapping.get("transition_norm_ids"):
                    errors.append(f"{nid}: data fora da vigência registrada sem regra intertemporal vinculada")
            except (TypeError, ValueError):
                errors.append(f"{nid}: marco temporal inválido")
        for transition in mapping.get("transition_norm_ids", []):
            if transition not in norms:
                errors.append(f"{nid}: regra intertemporal inexistente")
        if mapping.get("effective_from") and mapping.get("effective_until") and mapping["effective_from"] > mapping["effective_until"]:
            errors.append(f"{nid}: intervalo de vigência invertido")
        if not mapping.get("full_context") or not mapping.get("consequences") or not mapping.get("temporal_reason"):
            errors.append(f"{nid}: requisitos, consequências ou contexto normativo incompletos")
        if mapping.get("temporal_status") == "applicable" and not mapping.get("relevant_dates"):
            errors.append(f"{nid}: aplicabilidade temporal sem marco relevante conferido")
    if output is not None:
        for nid in changed_authorities(review, output):
            if not norm_map.get(nid, {}).get("source_change_treatment"):
                errors.append(f"{nid}: fonte consultada mudou; registrar comparação com a nova captura e eventual incidência histórica")
    expected_precedents = {nid for nid,norm in norms.items() if norm.get("kind") == "precedent"}
    if set(precedents) != expected_precedents:
        errors.append("precedent_comparisons: comparar todos e somente os precedentes usados")
    for nid, comparison in precedents.items():
        if nid not in norms:
            continue
        if comparison.get("holding_excerpt") not in norms[nid].get("official_text", ""):
            errors.append(f"{nid}: fundamento determinante não pertence ao texto consultado")
        if not comparison.get("facts_of_precedent") or not comparison.get("case_comparison") or not comparison.get("current_status_analysis"):
            errors.append(f"{nid}: comparação factual ou situação atual ausente")
        if set(comparison.get("issue_ids", [])) != set(norm_map.get(nid, {}).get("issue_ids", [])):
            errors.append(f"{nid}: precedente comparado em questões diferentes do mapa normativo")
    if set(thesis_reviews) != set(theses):
        errors.append("thesis_reviews: comparar força e objeções de cada tese")
    for tid, check in thesis_reviews.items():
        if tid not in theses:
            continue
        thesis = theses[tid]
        issue = issues.get(thesis.get("issue_id"), {})
        requirements = issue.get("requirements", [])
        checks = check.get("requirement_checks", [])
        indices = [item.get("requirement_index") for item in checks]
        if set(indices) != set(range(len(requirements))) or len(indices) != len(set(indices)):
            errors.append(f"{tid}: confrontar cada requisito da questão, sem omissão ou duplicidade")
        for item in checks:
            if not set(item.get("fact_ids", [])) <= set(thesis.get("fact_ids", [])):
                errors.append(f"{tid}: requisito usa fato não vinculado à tese")
            if item.get("assessment") == "supported" and not item.get("fact_ids"):
                errors.append(f"{tid}: requisito apoiado sem prova vinculada")
            if item.get("assessment") == "supported" and any(assertions.get(fid, {}).get("evidence_status") in {"unproven", "contradicted"} for fid in item.get("fact_ids", [])):
                errors.append(f"{tid}: requisito apoiado em proposição não provada ou contradita")
        if not set(check.get("contrary_norm_ids", [])) <= set(norms):
            errors.append(f"{tid}: autoridade contrária inexistente")
        if check.get("procedural_fit") == "unsatisfied" and thesis.get("role") != "not_pursued":
            errors.append(f"{tid}: tese processualmente incompatível precisa ser afastada")
        if thesis.get("characterization") == "consolidated" and check.get("normative_strength") in {"proposed", "unknown"}:
            errors.append(f"{tid}: proposta ou base desconhecida não equivale a tese consolidada")
        if any(key in check for key in ("success_probability", "win_percentage", "success_percent")):
            errors.append(f"{tid}: percentual de êxito não pertence a este contrato qualitativo")
        if thesis.get("characterization") == "consolidated" and any(norm_map.get(nid, {}).get("temporal_status") in {"excluded", "uncertain"} for nid in thesis.get("norm_ids", [])):
            errors.append(f"{tid}: tese consolidada com incidência temporal excluída ou incerta")
    for paragraph in review.get("paragraphs", []):
        for rid in paragraph.get("request_ids", []):
            request = next((r for r in review.get("requests", []) if r["id"] == rid), {})
            if not set(request.get("issue_ids", [])) <= set(paragraph.get("issue_ids", [])):
                errors.append(f"{paragraph['id']}: pedido redigido sem todas as questões que o sustentam")
    try:
        from .labor_analysis import validate_labor
    except ImportError:
        from labor_analysis import validate_labor
    errors.extend(validate_labor(review))
    return list(dict.fromkeys(errors))
