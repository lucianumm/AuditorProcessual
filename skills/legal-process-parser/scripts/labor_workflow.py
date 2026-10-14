"""Validate attributed claim development; these checks do not decide legal merit."""
from __future__ import annotations

import json
from datetime import date
from difflib import unified_diff
from pathlib import Path

try:
    from .contracts import validate_contract
    from .labor_catalog import claim_catalog, sector_catalog
    from .labor_ledger import apportion_workdays, ledger_markdown
    from .labor_time import count_date_window
    from .labor_calculations import decimal_value
except ImportError:
    from contracts import validate_contract
    from labor_catalog import claim_catalog, sector_catalog
    from labor_ledger import apportion_workdays, ledger_markdown
    from labor_time import count_date_window
    from labor_calculations import decimal_value

FIELDS = ("claim_reviews", "proof_plan", "material_questions", "reconciliations", "temporal_checks",
          "authority_checks", "prescription_reviews", "collective_comparisons", "appeal_chapters",
          "strategy_options", "instruction_questions", "sector_selections")


def pending_workflow() -> dict:
    return {"schema_version": "1.0", "analysis_date": date.today().isoformat(),
            "phase": "initial_intake", "document_availability": "none", "client_record_ids": [],
            **{field: [] for field in FIELDS}}


def drafting_possible(review: dict, issue_id: str) -> bool:
    claims = [c for c in review.get("labor_review", {}).get("workflow", {}).get("claim_reviews", []) if c["issue_id"] == issue_id]
    return bool(claims) and all(c["drafting_basis"] == "sufficient" and c["merit_status"] != "excluded" for c in claims)


