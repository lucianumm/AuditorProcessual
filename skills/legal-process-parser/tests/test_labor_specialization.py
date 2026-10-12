"""Synthetic adverse labor records; technical checks do not evaluate legal merit."""
from __future__ import annotations

import copy
import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CORE))

from scripts.contracts import validate_contract
from scripts.labor_analysis import pending_labor, validate_labor, labor_findings, topics_catalog
from scripts.labor_calculations import compute_calculations, compare_reference, store_calculation
from scripts.labor_time import working_day, count_deadline
from scripts.task_context import resolve_context
from scripts.procedural_catalog import candidates, validate_catalog_selection
from scripts.case_graph import build_case_graph, affected_elements
from scripts.ingest_document import run_ingest
from scripts.legal_review import finalize
from scripts.case_memory import atomic_json
from scripts.source_records import official_url
from scripts.validate_links import validate_links
from tests.test_precision_v4 import v4_fixture


def labor_fixture(review):
    review["strategy"].update(domain="trabalhista",regime="clt",subdomain="pagamento_sintetico")
    labor = pending_labor(review["corpus_revision"],["pay"])
    labor["scope"]["contextual_limitations"] = []
    labor["relationships"] = [{"id":"REL1","worker":"Parte do cenário","employers":["EMP1"],"regime":"clt",
                              "category":"teste","territory":"BR/SP/3550308","status":"asserted",
                              "fact_ids":["F1"],"norm_ids":["N1"],"reason":"Relação do cenário fictício; não enquadramento real."}]
    labor["contract_periods"] = [{"id":"PER1","relationship_id":"REL1","start":None,"end":None,
                                 "status":"limited","job":"cenário","fact_ids":["F1"],"norm_ids":["N1"],
                                 "law_version_analysis":"Somente o pagamento do cenário é examinado.","missing_information":["Datas contratuais fora do pedido."]}]
    labor["topic_assessments"] = [{"id":"LQ1","issue_id":"I1","topic_id":"pay","period_ids":["PER1"],"fact_ids":["F1"],
        "norm_ids":["N1"],"request_ids":[],"status":"applicable",
        "checks":[{"check_id":key,"status":"supported","fact_ids":["F1"],"norm_ids":["N1"],"reason":"Fonte literal do cenário restrito."}
                  for key in topics_catalog()["pay"]["checks"]],
        "burden":{"holder":"not_applicable","norm_ids":[],"decision_fact_ids":[],"reason":"Registro de teste, sem litígio real."},
        "collective_checks":[],"research_reason":"Autoridade fictícia apenas para testar vínculos.",
        "strongest_objection":"Pagamento pode ter alcance restrito.","response":"Limitar a conclusão ao registro.",
        "selection_reason":"Entrega pontual sobre conteúdo literal.","gaps":[]}]
    review["labor_review"] = labor
    return labor


def calculation_fixture():
    return json.loads((CORE / "templates/labor_calculation_example.json").read_text(encoding="utf-8"))


