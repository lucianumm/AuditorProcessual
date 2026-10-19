"""Explicit, append-only relationships between preserved document versions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .case_memory import atomic_json, identity, update_memory
except ImportError:
    from case_memory import atomic_json, identity, update_memory

RELATIONS = {"complements", "corrects", "supersedes", "contradicts", "same_document_version", "related_process"}


def record_relation(output: Path, *, older: str, newer: str, relation: str, reason: str, recorded_by: str) -> dict:
    memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8-sig"))
    hashes = {d["sha256"] for d in memory["documents"]}
    if older == newer or not {older,newer} <= hashes or relation not in RELATIONS or not reason.strip() or not recorded_by.strip():
        raise ValueError("Relação exige dois arquivos preservados distintos, tipo, motivo e responsável")
    path = output / "document_relations.json"
    records = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    if relation == "supersedes":
        edges = {}
        for record in records:
            if record["relation"] == "supersedes":
                edges.setdefault(record["older"],set()).add(record["newer"])
        todo, seen = [newer], set()
        while todo:
            node = todo.pop()
            if node == older:
                raise ValueError("Substituição circular de versões não permitida")
            if node not in seen:
                seen.add(node)
                todo.extend(edges.get(node, []))
    record = {"older":older,"newer":newer,"relation":relation,"reason":reason,"recorded_by":recorded_by}
    record["id"] = identity(record)
    if not any(r["id"] == record["id"] for r in records):
        records.append(record)
        atomic_json(path, records)
        updated = update_memory(output)
        try:
            from .artifact_tracking import track_artifacts, invalidate_legal_delivery
        except ImportError:
            from artifact_tracking import track_artifacts, invalidate_legal_delivery
        archived = invalidate_legal_delivery(output, updated["corpus_revision"],
            "Relações entre documentos alteradas. Reavaliar o significado das versões; originais preservados.")
        track_artifacts(output, ["document_relations.json", "case_memory.json", "memoria_processual.md", "indice_juridico.json", "indice_juridico.md", "passages.jsonl"],
                        status="stale_document_relationship_change", archived=archived, bundle=True)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Relaciona versões sem excluir originais ou inferir equivalência por similaridade")
    parser.add_argument("output",type=Path)
    for name in ("older","newer","reason","recorded-by"):
        parser.add_argument("--"+name,required=True)
    parser.add_argument("--relation",choices=sorted(RELATIONS),required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(record_relation(args.output,older=args.older,newer=args.newer,relation=args.relation,reason=args.reason,recorded_by=args.recorded_by),ensure_ascii=False,indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"error":str(error)},ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
