"""Synthetic gold cases exercise the evaluator without claiming legal accuracy."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("evaluate_quality", ROOT / "scripts" / "evaluate_quality.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
evaluate = module.evaluate


class EvaluationV2(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)

    def _artifacts(self, case_name: str):
        case_path = ROOT / "evaluation" / "cases" / case_name / "case.json"
        gold = json.loads(case_path.read_text(encoding="utf-8"))
        documents = []
        facts = []
        source_by_name = {}
        for index, item in enumerate(gold["source_files"], 1):
            path = case_path.parent / item["file"]
            raw = path.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            content = raw.decode("utf-8").strip()
            source_by_name[item["file"]] = (sha, content)
            documents.append({"sha256": sha, "pages": [{"pdf_page": 1, "text": content}]})
            facts.append({"id": f"F{index}", "text": content,
                          "sources": [{"source_sha256": sha, "pdf_page": 1, "quote": content}]})
        issues = []
        status_records = []
        for index, item in enumerate(gold["expected"]["issues"], 1):
            iid = f"I{index}"
            issues.append({"id": iid, "question": item["text_any"][0]})
            status_records.append({"id": iid, "analysis_status": item.get("analysis_status", "concluded")})
        requests = []
        for index, item in enumerate(gold["expected"].get("requests", []), 1):
            request_issues = [issues[next(i for i, issue in enumerate(gold["expected"]["issues"])
                                     if issue["id"] == label)]["id"] for label in item.get("issue_ids", [])]
            requests.append({"id": f"R{index}", "text": item["text_any"][0], "issue_ids": request_issues})
        conflicts = []
        for item in gold["expected"].get("contradictions", []):
            conflicts.append({"sources": [{"source_sha256": source_by_name[item[key]["file"]][0], "pdf_page": 1}
                                          for key in ("source_a", "source_b")]})
        review = {"facts": facts, "issues": issues, "requests": requests, "conflicts": conflicts}
        review["strategy"] = gold["expected"].get("strategy", {})
        review["piece_assessment"] = {"catalog_id":gold["expected"].get("catalog_id")}
        review["assertion_reviews"] = []
        for label in gold["expected"].get("facts", []):
            if label.get("source"):
                digest = source_by_name[label["source"]["file"]][0]
                fact = next(item for item in facts if item["sources"][0]["source_sha256"] == digest)
                review["assertion_reviews"].append({"fact_id":fact["id"],"atoms":label.get("atoms", {}),"evidence_status":label.get("evidence_status")})
        validation = {"issue_statuses": status_records,
                      "execution_status": gold["expected"].get("execution_status", "completed"),
                      "draft_status": gold["expected"].get("draft_status", "not_requested")}
        for name, value in (("case_memory.json", {"documents": documents}),
                            ("legal_review.json", review), ("legal_review_validation.json", validation)):
            (self.output / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return case_path, review

    def test_all_gold_cases_detect_observable_expectations(self):
        for path in sorted((ROOT / "evaluation/cases").glob("*/case.json")):
            name = path.parent.name
            with self.subTest(name=name):
                case_path, _ = self._artifacts(name)
                result = evaluate(case_path, self.output)
                self.assertTrue(result["passed_observable_checks"], result["violations"])
                self.assertEqual(result["metrics"]["citation_precision"], 1.0)
                self.assertIsNone(result["metrics"]["elapsed_seconds"])

    def test_atomic_mismatch_is_detected_even_when_quote_exists(self):
        case_path,review = self._artifacts("partial_payment")
        review["assertion_reviews"][0]["atoms"]["amount"] = "500.00"
        (self.output / "legal_review.json").write_text(json.dumps(review,ensure_ascii=False),encoding="utf-8")
        result = evaluate(case_path,self.output)
        self.assertFalse(result["passed_observable_checks"])
        self.assertEqual(result["metrics"]["citation_precision"],1.0)
        self.assertLess(result["metrics"]["atomic_field_accuracy"],1.0)

    def test_wrong_regime_and_procedural_measure_are_detected(self):
        case_path,review = self._artifacts("assistential_regime")
        review["strategy"]["regime"] = "rgps"
        (self.output / "legal_review.json").write_text(json.dumps(review,ensure_ascii=False),encoding="utf-8")
        self.assertFalse(evaluate(case_path,self.output)["passed_observable_checks"])
        case_path,review = self._artifacts("worker_appeal")
        review["piece_assessment"]["catalog_id"] = "apelacao_civel"
        (self.output / "legal_review.json").write_text(json.dumps(review,ensure_ascii=False),encoding="utf-8")
        self.assertTrue(any("Peça específica" in error for error in evaluate(case_path,self.output)["violations"]))

    def test_human_review_requires_real_version_link_not_a_fake_score(self):
        self._artifacts("partial_payment")
        review_path = self.output / "legal_review.json"
        human = {"schema_version":"1.0","reviewer":"Revisor sintético de teste, não profissional real","reviewer_role":"test-fixture",
                 "reviewed_on":"2026-10-10","comments":"Exercício do contrato; não avaliação profissional.",
                 "review_sha256":hashlib.sha256(review_path.read_bytes()).hexdigest(),
                 "dimensions":{key:3 for key in module.HUMAN_DIMENSIONS},"critical_errors":[]}
        human_path = self.output / "human-test.json"
        human_path.write_text(json.dumps(human),encoding="utf-8")
        record = module.inspect_human_review(human_path,review_path)
        self.assertIn("not_independently_attested",record["status"])
        human["review_sha256"] = "0" * 64
        human_path.write_text(json.dumps(human),encoding="utf-8")
        with self.assertRaises(ValueError):
            module.inspect_human_review(human_path,review_path)

    def test_omitted_fact_is_not_hidden_by_other_matches(self):
        case_path, review = self._artifacts("partial_independent")
        review["facts"].pop()
        (self.output / "legal_review.json").write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
        result = evaluate(case_path, self.output)
        self.assertFalse(result["passed_observable_checks"])
        self.assertTrue(any("Fato esperado omitido" in value for value in result["violations"]))


if __name__ == "__main__":
    unittest.main()
