"""Execute the same frozen synthetic controls on two supplied repository trees."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    from .evaluate_labor_batch import evaluate_batch
except ImportError:
    from evaluate_labor_batch import evaluate_batch

ROOT = Path(__file__).resolve().parents[1]
RUNNER = '''
import copy, json, sys, time
sys.path.insert(0, sys.argv[1])
from scripts.labor_parameters import review_parameters
from scripts.labor_ledger import apportion_workdays
suite = json.load(sys.stdin)
observed = {}
for case in suite["cases"]:
    started = time.perf_counter()
    if case["kind"] == "numeric":
        fixture = copy.deepcopy(suite["fixtures"]["numeric"])
        fixture["checks"]["inputs"][1]["quote"] = case["quote"]
        fixture["texts"][fixture["citations"][0]["source_record_id"]] = case["quote"]
        result = review_parameters(*(fixture[key] for key in ("payload", "checks", "review", "citations", "texts")))
        value = not bool(result["errors"])
    elif case["kind"] == "weekly":
        try:
            result = apportion_workdays(copy.deepcopy(suite["fixtures"]["weekly"]))
            value = result["weeks"][0]["total_excess_without_double_count"] if len(result["weeks"]) == 1 else "not_computed"
        except ValueError:
            value = "not_computed"
    else:
        raise ValueError("Unsupported frozen regression type")
    observed[case["id"]] = {"value": value, "elapsed_seconds": time.perf_counter() - started}
print(json.dumps(observed))
'''


def observe(repository: Path, suite: dict) -> dict:
    core = repository.resolve() / "skills/legal-process-parser"
    if not (core / "scripts/labor_parameters.py").is_file():
        raise ValueError("Selecionar uma árvore do AuditorProcessual com scripts e schemas completos")
    result = subprocess.run([sys.executable, "-I", "-c", RUNNER, str(core)], input=json.dumps(suite),
                            capture_output=True, text=True, encoding="utf-8", cwd=core, timeout=120)
    if result.returncode:
        raise ValueError("Falha na execução da versão: " + result.stderr[-2000:])
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara controles sintéticos congelados entre duas versões locais")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, default=ROOT)
    parser.add_argument("--suite", type=Path, default=ROOT / "evaluation/labor_upgrade_cases.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        raw = args.suite.read_bytes()
        suite = json.loads(raw)
        runs = {"baseline": observe(args.baseline, suite), "candidate": observe(args.candidate, suite)}
        cases = [{"id": case["id"], "checks": [{"id": case["id"], "category": case["category"], "critical": case["critical"],
                  "expected": case["expected"], "observed": {v: run[case["id"]]["value"] for v, run in runs.items()}}],
                  "measurements": {v: {"elapsed_seconds": run[case["id"]]["elapsed_seconds"], "context_tokens": None} for v, run in runs.items()}}
                 for case in suite["cases"]]
        result = evaluate_batch({"schema_version": "1.0", "dataset_type": "synthetic", "split": "development", "versions": list(runs), "cases": cases})
        result.update(fixture_sha256=hashlib.sha256(raw).hexdigest(), observed_cases=cases,
                      scope="Four frozen code regressions only; not held-out professional evaluation, model comprehension, or real PJe-Calc execution.")
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            if args.output.resolve() == args.suite.resolve():
                raise ValueError("Preservar o conjunto congelado")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        print(text)
        return int(bool(result["metrics"]["candidate"]["mismatches"]))
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
