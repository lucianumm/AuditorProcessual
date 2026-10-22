"""Deterministic candidate routing. The host must evaluate actual admissibility."""
from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "references" / "procedural_catalog.json"


def canonical(value: str) -> str:
    text = "".join(c for c in unicodedata.normalize("NFD",value.casefold()) if unicodedata.category(c) != "Mn").strip().replace(" ","_")
    return {"civel":"civil","familia":"civil","direito_do_trabalho":"trabalhista","direito_trabalhista":"trabalhista",
            "laboral":"trabalhista","labor":"trabalhista","labour":"trabalhista"}.get(text,text)


def candidates(domain: str, phase: str, family: str | None = None) -> dict:
    domain, phase = canonical(domain), canonical(phase)
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
    domain, phase = canonical(review.get("strategy",{}).get("domain","")), canonical(review.get("strategy",{}).get("phase",""))
    if "*" not in entry["domains"] and domain not in entry["domains"]:
        errors.append("Peça do catálogo incompatível com a área confirmada; pesquisar instrumento próprio ou custom fundamentado")
    if "*" not in entry["phases"] and phase not in entry["phases"] and not (assessment.get("phase_exception_reason") and assessment.get("norm_ids")):
        errors.append("Fase da peça difere do catálogo; registrar phase_exception_reason e norma específica")
    if review.get("task") == "petition" and entry["family"] != review.get("piece_type"):
        errors.append("Peça específica do catálogo diverge da família da minuta")
    recorded = {check.get("check_id") for check in assessment.get("admissibility_checks", [])}
    if len(recorded) != len(assessment.get("admissibility_checks", [])):
        errors.append("Temas de admissibilidade duplicados")
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
