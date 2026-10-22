"""Check labor-specific recorded links and render attributed analysis."""
from __future__ import annotations

import argparse
import json
import unicodedata
from datetime import date
from pathlib import Path

try:
    from .contracts import validate_contract
    from .labor_calculations import compute_calculations, decimal_value
    from .labor_time import working_day, count_deadline
except ImportError:
    from contracts import validate_contract
    from labor_calculations import compute_calculations, decimal_value
    from labor_time import working_day, count_deadline

TOPICS_PATH = Path(__file__).resolve().parents[1] / "references/labor_topics.json"
RECORD_FIELDS = ("relationships","contract_periods","collective_instruments","topic_assessments",
                 "evidence_checks","health_assessments","procedure_reviews")


def folded(value) -> str:
    return "".join(c for c in unicodedata.normalize("NFD",str(value).casefold()) if unicodedata.category(c) != "Mn").strip()


def topics_catalog() -> dict:
    return {item["id"]:item for item in json.loads(TOPICS_PATH.read_text(encoding="utf-8"))["topics"]}


def is_labor(review: dict) -> bool:
    strategy = review.get("strategy",{})
    return (folded(strategy.get("domain","")) in {"trabalhista","direito do trabalho","direito trabalhista","laboral","labor","labour"} or
            bool(set(strategy.get("specialization_ids",[])) & {item["specialization_id"] for item in topics_catalog().values()}))


def pending_labor(corpus_revision: str, topic_ids: list[str] | None = None) -> dict:
    """A deliberate authoring template, not a completed analysis."""
    return {"schema_version":"1.0","corpus_revision":corpus_revision,
            "scope":{"mode":"targeted","topic_ids":topic_ids or [],"excluded_topics":[],
                     "represented_role":"neutral","contextual_limitations":["Preenchimento pendente após exame dos autos."]},
            **{field:[] for field in RECORD_FIELDS},
            "calculation_scope":{"status":"not_requested","reason":"Confirmar a entrega solicitada.",
                                 "title_fact_ids":[],"title_scope_analysis":""}}


def scope_matches(value: str, scopes: list[str], *, hierarchy: bool = False) -> bool:
    value = folded(value)
    if not value:
        return False
    return any(folded(scope) == "*" or folded(scope) == value or
               (hierarchy and value.startswith(folded(scope).rstrip("/") + "/")) for scope in scopes)


