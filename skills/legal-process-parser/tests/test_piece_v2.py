"""Behavioral checks for piece-specific traceability; all examples are synthetic."""

import copy
import sys
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))

from scripts.piece_validation import initial_voice_findings, validate_piece
from scripts.readiness import normalize_findings, validate_findings


def review_for(piece_type):
    reasoning_section = {
        "inicial": "fundamentos", "contestacao": "impugnacao", "replica": "impugnacao",
        "recurso": "impugnacao", "pericia": "analise_tecnica",
        "cumprimento": "obrigacao", "manifestacao": "fundamentos",
    }[piece_type]
    return {
        "task": "petition", "piece_type": piece_type,
        "facts": [{"id": "F1", "text": "Fato sintético."}],
        "issues": [{"id": "I1", "fact_ids": ["F1"], "question": "Questão sintética."}],
        "requests": [{"id": "R1", "priority": "principal", "issue_ids": ["I1"],
                      "fact_ids": ["F1"], "text": "Pedido sintético."}],
        "paragraphs": [
            {"id": "P1", "section": "fatos", "text": "A obrigação surgiu.", "fact_ids": ["F1"],
             "issue_ids": [], "request_ids": []},
            {"id": "P2", "section": reasoning_section, "text": "O fato preenche o requisito.",
             "fact_ids": ["F1"], "issue_ids": ["I1"], "request_ids": []},
            {"id": "P3", "section": "pedidos", "text": "Requer-se a providência.",
             "fact_ids": [], "issue_ids": [], "request_ids": ["R1"]},
        ],
    }


def codes(review):
    return {finding["code"] for finding in validate_piece(review, {})}


class PieceValidationV2(unittest.TestCase):
    def test_initial_voice_excludes_literal_opponent_quote(self):
        self.assertEqual(initial_voice_findings({
            "section": "fatos", "text": "A ré declarou: “A autora alega inadimplemento.” O pagamento venceu."
        }), [])
        self.assertEqual(initial_voice_findings({
            "section": "fatos", "text": "A autora sustenta que a parcela venceu."
        }), ["narrativa da própria parte com distanciamento"])
        review = review_for("inicial")
        review["paragraphs"][0]["text"] = "A autora sustenta que prestou serviços."
        self.assertIn("INITIAL_DISTANCED_VOICE", codes(review))
        review["paragraphs"][0]["text"] = "A autora prestou serviços."
        self.assertNotIn("INITIAL_DISTANCED_VOICE", codes(review))

    def test_contestacao_registered_claim_has_drafted_answer(self):
        review = review_for("contestacao")
        self.assertEqual(codes(review), set())  # Legacy revisions need no invented inventory.
        review["contested_claims"] = [{"id": "C1", "source_fact_id": "F1",
                                        "response_issue_id": "I1", "disposition": "disputed"}]
        self.assertEqual(codes(review), set())
        review["paragraphs"][1]["issue_ids"] = []
        self.assertIn("PIECE_RESPONSE_NOT_DRAFTED", codes(review))
        review["contested_claims"][0]["disposition"] = "unanswered"
        self.assertIn("PIECE_GROUND_UNANSWERED", codes(review))

    def test_replica_new_document_is_answered_or_explained(self):
        review = review_for("replica")
        review["defense_points"] = [{"id": "D1", "kind": "new_document", "source_fact_id": "F1",
                                      "response_issue_id": "I1", "disposition": "answered"}]
        self.assertEqual(codes(review), set())
        review["defense_points"][0].update(disposition="irrelevant", response_issue_id=None)
        self.assertIn("PIECE_DISPOSITION_UNEXPLAINED", codes(review))
        review["defense_points"][0]["reason"] = "Não se relaciona ao pedido impugnado."
        self.assertNotIn("PIECE_DISPOSITION_UNEXPLAINED", codes(review))

    def test_recurso_decision_ground_requires_response_when_essential(self):
        review = review_for("recurso")
        review["decision_grounds"] = [{"id": "G1", "source_fact_id": "F1", "response_issue_id": "I1"}]
        self.assertEqual(codes(review), set())
        review["decision_grounds"].append({"id": "G2", "source_fact_id": "F1",
                                            "disposition": "not_challenged", "essential": True})
        finding = next(f for f in validate_piece(review, {}) if f["code"] == "PIECE_GROUND_UNANSWERED")
        self.assertEqual(finding["delivery_effect"], "blocks_delivery")
        review["decision_grounds"][1].update(essential=False, reason="Fundamento acessório sem efeito no capítulo recorrido.")
        self.assertNotIn("PIECE_GROUND_UNANSWERED", codes(review))

    def test_requests_require_reasoning_and_compatible_order(self):
        review = review_for("inicial")
        review["requests"].append({"id": "R2", "priority": "principal", "issue_ids": ["I1"],
                                   "fact_ids": ["F1"], "text": "Pedido incompatível."})
        review["requests"][0]["incompatible_with"] = ["R2"]
        self.assertIn("PIECE_PRINCIPAL_CONFLICT", codes(review))
        self.assertIn("PIECE_REQUEST_NOT_DRAFTED", codes(review))
        review["requests"][1].update(priority="alternative", related_request_id="R1",
                                     condition="Se o pedido principal não for acolhido")
        review["paragraphs"][2]["request_ids"].append("R2")
        self.assertNotIn("PIECE_PRINCIPAL_CONFLICT", codes(review))
        self.assertNotIn("PIECE_REQUEST_NOT_DRAFTED", codes(review))
        review["requests"][0]["related_request_id"] = "R2"
        self.assertIn("PIECE_REQUEST_RELATION_CYCLE", codes(review))
        review["requests"][0].pop("related_request_id")
        review["paragraphs"][1]["issue_ids"] = []
        self.assertIn("PIECE_REQUEST_NO_REASONING", codes(review))

    def test_non_petition_review_has_no_piece_gate(self):
        review = review_for("inicial")
        review["task"] = "analyze"
        review["paragraphs"][0]["text"] = "A autora alega inadimplemento."
        self.assertEqual(validate_piece(review, {}), [])

    def test_piece_findings_use_resolvable_scopes(self):
        review = review_for("recurso")
        review["decision_grounds"] = [
            {"id": "G1", "source_fact_id": "missing", "disposition": "challenged"},
            {"id": "G2", "source_fact_id": "F1", "disposition": "not_challenged", "essential": True},
            {"id": "G3", "source_fact_id": "F1", "disposition": "accepted"},
        ]
        findings = normalize_findings(review, validate_piece(review, {}))
        self.assertEqual(validate_findings(findings, review, {"documents": []}), [])


if __name__ == "__main__":
    unittest.main()