class LaborCalculations(unittest.TestCase):
    def test_decimal_formula_reflex_and_single_payment(self):
        result = compute_calculations(calculation_fixture())
        self.assertEqual(result["total"],"140.00")
        self.assertEqual(result["items"][1]["depends_on"],["HE1"])
        self.assertEqual(result["legal_parameters_status"],"host_authored_requires_legal_review")

    def test_wrong_amount_and_incompatible_units(self):
        data = calculation_fixture()
        data["items"][0]["expected_result"] = "180.00"
        with self.assertRaisesRegex(ValueError,"diverge"):
            compute_calculations(data)
        data = calculation_fixture()
        data["items"][0].update(expression="sal + horas",bindings={"sal":"SAL","horas":"H"})
        with self.assertRaisesRegex(ValueError,"unidades"):
            compute_calculations(data)

    def test_code_hidden_factor_and_zero_divisor_are_rejected(self):
        for expression in ("__import__('os').system('whoami')","sal ** 2","sal * 1.5","sal[0]","abs(sal)"):
            data = calculation_fixture()
            data["items"][0].update(expression=expression,bindings={"sal":"SAL"})
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                compute_calculations(data)
        data = calculation_fixture()
        data["inputs"][1]["value"] = "0"
        with self.assertRaisesRegex(ValueError,"zero"):
            compute_calculations(data)

    def test_duplicate_payment_and_parcel_are_rejected(self):
        data = calculation_fixture()
        duplicate = copy.deepcopy(data["items"][-1])
        duplicate.update(id="AB2",segment="outro")
        data["items"].append(duplicate)
        with self.assertRaisesRegex(ValueError,"Pagamento abatido"):
            compute_calculations(data)
        data = calculation_fixture()
        duplicate = copy.deepcopy(data["items"][0])
        duplicate["id"] = "HE2"
        data["items"].append(duplicate)
        with self.assertRaisesRegex(ValueError,"Parcela repetida"):
            compute_calculations(data)

    def test_cycle_and_subtotal_double_count_are_rejected(self):
        data = calculation_fixture()
        data["items"][0].update(expression="base",bindings={"base":"REF1"})
        with self.assertRaisesRegex(ValueError,"circular"):
            compute_calculations(data)
        data = calculation_fixture()
        data["items"][0]["kind"] = "subtotal"
        with self.assertRaises(ValueError):
            compute_calculations(data)

    def test_rounding_policy_changes_only_recorded_total(self):
        data = calculation_fixture()
        data["inputs"] = [dict(id="SAL",value="0.10",unit="money",fact_ids=["F1"],norm_ids=[],reason="Fictício"),
                          dict(id="DIV",value="3",unit="factor",fact_ids=[],norm_ids=["N1"],reason="Fictício")]
        data["items"] = []
        for number in (1,2):
            data["items"].append(dict(id=f"C{number}",relationship_id="REL1",competence="2026-01",
                claim_type=f"exemplo{number}",segment="integral",kind="principal",expression="sal / div",
                bindings={"sal":"SAL","div":"DIV"},norm_ids=["N1"],request_ids=[],expected_result="0.03",
                include_in_total=True,reason="Divisão sintética"))
        self.assertEqual(compute_calculations(data)["total"],"0.06")
        data["rounding"] = "final_only"
        self.assertEqual(compute_calculations(data)["total"],"0.07")

    def test_reference_is_bound_to_input_and_compares_all_items(self):
        result = compute_calculations(calculation_fixture())
        reference = {"input_revision":result["input_revision"],"source_file_sha256":"f" * 64,
                     "tool":"synthetic-reference-not-real-PJe","tool_version":"fixture","table_revision":"fixture",
                     "reviewer":"fixture","items":[{"id":x["id"],"result":x["result"]} for x in result["items"]]}
        self.assertEqual(compare_reference(result,reference)["status"],"matched")
        reference["items"][0]["result"] = "151.00"
        self.assertEqual(compare_reference(result,reference)["status"],"divergent")
        reference["input_revision"] = "0" * 64
        with self.assertRaisesRegex(ValueError,"outros parâmetros"):
            compare_reference(result,reference)

    def test_external_reference_bytes_are_actually_checked(self):
        result = compute_calculations(calculation_fixture())
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "referencia.txt"
            source.write_bytes(b"Synthetic external result, not PJe-Calc execution")
            reference = dict(input_revision=result["input_revision"],source_file_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                             tool="fixture",tool_version="fixture",table_revision="fixture",reviewer="fixture",
                             items=[dict(id=x["id"],result=x["result"]) for x in result["items"]])
            self.assertEqual(compare_reference(result,reference,source)["source_integrity_status"],"verified_bytes")
            source.write_bytes(b"Changed reference")
            with self.assertRaisesRegex(ValueError,"hash registrado"):
                compare_reference(result,reference,source)

    def test_calculation_updates_preserve_original_results_and_parameters(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            store_calculation(output,compute_calculations(calculation_fixture()))
            previous = (output / "calculo_trabalhista.json").read_bytes()
            data = calculation_fixture()
            data["inputs"][2]["value"] = "20"
            data["items"][0]["expected_result"] = "300.00"
            data["items"][1]["expected_result"] = "60.00"
            preserved = store_calculation(output,compute_calculations(data))
            old = output / ("calculation_history/" + hashlib.sha256(previous).hexdigest() + "/calculo_trabalhista.json")
            self.assertEqual(old.read_bytes(),previous)
            self.assertIn(old.relative_to(output).as_posix(),preserved)
            current = json.loads((output / "calculo_trabalhista.json").read_text(encoding="utf-8"))
            self.assertEqual(current["total"],"320.00")
            self.assertEqual(current["inputs"][2]["value"],"20")
            self.assertIn("F-HORAS",current["items"][1]["source_fact_ids"])

    def test_monthly_scope_and_source_ids(self):
        data = calculation_fixture()
        data["items"][0].update(period_start="2025-12-31",period_end="2026-01-31")
        with self.assertRaisesRegex(ValueError,"competência"):
            compute_calculations(data)
        with self.assertRaisesRegex(ValueError,"fonte"):
            compute_calculations(calculation_fixture(),facts={},norms={})


class LaborTime(unittest.TestCase):
    def test_overnight_clock_with_break(self):
        record = dict(clock_in="2026-01-01T22:00:00-03:00",clock_out="2026-01-02T06:00:00-03:00",
                      break_minutes=60,fact_ids=["F1"],expected_minutes="420")
        self.assertEqual(Decimal(working_day(record)["worked_hours"]),Decimal(7))
        record["clock_out"] = "2026-01-01T06:00:00-03:00"
        with self.assertRaises(ValueError):
            working_day(record)

    def test_explicit_offsets_preserve_actual_duration(self):
        record = dict(clock_in="2018-11-03T23:00:00-03:00",clock_out="2018-11-04T03:00:00-02:00",
                      break_minutes=0,fact_ids=["F1"],expected_minutes="180")
        self.assertEqual(Decimal(working_day(record)["worked_hours"]),Decimal(3))
        record["clock_in"] = "2018-11-03T23:00:00"
        with self.assertRaisesRegex(ValueError,"offset"):
            working_day(record)

    def test_calendar_requires_scope_and_handles_holiday_suspension(self):
        record = dict(event_date="2026-10-09",days=3,include_event_day=False,mode="business",
                      trigger_fact_id="F1",norm_id="N1",jurisdiction="TRT sintético",calendar_norm_ids=["N2"],
                      holidays=["2026-10-12"],suspensions=[],expected_due_date="2026-10-15")
        result = count_deadline(record)
        self.assertEqual(result["counted_days"],["2026-10-13","2026-10-14","2026-10-15"])
        record["calendar_norm_ids"] = []
        with self.assertRaisesRegex(ValueError,"calendário"):
            count_deadline(record)
        record.update(calendar_norm_ids=["N2"],suspensions=[dict(start="2026-10-13",end="2026-10-14",norm_id="N3")],
                      expected_due_date="2026-10-19")
        self.assertEqual(count_deadline(record)["due_date"],"2026-10-19")


class LaborReview(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / "fonte.txt"
        source.write_text("O pagamento foi realizado.",encoding="utf-8")
        self.output = self.root / "saida"
        run_ingest(source,self.output,task="analyze")
        self.review,self.memory = v4_fixture(self.output)
        self.labor = labor_fixture(self.review)

    def test_contract_and_full_finalization_with_navigable_report(self):
        self.assertEqual(validate_contract(self.review,"legal_review.schema.json"),[])
        self.assertEqual(validate_labor(self.review),[])
        path = self.root / "review.json"
        atomic_json(path,self.review)
        report = finalize(self.output,path)
        self.assertEqual(report["technical_status"],"passed",report["errors"])
        self.assertFalse(report["can_issue_final_legal_conclusion"])
        self.assertTrue((self.output / "analise_trabalhista.md").is_file())
        self.assertEqual(validate_links(self.output),[])

    def test_labor_records_required_only_for_v4_labor(self):
        self.review.pop("labor_review")
        self.assertTrue(validate_labor(self.review))
        self.review["strategy"]["domain"] = "civil"
        self.assertEqual(validate_labor(self.review),[])

    def test_wrong_request_and_dynamic_burden_without_decision(self):
        self.review["requests"] = [{"id":"R1","issue_ids":["OTHER"]}]
        self.labor["topic_assessments"][0]["request_ids"] = ["R1"]
        self.assertTrue(any("outra questão" in e for e in validate_labor(self.review)))
        self.labor["topic_assessments"][0]["burden"]["holder"] = "dynamic"
        self.assertTrue(any("distribuição dinâmica" in e for e in validate_labor(self.review)))

    def test_integral_coverage_and_pending_are_issue_scoped(self):
        self.labor["scope"]["mode"] = "integral"
        self.assertTrue(any("cada tema" in e for e in validate_labor(self.review)))
        self.labor["scope"]["excluded_topics"] = [{"topic_id":key,"reason":"Fora do cenário"}
                                                 for key in topics_catalog() if key != "pay"]
        self.assertEqual(validate_labor(self.review),[])
        self.labor["topic_assessments"][0]["checks"][0]["status"] = "pending"
        findings = labor_findings(self.review)
        self.assertTrue(findings)
        self.assertTrue(all(x["scope"] == "issue" and x["target_ids"] == ["I1"] for x in findings))
        self.assertFalse(any(x["delivery_effect"] == "blocks_delivery" for x in findings))

    def test_wrong_source_and_unproven_evidence_are_rejected(self):
        evidence = dict(id="EV1",topic_assessment_id="LQ1",relationship_id="REL1",period_ids=["PER1"],
                        document_type="payslip",sources=[dict(fact_id="F1",source_index=3)],
                        status="confirmed",reason="Exemplo")
        self.labor["evidence_checks"] = [evidence]
        self.assertTrue(any("fonte documental" in e for e in validate_labor(self.review)))
        evidence["sources"][0]["source_index"] = 0
        self.review["assertion_reviews"][0]["evidence_status"] = "unproven"
        self.assertTrue(any("prova confirmada" in e for e in validate_labor(self.review)))

    def test_collective_scope_and_expired_period_are_rejected(self):
        period = self.labor["contract_periods"][0]
        period.update(start="2026-01-01",end="2026-01-31")
        norm = self.review["norms"][0]
        norm["kind"] = "collective_instrument"
        self.labor["collective_instruments"] = [dict(id="CCT1",norm_id="N1",instrument_type="CCT",
            registration_reference="Registro fictício",category_scope=["teste"],territory_scope=["BR/SP"],
            employer_scope=[],effective_from="2026-01-01",effective_until="2026-12-31",
            clauses=[dict(id="C1",provision="Cláusula fictícia",quote=norm["official_text"],reason="Teste")])]
        self.labor["topic_assessments"][0]["collective_checks"] = [dict(instrument_id="CCT1",clause_ids=["C1"],
                                                                     fit="applicable",reason="Cenário")]
        self.assertEqual(validate_labor(self.review),[])
        self.labor["collective_instruments"][0]["category_scope"] = ["outra"]
        self.assertTrue(any("categoria/território" in e for e in validate_labor(self.review)))
        self.labor["collective_instruments"][0]["category_scope"] = ["teste"]
        period["end"] = "2027-01-01"
        self.assertTrue(any("fora do período" in e for e in validate_labor(self.review)))

    def test_collective_clause_must_exist_in_observed_text(self):
        self.test_collective_scope_and_expired_period_are_rejected()
        self.labor["collective_instruments"][0]["clauses"][0]["quote"] = "Cláusula inventada"
        self.assertTrue(any("ausente do texto" in e for e in validate_labor(self.review)))

    def test_health_elements_are_separate_and_need_their_sources(self):
        self.labor["scope"]["topic_ids"] = ["occupational_health"]
        topic = self.labor["topic_assessments"][0]
        topic["topic_id"] = "occupational_health"
        topic["checks"] = [dict(check_id=key,status="supported",fact_ids=["F1"],norm_ids=["N1"],reason="Fictício")
                           for key in topics_catalog()["occupational_health"]["checks"]]
        self.assertTrue(any("saúde ocupacional" in e for e in validate_labor(self.review)))
        limited = dict(status="pending",fact_ids=[],reason="Nexo não conferido")
        self.labor["health_assessments"] = [dict(id="H1",issue_ids=["I1"],relationship_id="REL1",period_ids=["PER1"],
            fact_ids=["F1"],norm_ids=["N1"],causation=copy.deepcopy(limited),concausation=copy.deepcopy(limited),
            incapacity=copy.deepcopy(limited),exposure=copy.deepcopy(limited),expertise_status="pending",
            technical_questions=["Conferir nexo do cenário"],consequences_reason="Conclusão limitada")]
        self.assertEqual(validate_labor(self.review),[])
        self.labor["health_assessments"][0]["causation"]["status"] = "supported"
        self.assertTrue(any("sem prova" in e for e in validate_labor(self.review)))

    def test_graph_propagates_sources_to_labor_periods_and_topics(self):
        impact = affected_elements(build_case_graph(self.review),["x:1"],changed_norms=["N1"])
        self.assertIn("contract_periods:PER1",impact["labor_ids"])
        self.assertIn("topic_assessments:LQ1",impact["labor_ids"])
        self.assertIn("I1",impact["issue_ids"])

    def test_independent_labor_issue_is_delivered_when_another_is_pending(self):
        second = copy.deepcopy(self.review["issues"][0])
        second.update(id="I2",question="Questão independente do cenário")
        self.review["issues"].append(second)
        self.review["assertion_reviews"][0]["issue_ids"].append("I2")
        self.review["normative_map"][0]["issue_ids"].append("I2")
        application = copy.deepcopy(self.review["norm_applications"][0])
        application.update(id="A2",issue_id="I2")
        self.review["norm_applications"].append(application)
        thesis = copy.deepcopy(self.review["theses"][0])
        thesis.update(id="T2",issue_id="I2",norm_application_ids=["A2"])
        self.review["theses"].append(thesis)
        thesis_review = copy.deepcopy(self.review["thesis_reviews"][0])
        thesis_review["thesis_id"] = "T2"
        self.review["thesis_reviews"].append(thesis_review)
        paragraph = copy.deepcopy(self.review["paragraphs"][0])
        paragraph.update(id="P2",issue_ids=["I2"])
        self.review["paragraphs"].append(paragraph)
        topic = copy.deepcopy(self.labor["topic_assessments"][0])
        topic.update(id="LQ2",issue_id="I2")
        self.labor["topic_assessments"].append(topic)
        self.labor["topic_assessments"][0]["status"] = "pending"
        path = self.root / "partial.json"
        atomic_json(path,self.review)
        report = finalize(self.output,path)
        self.assertEqual(report["technical_status"],"passed",report["errors"])
        states = {item["id"]:item["analysis_status"] for item in report["issue_statuses"]}
        self.assertEqual(states["I2"],"concluded")
        self.assertEqual(report["execution_status"],"partial")
        self.assertTrue((self.output / "analise_juridica.md").is_file())

    def test_international_instrument_requires_real_ratification_records(self):
        self.review["norms"][0]["kind"] = "international_instrument"
        self.assertTrue(any("ratificação" in x for x in validate_labor(self.review)))
        self.labor["international_checks"] = [dict(id="INT1",norm_id="N1",country="BR",ratification_status="not_ratified",
            effective_from=None,effective_until=None,domestic_norm_ids=[],status_norm_ids=["N1"],reason="Convenção fictícia sem ratificação")]
        errors = validate_labor(self.review)
        self.assertTrue(any("tese consolidada" in x for x in errors))
        self.assertTrue(any("aplicação direta" in x for x in errors))

    def test_established_period_must_match_rechecked_atomic_dates(self):
        self.labor["contract_periods"][0].update(status="established",start="2026-01-01",end="2026-01-31")
        self.assertTrue(any("marco contratual" in x for x in validate_labor(self.review)))

    def test_calculation_cannot_borrow_another_relationships_sources(self):
        data = calculation_fixture()
        data["corpus_revision"] = self.review["corpus_revision"]
        for parameter in data["inputs"]:
            parameter["norm_ids"] = ["N1"] if parameter["norm_ids"] else []
            parameter["fact_ids"] = ["F1"] if parameter["fact_ids"] else []
        data["inputs"][0]["fact_ids"] = ["F2"]
        for item in data["items"]:
            item["norm_ids"],item["request_ids"] = ["N1"],[]
            if item.get("payment_fact_ids"):
                item["payment_fact_ids"] = ["F1"]
        self.review["facts"].append(dict(id="F2",sources=[]))
        self.labor["calculation_scope"]["status"] = "calculated"
        self.labor["calculation_set"] = data
        self.assertTrue(any("fora da relação" in x for x in validate_labor(self.review)))

    def test_labor_calculation_is_emitted_and_liquidation_needs_title(self):
        data = calculation_fixture()
        data["corpus_revision"] = self.review["corpus_revision"]
        for parameter in data["inputs"]:
            parameter["norm_ids"] = ["N1"] if parameter["norm_ids"] else []
            parameter["fact_ids"] = ["F1"] if parameter["fact_ids"] else []
        for item in data["items"]:
            item["norm_ids"],item["request_ids"] = ["N1"],[]
            if item.get("payment_fact_ids"):
                item["payment_fact_ids"] = ["F1"]
        self.labor["calculation_scope"]["status"] = "calculated"
        self.labor["calculation_set"] = data
        path = self.root / "calculation-review.json"
        atomic_json(path,self.review)
        report = finalize(self.output,path)
        self.assertEqual(report["technical_status"],"passed",report["errors"])
        calculation = json.loads((self.output / "calculo_trabalhista.json").read_text(encoding="utf-8"))
        self.assertEqual(calculation["total"],"140.00")
        self.assertEqual(validate_links(self.output),[])
        data["purpose"] = "liquidation"
        self.assertTrue(any("título" in x for x in validate_labor(self.review)))

    def test_wrong_domain_catalog_and_missing_phase_rationale(self):
        self.review["piece_assessment"].update(status="selected",catalog_id="apelacao_civel",selected_piece="Apelação")
        self.assertTrue(any("incompatível" in x for x in validate_catalog_selection(self.review)))
        self.review["piece_assessment"]["catalog_id"] = "recurso_revista_trabalhista"
        self.assertTrue(any("Fase" in x for x in validate_catalog_selection(self.review)))

    def test_source_hosts_and_selective_routing(self):
        self.assertTrue(official_url("https://normlex.ilo.org/dyn/nrmlx_en/"))
        self.assertFalse(official_url("https://normlex.ilo.org.evil.example/"))
        self.assertFalse(official_url("https://other.ilo.org/"))
        context = resolve_context("gemini_gem","analyze",domain="trabalhista",labor_topics=["working_time"])
        paths = [x["path"] for x in context["references"]]
        self.assertTrue(any("labor_evidence_rules" in x for x in paths))
        self.assertFalse(any("labor_health_rules" in x or "labor_review.schema" in x or "chatgpt" in x for x in paths))
        self.assertFalse(any("labor_" in x["path"] for x in resolve_context("generic","ingest")["references"]))
        with self.assertRaises(ValueError):
            resolve_context("generic","analyze",labor_topics=["invented"])

    def test_recurso_revista_and_execution_candidates(self):
        found = candidates("trabalhista","acordao","recurso")
        self.assertIn("recurso_revista_trabalhista",{x["id"] for x in found["candidates"]})
        self.assertNotIn("recurso_especial",{x["id"] for x in found["candidates"]})
        found = candidates("trabalhista","execucao")
        self.assertIn("embargos_execucao_trabalhista",{x["id"] for x in found["candidates"]})
        self.assertIn("incidente_desconsideracao_trabalhista",{x["id"] for x in found["candidates"]})


if __name__ == "__main__":
    unittest.main()