def validate_labor(review: dict, memory: dict | None = None) -> list[str]:
    if not isinstance(review,dict):
        return ["Revisão jurídica deve ser objeto JSON"]
    labor = review.get("labor_review")
    if labor is None:
        return ["Revisão trabalhista v4 exige labor_review com escopo e questões efetivamente examinadas"] if review.get("schema_version") == "4.0" and is_labor(review) else []
    errors = validate_contract(labor,"labor_review.schema.json")
    if errors:
        return errors
    if review.get("schema_version") != "4.0":
        errors.append("labor_review exige o contrato jurídico v4")
    if labor["corpus_revision"] != review.get("corpus_revision"):
        errors.append("labor_review vinculado a corpus anterior")
    maps = {}
    for field in RECORD_FIELDS:
        maps[field] = {item["id"]:item for item in labor[field]}
        if len(maps[field]) != len(labor[field]):
            errors.append("labor_review: IDs duplicados em " + field)
    facts = {item["id"]:item for item in review.get("facts",[])}
    norms = {item["id"]:item for item in review.get("norms",[])}
    issues = {item["id"]:item for item in review.get("issues",[])}
    requests = {item["id"]:item for item in review.get("requests",[])}
    assertions = {item["fact_id"]:item for item in review.get("assertion_reviews",[])}
    relationships, periods, instruments, topics = (maps[key] for key in RECORD_FIELDS[:4])
    catalog = topics_catalog()
    scope = labor["scope"]
    selected = set(scope["topic_ids"])
    excluded = {item["topic_id"] for item in scope["excluded_topics"]}
    if not selected or not selected | excluded <= set(catalog):
        errors.append("labor_review: selecionar temas existentes e pertinentes")
    if selected & excluded or len(excluded) != len(scope["excluded_topics"]):
        errors.append("labor_review: seleção/exclusão de temas contraditória ou duplicada")
    if scope["mode"] == "integral" and selected | excluded != set(catalog):
        errors.append("Análise integral trabalhista deve examinar ou afastar fundamentadamente cada tema")
    if review.get("task") == "audit" and scope["mode"] != "integral":
        errors.append("Auditoria trabalhista solicitada exige escopo integral")
    if not relationships and not scope["contextual_limitations"]:
        errors.append("Relação não identificada exige delimitação contextual")

    def refs(item, field, known, label=None):
        if not set(item.get(field,[])) <= set(known):
            errors.append(str(item.get("id","registro")) + ": referência inexistente em " + (label or field))

    for field in RECORD_FIELDS:
        for item in labor[field]:
            for key, known in (("fact_ids",facts),("norm_ids",norms),("issue_ids",issues),
                               ("request_ids",requests),("period_ids",periods)):
                refs(item,key,known)
    for relation in relationships.values():
        if relation["status"] == "established" and (not relation["fact_ids"] or not relation["norm_ids"] or relation["regime"] in {"unknown","disputed"}):
            errors.append(relation["id"] + ": enquadramento estabelecido sem fatos/base/regime confirmados")
    for period in periods.values():
        if period["relationship_id"] not in relationships:
            errors.append(period["id"] + ": relação contratual inexistente")
        if period["start"] and period["end"] and period["start"] > period["end"]:
            errors.append(period["id"] + ": período contratual invertido")
        if period["status"] == "established":
            if not period["start"] or not period["fact_ids"] or not period["norm_ids"]:
                errors.append(period["id"] + ": período estabelecido sem marco, fatos e normas")
            dates = {str(value) for fid in period["fact_ids"] for key,value in assertions.get(fid,{}).get("atoms",{}).items()
                     if key in {"date","period_start","period_end"} and value}
            if any(bound and bound not in dates for bound in (period["start"],period["end"])):
                errors.append(period["id"] + ": marco contratual não reconferido nas afirmações atômicas")
    for instrument in instruments.values():
        norm = norms.get(instrument["norm_id"])
        if not norm:
            errors.append(instrument["id"] + ": instrumento coletivo sem norma existente")
            continue
        if norm.get("kind") != "collective_instrument":
            errors.append(instrument["id"] + ": classificar a fonte como instrumento coletivo")
        if instrument["effective_from"] > instrument["effective_until"]:
            errors.append(instrument["id"] + ": vigência coletiva invertida")
        if instrument["instrument_type"] == "ACT" and not instrument["employer_scope"]:
            errors.append(instrument["id"] + ": ACT sem empregadores abrangidos")
        clause_ids = [clause["id"] for clause in instrument["clauses"]]
        if len(clause_ids) != len(set(clause_ids)):
            errors.append(instrument["id"] + ": cláusulas duplicadas")
        for clause in instrument["clauses"]:
            if clause["quote"] not in norm.get("official_text",""):
                errors.append(instrument["id"] + ": cláusula ausente do texto integral registrado")
    covered_issues, covered_topics = set(), set()
    for topic in topics.values():
        issue = issues.get(topic["issue_id"])
        topic_spec = catalog.get(topic["topic_id"])
        if not issue or not topic_spec or topic["topic_id"] not in selected:
            errors.append(topic["id"] + ": questão/tema não selecionado ou inexistente")
            continue
        covered_issues.add(topic["issue_id"])
        covered_topics.add(topic["topic_id"])
        if not set(topic["fact_ids"]) <= set(issue.get("fact_ids",[])) or not set(topic["norm_ids"]) <= set(issue.get("norm_ids",[])):
            errors.append(topic["id"] + ": fatos/normas divergem da questão vinculada")
        for rid in topic["request_ids"]:
            if topic["issue_id"] not in requests.get(rid,{}).get("issue_ids",[]):
                errors.append(topic["id"] + ": pedido pertence a outra questão")
        checks = {item["check_id"]:item for item in topic["checks"]}
        if len(checks) != len(topic["checks"]) or set(checks) != set(topic_spec["checks"]):
            errors.append(topic["id"] + ": conferir exatamente os requisitos do tema " + topic["topic_id"])
        for check in topic["checks"]:
            refs(check,"fact_ids",facts); refs(check,"norm_ids",norms)
            if check["status"] == "supported" and not (check["fact_ids"] or check["norm_ids"]):
                errors.append(topic["id"] + ": requisito apoiado sem fonte")
        if topic["status"] == "applicable" and not topic["norm_ids"]:
            errors.append(topic["id"] + ": conclusão aplicável sem base normativa")
        burden = topic["burden"]
        refs(burden,"norm_ids",norms); refs(burden,"decision_fact_ids",facts)
        if burden["holder"] == "dynamic" and not (burden["norm_ids"] and burden["decision_fact_ids"]):
            errors.append(topic["id"] + ": distribuição dinâmica exige regra e decisão vinculadas")
        for check in topic["collective_checks"]:
            instrument = instruments.get(check["instrument_id"])
            if not instrument:
                errors.append(topic["id"] + ": instrumento coletivo inexistente")
                continue
            if not set(check["clause_ids"]) <= {clause["id"] for clause in instrument["clauses"]}:
                errors.append(topic["id"] + ": cláusula coletiva inexistente")
            if check["fit"] == "applicable":
                if instrument["norm_id"] not in topic["norm_ids"] or not check["clause_ids"] or not topic["period_ids"]:
                    errors.append(topic["id"] + ": incidência coletiva sem norma, cláusula e período")
                for pid in topic["period_ids"]:
                    period = periods.get(pid,{})
                    relation = relationships.get(period.get("relationship_id"),{})
                    if not period.get("start") or not period.get("end") or period["start"] < instrument["effective_from"] or period["end"] > instrument["effective_until"]:
                        errors.append(topic["id"] + ": norma coletiva fora do período; decompor períodos e versões")
                    if not scope_matches(relation.get("category",""),instrument["category_scope"]) or not scope_matches(relation.get("territory",""),instrument["territory_scope"],hierarchy=True):
                        errors.append(topic["id"] + ": categoria/território fora do instrumento coletivo")
                    if instrument["employer_scope"] and not set(relation.get("employers",[])) & set(instrument["employer_scope"]):
                        errors.append(topic["id"] + ": empregador fora do instrumento coletivo")
    if covered_topics != selected:
        errors.append("Tema selecionado sem avaliação trabalhista")
    if set(issues) - covered_issues and scope["mode"] == "integral":
        errors.append("Questão jurídica sem avaliação trabalhista no escopo integral")
    for evidence in maps["evidence_checks"].values():
        topic = topics.get(evidence["topic_assessment_id"])
        if not topic or evidence["relationship_id"] not in relationships:
            errors.append(evidence["id"] + ": questão/relação da prova inexistente")
        if any(periods.get(pid,{}).get("relationship_id") != evidence["relationship_id"] for pid in evidence["period_ids"]):
            errors.append(evidence["id"] + ": prova mistura períodos de outra relação")
        for source in evidence["sources"]:
            fact = facts.get(source["fact_id"],{})
            if source["source_index"] >= len(fact.get("sources",[])):
                errors.append(evidence["id"] + ": fonte documental inexistente")
            if topic and source["fact_id"] not in topic["fact_ids"]:
                errors.append(evidence["id"] + ": prova não vinculada à questão examinada")
            if evidence["status"] == "confirmed" and assertions.get(source["fact_id"],{}).get("evidence_status") != "supported":
                errors.append(evidence["id"] + ": prova confirmada apoiada em afirmação disputada ou não comprovada")
        if evidence.get("working_day"):
            refs(evidence["working_day"],"fact_ids",facts)
            if not set(evidence["working_day"]["fact_ids"]) <= {source["fact_id"] for source in evidence["sources"]}:
                errors.append(evidence["id"] + ": marcações usam fontes não conferidas nesta prova")
            try:
                counted = working_day(evidence["working_day"])
                if evidence["status"] == "confirmed" and not any(p.get("start") and p["start"] <= counted["calendar_start"] and
                       (not p.get("end") or counted["calendar_start"] <= p["end"]) for p in (periods.get(pid,{}) for pid in evidence["period_ids"])):
                    errors.append(evidence["id"] + ": marcação fora dos períodos vinculados")
            except (ValueError,KeyError,TypeError) as error:
                errors.append(evidence["id"] + ": " + str(error))
    for health in maps["health_assessments"].values():
        if health["relationship_id"] not in relationships:
            errors.append(health["id"] + ": relação da questão médica inexistente")
        if any(periods.get(pid,{}).get("relationship_id") != health["relationship_id"] for pid in health["period_ids"]):
            errors.append(health["id"] + ": saúde mistura períodos de outra relação")
        if not set(health["fact_ids"]) <= {fid for iid in health["issue_ids"] for fid in issues.get(iid,{}).get("fact_ids",[])}:
            errors.append(health["id"] + ": avaliação médica utiliza fatos de outras questões")
        for key in ("causation","concausation","incapacity","exposure"):
            medical = health[key]
            refs(medical,"fact_ids",facts)
            if not set(medical["fact_ids"]) <= set(health["fact_ids"]):
                errors.append(health["id"] + ": avaliação médica usa fonte de outra análise")
            if medical["status"] == "supported" and not medical["fact_ids"]:
                errors.append(health["id"] + ": nexo/incapacidade/exposição sem prova vinculada")
            if medical["status"] == "supported" and any(assertions.get(fid,{}).get("evidence_status") in {"unproven","contradicted","disputed","client_account"} for fid in medical["fact_ids"]):
                errors.append(health["id"] + ": conclusão médica apoiada em afirmação não comprovada")
    health_issues = {iid for item in labor["health_assessments"] for iid in item["issue_ids"]}
    for topic in topics.values():
        if topic["topic_id"] == "occupational_health" and topic["status"] != "excluded" and topic["issue_id"] not in health_issues:
            errors.append(topic["id"] + ": saúde ocupacional exige avaliação de nexo, exposição e incapacidade separadas")
    for procedure in labor["procedure_reviews"]:
        refs(procedure,"act_fact_ids",facts)
        if procedure["status"] == "verified" and not procedure["norm_ids"]:
            errors.append(procedure["id"] + ": pressuposto processual sem norma")
        if procedure.get("deadline"):
            deadline = procedure["deadline"]
            if procedure["status"] != "verified":
                errors.append(procedure["id"] + ": vencimento informado em pressuposto não confirmado")
            if deadline["trigger_fact_id"] not in facts or deadline["norm_id"] not in norms:
                errors.append(procedure["id"] + ": marco/regra de prazo inexistente")
            if deadline["trigger_fact_id"] not in procedure["act_fact_ids"] or deadline["norm_id"] not in procedure["norm_ids"]:
                errors.append(procedure["id"] + ": marco/regra não vinculados ao pressuposto")
            if assertions.get(deadline["trigger_fact_id"],{}).get("atoms",{}).get("date") != deadline["event_date"]:
                errors.append(procedure["id"] + ": marco de prazo diverge da data reconferida")
            refs(deadline,"calendar_norm_ids",norms)
            if any(item["norm_id"] not in norms for item in deadline["suspensions"]):
                errors.append(procedure["id"] + ": suspensão sem norma existente")
            try:
                count_deadline(deadline)
            except (ValueError,KeyError,TypeError,OverflowError) as error:
                errors.append(procedure["id"] + ": " + str(error))
    international = labor.get("international_checks",[])
    international_norms = {item["norm_id"] for item in international}
    expected_international = {nid for nid,norm in norms.items() if norm.get("kind") == "international_instrument"}
    if international_norms != expected_international or len(international_norms) != len(international):
        errors.append("Conferir ratificação e situação de cada instrumento internacional usado")
    for item in international:
        refs(item,"domestic_norm_ids",norms); refs(item,"status_norm_ids",norms)
        if item["ratification_status"] == "in_force" and not (item["effective_from"] and item["domestic_norm_ids"] and item["status_norm_ids"]):
            errors.append(item["id"] + ": vigência internacional exige marco, ato brasileiro e fonte de situação")
        if item["effective_from"] and item["effective_until"] and item["effective_from"] > item["effective_until"]:
            errors.append(item["id"] + ": vigência internacional invertida")
        if item["ratification_status"] != "in_force":
            if any(thesis.get("characterization") == "consolidated" and item["norm_id"] in thesis.get("norm_ids",[]) for thesis in review.get("theses",[])):
                errors.append(item["id"] + ": instrumento sem vigência confirmada não sustenta tese consolidada")
            if any(application.get("norm_id") == item["norm_id"] and application.get("method") == "direct" and application.get("result") == "applied" for application in review.get("norm_applications",[])):
                errors.append(item["id"] + ": aplicação direta de instrumento sem vigência confirmada")
    calculation_scope = labor["calculation_scope"]
    refs(calculation_scope,"title_fact_ids",facts)
    if labor.get("calculation_set"):
        if calculation_scope["status"] != "calculated":
            errors.append("Cálculo fornecido sem declaração de cálculo executado")
        payload = labor["calculation_set"]
        if payload.get("corpus_revision") != labor["corpus_revision"]:
            errors.append("Cálculo trabalhista vinculado a corpus anterior")
        try:
            result = compute_calculations(payload,facts=facts,norms=norms,requests=requests)
            if payload["purpose"] == "liquidation" and not (calculation_scope["title_fact_ids"] and calculation_scope["title_scope_analysis"]):
                errors.append("Liquidação exige título e delimitação de seus comandos")
            for item in result["items"]:
                if item["relationship_id"] not in relationships:
                    errors.append(item["id"] + ": relação da parcela inexistente")
                    continue
                relation_facts = set(relationships[item["relationship_id"]]["fact_ids"])
                for period in periods.values():
                    if period["relationship_id"] == item["relationship_id"]:
                        relation_facts.update(period["fact_ids"])
                if not set(item["source_fact_ids"]) <= relation_facts:
                    errors.append(item["id"] + ": parâmetro factual fora da relação/período da parcela")
                for rid in item["request_ids"]:
                    linked = [topic for topic in topics.values() if rid in topic["request_ids"]]
                    if not linked or not set(item["source_fact_ids"]) <= {fid for topic in linked for fid in topic["fact_ids"]}:
                        errors.append(item["id"] + ": fatos do cálculo não sustentam o pedido vinculado")
            for parameter in payload["inputs"]:
                if parameter["unit"] == "money" and len(parameter["fact_ids"]) == 1:
                    amount = assertions.get(parameter["fact_ids"][0],{}).get("atoms",{}).get("amount")
                    if amount is not None and decimal_value(amount) != decimal_value(parameter["value"]):
                        errors.append(parameter["id"] + ": valor diverge da afirmação reconferida")
        except (ValueError,KeyError,TypeError) as error:
            errors.append("Cálculo trabalhista: " + str(error))
    try:
        from .labor_workflow import validate_workflow
    except ImportError:
        from labor_workflow import validate_workflow
    errors.extend(validate_workflow(review, memory))
    return list(dict.fromkeys(errors))


