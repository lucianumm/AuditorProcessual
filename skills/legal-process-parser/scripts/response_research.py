"""Per-response official consultation and attributed legal/cause review.

HTTP collection actually runs here. Host browser references remain self-reported.
Hashes prove binding/integrity, not that a source entails an authored conclusion.
"""
from __future__ import annotations

import argparse
import json
import re
import uuid
from http.client import HTTPException
from datetime import datetime, timezone
from pathlib import Path

try:
    from .case_memory import atomic_json, atomic_text, identity
    from .contracts import validate_contract
    from .research_memory import research_revision
    from .research_sources import capture
    from .source_records import official_url, inspect_source_record, record_browser_observation, record_unavailable_source, same_source_url
    from .artifact_tracking import track_artifacts
    from .citation_check import check_record, contains, quote_words, PRECEDENT_STATUS
except ImportError:
    from case_memory import atomic_json, atomic_text, identity
    from contracts import validate_contract
    from research_memory import research_revision
    from research_sources import capture
    from source_records import official_url, inspect_source_record, record_browser_observation, record_unavailable_source, same_source_url
    from artifact_tracking import track_artifacts
    from citation_check import check_record, contains, quote_words, PRECEDENT_STATUS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp(value: str) -> datetime:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.utcoffset() is None:
        raise ValueError("Registro de pesquisa exige timestamp com timezone")
    return moment.astimezone(timezone.utc)


def target_hash(artifact: dict) -> str:
    return identity({k: v for k, v in artifact.items() if k != "response_research"})


