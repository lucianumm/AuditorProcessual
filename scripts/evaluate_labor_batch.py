"""Compare recorded labor runs against independently supplied expected results.

No model is called and no professional judgment is fabricated. Measurements and
reviewer identities remain attributed observations, not independent attestations.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


CATEGORIES = ("omitted_right", "improper_request", "temporal_error", "inadequate_citation", "numeric_divergence", "unnecessary_block")


def evaluate_batch(payload: dict) -> dict:
    if payload.get("schema_version") != "1.0" or payload.get("dataset_type") not in {"synthetic", "authorized_anonymized"}:
        raise ValueError("Identificar versão e natureza do conjunto")
    if payload.get("split") not in {"development", "held_out_test"}:
        raise ValueError("Distinguir desenvolvimento de teste separado")
    versions = payload.get("versions", [])
    cases = payload.get("cases", [])
    if len(versions) != len(set(versions)) or len(versions) < 2 or any(not isinstance(v, str) or not v.strip() for v in versions):
        raise ValueError("Identificar ao menos duas versões distintas")
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Caso duplicado na comparação")
    independent = payload["dataset_type"] == "authorized_anonymized"
    if independent and (not payload.get("authorization_reference") or not payload.get("anonymization_review_reference")
                        or len(set(payload.get("independent_reviewers", []))) < 2):
        raise ValueError("Casos reais exigem autorização, anonimização e dois revisores independentes registrados")
    metrics = {v: {"checks": 0, "mismatches": 0, "critical_errors": [], "errors_by_category": {c: 0 for c in CATEGORIES}, "checks_by_category": {c: 0 for c in CATEGORIES},
                   "elapsed_seconds": [], "context_tokens": []} for v in versions}
    details = []
    for case in cases:
        if not case.get("checks"):
            raise ValueError("Caso sem rótulos observáveis")
        if independent and (not case.get("label_reference") or not case.get("case_revision")):
            raise ValueError("Caso real sem referência dos rótulos independentes e revisão anonimizada")
        for check in case["checks"]:
            if check.get("category") not in CATEGORIES or "expected" not in check or not isinstance(check.get("critical"), bool):
                raise ValueError("Rótulo sem categoria, expectativa ou criticidade")
            if set(check.get("observed", {})) != set(versions):
                raise ValueError("Cada rótulo precisa da observação de todas as versões")
            for version in versions:
                correct = check["observed"][version] == check["expected"]
                row = metrics[version]
                row["checks"] += 1
                row["checks_by_category"][check["category"]] += 1
                if not correct:
                    row["mismatches"] += 1
                    row["errors_by_category"][check["category"]] += 1
                    if check["critical"]:
                        row["critical_errors"].append({"case_id": case["id"], "check_id": check["id"], "category": check["category"]})
                details.append({"case_id": case["id"], "check_id": check["id"], "version": version, "matches_expected": correct})
        for version, measurement in case.get("measurements", {}).items():
            if version not in metrics:
                raise ValueError("Medição de versão desconhecida")
            for field in ("elapsed_seconds", "context_tokens"):
                value = measurement.get(field)
                if value is not None:
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or field == "context_tokens" and not isinstance(value, int):
                        raise ValueError("Tempo e tokens precisam de observações finitas não negativas")
                    metrics[version][field].append(value)
    for row in metrics.values():
        row["errors_by_category"] = {key: count if row["checks_by_category"][key] else None for key, count in row["errors_by_category"].items()}
        for field in ("elapsed_seconds", "context_tokens"):
            samples = row[field]
            row[field] = {"samples": len(samples), "total": sum(samples) if samples else None, "mean": sum(samples) / len(samples) if samples else None}
        row["has_critical_error"] = bool(row["critical_errors"])
    return {"schema_version": "1.0", "dataset_type": payload["dataset_type"], "split": payload["split"], "case_count": len(cases),
            "status": "compared_recorded_runs" if cases else "not_evaluated_no_cases", "metrics": metrics, "details": details,
            "professional_evaluation": "attributed_independent_labels" if independent and cases else "not_recorded",
            "scope": "Recorded observations only; synthetic checks do not establish legal accuracy. Critical errors remain explicit; missing time/tokens stay null."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara versões por seis classes de erro com rótulos e medições reais fornecidos")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate_batch(json.loads(args.input.read_text(encoding="utf-8-sig")))
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            if args.output.resolve() == args.input.resolve():
                raise ValueError("Preservar o arquivo de rótulos e observações")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
