"""Resolve only this platform/task's references, with measured character cost."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]


def routing_root() -> Path:
    for root in (CORE, *CORE.parents):
        if (root / "routing/task-router.json").is_file():
            return root
    raise ValueError("Roteador ausente; use o pacote completo ou a raiz do repositório")


def resolve_context(platform: str, task: str, *, triggers: list[str] | None = None,
                    specialization_ids: list[str] | None = None, domain: str = "",
                    labor_topics: list[str] | None = None, labor_claims: list[str] | None = None,
                    labor_sectors: list[str] | None = None, labor_intake: bool = False) -> dict:
    root = routing_root()
    router = json.loads((root / "routing/task-router.json").read_text(encoding="utf-8"))
    # A wheel installs core resources directly, unlike the repository layout.
    if not (root / "skills/legal-process-parser/references").is_dir() and (root / "references").is_dir():
        router = json.loads(json.dumps(router).replace("skills/legal-process-parser/", ""))
    if task not in router["tasks"]:
        raise ValueError("Tarefa desconhecida")
    spec = router["tasks"][task]
    modules = json.loads((root / router["specializations"]).read_text(encoding="utf-8"))["modules"]
    topic_specs = json.loads((root / router["labor_topics"]).read_text(encoding="utf-8"))["topics"] if router.get("labor_topics") else []
    known_topics = {item["id"]:item for item in topic_specs}
    try:
        from .labor_catalog import select_claims, select_sectors
    except ImportError:
        from labor_catalog import select_claims, select_sectors
    claims = select_claims(labor_claims or [])
    sectors = select_sectors(labor_sectors or [])
    requested_topics = set(labor_topics or [])
    requested_topics |= {c["topic_id"] for c in claims}
    if not requested_topics:
        requested_topics |= {t for s in sectors for t in s["topic_ids"]}
    if requested_topics - set(known_topics):
        raise ValueError("Tema trabalhista desconhecido: " + ", ".join(sorted(requested_topics - set(known_topics))))
    selected_ids = set(specialization_ids or []) | {known_topics[key]["specialization_id"] for key in requested_topics}
    selected = [item for item in modules if item["id"] in selected_ids]
    if selected_ids - {item["id"] for item in selected}:
        raise ValueError("Especialização desconhecida; confirmar área/subárea/regime antes de selecionar")
    requested_topics |= {item["id"] for item in topic_specs if item["specialization_id"] in selected_ids}
    try:
        from .labor_analysis import folded
    except ImportError:
        from labor_analysis import folded
    labor_names = {"trabalhista", "direito do trabalho", "direito trabalhista", "laboral", "labor", "labour"}
    labor = folded(domain) in labor_names or bool(requested_topics) or labor_intake or any(item["domain"] == "trabalhista" for item in selected)
    active = set(triggers or []) | set(spec.get("automatic_triggers", []))
    if "response_research" in active and {"local_contract", "petition_chapter_contract"} & active:
        active.add("response_contract")
    if "response_contract" in active and "labor_calculation" in active:
        active.add("parameter_contract")
    if "local_contract" in active and "source_verification" in active:
        active.add("source_registry")
    if labor_intake:
        # Intake starts with the client's account, usually under the default ingest task.
        active.update({"labor", "labor_intake", "labor_development"})
    if labor and task != "ingest":
        active.add("labor")
        if claims or sectors or labor_intake:
            active.add("labor_development")
        if labor_intake:
            active.add("labor_intake")
        if "local_contract" in active:
            active.add("labor_contract_schema")
            if "labor_development" in active:
                active.add("labor_workflow_schema")
    conditional = router.get("conditional_references", [])
    known = {item["trigger"] for item in conditional}
    if active - known:
        raise ValueError("Gatilho desconhecido: " + ", ".join(sorted(active - known)))
    paths = list(spec["references"])
    for item in conditional:
        if item["trigger"] in active:
            paths += item["references"]
    for item in selected:
        paths.append((Path(router["specializations"]).parent / item["reference"]).as_posix())
    for sector in sectors:
        paths.append((Path(router["specializations"]).parent / sector["reference"]).as_posix())
    for claim in claims:
        if claim.get("reference"):
            paths.append((Path(router["specializations"]).parent / claim["reference"]).as_posix())
    paths = list(dict.fromkeys(paths))
    references = []
    for path in paths:
        full = (root / path).resolve()
        if not full.is_relative_to(root.resolve()) or not full.is_file():
            raise ValueError("Referência ausente ou fora do pacote: " + path)
        references.append({"path":path,"characters":len(full.read_text(encoding="utf-8-sig"))})
    adapter = router.get("platforms", {}).get(platform)
    if router.get("platforms") and adapter is None:
        adapter = "AI_ENTRYPOINT.md"
    if adapter and not (root / adapter).is_file():
        adapter = None
    return {"platform":platform,"task":task,"domain":"trabalhista" if labor else domain,
            "labor_topic_ids":sorted(requested_topics),"adapter":adapter,"triggers":sorted(active),
            "labor_claims":claims,"labor_sectors":sectors,
            "references":references,"specializations":selected,
            "reference_characters":sum(item["characters"] for item in references),
            "budget_meaning":"Caracteres medidos; tokens dependem do modelo. Toda página do corpus continua no escopo de leitura integral.",
            "capabilities":{"vision":"not_tested","browsing":"not_tested","code_execution":"not_tested","persistence":"not_tested"}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Roteia uma plataforma/tarefa sem carregar outros adaptadores")
    parser.add_argument("--platform", default="generic")
    parser.add_argument("--task", default="ingest", choices=["ingest", "analyze", "petition", "deadlines", "evidence", "audit"])
    parser.add_argument("--trigger", action="append", default=[])
    parser.add_argument("--specialization", action="append", default=[])
    parser.add_argument("--domain", default="")
    parser.add_argument("--labor-topic", action="append", default=[])
    parser.add_argument("--labor-claim", action="append", default=[])
    parser.add_argument("--labor-sector", action="append", default=[])
    parser.add_argument("--labor-intake", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(resolve_context(args.platform,args.task,triggers=args.trigger,specialization_ids=args.specialization,
                                        domain=args.domain,labor_topics=args.labor_topic,labor_claims=args.labor_claim,
                                        labor_sectors=args.labor_sector,labor_intake=args.labor_intake),ensure_ascii=False,indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