def validate_workflow(review: dict, memory: dict | None = None) -> list[str]:
    labor = review.get("labor_review", {})
    w = labor.get("workflow")
    if w is None:
        return []
    errors = validate_contract(w, "labor_workflow.schema.json")
    if errors:
        return errors
    maps = {}
    for field in FIELDS:
        maps[field] = {row["id"]: row for row in w[field]}
        if len(maps[field]) != len(w[field]):
            errors.append("workflow: IDs duplicados em " + field)
    facts = {r["id"]: r for r in review.get("facts", [])}
    norms = {r["id"]: r for r in review.get("norms", [])}
    issues = {r["id"]: r for r in review.get("issues", [])}
    assertions = {r["fact_id"]: r for r in review.get("assertion_reviews", [])}
    periods = {r["id"]: r for r in labor["contract_periods"]}
    relationships = {r["id"]: r for r in labor["relationships"]}
    topics = {r["id"]: r for r in labor["topic_assessments"]}
    paragraphs = {r["id"]: r for r in review.get("paragraphs", [])}
    normative = {r["norm_id"]: r for r in review.get("normative_map", [])}
    proofs, claims = maps["proof_plan"], maps["claim_reviews"]
    catalog = claim_catalog()
    if not claims or set(issues) - {c["issue_id"] for c in claims.values()}:
        errors.append("workflow: desenvolver cada questão por uma pretensão pertinente")
    if set(w["client_record_ids"]) != {r["id"] for r in review.get("client_records", [])}:
        errors.append("workflow: preservar todos os relatos e retificações")
    has_documents = bool(memory.get("documents")) if memory is not None else any(f.get("sources") for f in facts.values())
    if w["document_availability"] == "none" and has_documents or memory is not None and not has_documents and w["document_availability"] != "none":
        errors.append("workflow: distinguir uploads recebidos de documentos pretendidos")

    def refs(row, field, known):
        if not set(row.get(field, [])) <= set(known):
            errors.append(str(row.get("id", "registro")) + ": referência inexistente em " + field)

    def atoms(fid):
        return assertions.get(fid, {}).get("atoms", {})

    def fact_link(row, fid):
        if fid not in facts or row.get("issue_id") and fid not in issues.get(row["issue_id"], {}).get("fact_ids", []):
            errors.append(row["id"] + ": fato de outra questão ou inexistente")

    for field in FIELDS:
        for row in w[field]:
            for key, known in (("fact_ids", facts), ("norm_ids", norms), ("issue_ids", issues), ("period_ids", periods)):
                refs(row, key, known)
            if row.get("issue_id") and row["issue_id"] not in issues:
                errors.append(row["id"] + ": questão inexistente")
            if row.get("relationship_id") and row["relationship_id"] not in relationships:
                errors.append(row["id"] + ": relação inexistente")
            if row.get("issue_id") and not set(row.get("fact_ids", [])) <= set(issues.get(row["issue_id"], {}).get("fact_ids", [])):
                errors.append(row["id"] + ": fatos fora da questão")
    for row in claims.values():
        spec, topic = catalog.get(row["claim_id"]), topics.get(row["topic_assessment_id"], {})
        if not spec or topic.get("issue_id") != row["issue_id"] or spec["topic_id"] != topic.get("topic_id"):
            errors.append(row["id"] + ": pretensão e tema/questão incompatíveis")
            continue
        requirements = {r["requirement_id"]: r for r in row["requirements"]}
        if len(requirements) != len(row["requirements"]) or set(requirements) != set(spec["requirements"]):
            errors.append(row["id"] + ": conferir cada requisito da pretensão selecionada")
        refs(row, "proof_plan_ids", proofs)
        if not set(row["norm_ids"]) <= set(issues.get(row["issue_id"], {}).get("norm_ids", [])):
            errors.append(row["id"] + ": normas de outra questão na pretensão")
        for pid in row["proof_plan_ids"]:
            if pid in proofs and proofs[pid]["issue_id"] != row["issue_id"]:
                errors.append(row["id"] + ": plano de prova pertence a outra questão")
        for requirement in requirements.values():
            for key, known in (("fact_ids", facts), ("norm_ids", norms), ("proof_plan_ids", proofs)):
                refs(requirement, key, known)
            if not set(requirement["fact_ids"]) <= set(row["fact_ids"]) or not set(requirement["norm_ids"]) <= set(row["norm_ids"]):
                errors.append(row["id"] + ": requisito usa fontes de outra pretensão")
            if requirement["status"] == "verified" and (not requirement["fact_ids"] or not requirement["norm_ids"] or any(
                    assertions.get(fid, {}).get("evidence_status") != "supported" for fid in requirement["fact_ids"])):
                errors.append(row["id"] + ": relato ou prova pendente não confirma requisito")
            if requirement["status"] in {"alleged", "disputed", "awaiting_proof"} and not requirement["fact_ids"]:
                errors.append(row["id"] + ": alegação precisa de fatos atribuídos")
        missing = any(r["status"] == "missing_material" for r in requirements.values())
        if row["drafting_basis"] == "sufficient" and (missing or not row["fact_ids"] or not row["norm_ids"] or row["merit_status"] == "excluded"):
            errors.append(row["id"] + ": minuta suficiente sem dados essenciais, base ou pretensão compatível")
        if row["merit_status"] == "supported" and any(r["status"] not in {"verified", "not_applicable"} for r in requirements.values()):
            errors.append(row["id"] + ": mérito sustentado com requisito ainda alegado/pendente")
        if row["merit_status"] == "awaiting_proof" and not row["proof_plan_ids"]:
            errors.append(row["id"] + ": prova futura exige providência concreta")
        if topic.get("pending_cause") == "future_proof" and row["drafting_basis"] == "sufficient" and any(
                p["issue_id"] == row["issue_id"] and p["criticality"] != "future_proof" and p["status"] != "received" for p in proofs.values()):
            errors.append(row["id"] + ": dado/requisito do ato pendente não pode ser reduzido a prova futura")
    for row in proofs.values():
        if row["status"] == "received" and (not row["fact_ids"] or all(facts.get(fid, {}).get("origin") == "client" for fid in row["fact_ids"])):
            errors.append(row["id"] + ": prova recebida exige fonte distinta do relato")
        if row["method"] == "exhibition" and not row["norm_ids"]:
            errors.append(row["id"] + ": exibição exige base processual específica")
    for row in w["material_questions"]:
        claim = claims.get(row["claim_review_id"], {})
        refs(row, "answer_fact_ids", facts)
        if not claim or row["status"] == "open" and claim.get("drafting_basis") == "sufficient":
            errors.append(row["id"] + ": pergunta material aberta incompatível com suficiência declarada")
        if row["status"] == "answered" and not row["answer_fact_ids"]:
            errors.append(row["id"] + ": resposta sem fato recebido")
    for row in w["reconciliations"]:
        for fid in (row["left_fact_id"], row["right_fact_id"]):
            fact_link(row, fid)
        left, right, atom = atoms(row["left_fact_id"]), atoms(row["right_fact_id"]), row["atom"]
        if row["left_fact_id"] == row["right_fact_id"]:
            errors.append(row["id"] + ": conciliação exige duas fontes/fatos distintos")
        if row["status"] == "agrees":
            agrees = left.get(atom) is not None and right.get(atom) is not None
            if agrees:
                agrees = (decimal_value(left[atom]) == decimal_value(right[atom]) if atom == "amount"
                          else str(left[atom]).casefold() == str(right[atom]).casefold())
            if not agrees:
                errors.append(row["id"] + ": concordância diverge dos campos reconferidos")
            if any(left.get(key) != right.get(key) for key in ("actor", "object", "period_start", "period_end", "currency") if key in left or key in right):
                errors.append(row["id"] + ": conciliação mistura sujeito, objeto, período ou moeda")
    for row in w["temporal_checks"]:
        period, mapping = periods.get(row["period_id"], {}), normative.get(row["norm_id"], {})
        if row["norm_id"] not in norms or row["period_id"] not in periods:
            errors.append(row["id"] + ": norma/período inexistente")
        if row["status"] == "applicable":
            start, end = period.get("start"), period.get("end") or row["reviewed_until"]
            if not start or not end or end > w["analysis_date"] and not period.get("end"):
                errors.append(row["id"] + ": delimitar período examinado sem inventar término contratual")
            elif mapping.get("temporal_status") != "applicable" or not mapping.get("effective_from") or mapping["effective_from"] > start or mapping.get("effective_until") and mapping["effective_until"] < end:
                errors.append(row["id"] + ": versão normativa não cobre o período")
    for row in w["authority_checks"]:
        norm = norms.get(row["norm_id"], {})
        refs(row, "status_norm_ids", norms)
        if not norm or row["checked_on"] > w["analysis_date"] or row["checked_on"] < norm.get("accessed_on", ""):
            errors.append(row["id"] + ": consulta datada incoerente")
        detail = row.get("procedural_detail")
        effective_holding = bool(detail and detail["merit_state"] == "decided" and detail["holding_effect"] in {"effective", "limited"}
                                 and row["status"] in {"decided", "suspended"} and row["status_norm_ids"])
        if detail and not row["status_norm_ids"]:
            errors.append(row["id"] + ": distinguir mérito, situação processual e efeitos com fonte da situação")
        if row["use"] == "merit_support" and (detail and not effective_holding or not detail and row["status"] != "decided"):
            errors.append(row["id"] + ": situação pendente/suspensa/cancelada não confirma tese atual de mérito")
        if row["status"] in {"cancelled", "revised"} and row["use"] != "excluded" and not row["status_norm_ids"]:
            errors.append(row["id"] + ": uso histórico/distinção exige fonte da alteração")
    for row in w["prescription_reviews"]:
        fact_link(row, row["anchor_fact_id"])
        if row["action_fact_id"]:
            fact_link(row, row["action_fact_id"])
        if not row["norm_ids"]:
            errors.append(row["id"] + ": prescrição exige regra por pretensão")
        window = row["window"]
        if window:
            if window["anchor_date"] not in {atoms(row["anchor_fact_id"]).get(k) for k in ("date", "period_start", "period_end")}:
                errors.append(row["id"] + ": marco não corresponde ao fato reconferido")
            for adjustment in window["adjustments"]:
                refs(adjustment, "fact_ids", facts); refs(adjustment, "norm_ids", norms)
            try:
                result = count_date_window(window)
                if row["status"] in {"within_supplied_window", "outside_supplied_window"}:
                    action = atoms(row["action_fact_id"]).get("date")
                    if not action or window["direction"] != "forward":
                        errors.append(row["id"] + ": comparação exige marco e janela prospectiva")
                    elif (action <= result["date"]) != (row["status"] == "within_supplied_window"):
                        errors.append(row["id"] + ": conclusão temporal diverge da contagem")
            except (ValueError, TypeError, KeyError, OverflowError) as error:
                errors.append(row["id"] + ": " + str(error))
        elif row["status"] in {"within_supplied_window", "outside_supplied_window"}:
            errors.append(row["id"] + ": comparação temporal sem contagem")
    instruments = {r["id"]: r for r in labor["collective_instruments"]}
    for row in w["collective_comparisons"]:
        for side in ("left", "right"):
            instrument = instruments.get(row[side + "_instrument_id"], {})
            if row[side + "_clause_id"] not in {c["id"] for c in instrument.get("clauses", [])}:
                errors.append(row["id"] + ": cláusula coletiva inexistente")
        if row["selection"] in {"left", "right"} and not row["norm_ids"]:
            errors.append(row["id"] + ": preferência coletiva sem fundamento")
    measures = json.loads((Path(__file__).resolve().parents[1] / "references/procedural_catalog.json").read_text(encoding="utf-8"))["entries"]
    for row in w["appeal_chapters"]:
        fact_link(row, row["act_fact_id"])
        source = facts.get(row["act_fact_id"], {})
        if source.get("origin") != "document" or not any(row["decision_excerpt"] in s.get("quote", "") for s in source.get("sources", [])):
            errors.append(row["id"] + ": capítulo precisa de trecho real da decisão")
        if row["measure_catalog_id"] != "custom" and not any(
                c["id"] == row["measure_catalog_id"] and ("trabalhista" in c["domains"] or "*" in c["domains"])
                and (c["family"] == "recurso" or c["id"] == "contrarrazoes_trabalhistas") for c in measures):
            errors.append(row["id"] + ": instrumento incompatível com catálogo trabalhista")
        ground_ids = set()
        if not row["grounds"]:
            errors.append(row["id"] + ": identificar fundamentos autônomos")
        for ground in row["grounds"]:
            refs(ground, "norm_ids", norms); refs(ground, "response_paragraph_ids", paragraphs)
            if ground["id"] in ground_ids or ground["excerpt"] not in row["decision_excerpt"]:
                errors.append(row["id"] + ": fundamento duplicado ou ausente do trecho")
            ground_ids.add(ground["id"])
            if ground["status"] == "challenged" and (not ground["response_paragraph_ids"] or any(
                    row["issue_id"] not in paragraphs[p]["issue_ids"] for p in ground["response_paragraph_ids"] if p in paragraphs)):
                errors.append(row["id"] + ": impugnação sem parágrafo da questão")
    options = maps["strategy_options"]
    thesis_ids = {r["id"] for r in review.get("theses", [])}
    for row in options.values():
        refs(row, "exclusive_with", options)
        if row["thesis_id"] not in thesis_ids:
            errors.append(row["id"] + ": tese inexistente")
        for opposite in row["exclusive_with"]:
            other = options.get(opposite, {})
            if other.get("selected") and row["selected"] and other.get("scenario_id") == row["scenario_id"]:
                errors.append(row["id"] + ": teses incompatíveis no mesmo cenário")
    for row in w["instruction_questions"]:
        refs(row, "answer_fact_ids", facts)
        if proofs.get(row["proof_plan_id"], {}).get("issue_id") != row["issue_id"]:
            errors.append(row["id"] + ": pergunta/quesito sem controvérsia e plano correspondente")
        if row["status"] == "answered" and not row["answer_fact_ids"]:
            errors.append(row["id"] + ": resposta de instrução não recebida")
    for row in w["sector_selections"]:
        if row["sector_id"] not in sector_catalog():
            errors.append(row["id"] + ": setor desconhecido")
    if w.get("ledger"):
        try:
            apportion_workdays(w["ledger"])
        except (ValueError, KeyError, TypeError, OverflowError) as error:
            errors.append("Conciliação de jornada/folha: " + str(error))
        else:
            for row in w["ledger"]["days"] + w["ledger"]["payroll"]:
                refs(row, "fact_ids", facts)
                relation = relationships.get(row["relationship_id"], {})
                actors = {str(a).casefold() for a in (relation.get("worker"), *relation.get("employers", [])) if a}
                for fid in row["fact_ids"]:
                    fields = atoms(fid)
                    if str(fields.get("actor", "")).casefold() not in actors:
                        errors.append(row["id"] + ": fonte de outro sujeito na conciliação")
                    if row["origin"] == "document" and facts.get(fid, {}).get("origin") == "client":
                        errors.append(row["id"] + ": relato convertido em marcação/valor documental")
                    if row["origin"] == "document" and assertions.get(fid, {}).get("evidence_status") != "supported":
                        errors.append(row["id"] + ": valor/marcação documental sem fonte conferida")
                    if row.get("date") and fields.get("date") and row["date"] != fields["date"]:
                        errors.append(row["id"] + ": dia da marcação difere do fato reconferido")
                    if "amount" in row and fields.get("amount") is not None and len(row["fact_ids"]) == 1 and decimal_value(row["amount"]) != decimal_value(fields["amount"]):
                        errors.append(row["id"] + ": valor diverge da fonte reconferida")
            for rule in w["ledger"]["rules"]:
                refs(rule, "norm_ids", norms)
                if rule["relationship_id"] not in relationships:
                    errors.append(rule["id"] + ": regra de relação inexistente")
                for nid in rule["norm_ids"]:
                    mapping = normative.get(nid, {})
                    if mapping.get("temporal_status") != "applicable" or not mapping.get("effective_from") or mapping["effective_from"] > rule["period_start"] or (mapping.get("effective_until") and mapping["effective_until"] < rule["period_end"]):
                        errors.append(rule["id"] + ": regra fornecida fora da vigência registrada")
    return list(dict.fromkeys(errors))


