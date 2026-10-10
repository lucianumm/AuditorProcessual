"""Prepare a pending v4 authoring skeleton; never mark pages read or law verified."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .case_memory import atomic_json
    from .research_memory import research_revision
except ImportError:
    from case_memory import atomic_json
    from research_memory import research_revision


def skeleton(output: Path, *, task: str = "analyze", platform: str = "generic") -> dict:
    if task not in {"analyze", "petition", "audit"}:
        raise ValueError("Revisão estruturada é destinada a analyze, petition ou audit")
    memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8-sig"))
    return {"schema_version":"4.0", "authoring_status":"pending_not_reviewed",
            "corpus_revision":memory["corpus_revision"], "research_revision":research_revision(output), "task":task,
            "execution_context":{"platform":platform,"mode":"local","capabilities":{
                key:{"status":"not_tested"} for key in ("vision","browsing","code_execution","persistence")}},
            "strategy":{"objective":"","jurisdiction":"","domain":"","subdomain":"","regime":"","phase":""},
            "expected_page_ids":[f"{d['sha256']}:{p['pdf_page']}" for d in memory["documents"] for p in d["pages"]],
            "reviewed_pages":[],"page_reviews":[],"reading_coverage":[],"facts":[],"client_records":[],"norms":[],
            "assertion_reviews":[],"normative_map":[],"precedent_comparisons":[],"piece_assessment":{},
            "norm_applications":[],"theses":[],"thesis_reviews":[],"issues":[],"requests":[],"paragraphs":[],
            "research_closure":{"searched_topics":[],"stop_reason":""},"findings":[],"unresolved":[],
            "authoring_note":"Preencher após leitura e pesquisa reais. Este esqueleto é deliberadamente inválido para entrega e não constitui revisão."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara revisão v4 pendente, sem inventar fatos, conferências ou leitura")
    parser.add_argument("output", type=Path)
    parser.add_argument("--task", default="analyze")
    parser.add_argument("--platform", default="generic")
    parser.add_argument("--save", type=Path, help="Novo arquivo de trabalho; recusa sobrescrever arquivo existente")
    args = parser.parse_args()
    try:
        result = skeleton(args.output, task=args.task, platform=args.platform)
        if args.save:
            if args.save.exists():
                raise ValueError("Arquivo já existe; escolha um novo nome para preservar a revisão")
            atomic_json(args.save, result)
            print(args.save)
        else:
            print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
