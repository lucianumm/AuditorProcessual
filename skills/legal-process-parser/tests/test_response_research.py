"""Fresh-query and numeric-criteria fixtures; no real legal merit evaluation."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.case_memory import atomic_json, atomic_bytes, identity
from scripts.response_research import begin_response, consult_http, consult_browser, bind_response, validate_response, utc_now, target_hash
from scripts.research_memory import register_source_record, research_revision
from scripts.petition_workspace import initialize, save_chapter, assemble
from scripts.labor_parameters import review_parameters, numbers_in_excerpt, select_calculations
from scripts.client_intake import receive_accounts
from scripts.validate_links import validate_links
from scripts.precision_validation import validate_precision
from scripts.task_context import resolve_context
from tests.test_labor_workflow import synthetic_case
from tests.test_incremental_petition import chapter_fixture


class ResponseResearch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output, self.review, _ = synthetic_case(Path(self.temp.name))
        source = self.review["norms"][0]
        self.original_record = json.loads((self.output / "research_sources" / (source["capture_id"] + ".json")).read_text(encoding="utf-8"))
        self.raw = (self.output / "research_sources" / (source["capture_id"] + ".source")).read_bytes()

    def fake_http(self, url, output, *, response_id=None):
        # Controlled fixture simulates downloaded bytes; never a real HTTP call.
        record = {k: v for k, v in self.original_record.items() if k != "capture_id"}
        record.update(requested_url=url, url=url, captured_at=utc_now(),
                      accessed_on=datetime.now(timezone.utc).date().isoformat(), response_id=response_id)
        record["capture_id"] = identity(record)
        atomic_bytes(output / "research_sources" / (record["capture_id"] + ".source"), self.raw)
        atomic_json(output / "research_sources" / (record["capture_id"] + ".json"), record)
        register_source_record(output, record)
        return record

    def researched(self, *, artifact=None, browser=False):
        state = begin_response(self.output, ["I1"], "synthetic-request-not-real-client")
        norm = self.review["norms"][0]
        if browser:
            consulted = consult_browser(self.output, state["response_id"], "I1", "N1", purpose="Teste de observação declarada",
                url=norm["url"], accessed_on=datetime.now(timezone.utc).date().isoformat(),
                text=norm["official_text"], context="Fixture, não consulta real.", tool_reference="synthetic-tool-reference",
                observed_by="synthetic-fixture", observed_at=utc_now())
            self.review["research_revision"] = research_revision(self.output)
        else:
            with patch("scripts.response_research.capture", side_effect=self.fake_http):
                consulted = consult_http(self.output, state["response_id"], "I1", "N1", norm["url"], purpose="Teste estrutural, não direito real.")
        target = artifact or self.review
        payload = {"schema_version": "1.0", "response_id": state["response_id"], "issue_ids": ["I1"],
                   "artifact_hash": target_hash(target), "research_revision": research_revision(self.output), "checked_at": utc_now(),
                   "citations": [{"issue_id": "I1", "norm_id": "N1", "source_record_id": consulted["source_record_id"],
                                  "quote": norm["quote"], "applicability_analysis": "Vínculos do cenário, não interpretação real.",
                                  "version_analysis": "Versão da fixture."}],
                   "causes": [{"id": "CAUSE1", "issue_id": "I1", "paragraph_ids": [p["id"] for p in target["paragraphs"]],
                               "fact_ids": ["F1"], "norm_ids": ["N1"], "request_ids": ["R1"],
                               "requirements_analysis": "Requisitos sintéticos.", "exceptions_analysis": "Limites do cenário.",
                               "contrary_analysis": "Prova futura prevista.", "consequence": "Pedido sintético.",
                               "status": "qualified", "limitation": "Fixture não certifica mérito."}]}
        return payload

    def test_agenda_or_cached_authority_does_not_satisfy_new_response(self):
        initialize(self.output, self.review)
        with self.assertRaises(ValueError):
            save_chapter(self.output, chapter_fixture(self.review))
        with self.assertRaises(ValueError):
            begin_response(self.output, [], "missing-scope")

    def test_response_contracts_load_only_for_local_json_and_selected_calculation(self):
        brief = resolve_context("generic", "petition", labor_claims=["overtime"])
        self.assertIn("response_research", brief["triggers"])
        self.assertNotIn("response_contract", brief["triggers"])
        self.assertFalse(any("response_research.schema" in r["path"] for r in brief["references"]))
        local = resolve_context("generic", "petition", labor_claims=["overtime"],
                                triggers=["local_contract", "labor_calculation"])
        self.assertTrue({"response_contract", "parameter_contract"} <= set(local["triggers"]))
        self.assertTrue(any("local_response_workflow" in r["path"] for r in local["references"]))
        self.assertFalse(any("labor_sectors/domestic" in r["path"] for r in local["references"]))

    def test_fresh_http_binding_and_current_chapter_end_to_end(self):
        initialize(self.output, self.review)
        chapter = chapter_fixture(self.review)
        chapter["schema_version"] = "2.0"
        research = self.researched(artifact=chapter)
        bound = bind_response(self.output, research, self.review, chapter)
        chapter["response_research"] = bound
        result = save_chapter(self.output, chapter)
        self.assertEqual(result["response_policy"], "per_response")
        self.assertFalse(validate_response(self.output, bound, self.review, chapter)["errors"])
        self.assertEqual(validate_links(self.output), [])

    def test_body_change_cannot_reuse_bound_consultation(self):
        chapter = chapter_fixture(self.review)
        payload = bind_response(self.output, self.researched(artifact=chapter), self.review, chapter)
        modified = copy.deepcopy(chapter)
        modified["paragraphs"][0]["text"] += " Outro desenvolvimento."
        self.assertTrue(validate_response(self.output, payload, self.review, modified)["errors"])
        with self.assertRaises(ValueError):
            bind_response(self.output, payload, self.review, modified)

    def test_bound_response_is_preserved_not_overwritten(self):
        payload = bind_response(self.output, self.researched(), self.review)
        path = self.output / "response_research" / payload["response_id"] / "response.json"
        previous = path.read_bytes()
        with self.assertRaises(ValueError):
            bind_response(self.output, payload, self.review)
        self.assertEqual(path.read_bytes(), previous)

    def test_current_numeric_review_executes_and_preserves_portable_markdown(self):
        calculation, checks, _, _, _ = numeric_fixture()
        calculation["corpus_revision"] = self.review["corpus_revision"]
        self.review["labor_review"]["calculation_set"] = calculation
        self.review["normative_map"][0].update(temporal_status="applicable", effective_from="2020-01-01", effective_until=None)
        rate_quote = "Critério inteiramente sintético 50%, não norma real."
        self.review["norms"][0]["official_text"] += " " + rate_quote
        payload = self.researched(browser=True)
        checks["inputs"][1].update(source_record_id=payload["citations"][0]["source_record_id"], quote=rate_quote)
        payload["parameter_review"] = checks
        bound = bind_response(self.output, payload, self.review)
        directory = self.output / "response_research" / bound["response_id"]
        result = json.loads((directory / "calculo.json").read_text(encoding="utf-8"))
        self.assertEqual(result["total"], "3300.00")
        self.assertIn("3300.00", (directory / "memoria_calculo.md").read_text(encoding="utf-8"))
        self.assertEqual(validate_links(self.output), [])

    def test_old_capture_cannot_be_substituted_for_new_query(self):
        payload = self.researched()
        payload["citations"][0]["source_record_id"] = self.review["norms"][0]["capture_id"]
        self.assertTrue(any("consulta nova" in e for e in validate_response(self.output, payload, self.review)["errors"]))

    def test_browser_remains_declared_not_independently_attested(self):
        payload = self.researched(browser=True)
        result = validate_response(self.output, payload, self.review)
        self.assertFalse(result["errors"], result)
        self.assertEqual(set(result["source_levels"].values()), {"self_recorded_unverified"})

    def test_old_or_future_browser_observation_does_not_pass_freshness(self):
        for shift in (-1, 1):
            with self.subTest(shift=shift):
                state = begin_response(self.output, ["I1"], "timestamp-fixture")
                norm = self.review["norms"][0]
                moment = datetime.now(timezone.utc) + timedelta(seconds=shift * 60)
                row = consult_browser(self.output, state["response_id"], "I1", "N1", purpose="Fixture timestamp",
                    url=norm["url"], accessed_on=moment.date().isoformat(), text=norm["official_text"],
                    context="Fixture sem navegação real", tool_reference="synthetic", observed_by="fixture", observed_at=moment.isoformat())
                payload = self.researched()
                payload.update(response_id=state["response_id"], research_revision=research_revision(self.output))
                payload["citations"][0]["source_record_id"] = row["source_record_id"]
                self.assertTrue(any("Fonte anterior" in e for e in validate_response(self.output, payload, self.review)["errors"]))

    def test_raw_capture_bytes_are_checked_not_only_source_metadata(self):
        payload = self.researched()
        source_id = payload["citations"][0]["source_record_id"]
        atomic_bytes(self.output / "research_sources" / (source_id + ".source"), b"tampered synthetic bytes")
        self.assertTrue(validate_response(self.output, payload, self.review)["errors"])

    def test_precedent_requires_current_merit_and_status_excerpts(self):
        status_line = "Situação sintética: tese firmada e publicada, sem modulação nesta fixture."
        self.review["norms"][0]["official_text"] += " " + status_line
        payload = self.researched(browser=True)
        self.review["norms"][0]["kind"] = "precedent"
        payload["artifact_hash"] = target_hash(self.review)
        self.assertTrue(validate_response(self.output, payload, self.review)["errors"])
        source_id = payload["citations"][0]["source_record_id"]
        payload["precedents"] = [{"norm_id": "N1", "issue_id": "I1", "holding_source_id": source_id,
            "status_source_id": source_id, "holding_excerpt": self.review["norms"][0]["quote"],
            "status_excerpt": self.review["norms"][0]["quote"], "merit_analysis": "Synthetic merit, not real law.",
            "process_analysis": "Fixture process state.", "effect_analysis": "Fixture effect.",
            "modulation_analysis": "Fixture limits.", "case_comparison": "Synthetic comparison.", "contrary_analysis": "Synthetic objection."}]
        self.assertTrue(any("situação" in e for e in validate_response(self.output, payload, self.review)["errors"]))
        payload["precedents"][0]["status_excerpt"] = status_line
        self.assertFalse(validate_response(self.output, payload, self.review)["errors"])
        payload["precedents"][0]["status_source_id"] = self.review["norms"][0]["capture_id"]
        self.assertTrue(validate_response(self.output, payload, self.review)["errors"])

    def test_legal_support_does_not_certify_an_unproven_account(self):
        payload = self.researched()
        payload["causes"][0]["status"] = "supported"
        self.assertTrue(any("relatado" in e for e in validate_response(self.output, payload, self.review)["errors"]))
        payload["causes"][0]["status"] = "qualified"
        self.assertFalse(validate_response(self.output, payload, self.review)["errors"])

    def test_wrong_quote_wrong_issue_and_unreviewed_paragraph_rejected(self):
        payload = self.researched()
        for mode in ("quote", "issue", "paragraph"):
            modified = copy.deepcopy(payload)
            if mode == "quote":
                modified["citations"][0]["quote"] = "Inexistent legal quotation."
            elif mode == "issue":
                modified["citations"][0]["issue_id"] = "OTHER"
            else:
                modified["causes"][0]["paragraph_ids"] = []
            with self.subTest(mode=mode):
                self.assertTrue(validate_response(self.output, modified, self.review)["errors"])

    def test_unavailable_lookup_is_scoped_and_alternative_is_executed(self):
        state = begin_response(self.output, ["I1"], "synthetic")
        url = self.review["norms"][0]["url"]
        with patch("scripts.response_research.capture", side_effect=OSError("synthetic access failure")):
            row = consult_http(self.output, state["response_id"], "I1", "N1", url, purpose="Fixture")
        payload = {"schema_version": "1.0", "response_id": state["response_id"], "issue_ids": ["I1"],
                   "artifact_hash": target_hash(self.review), "research_revision": research_revision(self.output), "checked_at": utc_now(),
                   "citations": [], "causes": [{"id": "C1", "issue_id": "I1", "paragraph_ids": [p["id"] for p in self.review["paragraphs"]],
                   "fact_ids": ["F1"], "norm_ids": [], "request_ids": ["R1"], "requirements_analysis": "Dados lidos.",
                   "exceptions_analysis": "Fonte pendente.", "contrary_analysis": "Fonte pendente.", "consequence": "Delimitar tese.",
                   "status": "pending", "limitation": "Consulta falhou, sem conclusão jurídica atual."}]}
        result = validate_response(self.output, payload, self.review)
        self.assertEqual(result["status"], "partial", result)
        next_state = begin_response(self.output, ["I1"], "new-synthetic")
        calls = []
        def fallback(target, output, *, response_id=None):
            calls.append(target)
            if len(calls) == 1:
                raise OSError("synthetic failure")
            return self.fake_http(target, output, response_id=response_id)
        with patch("scripts.response_research.capture", side_effect=fallback):
            result = consult_http(self.output, next_state["response_id"], "I1", "N1", url,
                                  alternatives=["https://www.tst.jus.br/"], purpose="Fixture alternative")
        self.assertEqual(result["status"], "consulted")
        self.assertEqual(len(calls), 2)

    def test_stale_corpus_invalidates_only_recorded_response_use(self):
        payload = self.researched()
        receive_accounts(self.output, {"schema_version": "1.0", "entries": [
            {"id": "C2", "text": "Novo relato sintético.", "conversation_reference": "synthetic"}]})
        self.assertTrue(any("Corpus" in e for e in validate_response(self.output, payload, self.review)["errors"]))

    def test_new_review_policy_requires_actual_contract(self):
        review = copy.deepcopy(self.review)
        review["response_policy"] = "per_response"
        review["response_research"] = {}
        memory = json.loads((self.output / "case_memory.json").read_text(encoding="utf-8"))
        self.assertTrue(validate_precision(review, memory, self.output))
        review["response_research"] = self.researched(artifact=review)
        self.assertFalse(validate_precision(review, memory, self.output))

    def test_current_assembly_requires_its_own_research(self):
        initialize(self.output, self.review)
        chapter = chapter_fixture(self.review)
        chapter["schema_version"] = "2.0"
        chapter["response_research"] = bind_response(self.output, self.researched(artifact=chapter), self.review, chapter)
        save_chapter(self.output, chapter)
        with self.assertRaises(ValueError):
            assemble(self.output, ["salary"], allow_drafts=True)
        preview = assemble(self.output, ["salary"], allow_drafts=True, preview=True)
        payload = bind_response(self.output, self.researched(artifact=preview), self.review, preview)
        result = assemble(self.output, ["salary"], allow_drafts=True, response=payload)
        self.assertEqual(result["response_policy"], "per_response")
        self.assertEqual(validate_links(self.output), [])


def numeric_fixture():
    payload = {"schema_version": "1.0", "corpus_revision": "0" * 64, "purpose": "estimate", "currency": "BRL",
               "rounding": "per_item", "legal_parameters_reason": "Exercício sintético sem taxa legal real.",
               "inputs": [{"id": "SAL", "value": "2200.00", "unit": "money", "fact_ids": ["F1"], "norm_ids": [], "reason": "Relato sintético."},
                          {"id": "RATE", "value": "1.50", "unit": "factor", "fact_ids": [], "norm_ids": ["N1"], "reason": "Critério fictício."}],
               "items": [{"id": "C1", "relationship_id": "REL1", "competence": "2026-06", "claim_type": "fixture", "segment": "integral",
                          "kind": "principal", "expression": "sal * rate", "bindings": {"sal": "SAL", "rate": "RATE"}, "norm_ids": ["N1"],
                          "request_ids": ["R1"], "expected_result": "3300.00", "include_in_total": True, "reason": "Conta de teste."}]}
    base = {"role": "synthetic", "source_value": "2200.00", "transform": "identity", "fact_id": "F1", "fact_field": "amount",
            "norm_id": None, "source_record_id": None, "quote": "", "expression": None, "bindings": {}, "period_id": "PER1",
            "effective_from": "2026-06-01", "effective_until": "2026-06-30", "applicability_analysis": "Somente fixture."}
    checks = {"schema_version": "1.0", "inputs": [
        dict(base, input_id="SAL", basis="fact"),
        dict(base, input_id="RATE", basis="legal_rule", source_value="50", transform="percent_to_factor", fact_id=None,
             fact_field=None, norm_id="N1", source_record_id="a" * 64, quote="Critério sintético 50%, sem regra real.")] }
    review = {"corpus_revision": "0" * 64, "facts": [{"id": "F1"}], "norms": [{"id": "N1"}], "requests": [{"id": "R1"}],
              "assertion_reviews": [{"fact_id": "F1", "atoms": {"amount": "2200.00"}}],
              "normative_map": [{"norm_id": "N1", "temporal_status": "applicable", "effective_from": "2020-01-01", "effective_until": None}],
              "labor_review": {"contract_periods": [{"id": "PER1", "relationship_id": "REL1"}]}}
    citations = [{"norm_id": "N1", "source_record_id": "a" * 64}]
    texts = {"a" * 64: "Critério sintético 50%, sem regra real."}
    return payload, checks, review, citations, texts


class NumericCriteria(unittest.TestCase):
    def test_requested_calculation_preserves_dependencies_without_other_claims(self):
        payload, checks, review, cites, texts = numeric_fixture()
        unrelated = dict(payload["items"][0], id="OTHER", request_ids=["R_OTHER"], claim_type="unrelated",
                         bindings={"sal": "OTHER_SAL", "rate": "OTHER_RATE"})
        payload["items"].append(unrelated)
        payload["inputs"] += [dict(payload["inputs"][0], id="OTHER_SAL"), dict(payload["inputs"][1], id="OTHER_RATE")]
        selected = select_calculations(payload, {"R1"}, checks)
        self.assertEqual({r["id"] for r in selected["items"]}, {"C1"})
        self.assertEqual({r["id"] for r in selected["inputs"]}, {"SAL", "RATE"})
        self.assertFalse(review_parameters(selected, checks, review, cites, texts)["errors"])
        dependent = dict(payload["items"][0], id="REFLEX", request_ids=["R2"], claim_type="reflex",
                         expression="base", bindings={"base": "C1"})
        payload["items"].append(dependent)
        selected = select_calculations(payload, {"R2"}, checks)
        self.assertEqual({r["id"] for r in selected["items"]}, {"C1", "REFLEX"})
        self.assertFalse(next(r for r in selected["items"] if r["id"] == "C1")["include_in_total"])
        self.assertEqual(review_parameters(selected, checks, dict(review, requests=review["requests"] + [{"id": "R2"}]), cites, texts)["total"], "3300.00")

    def test_recorded_origin_transform_and_actual_calculation(self):
        result = review_parameters(*numeric_fixture())
        self.assertFalse(result["errors"], result)
        self.assertEqual(result["arithmetic_status"], "executed")
        self.assertEqual(result["total"], "3300.00")

    def test_unquoted_rate_wrong_value_and_wrong_legal_period_rejected(self):
        for variant in ("quote", "value", "period", "fact", "coverage"):
            payload, checks, review, cites, texts = numeric_fixture()
            if variant == "quote":
                checks["inputs"][1]["source_value"] = "75"
            elif variant == "value":
                payload["inputs"][0]["value"] = "2300.00"
            elif variant == "period":
                review["normative_map"][0]["effective_from"] = "2026-07-01"
            elif variant == "fact":
                review["assertion_reviews"][0]["atoms"]["amount"] = "2000.00"
            else:
                checks["inputs"].pop()
            with self.subTest(variant=variant):
                self.assertTrue(review_parameters(payload, checks, review, cites, texts)["errors"])

    def test_mutually_derived_numbers_without_original_source_are_rejected(self):
        payload, checks, review, cites, texts = numeric_fixture()
        for i, other in ((0, "RATE"), (1, "SAL")):
            checks["inputs"][i].update(basis="derived", expression="x", bindings={"x": other})
        self.assertTrue(any("circular" in e for e in review_parameters(payload, checks, review, cites, texts)["errors"]))

    def test_brazilian_numeric_excerpt_keeps_thousand_separator_semantics(self):
        values = numbers_in_excerpt("Parâmetro fictício: 1.000,00; percentual fictício 50%; limite 2.000.")
        from decimal import Decimal
        self.assertTrue({Decimal("1000.00"), Decimal("50"), Decimal("2000")} <= values)


if __name__ == "__main__":
    unittest.main()
