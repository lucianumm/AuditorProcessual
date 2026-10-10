"""Deterministic candidate routing. The host must evaluate actual admissibility."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "references" / "procedural_catalog.json"


def candidates(domain: str, phase: str, family: str | None = None) -> dict:
    entries = json.loads(CATALOG.read_text(encoding="utf-8"))["entries"]
    selected = [entry for entry in entries if (domain in entry["domains"] or "*" in entry["domains"])
                and (phase in entry["phases"] or "*" in entry["phases"])
                and (not family or entry["family"] == family)]
    return {"domain":domain, "phase":phase, "candidates":selected,
            "status":"candidates_not_admissibility_confirmation",
            "limitation":"Sem candidato específico, pesquisar o instrumento próprio; não forçar classificação genérica."}


def validate_catalog_selection(review: dict) -> list[str]:
    if review.get("schema_version") != "4.0":
        return []
    assessment = review.get("piece_assessment", {})
    if assessment.get("status") != "selected":
        return []
    catalog = {item["id"]:item for item in json.loads(CATALOG.read_text(encoding="utf-8"))["entries"]}
    chosen = assessment.get("catalog_id")
    if chosen == "custom":
        return [] if assessment.get("custom_catalog_reason") and assessment.get("norm_ids") else ["Peça fora do catálogo exige razão específica e norma de cabimento vinculada"]
    if chosen not in catalog:
        return ["piece_assessment: catalog_id válido ou custom fundamentado obrigatório na v4"]
    entry = catalog[chosen]
    errors = []
    if review.get("task") == "petition" and entry["family"] != review.get("piece_type"):
        errors.append("Peça específica do catálogo diverge da família da minuta")
    recorded = {check.get("check_id") for check in assessment.get("admissibility_checks", [])}
    missing = set(entry["checks"]) - recorded
    if missing:
        errors.append("Peça selecionada sem conferir temas de admissibilidade: " + ", ".join(sorted(missing)))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Localiza candidatos por área/fase; não decide cabimento jurídico")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--family")
    args = parser.parse_args()
    print(json.dumps(candidates(args.domain, args.phase, args.family), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
