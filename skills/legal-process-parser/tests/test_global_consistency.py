"""Coherence across chapters on synthetic scenarios; no model or expert run."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from functools import partial
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.global_consistency import check_consistency
from scripts.petition_workspace import assemble, initialize, save_chapter, set_status
from tests.test_incremental_petition import chapter_fixture
from tests.test_labor_workflow import synthetic_case

save_chapter = partial(save_chapter, require_response=False)
assemble = partial(assemble, require_response=False)


def paragraph(pid, text, requests=(), facts=("F1",), norms=()):
    return {"id": pid, "text": text, "fact_ids": list(facts), "norm_ids": list(norms), "issue_ids": ["I1"],
            "request_ids": list(requests), "assertions": []}


def chapter(cid, issues, requests, paragraphs):
    return {"id": cid, "issue_ids": issues, "request_ids": requests, "paragraphs": paragraphs}


REVIEW = {"requests": [{"id": "R1", "issue_ids": ["I1"]}, {"id": "R2", "issue_ids": ["I2"]}],
          "facts": [{"id": "F1", "text": "CNPJ 12.345.678/0001-90 e processo 0001234-56.2026.5.02.0001."}]}


class PureConsistency(unittest.TestCase):
    def kinds(self, report, severity="blocking"):
        return sorted(f["kind"] for f in report["findings"] if f["severity"] == severity)

    def test_salary_divergence_between_chapters_blocks(self):
        a = chapter("A", ["I1"], ["R1"], [paragraph("P1", "A reclamante recebia salário de R$ 2.200,00.", ["R1"])])
        b = chapter("B", ["I2"], ["R2"], [paragraph("P1", "O salário base era de R$ 2.500,00.", ["R2"])])
        report = check_consistency([a, b], REVIEW)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(self.kinds(report), ["parameter"])
        self.assertEqual(report["findings"][0]["chapters"], ["A", "B"])

    def test_salary_with_distinct_periods_is_not_a_conflict(self):
        a = chapter("A", ["I1"], ["R1"], [paragraph("P1", "Salário de R$ 2.200,00 de 06/2026 a 12/2026.", ["R1"])])
        b = chapter("B", ["I2"], ["R2"], [paragraph("P1", "Salário de R$ 2.500,00 a partir de 01/2027.", ["R2"])])
        self.assertEqual(check_consistency([a, b], REVIEW)["blocking_count"], 0)

    def test_comparison_inside_one_sentence_and_paradigm_are_not_conflicts(self):
        a = chapter("A", ["I1"], ["R1"], [paragraph("P1", "Recebia salário de R$ 2.200,00, e o salário do paradigma era de R$ 3.100,00.", ["R1"]),
                                          paragraph("P2", "O salário de R$ 2.200,00 consta do relato.")])
        self.assertEqual(check_consistency([a], {"requests": [{"id": "R1", "issue_ids": ["I1"]}]})["blocking_count"], 0)

    def test_admission_date_divergence_blocks_and_month_precision_is_compatible(self):
        a = chapter("A", ["I1"], ["R1"], [paragraph("P1", "Foi admitida em 01/06/2026.", ["R1"])])
        b = chapter("B", ["I2"], ["R2"], [paragraph("P1", "Admitida em 02/06/2026, foi dispensada sem justa causa.", ["R2"])])
        self.assertIn("event_date", self.kinds(check_consistency([a, b], REVIEW)))
        b["paragraphs"][0]["text"] = "Admitida em junho de 2026."
        self.assertNotIn("event_date", self.kinds(check_consistency([a, b], REVIEW)))

    def test_identifier_must_exist_in_sources(self):
        a = chapter("A", ["I1"], ["R1"], [paragraph("P1", "A ré, CNPJ 12.345.678/0001-90, no processo 0001234-56.2026.5.02.0001.", ["R1"])])
        self.assertNotIn("entity", self.kinds(check_consistency([a], REVIEW)))
        a["paragraphs"][0]["text"] = "A ré, CNPJ 12.345.678/0001-99."
        self.assertIn("entity", self.kinds(check_consistency([a], REVIEW)))

    def test_request_coverage_both_directions(self):
        bare = chapter("A", ["I1", "I2"], ["R1"], [paragraph("P1", "Requer o pagamento.", ["R1"], facts=())])
        kinds = [f["detail"] for f in check_consistency([bare], REVIEW)["findings"] if f["kind"] == "coverage"]
        self.assertTrue(any("sem causa de pedir" in k for k in kinds))
        self.assertTrue(any("sem o pedido R2" in k for k in kinds))

    def test_subsidiary_request_requires_condition(self):
        review = {"requests": [{"id": "R1", "issue_ids": ["I1"], "priority": "subsidiary"}]}
        a = chapter("A", ["I1"], ["R1"], [paragraph("P1", "Sucessivamente, requer.", ["R1"])])
        self.assertIn("coverage", self.kinds(check_consistency([a], review)))
        review["requests"][0]["condition"] = "Se rejeitado o pedido principal."
        self.assertNotIn("coverage", self.kinds(check_consistency([a], review)))

    def test_bis_in_idem_in_calculation_set(self):
        item = {"relationship_id": "REL1", "competence": "2026-07", "claim_type": "horas_extras", "segment": "50",
                "kind": "principal", "include_in_total": True}
        review = copy.deepcopy(REVIEW)
        review["labor_review"] = {"calculation_set": {"items": [dict(item, request_ids=["R1"]), dict(item, request_ids=["R2"])]}}
        a = chapter("A", ["I1"], ["R1"], [paragraph("P1", "Horas extras.", ["R1"])])
        b = chapter("B", ["I2"], ["R2"], [paragraph("P1", "Horas extras pelo intervalo.", ["R2"])])
        self.assertIn("bis_in_idem", self.kinds(check_consistency([a, b], review)))
        review["requests"][1]["priority"] = "subsidiary"
        review["requests"][1]["condition"] = "Se rejeitado R1."
        self.assertNotIn("bis_in_idem", self.kinds(check_consistency([a, b], review)))

    def test_glossary_and_cross_references_are_warnings(self):
        a = chapter("A", ["I1"], ["R1"], [paragraph("P1", "A reclamada e a ré, conforme item 4.1.", ["R1"])])
        report = check_consistency([a], {"requests": [{"id": "R1", "issue_ids": ["I1"]}]})
        self.assertEqual(report["blocking_count"], 0)
        self.assertEqual(self.kinds(report, "warning"), ["cross_reference", "glossary"])
        self.assertEqual(self.kinds(check_consistency([a], {"requests": []}, sections={"4.1"}), "warning"), ["glossary"])


class AssembledConsistency(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        text = "REGISTRO INTEIRAMENTE SINTÉTICO. Holerite de teste: salário de R$ 2.500,00 na competência 08/2026."
        self.output, self.review, _ = synthetic_case(Path(self.temp.name), documents=1, document_text=text)
        initialize(self.output, self.review)

    def tearDown(self):
        self.temp.cleanup()

    def record(self, second_text):
        record = chapter_fixture(self.review)
        record["paragraphs"][0]["text"] = "A parte recebia salário de R$ 2.200,00. Requer o acolhimento do pedido sintético."
        record["paragraphs"].append({"id": "P2", "text": second_text, "fact_ids": ["F2"], "norm_ids": [], "issue_ids": ["I1"],
                                     "request_ids": [], "assertions": [{"fact_id": "F2", "fields": {"actor": "Parte do cenário"}}]})
        return record

    def test_divergent_salary_in_saved_chapters_blocks_assembly(self):
        save_chapter(self.output, self.record("O registro sintético aponta salário de R$ 2.500,00."))
        set_status(self.output, "salary", "approved", "synthetic-user-reference")
        preview = assemble(self.output, ["salary"], preview=True)
        self.assertEqual(preview["consistency"]["status"], "blocked")
        with self.assertRaisesRegex(ValueError, "Coerência entre capítulos"):
            assemble(self.output, ["salary"])
        self.assertFalse((self.output / "peticao_consolidada.md").exists())

    def test_period_qualified_salary_assembles(self):
        save_chapter(self.output, self.record("O registro sintético aponta salário de R$ 2.500,00 na competência 08/2026."))
        set_status(self.output, "salary", "approved", "synthetic-user-reference")
        result = assemble(self.output, ["salary"])
        self.assertIn(result["consistency"]["status"], {"consistent", "warnings"})


if __name__ == "__main__":
    unittest.main()