def labor_findings(review: dict) -> list[dict]:
    labor = review.get("labor_review",{})
    if not labor or validate_contract(labor,"labor_review.schema.json"):
        return []
    findings = []
    topics = {item["id"]:item for item in labor["topic_assessments"]}

    def add(code, issue_ids, description, action, effect="qualifies_conclusion", category="evidence"):
        if issue_ids:
            findings.append({"code":code,"category":category,"severity":"material" if effect != "none" else "advisory",
                             "scope":"issue","target_ids":issue_ids,"description":description,
                             "impact":"Limitação restrita às questões e pedidos dependentes.",
                             "delivery_effect":effect,"required_action":action})

    for topic in topics.values():
        for gap in topic["gaps"]:
            add("LABOR_GAP_" + topic["id"],[topic["issue_id"]],gap["description"],gap["action"],gap["effect"])
        if topic["status"] == "pending":
            try:
                from .labor_workflow import drafting_possible
            except ImportError:
                from labor_workflow import drafting_possible
            future_proof = topic.get("pending_cause") == "future_proof" and drafting_possible(review, topic["issue_id"])
            add("LABOR_TOPIC_PENDING_" + topic["id"],[topic["issue_id"]],"Questão trabalhista ainda indeterminada.",
                "Executar o plano de prova." if future_proof else "Resolver os dados/requisitos identificados nesta questão.",
                "qualifies_conclusion" if future_proof else "blocks_issue","evidence" if future_proof else "legal")
        elif topic["status"] == "applicable" and any(check["status"] in {"pending","disputed"} for check in topic["checks"]):
            add("LABOR_CHECK_LIMIT_" + topic["id"],[topic["issue_id"]],"Há requisito trabalhista pendente ou disputado.",
                "Conferir a premissa e ajustar a conclusão à prova disponível.")
        if topic["burden"]["holder"] == "unknown":
            add("LABOR_BURDEN_" + topic["id"],[topic["issue_id"]],"Distribuição do ônus ainda não definida.",
                "Verificar regra especial e decisões sobre o ônus.","qualifies_conclusion","procedural")
        if any(check["fit"] == "pending" for check in topic["collective_checks"]):
            add("LABOR_COLLECTIVE_" + topic["id"],[topic["issue_id"]],"Incidência coletiva ainda não confirmada.",
                "Conferir enquadramento, âmbito, cláusula e vigência.","qualifies_conclusion","legal")
    for evidence in labor["evidence_checks"]:
        topic = topics.get(evidence["topic_assessment_id"])
        if topic and evidence["status"] != "confirmed":
            add("LABOR_EVIDENCE_" + evidence["id"],[topic["issue_id"]],evidence["reason"],
                "Reconciliar as fontes e preservar a prova contrária.")
    for health in labor["health_assessments"]:
        if any(health[key]["status"] in {"pending","disputed"} for key in ("causation","concausation","incapacity","exposure")):
            add("LABOR_HEALTH_" + health["id"],health["issue_ids"],"Nexo, exposição ou incapacidade têm limites probatórios.",
                "Conferir a prova técnica e formular os quesitos pertinentes.")
    for procedure in labor["procedure_reviews"]:
        if procedure["status"] == "limited":
            add("LABOR_PROCEDURE_" + procedure["id"],procedure["issue_ids"],procedure["reason"],
                "Conferir o ato, regra e calendário pertinentes.","qualifies_conclusion","procedural")
    for international in labor.get("international_checks",[]):
        if international["ratification_status"] == "unknown":
            issue_ids = [item["id"] for item in review.get("issues",[]) if international["norm_id"] in item.get("norm_ids",[])]
            add("LABOR_INTERNATIONAL_" + international["id"],issue_ids,"Situação de ratificação/vigência ainda não confirmada.",
                "Conferir NORMLEX e ato brasileiro correspondente.","qualifies_conclusion","legal")
    try:
        from .labor_workflow import workflow_findings
    except ImportError:
        from labor_workflow import workflow_findings
    return findings + workflow_findings(review)


