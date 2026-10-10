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
                    specialization_ids: list[str] | None = None) -> dict:
    root = routing_root()
    router = json.loads((root / "routing/task-router.json").read_text(encoding="utf-8"))
    # A wheel installs core resources directly, unlike the repository layout.
    if not (root / "skills/legal-process-parser/references").is_dir() and (root / "references").is_dir():
        router = json.loads(json.dumps(router).replace("skills/legal-process-parser/", ""))
    if task not in router["tasks"]:
        raise ValueError("Tarefa desconhecida")
    spec = router["tasks"][task]
    active = set(triggers or []) | set(spec.get("automatic_triggers", []))
    conditional = router.get("conditional_references", [])
    known = {item["trigger"] for item in conditional}
    if active - known:
        raise ValueError("Gatilho desconhecido: " + ", ".join(sorted(active - known)))
    paths = list(spec["references"])
    for item in conditional:
        if item["trigger"] in active:
            paths += item["references"]
    modules = json.loads((root / router["specializations"]).read_text(encoding="utf-8"))["modules"]
    selected = [item for item in modules if item["id"] in (specialization_ids or [])]
    if set(specialization_ids or []) - {item["id"] for item in selected}:
        raise ValueError("Especialização desconhecida; confirmar área/subárea/regime antes de selecionar")
    for item in selected:
        paths.append((Path(router["specializations"]).parent / item["reference"]).as_posix())
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
    return {"platform":platform,"task":task,"adapter":adapter,"triggers":sorted(active),
            "references":references,"specializations":selected,
            "reference_characters":sum(item["characters"] for item in references),
            "budget_meaning":"Caracteres medidos; tokens dependem do modelo. Toda página do corpus continua no escopo de leitura integral.",
            "capabilities":{"vision":"not_tested","browsing":"not_tested","code_execution":"not_tested","persistence":"not_tested"}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Roteia uma plataforma/tarefa sem carregar outros adaptadores")
    parser.add_argument("--platform", default="generic")
    parser.add_argument("--task", default="ingest")
    parser.add_argument("--trigger", action="append", default=[])
    parser.add_argument("--specialization", action="append", default=[])
    args = parser.parse_args()
    try:
        print(json.dumps(resolve_context(args.platform,args.task,triggers=args.trigger,specialization_ids=args.specialization),ensure_ascii=False,indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
