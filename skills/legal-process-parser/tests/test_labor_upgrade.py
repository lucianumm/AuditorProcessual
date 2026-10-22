"""Observable labor regressions; fixtures do not measure professional merit."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.case_memory import identity
from scripts.labor_parameters import review_parameters, numbers_in_excerpt
from scripts.numeric_criteria import quantities
from scripts.labor_ledger import apportion_workdays
from scripts.labor_case_state import case_state, compare_reviews, impact, collective_candidates
from scripts.labor_calculations import compute_calculations, compare_reference
from scripts.labor_workflow import validate_workflow
from scripts.prose_review import prose_errors
from scripts.research_locator import rank_links, discover_candidates
from scripts.labor_research import research_agenda
from scripts.petition_workspace import dependencies, validate_chapter
from scripts.legal_review import finalize
from tests.test_labor_workflow import synthetic_case, ledger_fixture
from tests.test_response_research import numeric_fixture
from tests.test_incremental_petition import chapter_fixture


class NumericUnits(unittest.TestCase):
    def check_quote(self, quote, **updates):
        payload, checks, review, cites, texts = numeric_fixture()
        checks["inputs"][1].update(quote=quote, **updates)
        texts[cites[0]["source_record_id"]] = quote
        return review_parameters(payload, checks, review, cites, texts)

    def test_words_are_accepted_as_percent_not_bare_numeric_coincidence(self):
        result = self.check_quote("Critério sintético: cinquenta por cento.")
        self.assertFalse(result["errors"], result)
        self.assertEqual(result["total"], "3300.00")

    def test_days_do_not_support_a_percentage(self):
        result = self.check_quote("Critério sintético: 50 dias.")
        self.assertTrue(result["errors"])
        self.assertEqual(result["arithmetic_status"], "not_run")

    def test_number_in_article_is_not_a_rate(self):
        self.assertTrue(self.check_quote("Art. 50. Critério sem percentual.")["errors"])

    def test_same_value_separate_units_preserves_the_correct_span(self):
        result = self.check_quote("Após 50 dias, percentual sintético de cinquenta por cento.")
        self.assertFalse(result["errors"], result)
        self.assertEqual(result["numeric_criteria"]["RATE"][0]["unit"], "percent")

    def test_bound_requires_conditions_and_correct_relation(self):
        self.assertTrue(self.check_quote("No mínimo cinquenta por cento.")["errors"])
        self.assertFalse(self.check_quote("No mínimo cinquenta por cento.", source_relation="minimum", conditions_analysis="Limite mínimo do exercício; condição conferida.")["errors"])
        self.assertTrue(self.check_quote("No máximo cinquenta por cento.", source_relation="minimum", conditions_analysis="Condição.")["errors"])

    def test_inconsistent_declared_unit_cannot_override_transformation(self):
        self.assertTrue(self.check_quote("50 dias", source_unit="days")["errors"])

    def test_identity_cannot_convert_days_into_a_dimensionless_factor(self):
        payload, checks, review, cites, texts = numeric_fixture()
        payload["inputs"][1]["value"] = "50"
        checks["inputs"][1].update(transform="identity", source_unit="days", quote="50 dias")
        texts[cites[0]["source_record_id"]] = "50 dias"
        self.assertTrue(review_parameters(payload, checks, review, cites, texts)["errors"])

    def test_conditional_percentage_requires_condition_analysis(self):
        self.assertTrue(self.check_quote("50% quando preenchida a condição sintética.")["errors"])
        self.assertFalse(self.check_quote("50% quando preenchida a condição sintética.", conditions_analysis="Condição do exercício conferida.")["errors"])

    def test_portuguese_decimals_and_parenthetical_spelling(self):
        rows = quantities("52,5% (cinquenta e dois vírgula cinco por cento); 220 horas; R$ 1.000,00.")
        self.assertEqual([(Decimal(r["value"]), r["unit"]) for r in rows],
                         [(Decimal("52.5"), "percent"), (Decimal("52.5"), "percent"), (Decimal(220), "hours"), (Decimal(1000), "money")])
        self.assertIn(Decimal(50), numbers_in_excerpt("cinquenta por cento"))

    def test_limits_with_same_number_need_selection(self):
        self.assertTrue(self.check_quote("No mínimo 50%; no máximo 50%.", conditions_analysis="Condição.")["errors"])


def mixed_week():
    payload = ledger_fixture()
    payload["rules"][0]["period_end"] = "2026-06-03"
    payload["rules"].append(dict(payload["rules"][0], id="RULE2", period_start="2026-06-04", period_end="2026-06-30", daily_limit_minutes="420"))
    payload["days"] = []
    for i in range(7):
        day = (date(2026, 6, 1) + timedelta(days=i)).isoformat()
        payload["days"].append(dict(ledger_fixture()["days"][0], id="D" + str(i), date=day,
                                    intervals=[{"start": day + "T09:00:00-03:00", "end": day + "T17:00:00-03:00"}] if i < 6 else [],
                                    day_status="worked" if i < 6 else "rest"))
    return payload


class GlobalWeeklyRule(unittest.TestCase):
    def criterion(self):
        return {"id": "W1", "relationship_id": "REL1", "week_start": "2026-06-01", "rule_ids": ["RULE1", "RULE2"],
                "limit_basis": "physical", "weekly_limit_minutes": "2400", "norm_ids": ["N1"], "reason": "Critério global sintético confirmado."}

    def test_no_criterion_preserves_pending_state(self):
        self.assertTrue(all(w["total_excess_without_double_count"] is None for w in apportion_workdays(mixed_week())["weeks"]))

    def test_global_week_is_counted_once_with_daily_excess_preserved(self):
        payload = mixed_week()
        payload["weekly_criteria"] = [self.criterion()]
        result = apportion_workdays(payload)
        self.assertEqual(len(result["weeks"]), 1)
        row = result["weeks"][0]
        self.assertEqual(Decimal(row["daily_excess_minutes"]), 180)
        self.assertEqual(Decimal(row["additional_weekly_minutes"]), 300)
        self.assertEqual(Decimal(row["total_excess_without_double_count"]), 480)
        self.assertEqual(row["coverage"], "complete")

    def test_unknown_day_is_not_invented_as_rest(self):
        payload = mixed_week()
        payload["days"][-1]["day_status"] = "unknown"
        payload["weekly_criteria"] = [self.criterion()]
        self.assertEqual(apportion_workdays(payload)["weeks"][0]["coverage"], "partial")

    def test_wrong_rule_duplicate_criterion_or_basis_rejected(self):
        for mode in ("rule", "duplicate", "basis"):
            payload = mixed_week()
            payload["weekly_criteria"] = [self.criterion()]
            if mode == "rule":
                payload["weekly_criteria"][0]["rule_ids"] = ["RULE1"]
            elif mode == "basis":
                payload["weekly_criteria"][0]["limit_basis"] = "legal"
            else:
                payload["weekly_criteria"].append(self.criterion())
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                apportion_workdays(payload)


class ContractAndProse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output, cls.review, cls.memory = synthetic_case(Path(cls.temp.name), documents=1)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_client_observation_is_not_documentary_proof(self):
        state = case_state(self.review)
        row = next(r for r in state["timeline"] if r["id"] == "F1")
        self.assertEqual(row["evidence_status"], "client_account")
        action = state["proof_strategy"][0]["proof_actions"][0]
        self.assertEqual((action["holder"], action["stage"]), ("employer", "instrucao"))

    def test_atomic_salary_correction_reaches_paragraph_requests_and_accounts(self):
        old = copy.deepcopy(self.review)
        old["labor_review"]["calculation_set"] = numeric_fixture()[0]
        new = copy.deepcopy(old)
        new["assertion_reviews"][0]["atoms"]["amount"] = "2400.00"
        delta = compare_reviews(old, new)
        row = next(r for r in delta["changes"] if r["field"] == "assertion_reviews")
        self.assertIn("R1", row["impact"]["request_ids"])
        self.assertIn("P-fatos", row["impact"]["paragraph_ids"])
        self.assertIn("C1", row["impact"]["calculation_item_ids"])
        self.assertEqual(old["assertion_reviews"][0]["atoms"]["amount"], "2200.00")

    def test_late_documentary_contradiction_changes_dependent_conclusion(self):
        new = copy.deepcopy(self.review)
        new["facts"][1]["text"] = "Documento sintético decisivo da última página: pagamento não realizado."
        new["assertion_reviews"][1]["evidence_status"] = "contradicted"
        new["issues"][0]["conclusion"] = "Reexaminar a conclusão diante do documento tardio."
        delta = compare_reviews(self.review, new)
        self.assertTrue(any("I1" in r["impact"]["issue_ids"] for r in delta["changes"] if r["id"] == "F2"))

    def test_unlinked_fact_does_not_invalidate_independent_request(self):
        changed = impact(self.review, ["UNRELATED"])
        self.assertEqual(changed["issue_ids"], [])
        self.assertEqual(changed["calculation_item_ids"], [])

    def test_prose_reports_unregistered_money_and_false_certainty(self):
        p = {"id": "P1", "text": "Está comprovado o salário de R$ 9.999,00 e o fato é incontroverso.", "fact_ids": ["F1"], "norm_ids": []}
        messages = prose_errors(p, self.review)
        self.assertEqual(len(messages), 3, messages)
        p["text"] = "A parte recebia R$ 2.200,00."
        self.assertEqual(prose_errors(p, self.review), [])

    def test_block_quote_does_not_become_authored_factual_assertion(self):
        p = {"id": "P1", "text": "> Está comprovado o pagamento de R$ 9.999,00.", "fact_ids": ["F1"], "norm_ids": []}
        self.assertEqual(prose_errors(p, self.review), [])

    def test_negative_statement_does_not_claim_proof_or_admission(self):
        p = {"id": "P1", "text": "O fato não está comprovado e não é incontroverso.", "fact_ids": ["F1"], "norm_ids": []}
        self.assertEqual(prose_errors(p, self.review), [])

    def test_unknown_dates_and_corrected_events_remain_preserved(self):
        events = [{"id": "EV1", "bounds": {"earliest": "2025-01-01", "latest": "2025-01-31", "exact": False}, "description": "Admissão aproximada."},
                  {"id": "EV2", "bounds": {"earliest": None, "latest": None, "exact": False}, "description": "Retificação com data desconhecida.", "supersedes": "EV1"}]
        state = case_state(self.review, events={"events": events, "revision": identity(events)})
        rows = [r for r in state["timeline"] if r["kind"] == "client_event"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["bounds"]["earliest"], None)
        self.assertEqual(rows[1]["supersedes"], "EV1")
        with self.assertRaises(ValueError):
            case_state(self.review, events={"events": events, "revision": "tampered"})

    def test_change_in_proof_strategy_has_an_explained_impact(self):
        review = copy.deepcopy(self.review)
        review["labor_review"]["workflow"]["proof_plan"][0]["status"] = "requested"
        delta = compare_reviews(self.review, review)
        row = next(r for r in delta["changes"] if r["field"] == "workflow.proof_plan")
        self.assertIn("I1", row["impact"]["issue_ids"])

    def test_chapter_rejects_prose_value_outside_declared_assertions(self):
        chapter = chapter_fixture(self.review)
        chapter["paragraphs"][0]["text"] = "O salário era R$ 9.999,00."
        self.assertTrue(any("prosa" in e for e in validate_chapter(chapter, self.review)))

    def test_calculation_only_question_does_not_block_the_other_text(self):
        review = copy.deepcopy(self.review)
        review["labor_review"]["calculation_set"] = numeric_fixture()[0]
        w = review["labor_review"]["workflow"]
        w["material_questions"] = [{"id": "Q1", "claim_review_id": "CLAIM1", "field": "amount", "question": "Qual o salário do período?",
                                   "impact": "Somente a estimativa da parcela C1.", "status": "open", "answer_fact_ids": [], "reason": "Divergência salarial.",
                                   "impact_scope": "calculation_item", "calculation_item_ids": ["C1"], "searched_locations": ["relato C1 e documento F2 examinados"]}]
        self.assertFalse(validate_workflow(review, self.memory))
        w["material_questions"][0]["calculation_item_ids"] = ["MISSING"]
        self.assertTrue(validate_workflow(review, self.memory))

    def test_procedural_update_requires_the_actual_document(self):
        review = copy.deepcopy(self.review)
        row = {"id": "U1", "issue_id": "I1", "source_kind": "defense", "act_fact_id": "F2", "fact_ids": ["F1"],
               "norm_ids": ["N1"], "status": "denied", "reason": "A defesa sintética nega o fato."}
        review["labor_review"]["workflow"]["procedural_updates"] = [row]
        self.assertFalse(validate_workflow(review, self.memory))
        row["act_fact_id"] = "F1"
        self.assertTrue(validate_workflow(review, self.memory))

    def test_finalization_generates_and_bundles_contract_proof_state(self):
        review_path = Path(self.temp.name) / "review.json"
        review_path.write_text(json.dumps(self.review), encoding="utf-8")
        report = finalize(self.output, review_path)
        self.assertFalse(report["errors"], report)
        path = self.output / "contrato_provas_impactos.json"
        self.assertTrue(path.is_file())
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["review_revision"], identity(self.review))
        import zipfile
        with zipfile.ZipFile(self.output / "processo_completo.zip") as bundle:
            self.assertTrue(any(n.endswith("contrato_provas_impactos.json") for n in bundle.namelist()))

    def test_calculation_change_is_part_of_chapter_dependencies(self):
        review = copy.deepcopy(self.review)
        review["labor_review"]["calculation_set"] = numeric_fixture()[0]
        old = identity(dependencies(review, ["I1"]))
        review["labor_review"]["calculation_set"]["items"][0]["expected_result"] = "9999.00"
        self.assertNotEqual(old, identity(dependencies(review, ["I1"])))

    def test_unrelated_contract_period_is_not_included_by_shared_legislation(self):
        review = copy.deepcopy(self.review)
        period = dict(review["labor_review"]["contract_periods"][0], id="PER_OTHER", fact_ids=["F_OTHER"])
        review["labor_review"]["contract_periods"].append(period)
        before = identity(dependencies(review, ["I1"]))
        period["job"] = "Função de outro período não selecionado."
        self.assertEqual(before, identity(dependencies(review, ["I1"])))

    def test_collective_scope_vigency_and_literal_clause_change(self):
        old = copy.deepcopy(self.review)
        old["labor_review"]["contract_periods"][0].update(start="2026-06-01", end="2026-08-31")
        relation = old["labor_review"]["relationships"][0]
        instrument = {"id": "COL1", "norm_id": "N1", "instrument_type": "CCT", "registration_reference": "MR-synthetic",
                      "category_scope": [relation["category"]], "territory_scope": [relation["territory"]], "employer_scope": relation["employers"],
                      "effective_from": "2026-01-01", "effective_until": "2026-12-31", "clauses": [{"id": "C1", "provision": "cláusula sintética", "quote": "50%", "reason": "Fixture"}]}
        old["labor_review"]["collective_instruments"] = [instrument]
        self.assertEqual(collective_candidates(old)[0]["status"], "candidate_requires_legal_selection")
        new = copy.deepcopy(old)
        new["labor_review"]["collective_instruments"][0]["clauses"][0]["quote"] = "60%"
        row = next(r for r in compare_reviews(old, new)["changes"] if r["field"] == "collective_instruments")
        self.assertEqual(row["clause_changes"][0]["id"], "C1")
        self.assertIn("P-fatos", row["impact"]["paragraph_ids"])
        new["labor_review"]["collective_instruments"][0]["category_scope"] = ["OUTRA"]
        self.assertIn("category_not_matched", collective_candidates(new)[0]["reasons"])


class ResearchLocation(unittest.TestCase):
    def test_selects_specific_official_links_and_rejects_external_sources(self):
        html = '<a href="/acordao/123">Horas extras: fundamento do acórdão</a><a href="https://example.com/">Horas extras</a><a href="/login">Entrar</a>'
        rows = rank_links(html, "https://www.tst.jus.br/indice", "horas extras")
        self.assertEqual([r["url"] for r in rows], ["https://www.tst.jus.br/acordao/123"])
        self.assertEqual(rows[0]["status"], "candidate_requires_full_text_selection")

    def test_discovery_records_http_execution_and_scoped_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            (output / "research_sources").mkdir()
            (output / "research_sources/fixture.source").write_text('<a href="/decisao/1">jornada noturna</a>', encoding="utf-8")
            result = {"capture_id": "fixture", "url": "https://www.tst.jus.br/indice", "content_type": "text/html", "encoding": "utf-8"}
            with patch("scripts.research_locator.capture", side_effect=[result, OSError("synthetic unavailable")]) as captured:
                value = discover_candidates(output, [result["url"], "https://portal.stf.jus.br/indice"], "jornada noturna")
            self.assertEqual(captured.call_count, 2)
            self.assertEqual(len(value["candidates"]), 1)
            self.assertEqual(value["indexes"][1]["status"], "unavailable")

    def test_empty_index_does_not_claim_no_right_or_instrument(self):
        self.assertEqual(rank_links("<p>Sem links</p>", "https://www.tst.jus.br/", "FGTS"), [])

    def test_agenda_uses_question_period_and_scope_without_faking_consultation(self):
        value = research_agenda(["overtime"], [], question="compensação semanal", context={"period_start": "2025-01-01", "period_end": "2025-12-31", "category": "bancários"})
        self.assertTrue(any("compensação semanal" in q and "2025-01-01" in q for q in value["targeted_queries"]))
        self.assertEqual(value["status"], "research_plan_not_executed")


class ExternalCalculationDetail(unittest.TestCase):
    def test_equal_totals_cannot_hide_wrong_competence_or_rounding(self):
        result = compute_calculations(numeric_fixture()[0])
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "synthetic-external.json"
            source.write_text("Fixture; not a real PJe-Calc execution.", encoding="utf-8")
            reference = {"schema_version": "2.0", "input_revision": result["input_revision"], "source_file_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                         "tool": "synthetic", "tool_version": "fixture", "table_revision": "fixture", "reviewer": "test", "rounding": result["rounding"], "total": result["total"],
                         "items": [dict(r, rounding_mode=r.get("rounding_mode", "HALF_UP"), external_locator="fixture row " + r["id"]) for r in result["items"]],
                         "inputs": [dict(r, external_locator="fixture parameter " + r["id"]) for r in result["inputs"]]}
            self.assertEqual(compare_reference(result, reference, source)["status"], "matched")
            reference["items"][0]["competence"] = "2026-07"
            value = compare_reference(result, reference, source)
            self.assertEqual(value["status"], "divergent")
            self.assertEqual(value["mismatches"][0]["field"], "competence")
            with self.assertRaises(ValueError):
                compare_reference(result, reference)


if __name__ == "__main__":
    unittest.main()
