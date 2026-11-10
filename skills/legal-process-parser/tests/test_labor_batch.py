from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("evaluate_labor_batch", ROOT / "scripts/evaluate_labor_batch.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LaborBatchComparison(unittest.TestCase):
    def payload(self):
        return {"schema_version": "1.0", "dataset_type": "synthetic", "split": "held_out_test", "versions": ["before", "after"],
                "cases": [{"id": "S1", "checks": [{"id": "numeric-unit", "category": "numeric_divergence", "critical": True,
                "expected": "rejected", "observed": {"before": "accepted", "after": "rejected"}}]}]}

    def test_critical_error_is_visible_and_missing_measurements_are_null(self):
        result = module.evaluate_batch(self.payload())
        self.assertTrue(result["metrics"]["before"]["has_critical_error"])
        self.assertFalse(result["metrics"]["after"]["has_critical_error"])
        self.assertIsNone(result["metrics"]["after"]["context_tokens"]["total"])
        self.assertEqual(result["professional_evaluation"], "not_recorded")

    def test_no_cases_cannot_be_presented_as_passed_evaluation(self):
        value = self.payload()
        value["cases"] = []
        self.assertEqual(module.evaluate_batch(value)["status"], "not_evaluated_no_cases")

    def test_real_dataset_requires_authorization_and_independent_labels(self):
        value = self.payload()
        value["dataset_type"] = "authorized_anonymized"
        with self.assertRaises(ValueError):
            module.evaluate_batch(value)

    def test_missing_run_cannot_disappear_from_comparison(self):
        value = self.payload()
        del value["cases"][0]["checks"][0]["observed"]["before"]
        with self.assertRaises(ValueError):
            module.evaluate_batch(value)

    def test_invalid_or_negative_measurements_are_rejected(self):
        for measurement in (-1, float("nan"), True, 1.5):
            value = self.payload()
            value["cases"][0]["measurements"] = {"after": {"context_tokens": measurement}}
            with self.subTest(measurement=measurement), self.assertRaises(ValueError):
                module.evaluate_batch(value)


if __name__ == "__main__":
    unittest.main()