def session_path(output: Path, response_id: str) -> Path:
    if not isinstance(response_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", response_id):
        raise ValueError("ID de resposta inválido")
    path = (output / "response_research" / response_id / "session.json").resolve()
    if not path.is_relative_to(output.resolve()):
        raise ValueError("Registro de resposta fora do caso")
    return path


def load_session(output: Path, response_id: str) -> dict:
    value = json.loads(session_path(output, response_id).read_text(encoding="utf-8"))
    digest = value.pop("integrity_hash", None)
    if digest != identity(value):
        raise ValueError("Registro de consulta alterado ou incompleto")
    value["integrity_hash"] = digest
    return value


def store_session(output: Path, value: dict) -> None:
    path = session_path(output, value["response_id"])
    names = [path.relative_to(output.resolve()).as_posix()]
    if path.is_file():
        previous = path.read_text(encoding="utf-8")
        history = path.parent / "history" / (identity(previous) + ".json")
        atomic_text(history, previous)
        names.append(history.relative_to(output.resolve()).as_posix())
    value.pop("integrity_hash", None)
    value["integrity_hash"] = identity(value)
    atomic_json(path, value)
    track_artifacts(output, names)


def begin_response(output: Path, issue_ids: list[str], request_reference: str, *, response_id: str | None = None) -> dict:
    if not issue_ids or len(set(issue_ids)) != len(issue_ids) or not request_reference.strip():
        raise ValueError("Indicar questões e referência do pedido efetivamente recebido")
    rid = response_id or uuid.uuid4().hex
    if session_path(output, rid).exists():
        raise ValueError("Resposta já registrada; criar ID novo para a nova consulta")
    memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8"))
    value = {"schema_version": "1.0", "response_id": rid, "request_reference": request_reference,
             "started_at": utc_now(), "corpus_revision": memory["corpus_revision"], "issue_ids": issue_ids,
             "consultations": [], "bound_artifact_hash": None, "status": "awaiting_consultation"}
    store_session(output, value)
    return value


def consult_http(output: Path, response_id: str, issue_id: str, norm_id: str,
                 url: str, *, alternatives: list[str] | None = None, purpose: str) -> dict:
    state = load_session(output, response_id)
    if state["bound_artifact_hash"] or issue_id not in state["issue_ids"] or not norm_id or not purpose.strip():
        raise ValueError("Consulta precisa de resposta aberta, questão pertinente e finalidade")
    targets = list(dict.fromkeys([url] + (alternatives or [])))
    if len(targets) > 4 or any(not official_url(t) for t in targets):
        raise ValueError("Selecionar até quatro fontes oficiais pertinentes, sem tentativas idênticas")
    result = None
    for target in targets:
        row = {"issue_id": issue_id, "norm_id": norm_id, "purpose": purpose, "requested_url": target,
               "attempted_at": utc_now(), "method": "official_http_capture"}
        try:
            record = capture(target, output, response_id=response_id)
            row.update(status="consulted", source_record_id=record["capture_id"], url=record["url"],
                       observed_at=record["captured_at"])
        except (OSError, ValueError, ImportError, LookupError, HTTPException, UnicodeError) as error:
            row.update(status="unavailable", reason=str(error) or type(error).__name__,
                       reason_code="blocked_by_portal" if type(error).__name__ == "SourceBlocked" else "unavailable")
        state["consultations"].append(row)
        result = row
        if row["status"] == "consulted":
            break
    state["status"] = "consultations_recorded"
    store_session(output, state)
    return result


def consult_browser(output: Path, response_id: str, issue_id: str, norm_id: str, *, purpose: str, **observation) -> dict:
    state = load_session(output, response_id)
    if state["bound_artifact_hash"] or issue_id not in state["issue_ids"] or not norm_id or not purpose.strip():
        raise ValueError("Observação precisa de resposta aberta, questão pertinente e finalidade")
    record = record_browser_observation(output, response_id=response_id, **observation)
    row = {"issue_id": issue_id, "norm_id": norm_id, "purpose": purpose, "status": "consulted",
           "source_record_id": record["source_record_id"], "url": record["url"],
           "method": "browser_observation", "observed_at": record["observed_at"]}
    state["consultations"].append(row)
    state["status"] = "consultations_recorded"
    store_session(output, state)
    return row


def record_unavailable_attempt(output: Path, response_id: str, issue_id: str, norm_id: str, *, url: str, reason: str,
                               attempt_reference: str, purpose: str) -> dict:
    """Preserve a real failed browser or upload attempt; it never supports a conclusion."""
    state = load_session(output, response_id)
    if state["bound_artifact_hash"] or issue_id not in state["issue_ids"] or not norm_id or not purpose.strip():
        raise ValueError("Tentativa precisa de resposta aberta, questão pertinente e finalidade")
    record = record_unavailable_source(output, url=url, accessed_on=datetime.now(timezone.utc).date().isoformat(),
                                       reason=reason, attempt_reference=attempt_reference, issue_ids=[issue_id])
    row = {"issue_id": issue_id, "norm_id": norm_id, "purpose": purpose, "status": "unavailable", "requested_url": url,
           "attempted_at": utc_now(), "method": "declared_attempt", "reason": reason,
           "reason_code": "blocked_by_portal" if "bloque" in reason.lower() or "blocked" in reason.lower() else "unavailable",
           "unavailable_record_id": record["source_record_id"]}
    state["consultations"].append(row)
    state["status"] = "consultations_recorded"
    store_session(output, state)
    return row


def fact_dates(review: dict, norm_id: str, issue_id: str) -> list[str]:
    """Dates that decide which version of a provision applies to this issue."""
    dates = [d.get("date") for row in review.get("normative_map", []) if row.get("norm_id") == norm_id
             for d in row.get("relevant_dates", [])]
    issue = next((i for i in review.get("issues", []) if i.get("id") == issue_id), {})
    for assertion in review.get("assertion_reviews", []):
        if assertion.get("fact_id") in issue.get("fact_ids", []):
            atoms = assertion.get("atoms", {})
            dates += [atoms.get(k) for k in ("date", "period_start")]
    return sorted({d for d in dates if isinstance(d, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)})


def verify_session(output: Path, response_id: str, review: dict, quotes: dict | None = None) -> list[dict]:
    """Structural check of every consulted source against the cited provision, before writing."""
    state = load_session(output, response_id)
    norms = {r["id"]: r for r in review.get("norms", [])}
    rows = []
    for row in state["consultations"]:
        if row["status"] != "consulted" or row["norm_id"] not in norms:
            rows.append({"norm_id": row["norm_id"], "issue_id": row["issue_id"], "status": row["status"],
                         "reason": row.get("reason"), "reason_code": row.get("reason_code")})
            continue
        sid = row["source_record_id"]
        record = json.loads((output / "research_sources" / (sid + ".json")).read_text(encoding="utf-8"))
        norm = norms[row["norm_id"]]
        quote = (quotes or {}).get(row["norm_id"], norm.get("quote", ""))
        check = check_record(record, norm.get("provision", ""), quote, fact_dates=fact_dates(review, row["norm_id"], row["issue_id"]))
        check.update(norm_id=row["norm_id"], issue_id=row["issue_id"], source_record_id=sid,
                     same_url_as_norm=same_source_url(record.get("url"), norm.get("url")) or same_source_url(record.get("requested_url"), norm.get("url")),
                     evidence_level=inspect_source_record(record, output)["evidence_level"])
        check.pop("segment", None)
        rows.append(check)
    return rows


def validate_response(output: Path, payload: dict, review: dict, artifact: dict | None = None) -> dict:
    errors = validate_contract(payload, "response_research.schema.json")
    result = {"errors": errors, "status": "invalid" if errors else "not_checked",
              "scope": "declared coverage, current consultation and artifact integrity; legal entailment is authored",
              "source_levels": {}, "issue_statuses": {}, "calculation": None, "citation_checks": []}
    if errors:
        return result
    try:
        state = load_session(output, payload["response_id"])
        memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8"))
        if payload["artifact_hash"] != target_hash(artifact or review):
            errors.append("Pesquisa vinculada a outro conteúdo de resposta")
        if state["bound_artifact_hash"] not in {None, payload["artifact_hash"]}:
            errors.append("Consulta já vinculada a outra resposta; executar nova consulta")
        if memory["corpus_revision"] != state["corpus_revision"] or review.get("corpus_revision") != memory["corpus_revision"]:
            errors.append("Corpus alterado: reanalisar os novos dados antes de responder")
        if payload["research_revision"] != research_revision(output):
            errors.append("Revisão das fontes mudou durante a preparação da resposta")
        completed = timestamp(payload["checked_at"])
        if completed < timestamp(state["started_at"]) or completed > timestamp(utc_now()):
            errors.append("Data de conferência fora do intervalo real da resposta")
        issues = {r["id"]: r for r in review.get("issues", [])}
        norms = {r["id"]: r for r in review.get("norms", [])}
        facts = {r["id"]: r for r in review.get("facts", [])}
        assertions = {r["fact_id"]: r for r in review.get("assertion_reviews", [])}
        requests = {r["id"]: r for r in review.get("requests", [])}
        paragraphs = {r["id"]: r for r in (artifact or review).get("paragraphs", [])}
        if set(payload["issue_ids"]) != set(state["issue_ids"]) or not set(payload["issue_ids"]) <= set(issues):
            errors.append("Escopo da resposta difere das questões recebidas e analisadas")
        if artifact and artifact.get("issue_ids") and set(artifact["issue_ids"]) != set(payload["issue_ids"]):
            errors.append("Consulta deve corresponder ao capítulo ou consolidação selecionados")
        current = {(r.get("source_record_id"), r["norm_id"], r["issue_id"]): r for r in state["consultations"] if r["status"] == "consulted"}
        successful = set()
        source_texts = {}
        for citation in payload["citations"]:
            key = (citation["source_record_id"], citation["norm_id"], citation["issue_id"])
            operation = current.get(key)
            if not operation or citation["norm_id"] not in norms or citation["issue_id"] not in payload["issue_ids"]:
                errors.append("Citação não corresponde a consulta nova e pertinente: " + citation["norm_id"])
                continue
            sid = citation["source_record_id"]
            if not re.fullmatch(r"[0-9a-f]{64}", sid):
                errors.append("Identidade de fonte inválida")
                continue
            path = (output / "research_sources" / (sid + ".json")).resolve()
            if not path.is_relative_to(output.resolve()):
                raise ValueError("Fonte fora do caso")
            record = json.loads(path.read_text(encoding="utf-8"))
            inspection = inspect_source_record(record, output)
            errors += inspection["errors"]
            result["source_levels"][sid] = inspection["evidence_level"]
            recorded_time = record.get("captured_at") or record.get("observed_at") or ""
            observed = timestamp(recorded_time)
            local_date = datetime.fromisoformat(recorded_time.replace("Z", "+00:00")).date().isoformat()
            if record.get("accessed_on") not in {local_date, observed.date().isoformat()}:
                errors.append("Data de acesso diverge da consulta registrada")
            if record.get("response_id") != payload["response_id"] or not timestamp(state["started_at"]) <= observed <= completed:
                errors.append("Fonte anterior ao pedido ou sem vínculo com a resposta atual")
            if not contains(record.get("text", ""), citation["quote"]):
                errors.append("Trecho da citação ausente da fonte efetivamente consultada")
            if quote_words(citation["quote"]) < 3:
                errors.append("Trecho curto demais para sustentar a citação: " + citation["norm_id"])
            if citation["norm_id"] not in issues[citation["issue_id"]].get("norm_ids", []):
                errors.append("Norma de outra questão na resposta")
            norm = norms[citation["norm_id"]]
            if not any(same_source_url(u, norm.get("url")) for u in (record.get("url"), record.get("requested_url"))):
                errors.append("Fonte consultada difere da URL registrada para a norma: " + citation["norm_id"])
            check = check_record(record, norm.get("provision", ""), citation["quote"],
                                 fact_dates=fact_dates(review, citation["norm_id"], citation["issue_id"]))
            result["citation_checks"].append({"norm_id": citation["norm_id"], "issue_id": citation["issue_id"],
                                              "source_record_id": sid, "status": check["status"], "located": check["located"],
                                              "markers": check["markers"], "findings": check["findings"]})
            errors += [citation["norm_id"] + ": " + f["message"] for f in check["findings"]
                       if f["severity"] == "blocking" and f["code"] not in {"quote_not_in_source", "quote_too_short"}]
            source_texts[sid] = record.get("text", "")
            successful.add((citation["norm_id"], citation["issue_id"]))
        precedent_rows = {(p["norm_id"], p["issue_id"]): p for p in payload.get("precedents", [])}
        expected_precedents = {(nid, iid) for nid, iid in successful if norms[nid].get("kind") == "precedent"}
        if set(precedent_rows) != expected_precedents or len(precedent_rows) != len(payload.get("precedents", [])):
            errors.append("Conferir fundamento, situação e efeitos de cada precedente usado na resposta")
        for key, comparison in precedent_rows.items():
            for prefix in ("holding", "status"):
                sid = comparison[prefix + "_source_id"]
                if (sid, key[0], key[1]) not in current or not contains(source_texts.get(sid, ""), comparison[prefix + "_excerpt"]):
                    errors.append("Precedente sem consulta atual do fundamento ou da situação: " + key[0])
            if quote_words(comparison["status_excerpt"]) < 3 or not PRECEDENT_STATUS.search(comparison["status_excerpt"]):
                errors.append("Trecho de situação do precedente não registra situação (tese firmada, vigente, cancelada, suspensa, julgada etc.): " + key[0])
        declared = set()
        rendered_requests = set()
        if len({c["id"] for c in payload["causes"]}) != len(payload["causes"]):
            errors.append("Causas/fundamentos com identificadores duplicados")
        for cause in payload["causes"]:
            iid = cause["issue_id"]
            if iid not in payload["issue_ids"]:
                errors.append("Causa de pedir fora do escopo")
                continue
            declared.add(iid)
            if not set(cause["fact_ids"]) <= set(issues[iid]["fact_ids"]) or not set(cause["fact_ids"]) <= set(facts):
                errors.append(cause["id"] + ": causa de pedir usa fato inexistente ou de outra questão")
            if not set(cause["request_ids"]) <= set(requests):
                errors.append(cause["id"] + ": pedido inexistente")
            for rid in cause["request_ids"]:
                if rid in requests and iid not in requests[rid]["issue_ids"]:
                    errors.append(cause["id"] + ": pedido de outra questão")
            rendered_requests.update(cause["request_ids"])
            for pid in cause["paragraph_ids"]:
                paragraph = paragraphs.get(pid)
                if not paragraph or iid not in paragraph.get("issue_ids", []):
                    errors.append(cause["id"] + ": causa de pedir sem parágrafo pertinente")
                elif not set(paragraph.get("fact_ids", [])) <= set(cause["fact_ids"]) or not set(paragraph.get("norm_ids", [])) <= set(cause["norm_ids"]) and cause["status"] != "pending":
                    errors.append(cause["id"] + ": parágrafo usa fatos ou fundamentos fora da causa de pedir")
            if cause["status"] == "supported" and any(assertions.get(fid, {}).get("evidence_status") != "supported" for fid in cause["fact_ids"]):
                errors.append(cause["id"] + ": distinguir apoio normativo de fato relatado ou ainda controvertido")
            if cause["status"] in {"supported", "qualified"}:
                if not cause["norm_ids"] or any((nid, iid) not in successful for nid in cause["norm_ids"]):
                    errors.append(cause["id"] + ": conclusão sem fundamento consultado nesta resposta")
            else:
                attempts = [r for r in state["consultations"] if r["issue_id"] == iid]
                if not attempts or not cause["limitation"]:
                    errors.append(cause["id"] + ": pendência exige tentativa concreta e efeito delimitado")
            ranks = {"supported": 0, "qualified": 1, "pending": 2}
            previous = result["issue_statuses"].get(iid, "supported")
            result["issue_statuses"][iid] = max([previous, cause["status"]], key=ranks.get)
        if declared != set(payload["issue_ids"]):
            errors.append("Desenvolver ou delimitar cada questão da resposta")
        for p in paragraphs.values():
            if not set(p.get("issue_ids", [])) & set(payload["issue_ids"]):
                continue
            for nid in p.get("norm_ids", []):
                pending = all(result["issue_statuses"].get(iid) == "pending" for iid in p["issue_ids"])
                if not pending and not any((nid, iid) in successful for iid in p["issue_ids"]):
                    errors.append(p["id"] + ": afirmação jurídica sem fonte nova vinculada")
            if p.get("norm_ids") and p["id"] not in {pid for c in payload["causes"] for pid in c["paragraph_ids"]}:
                errors.append(p["id"] + ": parágrafo jurídico fora da revisão de causas/fundamentos")
        target_requests = set((artifact or {}).get("request_ids", []))
        if target_requests - rendered_requests:
            errors.append("Pedido do capítulo sem causa de pedir correspondente")
        calculation_set = review.get("labor_review", {}).get("calculation_set")
        relevant_requests = {r["id"] for r in review.get("requests", []) if set(r["issue_ids"]) & set(payload["issue_ids"])}
        if calculation_set and not any(set(item["request_ids"]) & relevant_requests for item in calculation_set["items"]):
            calculation_set = None
        if calculation_set:
            if not payload.get("parameter_review"):
                errors.append("Resposta com cálculo exige conferência da origem e dos critérios dos parâmetros")
            else:
                parameter_errors = validate_contract(payload["parameter_review"], "labor_parameters.schema.json")
                if parameter_errors:
                    raise ValueError("; ".join(parameter_errors))
                try:
                    from .labor_parameters import review_parameters, select_calculations
                except ImportError:
                    from labor_parameters import review_parameters, select_calculations
                calculation_set = select_calculations(calculation_set, relevant_requests, payload["parameter_review"])
                result["calculation"] = review_parameters(calculation_set, payload["parameter_review"], review, payload["citations"], source_texts)
                errors += result["calculation"]["errors"]
        elif payload.get("parameter_review"):
            errors.append("Conferência de parâmetros sem calculation_set na análise")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append("Conferência de resposta incompleta: " + str(error))
    result["errors"] = list(dict.fromkeys(errors))
    result["status"] = "invalid" if result["errors"] else "partial" if "pending" in result["issue_statuses"].values() else "recorded_for_legal_review"
    result["legal_entailment"] = "host_authored_not_machine_certified"
    return result


def response_findings(review: dict, output: Path) -> list[dict]:
    if review.get("response_policy") != "per_response":
        return []
    result = validate_response(output, review.get("response_research", {}), review)
    findings = [{"code": "RESPONSE_SOURCE_PENDING", "category": "legal", "severity": "material",
             "scope": "issue", "target_ids": [iid],
             "description": "Consulta oficial atual ainda insuficiente para a conclusão desta questão.",
             "impact": "Delimitar a conclusão dependente e prosseguir nas questões independentes.",
             "delivery_effect": "blocks_conclusion",
             "required_action": "Consultar fonte oficial pertinente por meio disponível e reexaminar o fundamento."}
            for iid, status in result["issue_statuses"].items() if status == "pending"]
    observed_issues = {c["issue_id"] for c in review.get("response_research", {}).get("citations", [])
                       if result["source_levels"].get(c["source_record_id"]) == "self_recorded_unverified"}
    findings += [{"code": "RESPONSE_BROWSER_DECLARED", "category": "legal", "severity": "material",
                  "scope": "issue", "target_ids": [iid],
                  "description": "Consulta atual de navegador registrada pelo agente, sem atestado independente.",
                  "impact": "Conferir a chamada real, passagem e interpretação.",
                  "delivery_effect": "qualifies_conclusion",
                  "required_action": "Revisar a referência observada e a conclusão jurídica."} for iid in observed_issues]
    attention = {}
    for check in result.get("citation_checks", []):
        for item in check["findings"]:
            if item["severity"] == "qualifying":
                attention.setdefault(check["issue_id"], []).append(check["norm_id"] + ": " + item["message"])
    findings += [{"code": "CITATION_VERSION_ATTENTION", "category": "legal", "severity": "material",
                  "scope": "issue", "target_ids": [iid],
                  "description": "Marca de versão, revogação, controle ou situação na fonte consultada: " + " | ".join(dict.fromkeys(messages)),
                  "impact": "Aplicar a versão da época dos fatos e explicar a incidência antes de concluir.",
                  "delivery_effect": "qualifies_conclusion",
                  "required_action": "Registrar a análise intertemporal ou a situação atual na fundamentação."}
                 for iid, messages in attention.items()]
    return findings


def bind_response(output: Path, payload: dict, review: dict, artifact: dict | None = None) -> dict:
    if load_session(output, payload["response_id"])["bound_artifact_hash"] is not None:
        raise ValueError("Sessão já encerrada; preservar o registro e iniciar uma nova resposta")
    payload = dict(payload, artifact_hash=target_hash(artifact or review), research_revision=research_revision(output), checked_at=utc_now())
    result = validate_response(output, payload, review, artifact)
    if result["errors"]:
        raise ValueError("; ".join(result["errors"]))
    state = load_session(output, payload["response_id"])
    state.update(bound_artifact_hash=payload["artifact_hash"], status="bound", checked_at=payload["checked_at"])
    store_session(output, state)
    directory = session_path(output, payload["response_id"]).parent
    atomic_json(directory / "response.json", payload)
    atomic_json(directory / "validation.json", result)
    lines = ["# FONTES DA RESPOSTA", "", "Escopo: " + ", ".join(payload["issue_ids"]), "",
             "Registro da consulta e da revisão declarada; conferir a interpretação jurídica.", ""]
    state = load_session(output, payload["response_id"])
    for citation in payload["citations"]:
        operation = next(r for r in state["consultations"] if r.get("source_record_id") == citation["source_record_id"])
        check = next((c for c in result["citation_checks"] if c["norm_id"] == citation["norm_id"] and c["source_record_id"] == citation["source_record_id"]), {})
        level = {"verified_http": "conferida por captura HTTP", "self_recorded_unverified": "observada pela IA (não atestada)"}.get(
            result["source_levels"][citation["source_record_id"]], result["source_levels"][citation["source_record_id"]])
        notes = "; ".join(f["message"] for f in check.get("findings", []) if f["severity"] == "qualifying")
        lines += ["- [" + citation["norm_id"] + "](" + operation["url"] + ") · " + citation["issue_id"] + " · " + level
                  + (" · dispositivo localizado" if check.get("located") else "") + (" · atenção: " + notes if notes else "")]
    for row in state["consultations"]:
        if row["status"] == "unavailable" and row["issue_id"] in payload["issue_ids"]:
            lines += ["- Não conferida: " + row.get("requested_url", "") + " · " + row["issue_id"] + " · " + (
                "portal bloqueou acesso automatizado" if row.get("reason_code") == "blocked_by_portal" else str(row.get("reason", "")))]
    calculation_names = []
    if result["calculation"] and result["calculation"].get("arithmetic_status") == "executed":
        try:
            from .labor_calculations import calculation_markdown
        except ImportError:
            from labor_calculations import calculation_markdown
        atomic_json(directory / "calculo.json", result["calculation"])
        atomic_text(directory / "memoria_calculo.md", calculation_markdown(result["calculation"]))
        calculation_names = ["calculo.json", "memoria_calculo.md"]
        lines += ["", "[Memória de cálculo executada desta resposta](memoria_calculo.md)."]
    atomic_text(directory / "fontes.md", "\n".join(lines) + "\n")
    source_link = (directory / "fontes.md").relative_to(output.resolve()).as_posix()
    names = [(directory / name).relative_to(output.resolve()).as_posix() for name in ["response.json", "validation.json", "fontes.md"] + calculation_names]
    report = output / "relatorio_processual.md"
    if report.is_file():
        text = report.read_text(encoding="utf-8")
        link = "[Fontes da resposta " + payload["response_id"] + "](" + source_link + ")"
        if link not in text:
            atomic_text(report, text.rstrip() + "\n\n" + link + ".\n")
            names.append("relatorio_processual.md")
    track_artifacts(output, names, bundle=True)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Pesquisa oficial nova por resposta e conferência de causas/valores")
    parser.add_argument("output", type=Path)
    parser.add_argument("command", choices=["begin", "consult", "browser", "unavailable", "verify", "bind", "validate"])
    parser.add_argument("--id")
    parser.add_argument("--issue", action="append", default=[])
    parser.add_argument("--request-reference", default="")
    parser.add_argument("--norm", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--alternative", action="append", default=[])
    parser.add_argument("--purpose", default="")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--reason", default="")
    parser.add_argument("--attempt-reference", default="")
    args = parser.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
    output = args.output.resolve()
    try:
        if args.command == "begin":
            result = begin_response(output, args.issue, args.request_reference, response_id=args.id)
        elif args.command == "consult":
            if len(args.issue) != 1:
                raise ValueError("Indicar uma questão para a consulta")
            result = consult_http(output, args.id, args.issue[0], args.norm, args.url, alternatives=args.alternative, purpose=args.purpose)
        elif args.command == "browser":
            if args.input is None or len(args.issue) != 1:
                raise ValueError("Indicar --input e uma questão para a observação real do navegador")
            result = consult_browser(output, args.id, args.issue[0], args.norm, purpose=args.purpose, **read(args.input))
        elif args.command == "unavailable":
            if len(args.issue) != 1:
                raise ValueError("Indicar uma questão para a tentativa frustrada")
            result = record_unavailable_attempt(output, args.id, args.issue[0], args.norm, url=args.url, reason=args.reason,
                                                attempt_reference=args.attempt_reference, purpose=args.purpose)
        elif args.command == "verify":
            if args.review is None:
                raise ValueError("Indicar --review com as normas a conferir")
            result = {"checks": verify_session(output, args.id, read(args.review))}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if any(c.get("status") == "blocking" for c in result["checks"]) else 0
        else:
            if args.input is None or args.review is None:
                raise ValueError("Indicar a revisão e o contrato da resposta")
            result = (bind_response if args.command == "bind" else validate_response)(output, read(args.input), read(args.review), read(args.artifact) if args.artifact else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if isinstance(result, dict) and result.get("errors") else 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
