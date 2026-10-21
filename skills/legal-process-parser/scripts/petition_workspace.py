"""Version selected pleading chapters over an actually reviewed case baseline.

Integrity and dependency checks are executable; legal reasoning remains authored.
No model calls, automatic user approval, or automatic assembly.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

try:
    from .case_memory import atomic_json, atomic_text, identity, update_memory
    from .contracts import validate_contract
    from .legal_review import style_findings, validate_review
    from .precision_validation import validate_precision
    from .research_memory import research_revision, changed_authorities
    from .artifact_tracking import track_artifacts
    from .labor_calculations import decimal_value
    from .review_integrity import opposite_polarity
except ImportError:
    from case_memory import atomic_json, atomic_text, identity, update_memory
    from contracts import validate_contract
    from legal_review import style_findings, validate_review
    from precision_validation import validate_precision
    from research_memory import research_revision, changed_authorities
    from artifact_tracking import track_artifacts
    from labor_calculations import decimal_value
    from review_integrity import opposite_polarity

STATE = "petition_workspace/workspace.json"
MARKERS = ("<!-- petition-workspace:start -->", "<!-- petition-workspace:end -->")


def archive_markdown(output: Path, name: str, text: str) -> list[str]:
    # Preserve exact source text and a navigable copy with rebased local links.
    try:
        from .validate_links import LINK_RE
    except ImportError:
        from validate_links import LINK_RE
    destination = inside(output, name)
    def rebase(match):
        target = match.group(1)
        if target.startswith(("http://", "https://", "mailto:", "data:", "#")):
            return match.group(0)
        path, sep, fragment = target.partition("#")
        if not path or path.startswith("<"):
            return match.group(0)
        try:
            candidate = inside(output, path)
        except ValueError:
            # A link outside the case folder is preserved as written; archiving must not abort.
            return match.group(0)
        relative = os.path.relpath(candidate, destination.parent).replace("\\", "/")
        whole = match.group(0)
        # Rewrite only the destination "](...)", never the link text that may repeat the path.
        position = whole.rfind("](" + target)
        if position < 0:
            return whole
        return whole[:position + 2] + relative + (sep + fragment if sep else "") + whole[position + 2 + len(target):]
    atomic_text(destination, LINK_RE.sub(rebase, text))
    atomic_text(inside(output, name + ".snapshot.txt"), text)
    return [name, name + ".snapshot.txt"]


def safe_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ValueError("Identificador de capítulo inválido")
    return value


def inside(output: Path, name: str) -> Path:
    path = (output / name).resolve()
    if not path.is_relative_to(output.resolve()):
        raise ValueError("Arquivo do trabalho fora do diretório do caso")
    return path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_workspace(output: Path) -> tuple[dict, dict]:
    state = read_json(inside(output, STATE))
    digest = state.pop("integrity_hash", None)
    if digest != identity(state):
        raise ValueError("Registro de capítulos adulterado ou incompleto")
    state["integrity_hash"] = digest
    baseline = read_json(inside(output, state["baseline_path"]))
    if identity(baseline) != state["baseline_hash"]:
        raise ValueError("Análise-base adulterada")
    for cid, chapter in state["chapters"].items():
        safe_id(cid)
        record = read_json(inside(output, chapter["path"]))
        if identity(record) != chapter["hash"] or record["id"] != cid:
            raise ValueError("Versão de capítulo adulterada: " + cid)
    return state, baseline


def current_base(output: Path, review: dict) -> dict:
    if review.get("schema_version") != "4.0":
        raise ValueError("A elaboração incremental exige a revisão v4 da análise integral")
    memory = update_memory(output)
    errors = validate_contract(review, "legal_review.schema.json")
    if not errors:
        errors += validate_review(review, memory) + validate_precision(review, memory, output)
    if review.get("research_revision") != research_revision(output):
        errors.append("Atualizar a revisão das fontes jurídicas consultadas")
    if errors:
        raise ValueError("Análise-base precisa de atualização: " + "; ".join(dict.fromkeys(errors)))
    return memory


def dependencies(review: dict, issue_ids: list[str]) -> dict:
    known = {i["id"]: i for i in review["issues"]}
    if not issue_ids or len(set(issue_ids)) != len(issue_ids) or not set(issue_ids) <= set(known):
        raise ValueError("Selecionar questões existentes e sem duplicação")
    issues = [known[i] for i in issue_ids]
    fids = {f for i in issues for f in i["fact_ids"]}
    nids = {n for i in issues for n in i["norm_ids"]}
    facts = [f for f in review["facts"] if f["id"] in fids]
    cids = {f.get("client_record_id") for f in facts}
    selected = lambda field, key, ids: [r for r in review.get(field, []) if r.get(key) in ids]
    result = {"issues": issues, "facts": facts,
              "norms": selected("norms", "id", nids),
              "assertion_reviews": selected("assertion_reviews", "fact_id", fids),
              "normative_map": selected("normative_map", "norm_id", nids),
              "precedent_comparisons": selected("precedent_comparisons", "norm_id", nids),
              "client_records": selected("client_records", "id", cids),
              "strategy": review["strategy"], "piece_type": review.get("piece_type"),
              "piece_assessment": review.get("piece_assessment"),
              "requests": [r for r in review["requests"] if set(r["issue_ids"]) & set(issue_ids)],
              "theses": [t for t in review["theses"] if t["issue_id"] in issue_ids],
              "norm_applications": [r for r in review.get("norm_applications", []) if r.get("issue_id") in issue_ids]}
    tids = {t["id"] for t in result["theses"]}
    result["thesis_reviews"] = selected("thesis_reviews", "thesis_id", tids)
    labor = review.get("labor_review", {})
    result["labor_review"] = {}
    selected_topics = [r for r in labor.get("topic_assessments", []) if r["issue_id"] in issue_ids]
    period_ids = {pid for r in selected_topics for pid in r["period_ids"]}
    relation_ids = {r["relationship_id"] for r in labor.get("contract_periods", []) if r["id"] in period_ids}
    instrument_ids = {c["instrument_id"] for r in selected_topics for c in r["collective_checks"]}
    topic_ids = {r["id"] for r in selected_topics}
    claim_review_ids = {r["id"] for r in labor.get("workflow", {}).get("claim_reviews", []) if r.get("issue_id") in issue_ids}
    for field, rows in labor.items():
        if field == "workflow":
            # Questions and strategy options link through claim reviews and theses, not issue IDs.
            result["labor_review"][field] = {k: [r for r in v if isinstance(r, dict) and (r.get("issue_id") in issue_ids or
                set(r.get("issue_ids", [])) & set(issue_ids) or set(r.get("fact_ids", [])) & fids or
                r.get("claim_review_id") in claim_review_ids or r.get("thesis_id") in tids)]
                if isinstance(v, list) and k != "client_record_ids" else
                [cid for cid in v if cid in cids] if k == "client_record_ids" else v for k, v in rows.items()}
        elif field == "evidence_checks":
            result["labor_review"][field] = [r for r in rows if r.get("topic_assessment_id") in topic_ids]
        elif field == "international_checks":
            result["labor_review"][field] = [r for r in rows if r.get("norm_id") in nids or set(r.get("domestic_norm_ids", [])) & nids]
        elif field in {"relationships", "contract_periods", "collective_instruments"}:
            ids = {"relationships": relation_ids, "contract_periods": period_ids, "collective_instruments": instrument_ids}[field]
            result["labor_review"][field] = [r for r in rows if r["id"] in ids or set(r.get("fact_ids", [])) & fids or
                                            field == "collective_instruments" and r.get("norm_id") in nids]
        elif field == "calculation_set":
            try:
                from .labor_parameters import select_calculations
            except ImportError:
                from labor_parameters import select_calculations
            result["labor_review"][field] = select_calculations(rows, {r["id"] for r in result["requests"]},
                review.get("response_research", {}).get("parameter_review", {}))
        elif field == "calculation_scope":
            result["labor_review"][field] = rows
        elif isinstance(rows, list):
            result["labor_review"][field] = [r for r in rows if r.get("issue_id") in issue_ids or
                set(r.get("issue_ids", [])) & set(issue_ids) or field in {"relationships", "contract_periods", "collective_instruments"}]
    # Source text and structured links, not only cited IDs, determine invalidation.
    return result


def chapter_record(output: Path, chapter: dict) -> dict:
    return read_json(inside(output, chapter["path"]))


def base_pending(output: Path, state: dict) -> bool:
    memory = read_json(inside(output, "case_memory.json"))
    return state["corpus_revision"] != memory["corpus_revision"] or state["research_revision"] != research_revision(output)


def persist(output: Path, state: dict, baseline: dict) -> None:
    state.pop("integrity_hash", None)
    state["integrity_hash"] = identity(state)
    atomic_json(inside(output, STATE), state)
    names = [STATE, state["baseline_path"]]
    lines = ["# CONSTRUÇÃO DA PEÇA POR TESE", "", "Base pendente de reanálise: " + str(state["pending_reanalysis"]).lower(), "",
             "Estados registram versões e manifestação do usuário; não certificam mérito jurídico.", ""]
    for thesis in baseline["theses"]:
        lines += ["- Tese " + thesis["id"] + ": " + thesis["proposition"].replace("\n", " ")]
    lines += ["", "| Capítulo | Estado | Versão |", "|---|---|---|"]
    for cid, chapter in state["chapters"].items():
        record = chapter_record(output, chapter)
        target = "teses/" + cid + ".md"
        heading = record["title"].replace("\n", " ").replace("|", " ")
        body = "# " + heading + "\n\nRASCUNHO — NÃO PROTOCOLAR\n\nEstado: " + chapter["status"] + "\n\n"
        if state["pending_reanalysis"]:
            body += "A análise-base recebeu novos dados e precisa ser atualizada antes de reutilizar este capítulo.\n\n"
        body += "\n\n".join(p["text"] for p in record["paragraphs"]) + "\n"
        atomic_text(inside(output, target), body)
        lines.append("| [" + cid + "](" + target + ") | " + chapter["status"] + " | " + str(len(chapter["history"])) + " |")
        names += [target, chapter["path"]] + chapter["history"]
    board = "\n".join(lines) + "\n"
    atomic_text(inside(output, "mapa_teses.md"), board)
    names.append("mapa_teses.md")
    report = inside(output, "relatorio_processual.md")
    if report.is_file():
        original = report.read_text(encoding="utf-8")
        block = MARKERS[0] + "\n\n## Elaboração da peça\n\n[Mapa de teses e versões](mapa_teses.md).\n\n"
        block += "Análise-base pendente de atualização: " + str(state["pending_reanalysis"]).lower() + ".\n\n" + MARKERS[1]
        if MARKERS[0] in original and MARKERS[1] in original:
            before, rest = original.split(MARKERS[0], 1)
            _, after = rest.split(MARKERS[1], 1)
            updated = before + block + after
        else:
            updated = original.rstrip() + "\n\n" + block + "\n"
        if updated != original:
            archive = "petition_workspace/report_history/" + identity(original) + ".md"
            names += archive_markdown(output, archive, original)
            atomic_text(report, updated)
            names += [archive, "relatorio_processual.md"]
    index = inside(output, "indice_juridico.md")
    if index.is_file():
        original_index = index.read_text(encoding="utf-8")
        if "[Mapa de elaboração](mapa_teses.md)" not in original_index:
            atomic_text(index, original_index.rstrip() + "\n\n[Mapa de elaboração](mapa_teses.md).\n")
            names.append("indice_juridico.md")
    track_artifacts(output, list(dict.fromkeys(names)), bundle=True)


def sync_updates(output: Path) -> None:
    if not inside(output, STATE).is_file():
        return
    state, baseline = load_workspace(output)
    pending = base_pending(output, state)
    if pending != state["pending_reanalysis"]:
        state["pending_reanalysis"] = pending
        if pending:
            invalidate_assembly(output)
        persist(output, state, baseline)


def invalidate_assembly(output: Path) -> None:
    path = inside(output, "peticao_consolidada.md")
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        marker = "# CONSOLIDAÇÃO ANTERIOR — RECONFERIR"
        if not text.startswith(marker):
            archive = "petition_workspace/assemblies/" + identity(text) + "-previous.md"
            names = archive_markdown(output, archive, text)
            atomic_text(path, marker + "\n\nDados ou capítulos foram atualizados. Reconferir e consolidar novamente.\n\n" + text)
            track_artifacts(output, names + ["peticao_consolidada.md"])


def initialize(output: Path, review: dict) -> dict:
    if inside(output, STATE).exists():
        raise ValueError("Trabalho existente: usar refresh para preservar os capítulos")
    current_base(output, review)
    digest = identity(review)
    path = "petition_workspace/analyses/" + digest + ".json"
    atomic_json(inside(output, path), review)
    state = {"schema_version": "1.0", "baseline_path": path, "baseline_hash": digest,
             "corpus_revision": review["corpus_revision"], "research_revision": review["research_revision"],
             "pending_reanalysis": False, "chapters": {}, "analysis_history": [path], "assemblies": []}
    persist(output, state, review)
    return state


def refresh(output: Path, review: dict) -> dict:
    state, old = load_workspace(output)
    current_base(output, review)
    for chapter in state["chapters"].values():
        record = chapter_record(output, chapter)
        try:
            changed = chapter["dependency_hash"] != identity(dependencies(review, record["issue_ids"]))
        except ValueError:
            changed = True
        if changed:
            try:
                from .labor_case_state import compare_reviews
            except ImportError:
                from labor_case_state import compare_reviews
            chapter["status"] = "needs_review"
            chapter["update_reason"] = "Fatos, regras, pedidos, estratégia ou períodos dependentes mudaram."
            delta = compare_reviews(dict(old, paragraphs=record["paragraphs"]), dict(review, paragraphs=record["paragraphs"]))
            chapter["change_impact"] = [r for r in delta["changes"] if set(r["impact"]["issue_ids"]) & set(record["issue_ids"])]
    digest = identity(review)
    if digest != state["baseline_hash"]:
        invalidate_assembly(output)
    path = "petition_workspace/analyses/" + digest + ".json"
    atomic_json(inside(output, path), review)
    state.update(baseline_path=path, baseline_hash=digest, corpus_revision=review["corpus_revision"],
                 research_revision=review["research_revision"], pending_reanalysis=False)
    state["analysis_history"] = list(dict.fromkeys(state["analysis_history"] + [path]))
    persist(output, state, review)
    return state


def packet(output: Path, issue_ids: list[str]) -> dict:
    state, review = load_workspace(output)
    data = dependencies(review, issue_ids)
    data.update(baseline_hash=state["baseline_hash"], pending_reanalysis=base_pending(output, state),
                live_corpus_revision=read_json(inside(output, "case_memory.json"))["corpus_revision"],
                live_research_revision=research_revision(output),
                meaning="Contexto das questões selecionadas. Exportação não comprova compreensão.")
    return data


def context_batch(output: Path, issue_ids: list[str], offset: int = 0, max_chars: int = 12000,
                  expected_revision: str | None = None) -> dict:
    data = packet(output, issue_ids)
    revision = identity(data)
    if offset < 0 or not 1 <= max_chars <= 100000 or offset and not expected_revision:
        raise ValueError("Lote exige offset válido, 1–100000 caracteres e revisão esperada na continuação")
    if expected_revision and expected_revision != revision:
        raise ValueError("Contexto mudou entre lotes; recuperar novamente a partir do início")
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if offset > len(text):
        raise ValueError("Offset fora do contexto")
    end = min(len(text), offset + max_chars)
    return {"context_revision": revision, "issue_ids": issue_ids, "offset": offset, "end": end,
            "total_characters": len(text), "text": text[offset:end], "next_offset": end if end < len(text) else None,
            "pending_reanalysis": data["pending_reanalysis"], "meaning": "Lote integral recuperável, não compreensão certificada."}


def validate_chapter(record: dict, review: dict) -> list[str]:
    errors = validate_contract(record, "petition_chapter.schema.json")
    if errors:
        return errors
    safe_id(record["id"])
    context = dependencies(review, record["issue_ids"])
    maps = {key: {r["id"]: r for r in context[key]} for key in ("facts", "norms", "theses", "requests")}
    if not set(record["thesis_ids"]) <= set(maps["theses"]):
        errors.append("Tese inexistente ou fora das questões selecionadas")
    if any(maps["theses"].get(t, {}).get("role") == "not_pursued" for t in record["thesis_ids"]):
        errors.append("Tese afastada exige reavaliação da análise antes de ser redigida")
    claims = review.get("labor_review", {}).get("workflow", {}).get("claim_reviews", [])
    if any(c["issue_id"] in record["issue_ids"] and c["drafting_basis"] == "needs_material_information" for c in claims):
        errors.append("Informação material pendente limita o capítulo selecionado")
    if not set(record["request_ids"]) <= set(maps["requests"]):
        errors.append("Pedido inexistente ou fora das questões selecionadas")
    if {maps["theses"][t]["issue_id"] for t in record["thesis_ids"] if t in maps["theses"]} != set(record["issue_ids"]):
        errors.append("Cada questão selecionada precisa de tese desenvolvida")
    seen, rendered_requests = set(), set()
    assertions = {a["fact_id"]: a["atoms"] for a in review.get("assertion_reviews", [])}
    for p in record["paragraphs"]:
        try:
            from .prose_review import prose_errors
        except ImportError:
            from prose_review import prose_errors
        errors += [p["id"] + ": " + message for message in prose_errors(p, review)]
        if p["id"] in seen:
            errors.append("Parágrafo duplicado")
        seen.add(p["id"])
        for field, known in (("fact_ids", maps["facts"]), ("norm_ids", maps["norms"]),
                             ("request_ids", record["request_ids"]), ("issue_ids", record["issue_ids"])):
            if not set(p[field]) <= set(known):
                errors.append(p["id"] + ": referência fora do capítulo em " + field)
        if not p["issue_ids"] or not (p["fact_ids"] or p["norm_ids"] or p["request_ids"]):
            errors.append(p["id"] + ": vincular o desenvolvimento às fontes ou pedidos")
        rendered_requests.update(p["request_ids"])
        declared = [a["fact_id"] for a in p["assertions"]]
        if set(declared) != set(p["fact_ids"]) or len(declared) != len(set(declared)):
            errors.append(p["id"] + ": conferir campos factuais para cada fato utilizado")
        for assertion in p["assertions"]:
            atoms = assertions.get(assertion["fact_id"], {})
            for field, value in assertion["fields"].items():
                agrees = field in atoms and value == atoms[field]
                if field == "amount" and value is not None and atoms.get(field) is not None:
                    agrees = decimal_value(value) == decimal_value(atoms[field])
                if not agrees:
                    errors.append(p["id"] + ": campo factual diverge da análise-base: " + field)
        for fid in p["fact_ids"]:
            if fid in maps["facts"] and opposite_polarity(p["text"], maps["facts"][fid]["text"]):
                errors.append(p["id"] + ": negação diverge do fato vinculado")
        errors += [p["id"] + ": " + f for f in style_findings(p["text"], initial=review.get("piece_type") == "inicial")]
    if rendered_requests != set(record["request_ids"]):
        errors.append("Pedido selecionado sem parágrafo correspondente")
    # New facts, authorities and amounts enter via the analysis, never a bypass.
    return list(dict.fromkeys(errors))


def save_chapter(output: Path, record: dict, *, require_response: bool = True) -> dict:
    state, review = load_workspace(output)
    if base_pending(output, state):
        raise ValueError("Reexaminar os novos dados e usar refresh antes de alterar a tese")
    if changed_authorities(review, output):
        raise ValueError("Reexaminar as fontes jurídicas alteradas")
    errors = validate_chapter(record, review)
    if require_response:
        try:
            from .response_research import validate_response
        except ImportError:
            from response_research import validate_response
        research = validate_response(output, record.get("response_research", {}), review, record)
        errors.extend(research["errors"])
        if research["status"] == "partial":
            errors.append("Fundamento atual pendente: delimitar o capítulo e prosseguir nas teses independentes")
    if errors:
        raise ValueError("; ".join(errors))
    cid = safe_id(record["id"])
    digest = identity(record)
    dependency_hash = identity(dependencies(review, record["issue_ids"]))
    prior = state["chapters"].get(cid)
    if prior and prior["hash"] == digest and prior["dependency_hash"] == identity(dependencies(review, record["issue_ids"])):
        return prior
    path = "petition_workspace/chapters/" + cid + "/" + digest + "-" + dependency_hash + ".json"
    atomic_json(inside(output, path), record)
    history = list(dict.fromkeys((prior or {}).get("history", []) + [path]))
    chapter = {"path": path, "hash": digest, "history": history, "status": "draft",
               "dependency_hash": dependency_hash,
               "approvals": (prior or {}).get("approvals", []),
               "version_bases": dict((prior or {}).get("version_bases", {}))}
    chapter["response_policy"] = "per_response" if require_response else "legacy_not_per_response"
    chapter["version_bases"][path] = {"baseline_path": state["baseline_path"], "dependency_hash": dependency_hash}
    state["chapters"][cid] = chapter
    invalidate_assembly(output)
    persist(output, state, review)
    return chapter


def set_status(output: Path, cid: str, status: str, reference: str) -> dict:
    state, review = load_workspace(output)
    chapter = state["chapters"][safe_id(cid)]
    if status not in {"reviewed", "approved"} or not isinstance(reference, str) or not reference.strip():
        raise ValueError("Registrar referência real da revisão ou manifestação do usuário")
    record = chapter_record(output, chapter)
    if base_pending(output, state) or chapter["dependency_hash"] != identity(dependencies(review, record["issue_ids"])):
        raise ValueError("Capítulo desatualizado; conferir e salvar nova versão antes da aprovação")
    chapter["status"] = status
    chapter["approvals"].append({"status": status, "reference": reference, "chapter_hash": chapter["hash"],
                                 "dependency_hash": chapter["dependency_hash"]})
    persist(output, state, review)
    return chapter


def assemble(output: Path, order: list[str], *, allow_drafts: bool = False,
             response: dict | None = None, require_response: bool = True, preview: bool = False) -> dict:
    state, review = load_workspace(output)
    if not order or len(order) != len(set(order)):
        raise ValueError("Indicar os capítulos na ordem desejada, sem duplicação")
    if base_pending(output, state):
        raise ValueError("Conferir a análise-base atualizada antes de consolidar")
    selected, request_owners = [], {}
    for cid in order:
        chapter = state["chapters"][safe_id(cid)]
        record = chapter_record(output, chapter)
        if chapter["status"] == "needs_review" or chapter["dependency_hash"] != identity(dependencies(review, record["issue_ids"])):
            raise ValueError("Capítulo desatualizado: " + cid)
        if chapter["status"] != "approved" and not allow_drafts:
            raise ValueError("Capítulo sem aprovação registrada: " + cid + "; consolidação de rascunhos exige --allow-drafts")
        for rid in record["request_ids"]:
            if rid in request_owners:
                raise ValueError("Pedido repetido nos capítulos " + request_owners[rid] + " e " + cid)
            request_owners[rid] = cid
        selected.append(record)
    tids = {t for c in selected for t in c["thesis_ids"]}
    options = review.get("labor_review", {}).get("workflow", {}).get("strategy_options", [])
    selected_options = [o for o in options if o.get("thesis_id") in tids]
    for option in selected_options:
        if set(option.get("exclusive_with", [])) & {o["id"] for o in selected_options if o.get("scenario_id") == option.get("scenario_id")}:
            raise ValueError("Teses incompatíveis no mesmo cenário; delimitar hipóteses subsidiárias")
    text = "# CONSOLIDAÇÃO DOS CAPÍTULOS SELECIONADOS\n\nRASCUNHO — NÃO PROTOCOLAR\n\n"
    text += "\n\n".join("## " + c["title"].replace("\n", " ") + "\n\n" + "\n\n".join(p["text"] for p in c["paragraphs"]) for c in selected) + "\n"
    artifact = {"issue_ids": sorted({i for c in selected for i in c["issue_ids"]}),
                "request_ids": sorted(request_owners),
                "paragraphs": [{**p, "id": c["id"] + "--" + p["id"]} for c in selected for p in c["paragraphs"]],
                "chapter_hashes": [state["chapters"][cid]["hash"] for cid in order], "text": text}
    if preview:
        return artifact
    if require_response:
        try:
            from .response_research import validate_response
        except ImportError:
            from response_research import validate_response
        checked = validate_response(output, response or {}, review, artifact)
        if checked["errors"] or checked["status"] == "partial":
            raise ValueError("; ".join(checked["errors"]) or "Consolidação com fundamento atual pendente")
    digest = identity(text, [state["chapters"][cid]["hash"] for cid in order])
    archive = "petition_workspace/assemblies/" + digest + ".md"
    archived_names = archive_markdown(output, archive, text)
    atomic_text(inside(output, "peticao_consolidada.md"), text)
    result = {"id": digest, "chapter_ids": order, "chapter_hashes": [state["chapters"][cid]["hash"] for cid in order],
              "path": archive, "uncovered_request_ids": sorted({r["id"] for r in review["requests"]} - set(request_owners)),
              "scope": "selected_chapters_only", "legal_status": "professional_review_required"}
    result["response_policy"] = "per_response" if require_response else "legacy_not_per_response"
    state["assemblies"].append(result)
    persist(output, state, review)
    track_artifacts(output, archived_names + ["peticao_consolidada.md"], bundle=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Análise integral, capítulos versionados e consolidação explícita")
    parser.add_argument("output", type=Path)
    parser.add_argument("command", choices=["init", "refresh", "context", "save", "review", "approve", "preview", "assemble", "status"])
    parser.add_argument("--review", type=Path)
    parser.add_argument("--chapter-file", type=Path)
    parser.add_argument("--chapter", action="append", default=[])
    parser.add_argument("--issue", action="append", default=[])
    parser.add_argument("--reference")
    parser.add_argument("--allow-drafts", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-chars", type=int, default=12000)
    parser.add_argument("--expected-revision")
    parser.add_argument("--research-response", type=Path)
    parser.add_argument("--save-preview", default="")
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        if args.command in {"init", "refresh"}:
            if args.review is None:
                raise ValueError("Indicar --review com a análise efetivamente realizada")
            result = (initialize if args.command == "init" else refresh)(output, read_json(args.review))
        elif args.command == "context":
            result = context_batch(output, args.issue, args.offset, args.max_chars, args.expected_revision)
        elif args.command == "save":
            if args.chapter_file is None:
                raise ValueError("Indicar --chapter-file")
            result = save_chapter(output, read_json(args.chapter_file))
        elif args.command in {"review", "approve"}:
            if len(args.chapter) != 1:
                raise ValueError("Indicar um capítulo")
            result = set_status(output, args.chapter[0], "approved" if args.command == "approve" else "reviewed", args.reference)
        elif args.command in {"assemble", "preview"}:
            result = assemble(output, args.chapter, allow_drafts=args.allow_drafts,
                              response=read_json(args.research_response) if args.research_response else None,
                              preview=args.command == "preview")
            if args.save_preview and args.command == "preview":
                atomic_json(inside(output, args.save_preview), result)
        else:
            sync_updates(output)
            result, _ = load_workspace(output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