def workflow_findings(review: dict) -> list[dict]:
    w = review.get("labor_review", {}).get("workflow", {})
    if not w or validate_contract(w, "labor_workflow.schema.json"):
        return []
    findings = []
    def add(row, description, action, effect="qualifies_conclusion"):
        ids = row.get("issue_ids") or [row["issue_id"]]
        findings.append({"code": "LABOR_WORKFLOW_" + row["id"], "category": "evidence", "severity": "material",
                         "scope": "issue", "target_ids": ids, "description": description,
                         "impact": "Restrito à pretensão e dependências identificadas.", "delivery_effect": effect,
                         "required_action": action})
    for claim in w["claim_reviews"]:
        if claim["drafting_basis"] == "needs_material_information":
            add(claim, claim["reason"], "Esclarecer somente o dado material indicado.", "blocks_issue")
        elif claim["merit_status"] in {"awaiting_proof", "contested"}:
            add(claim, "Pretensão formulável com prova futura ou controvérsia.", "Executar plano de prova e enfrentar a prova contrária.")
    for proof in w["proof_plan"]:
        if proof["status"] != "received":
            add(proof, proof["description"], proof["alternatives"],
                "qualifies_conclusion" if proof["criticality"] == "future_proof" else "blocks_issue")
    for row in w["appeal_chapters"]:
        if any(g["status"] == "pending" for g in row["grounds"]):
            add(row, "Fundamento autônomo sem resposta definida.", "Conferir capítulo e impugnação.", "blocks_issue")
    for row in w["prescription_reviews"]:
        if row["status"] == "pending":
            add(row, "Marco ou regime prescricional ainda não confirmado.", row["reason"])
    return findings


