"""Mede a detecção dos erros plantados de `evaluation/planted_errors.json` pelos controles da v1.1.

    python scripts/run_planted_errors.py [--out evaluation/planted_errors_result.json]

Os casos são sintéticos e escritos pelo autor dos controles: o resultado mede
regressão e o limite declarado (casos `unforeseen`), não precisão em autos reais.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "legal-process-parser"))
from scripts.catalog_status import freshness  # noqa: E402
from scripts.global_consistency import check_consistency  # noqa: E402
from scripts.injection import detect_injection  # noqa: E402
from scripts.prose_review import prose_errors  # noqa: E402

ATOMS = {"actor": "Reclamada", "action": "pagar", "object": "horas extras", "polarity": "negated", "scope": "contrato",
         "period_start": "2026-06-01", "period_end": "2026-08-31", "date": "2026-06-01"}
REVIEW = {"facts": [{"id": "F1", "text": "Relato: admitida em 01/06/2026 e dispensada em 31/08/2026; horas extras em 07/2026. "
                                         "CNPJ 12.345.678/0001-90."}],
          "assertion_reviews": [{"fact_id": "F1", "atoms": ATOMS, "evidence_status": "client_account"}],
          "norms": [], "normative_map": [], "requests": [{"id": "R1", "issue_ids": ["I1"]}]}


def paragraph(text: str, requests=("R1",), facts=("F1",)) -> dict:
    return {"id": "P1", "text": text, "fact_ids": list(facts), "norm_ids": [], "issue_ids": ["I1"],
            "request_ids": list(requests), "assertions": []}


def detected(case: dict) -> bool:
    control = case["control"]
    if control == "consistency":
        chapters = [{"id": cid, "issue_ids": ["I1"], "request_ids": ["R1"] if i == 0 else [],
                     "paragraphs": [paragraph(text, ("R1",) if i == 0 else (), () if case.get("bare_request") else ("F1",))]}
                    for i, (cid, text) in enumerate(case["chapters"])]
        report = check_consistency(chapters, REVIEW)
        return any(f["kind"] == case["expect"] and f["severity"] == "blocking" for f in report["findings"])
    if control in {"prose", "none"}:
        errors = prose_errors(paragraph(case["text"]), REVIEW)
        return any(case.get("expect", "") in e for e in errors) if control == "prose" else bool(errors)
    if control == "injection":
        return bool(detect_injection(case["text"]))
    if control == "freshness":
        return freshness(case["authority"], date(2026, 11, 27))["state"] != "fresh"
    if control == "bis_in_idem":
        item = {"relationship_id": "REL1", "competence": "2026-07", "claim_type": "horas_extras", "segment": "50",
                "kind": "principal", "include_in_total": True}
        review = dict(REVIEW, requests=[{"id": "R1", "issue_ids": ["I1"]}, {"id": "R2", "issue_ids": ["I2"]}],
                      labor_review={"calculation_set": {"items": [dict(item, request_ids=["R1"]), dict(item, request_ids=["R2"])]}})
        chapters = [{"id": "A", "issue_ids": ["I1"], "request_ids": ["R1"], "paragraphs": [paragraph("Horas extras.")]},
                    {"id": "B", "issue_ids": ["I2"], "request_ids": ["R2"], "paragraphs": [paragraph("Intervalo.", ("R2",))]}]
        return any(f["kind"] == "bis_in_idem" for f in check_consistency(chapters, review)["findings"])
    raise ValueError("controle desconhecido: " + control)


def run(path: Path) -> dict:
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    rows = [{"id": c["id"], "kind": c["kind"], "control": c["control"], "detected": detected(c)} for c in cases]
    foreseen = [r for r in rows if r["kind"] != "unforeseen"]
    unforeseen = [r for r in rows if r["kind"] == "unforeseen"]
    return {"foreseen_total": len(foreseen), "foreseen_detected": sum(r["detected"] for r in foreseen),
            "foreseen_rate": round(sum(r["detected"] for r in foreseen) / max(1, len(foreseen)), 4),
            "unforeseen_total": len(unforeseen), "unforeseen_detected": sum(r["detected"] for r in unforeseen),
            "rows": rows, "meaning": "Casos sintéticos do próprio autor: regressão e limite declarado, não precisão em autos reais."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Detecção de erros plantados pelos controles determinísticos")
    parser.add_argument("--cases", type=Path, default=ROOT / "evaluation" / "planted_errors.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.cases)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False))
    return 0 if result["foreseen_rate"] == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
