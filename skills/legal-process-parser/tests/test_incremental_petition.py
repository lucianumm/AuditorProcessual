"""Observable incremental work on synthetic accounts; no model or expert run."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.case_memory import atomic_json, update_memory
from scripts.client_intake import receive_accounts
from scripts.labor_events import date_bounds, receive_events
from scripts.labor_ledger import apportion_workdays
from scripts.labor_research import research_agenda, renew_sources
from scripts.labor_workflow import validate_workflow
from scripts.petition_workspace import initialize, refresh, packet, context_batch, save_chapter, set_status, assemble, load_workspace
from scripts.task_context import resolve_context
from scripts.time_bank import reconcile_bank
from scripts.validate_links import validate_links
from tests.test_labor_workflow import synthetic_case, ledger_fixture


def chapter_fixture(review, cid="salary"):
    return {"schema_version": "1.0", "id": cid, "title": "Diferenças salariais — cenário sintético",
            "issue_ids": ["I1"], "thesis_ids": [review["theses"][0]["id"]], "request_ids": ["R1"],
            "paragraphs": [{"id": "P1", "text": "A parte prestou serviços para EMP1. Requer o acolhimento do pedido sintético.",
                            "fact_ids": ["F1"], "norm_ids": ["N1"], "issue_ids": ["I1"], "request_ids": ["R1"],
                            "assertions": [{"fact_id": "F1", "fields": {"actor": "Parte do cenário", "amount": "2200.00"}}]}],
            "semantic_review": {"reviewer": "synthetic-fixture", "requirements": "Conferência de vínculos do cenário.",
                                "contrary_evidence": "Prova futura, sem fonte real confirmada.",
                                "applicability": "Fonte sintética para teste, não tese jurídica real.",
                                "requests_consistency": "Um pedido do cenário."}}


class IncrementalPetition(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output, self.review, self.memory = synthetic_case(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def start(self):
        return initialize(self.output, self.review)

    def test_analysis_does_not_create_chapters_or_assembly(self):
        state = self.start()
        self.assertEqual(state["chapters"], {})
        self.assertFalse((self.output / "peticao_consolidada.md").exists())
        self.assertFalse((self.output / "teses").exists())
        self.assertIn(self.review["theses"][0]["proposition"], (self.output / "mapa_teses.md").read_text(encoding="utf-8"))
        self.assertIn("mapa_teses.md", (self.output / "relatorio_processual.md").read_text(encoding="utf-8"))

    def test_selected_context_contains_attributed_sources(self):
        self.start()
        result = packet(self.output, ["I1"])
        self.assertEqual([f["id"] for f in result["facts"]], ["F1"])
        self.assertEqual([c["id"] for c in result["client_records"]], ["C1"])
        self.assertFalse(result["pending_reanalysis"])
        with self.assertRaises(ValueError):
            packet(self.output, ["missing"])

    def test_bounded_context_is_complete_and_revision_checked(self):
        self.start()
        batch = context_batch(self.output, ["I1"], max_chars=1700)
        chunks = [batch["text"]]
        revision = batch["context_revision"]
        while batch["next_offset"] is not None:
            batch = context_batch(self.output, ["I1"], batch["next_offset"], 1700, revision)
            chunks.append(batch["text"])
        self.assertEqual(json.loads("".join(chunks)), packet(self.output, ["I1"]))
        with self.assertRaises(ValueError):
            context_batch(self.output, ["I1"], 100, 1700, "changed")

    def test_declared_atomic_values_cannot_drift_across_chapters(self):
        self.start()
        record = chapter_fixture(self.review)
        record["paragraphs"][0]["assertions"][0]["fields"]["amount"] = "3300.00"
        with self.assertRaisesRegex(ValueError, "campo factual"):
            save_chapter(self.output, record)
        record["paragraphs"][0]["assertions"] = []
        with self.assertRaises(ValueError):
            save_chapter(self.output, record)

    def test_draft_review_approval_and_explicit_assembly(self):
        self.start()
        record = chapter_fixture(self.review)
        self.assertEqual(save_chapter(self.output, record)["status"], "draft")
        self.assertFalse((self.output / "peticao_consolidada.md").exists())
        with self.assertRaises(ValueError):
            set_status(self.output, "salary", "approved", "")
        with self.assertRaises(ValueError):
            assemble(self.output, ["salary"])
        set_status(self.output, "salary", "reviewed", "synthetic-review-reference")
        set_status(self.output, "salary", "approved", "synthetic-user-reference")
        result = assemble(self.output, ["salary"])
        self.assertEqual(result["uncovered_request_ids"], [])
        self.assertEqual(result["scope"], "selected_chapters_only")
        self.assertTrue((self.output / "peticao_consolidada.md").is_file())

    def test_allow_drafts_does_not_fabricate_approval(self):
        self.start()
        save_chapter(self.output, chapter_fixture(self.review))
        assemble(self.output, ["salary"], allow_drafts=True)
        state, _ = load_workspace(self.output)
        self.assertEqual(state["chapters"]["salary"]["status"], "draft")
        self.assertEqual(state["chapters"]["salary"]["approvals"], [])

    def test_edit_preserves_version_and_invalidates_prior_assembly(self):
        self.start()
        record = chapter_fixture(self.review)
        first = save_chapter(self.output, record)
        set_status(self.output, "salary", "approved", "synthetic-user-reference")
        assemble(self.output, ["salary"])
        record["paragraphs"][0]["text"] += " O pedido mantém o período narrado."
        latest = save_chapter(self.output, record)
        self.assertEqual(latest["status"], "draft")
        self.assertEqual(len(latest["history"]), 2)
        self.assertTrue((self.output / first["path"]).is_file())
        self.assertTrue((self.output / "peticao_consolidada.md").read_text(encoding="utf-8").startswith("# CONSOLIDAÇÃO ANTERIOR"))

    def test_same_version_is_idempotent(self):
        self.start()
        record = chapter_fixture(self.review)
        save_chapter(self.output, record)
        set_status(self.output, "salary", "approved", "synthetic-user-reference")
        repeated = save_chapter(self.output, record)
        self.assertEqual(repeated["status"], "approved")
        self.assertEqual(len(repeated["history"]), 1)

    def test_new_upload_requires_reanalysis_preserves_original_chapter(self):
        self.start()
        prior = save_chapter(self.output, chapter_fixture(self.review))
        set_status(self.output, "salary", "approved", "synthetic-user-reference")
        assemble(self.output, ["salary"])
        receive_accounts(self.output, {"schema_version": "1.0", "entries": [
            {"id": "C2", "text": "Informação adicional sintética, fora do pedido.", "conversation_reference": "synthetic-only"}]})
        state, _ = load_workspace(self.output)
        self.assertTrue(state["pending_reanalysis"])
        self.assertTrue((self.output / prior["path"]).exists())
        with self.assertRaises(ValueError):
            assemble(self.output, ["salary"])
        updated = copy.deepcopy(self.review)
        memory = update_memory(self.output)
        updated.update(corpus_revision=memory["corpus_revision"], client_records=memory["client_records"])
        updated["labor_review"]["corpus_revision"] = memory["corpus_revision"]
        updated["labor_review"]["workflow"]["client_record_ids"] = [c["id"] for c in memory["client_records"]]
        refresh(self.output, updated)
        state, _ = load_workspace(self.output)
        self.assertFalse(state["pending_reanalysis"])
        self.assertEqual(state["chapters"]["salary"]["status"], "approved")

    def test_changed_request_invalidates_dependent_chapter_only(self):
        self.start()
        save_chapter(self.output, chapter_fixture(self.review))
        set_status(self.output, "salary", "approved", "synthetic-user-reference")
        updated = copy.deepcopy(self.review)
        updated["requests"][0]["text"] += " Respeitado o período narrado."
        state = refresh(self.output, updated)
        self.assertEqual(state["chapters"]["salary"]["status"], "needs_review")
        self.assertEqual(len(state["analysis_history"]), 2)
        with self.assertRaises(ValueError):
            set_status(self.output, "salary", "approved", "new-reference")

    def test_no_cross_issue_sources_or_duplicate_requests(self):
        self.start()
        record = chapter_fixture(self.review)
        record["paragraphs"][0]["fact_ids"] = ["invented"]
        with self.assertRaises(ValueError):
            save_chapter(self.output, record)
        save_chapter(self.output, chapter_fixture(self.review, "a"))
        save_chapter(self.output, chapter_fixture(self.review, "b"))
        with self.assertRaisesRegex(ValueError, "Pedido repetido"):
            assemble(self.output, ["a", "b"], allow_drafts=True)

    def test_initial_narrative_and_material_gap_are_checked(self):
        self.start()
        record = chapter_fixture(self.review)
        record["paragraphs"][0]["text"] = "Conforme documentação, a parte alega a prestação de serviços."
        with self.assertRaises(ValueError):
            save_chapter(self.output, record)

    def test_current_snapshot_tampering_and_unsafe_ids_rejected(self):
        state = self.start()
        path = self.output / state["baseline_path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        value["requests"][0]["text"] = "Adulteração sintética."
        atomic_json(path, value)
        with self.assertRaisesRegex(ValueError, "adulterada"):
            load_workspace(self.output)

    def test_invalid_baseline_and_reset_are_rejected(self):
        broken = copy.deepcopy(self.review)
        broken["corpus_revision"] = "invalid"
        with self.assertRaises(ValueError):
            initialize(self.output, broken)
        self.start()
        with self.assertRaises(ValueError):
            initialize(self.output, self.review)

    def test_portable_links_include_board_and_chapters(self):
        self.start()
        save_chapter(self.output, chapter_fixture(self.review))
        errors = validate_links(self.output)
        self.assertFalse(errors, errors)


class LaborPrecisionTools(unittest.TestCase):
    def test_uncertain_month_and_unknown_date_do_not_become_exact(self):
        bounds = date_bounds({"precision": "month", "value": "2024-02", "end": None})
        self.assertEqual(bounds, {"earliest": "2024-02-01", "latest": "2024-02-29", "exact": False})
        self.assertIsNone(date_bounds({"precision": "unknown", "value": None, "end": None})["earliest"])
        with self.assertRaises(ValueError):
            date_bounds({"precision": "range", "value": "2026-03-01", "end": "2026-02-01"})

    def test_events_preserve_retifications_and_require_actual_quote(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            receive_accounts(out, {"schema_version": "1.0", "entries": [
                {"id": "C1", "text": "Comecei por volta de março de 2026.", "conversation_reference": "synthetic-only"}]})
            event = {"id": "E1", "client_record_id": "C1", "quote": "Comecei por volta de março de 2026.",
                     "description": "Admissão narrada em mês aproximado.", "kind": "hiring",
                     "happened": {"precision": "month", "value": "2026-03", "end": None}}
            receive_events(out, {"schema_version": "1.0", "events": [event]})
            bad = dict(event, description="Alteração sem nova versão.")
            with self.assertRaises(ValueError):
                receive_events(out, {"schema_version": "1.0", "events": [bad]})
            corrected = dict(event, id="E2", supersedes="E1", description="Descrição retificada, preservando incerteza.")
            self.assertEqual(len(receive_events(out, {"schema_version": "1.0", "events": [corrected]})["events"]), 2)
            with self.assertRaises(ValueError):
                receive_events(out, {"schema_version": "1.0", "events": [dict(event, id="E3", quote="Trecho inexistente")]})

    def test_granular_routing_does_not_load_all_labor_guides(self):
        context = resolve_context("chatgpt", "petition", labor_claims=["fgts"])
        paths = [r["path"] for r in context["references"]]
        self.assertTrue(any("pay_detail_rules" in p for p in paths))
        self.assertFalse(any("working_time_detail_rules" in p or "occupational_strategy" in p for p in paths))

    def test_mixed_week_never_restarts_weekly_allowance_silently(self):
        payload = ledger_fixture()
        rule = payload["rules"][0]
        rule["period_end"] = "2026-06-03"
        payload["rules"].append(dict(rule, id="RULE2", period_start="2026-06-04", period_end="2026-06-30"))
        payload["days"].append(dict(payload["days"][0], id="DAY2", date="2026-06-04", intervals=[
            {"start": "2026-06-04T09:00:00-03:00", "end": "2026-06-04T17:00:00-03:00"}]))
        result = apportion_workdays(payload)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(all(w["additional_weekly_minutes"] is None for w in result["weeks"]))

    def test_process_stay_is_distinct_from_effective_holding(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, review, memory = synthetic_case(Path(temporary))
            row = {"id": "A1", "issue_ids": ["I1"], "norm_id": "N1", "status_norm_ids": ["N1"],
                   "checked_on": "2026-10-12", "status": "suspended", "use": "merit_support",
                   "scope_analysis": "Hipótese estrutural sintética.", "temporal_reason": "Efeito distinguido, não norma real.",
                   "procedural_detail": {"merit_state": "decided", "process_state": "stayed", "holding_effect": "effective",
                                         "reason": "Somente fixture de consistência; depende de consulta jurídica real."}}
            review["labor_review"]["workflow"]["authority_checks"] = [row]
            self.assertFalse(validate_workflow(review, memory))
            row["procedural_detail"]["holding_effect"] = "suspended"
            self.assertTrue(any("mérito" in e for e in validate_workflow(review, memory)))

    def test_research_agenda_is_not_capture_and_failures_are_scoped(self):
        agenda = research_agenda(["fgts"], [], "15")
        self.assertEqual(agenda["status"], "research_plan_not_executed")
        self.assertEqual(len(agenda["queries"]), 1)
        with tempfile.TemporaryDirectory() as temporary, patch("scripts.labor_research.capture", side_effect=[OSError("unavailable"),
                {"capture_id": "synthetic", "text_hash": "fixture", "accessed_on": "2026-10-12"}]):
            result = renew_sources(Path(temporary), ["https://www.tst.jus.br/", "https://portal.stf.jus.br/"])
            self.assertEqual([r["status"] for r in result], ["unavailable", "captured"])

    def test_bank_allocations_are_not_counted_twice(self):
        credit = {"id": "C", "relationship_id": "REL1", "kind": "credit", "date": "2026-06-01", "minutes": "120",
                  "expires_on": "2026-06-30", "fact_ids": ["F1"], "norm_ids": ["N1"], "allocations": []}
        debit = dict(credit, id="D", kind="debit", date="2026-06-02", minutes="60", expires_on=None,
                     allocations=[{"credit_id": "C", "minutes": "60"}])
        payload = {"schema_version": "1.0", "as_of": "2026-07-02", "movements": [credit, debit]}
        result = reconcile_bank(payload)
        self.assertEqual(result["balances"][0]["remaining_minutes"], "60")
        self.assertTrue(result["balances"][0]["expired_under_supplied_date"])
        payload["movements"].append(dict(debit, id="D2", minutes="90", allocations=[{"credit_id": "C", "minutes": "90"}]))
        with self.assertRaisesRegex(ValueError, "saldo"):
            reconcile_bank(payload)


if __name__ == "__main__":
    unittest.main()