def workflow_entries(review: dict) -> list[dict]:
    w = review.get("labor_review", {}).get("workflow", {})
    rows = []
    for field in FIELDS:
        for row in w.get(field, []):
            facts = list(row.get("fact_ids", [])) + list(row.get("answer_fact_ids", []))
            facts += [row[k] for k in ("left_fact_id", "right_fact_id", "anchor_fact_id", "action_fact_id", "act_fact_id") if row.get(k)]
            norms = list(row.get("norm_ids", [])) + list(row.get("status_norm_ids", []))
            for requirement in row.get("requirements", []):
                facts += requirement["fact_ids"]; norms += requirement["norm_ids"]
            if row.get("norm_id"):
                norms.append(row["norm_id"])
            rows.append({**row, "id": "workflow_" + field + ":" + row["id"], "record_id": row["id"],
                         "record_field": "workflow_" + field, "fact_ids": sorted(set(facts)), "norm_ids": sorted(set(norms)),
                         "label": row.get("reason") or row.get("scope_analysis") or row.get("question") or row["id"]})
    for field in ("rules", "days", "payroll"):
        for row in w.get("ledger", {}).get(field, []):
            rows.append({**row, "id": "ledger_" + field + ":" + row["id"], "record_id": row["id"],
                         "record_field": "ledger_" + field, "label": row["reason"]})
    return rows