def labor_markdown(review: dict) -> str:
    try:
        from .legal_index import anchor, safe_text
    except ImportError:
        from legal_index import anchor, safe_text
    labor = review["labor_review"]
    lines = ["# ANÁLISE TRABALHISTA", "", "Corpus: " + labor["corpus_revision"], "",
             "## Relações e períodos", ""]
    def links(item):
        output = []
        for field,kind in (("fact_ids","fact"),("norm_ids","norm"),("request_ids","request"),("issue_ids","issue")):
            output += [f"[{safe_text(identifier)}](indice_juridico.md#{anchor(kind,identifier)})" for identifier in item.get(field,[])]
        if item.get("issue_id"):
            output.append(f"[{safe_text(item['issue_id'])}](indice_juridico.md#{anchor('issue',item['issue_id'])})")
        return " · ".join(output)
    for relation in labor["relationships"]:
        lines += [f"### {safe_text(relation['worker'])} — {safe_text(relation['id'])}", "",
                  safe_text(relation["reason"]), "", "Regime: " + relation["regime"] + ". Categoria: " + safe_text(relation["category"]) + ".", "", links(relation), ""]
    for period in labor["contract_periods"]:
        lines += [f"### {safe_text(period['id'])}", "", f"Período: {period['start'] or 'marco pendente'} a {period['end'] or 'término não delimitado'}.",
                  "", safe_text(period["law_version_analysis"]), "", links(period), ""]
    lines += ["## Questões, fundamentos e pedidos", ""]
    catalog = topics_catalog()
    for topic in labor["topic_assessments"]:
        lines += ["### " + safe_text(topic["id"]) + " — " + safe_text(catalog[topic["topic_id"]]["label"]), "",
                  safe_text(topic["selection_reason"]), "", safe_text(topic["research_reason"]), "",
                  "Contraponto: " + safe_text(topic["strongest_objection"]), "", "Resposta: " + safe_text(topic["response"]), "",
                  "Ônus: " + safe_text(topic["burden"]["reason"]), "", links(topic), ""]
        for gap in topic["gaps"]:
            lines += ["Providência delimitada: " + safe_text(gap["description"]) + " " + safe_text(gap["action"]), ""]
    lines += ["## Provas e saúde ocupacional", ""]
    for evidence in labor["evidence_checks"]:
        lines += [safe_text(evidence["id"]) + ": " + safe_text(evidence["reason"]), ""]
        for source in evidence["sources"]:
            lines += [f"[{safe_text(source['fact_id'])}](indice_juridico.md#{anchor('fact',source['fact_id'])})", ""]
    for health in labor["health_assessments"]:
        lines += [safe_text(health["id"]) + ": " + safe_text(health["consequences_reason"]), "", links(health), ""]
    lines += ["## Cálculos e providências processuais", "", safe_text(labor["calculation_scope"]["reason"]), ""]
    for procedure in labor["procedure_reviews"]:
        lines += [safe_text(procedure["id"]) + ": " + safe_text(procedure["reason"]), "", links(procedure), ""]
    if labor.get("workflow"):
        try:
            from .labor_workflow import workflow_markdown
        except ImportError:
            from labor_workflow import workflow_markdown
        lines += ["", workflow_markdown(review)]
    return "\n".join(lines)


