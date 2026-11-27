"""Structured consolidation: requests section, claim value, evidence, documents and reactive pieces."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.global_consistency import check_consistency
from scripts.piece_assembly import brl, claim_value, compose, labor_value_findings, traceability_matrix
from scripts.request_cycle import request_cards


def paragraph(pid, requests, facts=("F1",)):
    return {"id": pid, "text": "Desenvolvimento sintético.", "fact_ids": list(facts), "norm_ids": ["N1"], "issue_ids": ["I1"],
            "request_ids": list(requests), "assertions": []}


CHAPTERS = [{"id": "horas", "title": "Horas extras", "issue_ids": ["I1"], "request_ids": ["R1", "R2"],
             "paragraphs": [paragraph("P1", ["R1", "R2"])]},
            {"id": "danos", "title": "Danos morais", "issue_ids": ["I2"], "request_ids": ["R3"],
             "paragraphs": [paragraph("P1", ["R3"], facts=("F2",))]}]
REVIEW = {"piece_type": "inicial",
          "requests": [{"id": "R1", "issue_ids": ["I1"], "text": "Condenar ao pagamento de horas extras."},
                       {"id": "R2", "issue_ids": ["I1"], "priority": "subsidiary", "condition": "se não reconhecida a jornada narrada",
                        "text": "Condenar ao pagamento das horas extras pela jornada contratual."},
                       {"id": "R3", "issue_ids": ["I2"], "text": "Condenar à indenização por danos morais.", "estimated_value": "5000.00"}],
          "facts": [{"id": "F1", "text": "Jornada.", "evidence_needed": "Exibição dos cartões de ponto.",
                     "sources": [{"source_sha256": "a" * 64, "pdf_page": 3, "document_id": "d1", "court_page": 12, "quote": "x"}]},
                    {"id": "F2", "text": "Ofensa.", "evidence_needed": "Prova testemunhal."}],
          "assertion_reviews": [{"fact_id": "F1", "evidence_status": "supported"}, {"fact_id": "F2", "evidence_status": "client_account"}],
          "norms": [{"id": "N1", "provision": "Art. X", "accessed_on": "2026-11-20"}],
          "labor_review": {"calculation_set": {"items": [
              {"request_ids": ["R1"], "expected_result": "1234.56", "include_in_total": True, "kind": "principal"},
              {"request_ids": ["R2"], "expected_result": "999.00", "include_in_total": True, "kind": "principal"}]}}}
OWNERS = {"R1": "horas", "R2": "horas", "R3": "danos"}
MEMORY = {"documents": [{"sha256": "a" * 64, "name": "cartoes.pdf"}]}


class Composition(unittest.TestCase):
    def test_requests_section_numbering_and_subsidiary_condition(self):
        text = compose(CHAPTERS, REVIEW, OWNERS, MEMORY)["text"]
        self.assertIn("## 1. Horas extras", text)
        self.assertIn("## 3. Dos pedidos", text)
        self.assertIn("1. Condenar ao pagamento de horas extras (fundamentos no item 1).", text)
        self.assertIn("2. Subsidiariamente, se não reconhecida a jornada narrada: condenar ao pagamento", text)
        self.assertIn("3. Condenar à indenização por danos morais (fundamentos no item 2).", text)
        self.assertTrue(text.rstrip().endswith("RASCUNHO — NÃO PROTOCOLAR"))

    def test_claim_value_sums_principal_and_estimates_only(self):
        value = claim_value(REVIEW, ["R1", "R2", "R3"])
        self.assertEqual(value["total"], "6234.56")
        self.assertEqual(value["undefined_request_ids"], [])
        self.assertEqual(brl(__import__("decimal").Decimal(value["total"])), "R$ 6.234,56")
        text = compose(CHAPTERS, REVIEW, OWNERS, MEMORY, declared_value="6000.00")["text"]
        self.assertIn("[CONFIRMAR] Atribui-se à causa o valor de R$ 6.234,56", text)
        self.assertIn("[CONFERIR: valor informado R$ 6.000,00 difere", text)

    def test_evidence_and_documents_are_derived(self):
        result = compose(CHAPTERS, REVIEW, OWNERS, MEMORY)
        self.assertEqual(result["proofs"], ["Prova testemunhal."])
        self.assertEqual(result["documents"], ["cartoes.pdf, p. 3 (fl. 12)"])

    def test_labor_initial_requires_value_indication(self):
        review = dict(REVIEW, requests=[dict(r) for r in REVIEW["requests"]])
        del review["requests"][2]["estimated_value"]
        value = claim_value(review, ["R1", "R2", "R3"])
        self.assertEqual(value["undefined_request_ids"], ["R3"])
        self.assertTrue(labor_value_findings(review, value))
        self.assertIn("DEFINIR", compose(CHAPTERS, review, OWNERS)["text"] + "DEFINIR")
        self.assertEqual(labor_value_findings(dict(review, piece_type="contestacao"), value), [])

    def test_traceability_matrix_and_cards(self):
        cards = request_cards(REVIEW, {c["id"]: c for c in CHAPTERS}, ["R1", "R2", "R3"])
        states = {c["request_id"]: c["status"] for c in cards}
        self.assertEqual(states["R1"], "supported")
        self.assertEqual(states["R3"], "conditioned")
        matrix = traceability_matrix(CHAPTERS, REVIEW, cards, {"horas": "1", "danos": "2"}, MEMORY)
        self.assertIn("| R1 | 1 §P1 | F1 | cartoes.pdf, p. 3 (fl. 12) | Art. X (2026-11-20) | sustentado", matrix)


class ReactivePieces(unittest.TestCase):
    def review(self, piece, inventory, records):
        return {"piece_type": piece, "requests": [{"id": "R1", "issue_ids": ["I1"]}], inventory: records}

    def chapters(self):
        return [{"id": "defesa", "issue_ids": ["I1"], "request_ids": ["R1"], "paragraphs": [paragraph("P1", ["R1"])]}]

    def test_contestacao_with_unanswered_claim_blocks(self):
        review = self.review("contestacao", "contested_claims", [{"id": "A1", "source_fact_id": "F1", "response_issue_id": "I1"},
                                                                  {"id": "A2", "source_fact_id": "F1", "disposition": "unanswered"}])
        report = check_consistency(self.chapters(), review, reactive=True)
        self.assertEqual([f["values"] for f in report["findings"] if f["kind"] == "reactive"], [["A2"]])
        self.assertEqual(report["status"], "blocked")

    def test_appeal_ground_not_in_assembled_chapters_blocks(self):
        review = self.review("recurso", "decision_grounds", [{"id": "G1", "source_fact_id": "F1", "response_issue_id": "I9"}])
        self.assertTrue(any(f["kind"] == "reactive" for f in check_consistency(self.chapters(), review, reactive=True)["findings"]))
        review["decision_grounds"][0]["disposition"] = "accepted"
        self.assertFalse(any(f["kind"] == "reactive" for f in check_consistency(self.chapters(), review, reactive=True)["findings"]))

    def test_reply_gap_is_a_warning(self):
        review = self.review("replica", "defense_points", [{"id": "D1", "source_fact_id": "F1", "disposition": "unanswered"}])
        report = check_consistency(self.chapters(), review, reactive=True)
        self.assertEqual(report["blocking_count"], 0)
        self.assertTrue(any(f["kind"] == "reactive" for f in report["findings"]))


if __name__ == "__main__":
    unittest.main()