def workflow_markdown(review: dict) -> str:
    try:
        from .legal_index import safe_text, anchor
    except ImportError:
        from legal_index import safe_text, anchor
    labor, w = review["labor_review"], review["labor_review"]["workflow"]
    lines = ["# DESENVOLVIMENTO TRABALHISTA", "", "Documentos recebidos: " + w["document_availability"], "",
             "Possibilidade de redigir e suficiência da prova são registradas por pretensão.", ""]
    for row in w["claim_reviews"]:
        lines += ["## " + safe_text(row["id"]), "", "Redação: " + row["drafting_basis"] + ". Prova/mérito: " + row["merit_status"] + ".", "",
                  safe_text(row["requested_effect"]), "", "Contraponto: " + safe_text(row["strongest_objection"]), "",
                  "Resposta: " + safe_text(row["response"]), "",
                  f"[Questão {safe_text(row['issue_id'])}](indice_juridico.md#{anchor('issue', row['issue_id'])})", ""]
        lines += ["- " + safe_text(r["requirement_id"]) + ": " + r["status"] + " — " + safe_text(r["reason"]) for r in row["requirements"]]
        lines.append("")
    for field in FIELDS[1:]:
        if w[field]:
            lines += ["## " + field.replace("_", " "), ""]
            for row in w[field]:
                lines += ["- " + safe_text(row["id"]) + ": " + safe_text(row.get("question") or row.get("description") or row.get("reason") or row.get("scope_analysis"))]
            lines.append("")
    instruments = {i["id"]: i for i in labor["collective_instruments"]}
    for row in w["collective_comparisons"]:
        def clause(side):
            return next(c["quote"] for c in instruments[row[side + "_instrument_id"]]["clauses"] if c["id"] == row[side + "_clause_id"])
        delta = unified_diff(clause("left").splitlines(), clause("right").splitlines(), lineterm="")
        lines += ["Comparação textual " + safe_text(row["id"]) + ": " + safe_text(" | ".join(delta)), ""]
    if w.get("ledger"):
        lines += [ledger_markdown(apportion_workdays(w["ledger"]))]
    return "\n".join(lines) + "\n"