def labor_entries(review: dict) -> list[dict]:
    """Flatten declared labor records for indexing and dependency propagation."""
    labor = review.get("labor_review",{})
    entries = []
    for field in (*RECORD_FIELDS,"international_checks"):
        for item in labor.get(field,[]):
            fact_ids = list(item.get("fact_ids",[])) + list(item.get("act_fact_ids",[]))
            fact_ids += [source["fact_id"] for source in item.get("sources",[]) if source.get("fact_id")]
            norm_ids = list(item.get("norm_ids",[])) + list(item.get("domestic_norm_ids",[])) + list(item.get("status_norm_ids",[]))
            entries.append({**item,"id":field + ":" + item["id"],"record_id":item["id"],"record_field":field,
                            "fact_ids":list(dict.fromkeys(fact_ids)),
                            "norm_ids":list(dict.fromkeys(norm_ids)),
                            "label":item.get("reason") or item.get("selection_reason") or item.get("law_version_analysis") or item.get("consequences_reason") or item["id"]})
            if field == "collective_instruments":
                for clause in item["clauses"]:
                    entries.append({**clause,"id":field + ":" + item["id"] + ":clause:" + clause["id"],
                                    "record_id":clause["id"],"record_field":"collective_clause",
                                    "norm_ids":[item["norm_id"]],"label":clause["provision"] + " — " + clause["quote"]})
    payload = labor.get("calculation_set",{})
    for field in ("inputs","items"):
        for item in payload.get(field,[]):
            entries.append({**item,"id":"calculation_" + field + ":" + item["id"],"record_id":item["id"],
                            "record_field":"calculation_" + field,"label":item["reason"]})
    try:
        from .labor_workflow import workflow_entries
    except ImportError:
        from labor_workflow import workflow_entries
    return entries + workflow_entries(review)


def main() -> int:
    parser = argparse.ArgumentParser(description="Confere relações, períodos, cláusulas, provas e cálculos trabalhistas na revisão v4")
    parser.add_argument("review",type=Path)
    args = parser.parse_args()
    try:
        review = json.loads(args.review.read_text(encoding="utf-8-sig"))
        errors = validate_contract(review,"legal_review.schema.json")
        if not errors:
            errors = validate_labor(review)
        print(json.dumps({"errors":errors,"status":"declared_links_checked" if not errors else "correction_required",
                          "findings":labor_findings(review) if not errors else []},ensure_ascii=False,indent=2))
        return 1 if errors else 0
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
