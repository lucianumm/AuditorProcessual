"""Observable synthetic scenarios; no provider, expert or real PJe execution."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.case_memory import atomic_json, update_memory
from scripts.case_packet import reading_packet
from scripts.client_intake import receive_accounts, load_accounts, account_packet
from scripts.case_search import search_client_records
from scripts.ingest_document import run_ingest
from scripts.labor_analysis import labor_findings, topics_catalog, validate_labor
from scripts.labor_catalog import claim_catalog
from scripts.labor_ledger import apportion_workdays
from scripts.labor_time import count_date_window
from scripts.labor_workflow import pending_workflow, validate_workflow
from scripts.legal_review import finalize, PIECE_SECTIONS
from scripts.research_memory import register_source_record, research_revision
from scripts.task_context import resolve_context
from scripts.validate_links import validate_links
from tests.test_labor_specialization import labor_fixture
from tests.test_precision_v4 import v4_fixture

SUITE = json.loads((CORE.parents[1] / "evaluation/labor_workflow_cases.json").read_text(encoding="utf-8"))


def synthetic_case(root, *, documents=0, claim_id="salary_differences", text="Pessoa sintética trabalhou para EMP1.", sector=None,
                   document_text=None):
    output = root / "case"
    account = text + " Em cenário sintético, a prestação ocorreu de 2026-06-01 a 2026-08-31; salário narrado 2200.00."
    receive_accounts(output, {"schema_version":"1.0", "entries":[{"id":"C1", "text":account, "conversation_reference":"synthetic-conversation-only"}]})
    if documents:
        source = root / "documento.txt"
        source.write_text(document_text or "REGISTRO INTEIRAMENTE SINTÉTICO. A decisão de teste contém dois fundamentos distintos. Este texto não é auto real.", encoding="utf-8")
        run_ingest(source, output, task="analyze")
    # Reuse a byte-integrity fixture only to exercise source plumbing.
    source = root / "authority_fixture.txt"
    source.write_text("O pagamento foi realizado.", encoding="utf-8")
    authority = root / "authority"
    run_ingest(source, authority, task="analyze")
    review, _ = v4_fixture(authority)
    for path in (authority / "research_sources").iterdir():
        target = output / "research_sources" / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    norm_record = json.loads((output / "research_sources" / (review["norms"][0]["capture_id"] + ".json")).read_text(encoding="utf-8"))
    register_source_record(output, norm_record)
    memory = update_memory(output)
    review.update(corpus_revision=memory["corpus_revision"], research_revision=research_revision(output),
                  task="petition", piece_type="inicial", client_records=memory["client_records"],
                  reviewed_pages=[], page_reviews=[], reading_coverage=[])
    review["strategy"].update(represented_party="Parte do cenário", phase="preprocessual")
    review["facts"] = [{"id":"F1","text":account,"nature":"alegacao","origin":"client","client_record_id":"C1",
                       "evidence_needed":"Documentos do empregador, testemunhas ou perícia conforme a controvérsia.",
                       "support":{"assessment":"client_account","reason":"Relato sintético recebido.","reviewed_by":"test-fixture"}}]
    atoms = {"actor":"Parte do cenário","action":"trabalhar","object":"contrato sintético","polarity":"affirmed","scope":"relato específico",
             "date":"2026-06-01","period_start":"2026-06-01","period_end":"2026-08-31","amount":"2200.00","currency":"BRL"}
    review["assertion_reviews"] = [{"fact_id":"F1","issue_ids":["I1"],"atoms":atoms,"evidence_status":"client_account",
        "evidence":[],"critical_checks":[{"field":k,"source_index":None,"method":"client_record","result":"reported","basis":"Informação narrada, sem confirmação documental."}
                                        for k in ("date","period_start","period_end","amount")],
        "treatment":"Afirmar na voz da parte e produzir prova futura; não declarar documento inexistente."}]
    if documents:
        packet = reading_packet(output)
        review["reading_coverage"] = [{"page_id":p["page_id"],"content_revision":p["content_revision"],"layer":p["layer"],
            "intervals":[[p["start"],p["end"]]],"method":"local_receipt","receipt_ids":[packet["receipt_id"]]} for p in packet["segments"]]
        for document in memory["documents"]:
            for page in document["pages"]:
                pid = document["sha256"] + ":" + str(page["pdf_page"])
                review["reviewed_pages"].append(pid)
                review["page_reviews"].append({"page_id":pid,"content_revision":page["content_revision"],"relevance":"relevant",
                                               "findings":"Registro sintético integral de teste.","fact_ids":["F2"],"reviewed_by":"test-fixture"})
                review["facts"].append({"id":"F2","text":page["text"],"nature":"prova","origin":"document",
                    "sources":[{"source_sha256":document["sha256"],"pdf_page":page["pdf_page"],"document_id":page["document_id"],"quote":page["text"]}],
                    "support":{"assessment":"direct","reason":"Trecho literal apenas para teste.","reviewed_by":"test-fixture"}})
                doc_atoms = {k:atoms[k] for k in ("actor","action","object","polarity","scope")}
                review["assertion_reviews"].append({"fact_id":"F2","issue_ids":["I1"],"atoms":doc_atoms,"evidence_status":"supported",
                    "evidence":[{"source_index":0,"relation":"supports","source_atoms":doc_atoms,"context":"Fonte sintética de teste."}],
                    "critical_checks":[],"treatment":"Não extrapolar o registro."})
    fids = [f["id"] for f in review["facts"]]
    review["issues"][0].update(fact_ids=fids, analysis_status="qualified", request_ids=["R1"],
        question="Pretensão sintética com prova futura", conclusion="Minuta formulável; prova pendente por questão.",
        evidence_assessment="Relato específico preservado e prova futura planejada.")
    review["issues"][0]["requirements"][0].update(assessment="disputed", fact_ids=["F1"], treatment="Produzir prova conforme plano.")
    review["theses"][0].update(characterization="provisional", request_ids=["R1"])
    review["thesis_reviews"][0].update(evidential_strength="weak")
    review["thesis_reviews"][0]["requirement_checks"][0]["assessment"] = "disputed"
    review["normative_map"][0]["relevant_dates"] = [{"date":"2026-06-01","reason":"Marco narrado do cenário","fact_ids":["F1"]}]
    review["requests"] = [{"id":"R1","issue_ids":["I1"],"fact_ids":["F1"],"origin":"user",
                           "text":"Acolher o pedido sintético compatível com os fatos.","compatibility":"Cenário de fluxo, sem mérito real."}]
    review["paragraphs"] = [{"id":"P-"+section,"section":section,
        "text":"A parte prestou serviços para EMP1." if section == "fatos" else "Texto de teste sintético: " + section + ".",
        "fact_ids":["F1"],"norm_ids":["N1"],"issue_ids":["I1"],"request_ids":["R1"] if section == "pedidos" else []}
        for section in PIECE_SECTIONS["inicial"]]
    checks = ["competencia","legitimidade_interesse","rito","causa_pedir_pedidos","prescricao","valores","prova"]
    review["piece_assessment"].update(status="selected",process_stage="preprocessual",selected_piece="Reclamação trabalhista sintética",
        catalog_id="reclamacao_trabalhista",drafted_piece_type="inicial",
        admissibility_checks=[{"check_id":k,"requirement":k,"status":"satisfied","reason":"Somente teste de contrato, não verificação jurídica.",
                               "fact_ids":["F1"],"norm_ids":["N1"]} for k in checks])
    labor = labor_fixture(review)
    spec = claim_catalog()[claim_id]
    labor["scope"]["topic_ids"] = [spec["topic_id"]]
    topic = labor["topic_assessments"][0]
    topic.update(topic_id=spec["topic_id"],fact_ids=fids,request_ids=["R1"],status="pending",pending_cause="future_proof")
    topic["checks"] = [{"check_id":k,"status":"pending","fact_ids":["F1"],"norm_ids":["N1"],"reason":"Prova futura no cenário."}
                       for k in topics_catalog()[spec["topic_id"]]["checks"]]
    if spec["topic_id"] == "occupational_health":
        labor["health_assessments"] = [{"id":"H1","issue_ids":["I1"],"relationship_id":"REL1","period_ids":["PER1"],
            "fact_ids":["F1"],"norm_ids":["N1"],**{k:{"status":"pending","fact_ids":["F1"],"reason":"Requer prova técnica real."}
            for k in ("causation","concausation","incapacity","exposure")},"expertise_status":"pending",
            "technical_questions":["Qual a exposição e o nexo, conforme os dados disponíveis?"],"consequences_reason":"Não emitir diagnóstico."}]
    w = pending_workflow()
    w.update(analysis_date="2026-10-12",document_availability="limited" if documents else "none",client_record_ids=["C1"])
    w["proof_plan"] = [{"id":"PROOF1","issue_id":"I1","fact_ids":["F1"],"norm_ids":["N1"],"holder":"employer",
        "method":"locate","stage":"instrucao","criticality":"future_proof","status":"planned","description":"Obter prova da controvérsia.",
        "alternatives":"Testemunhas ou fonte disponível pertinente.","reason":"Dados narrados, prova futura delimitada."}]
    w["claim_reviews"] = [{"id":"CLAIM1","issue_id":"I1","topic_assessment_id":"LQ1","claim_id":claim_id,
        "fact_ids":["F1"],"norm_ids":["N1"],"period_ids":["PER1"],"requirements":[
            {"requirement_id":k,"status":"alleged","fact_ids":["F1"],"norm_ids":["N1"],"proof_plan_ids":["PROOF1"],
             "reason":"Pauta sintética com relato atribuído."} for k in spec["requirements"]],
        "drafting_basis":"sufficient","merit_status":"awaiting_proof","proof_plan_ids":["PROOF1"],
        "requested_effect":"Formular o pedido sintético.","strongest_objection":"Prova ainda não produzida.",
        "response":"Providência específica de prova.","reason":"Informação para redação distinta de confirmação probatória."}]
    if sector:
        w["sector_selections"] = [{"id":"SECTOR1","sector_id":sector,"fact_ids":["F1"],"regime_analysis":"Roteiro do cenário sintético.",
                                  "reason":"Seleção de guia, não confirmação de regime."}]
    labor["workflow"] = w
    return output, review, memory


def ledger_fixture():
    return {"schema_version":"1.0","rules":[{"id":"RULE1","relationship_id":"REL1","period_start":"2026-06-01","period_end":"2026-06-30",
        "norm_ids":["N1"],"daily_limit_minutes":"480","weekly_limit_minutes":"2400","week_start":0,"limit_basis":"physical",
        "night_window":None,"night_reduction":False,"reason":"PARÂMETROS SINTÉTICOS, NÃO REGRA LEGAL UNIVERSAL."}],
        "days":[{"id":"DAY1","relationship_id":"REL1","date":"2026-06-01","day_status":"worked","origin":"client","fact_ids":["F1"],
                 "intervals":[{"start":"2026-06-01T09:00:00-03:00","end":"2026-06-01T17:00:00-03:00"}],"reason":"Marcações narradas."}],
        "payroll":[]}


class LaborScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output, cls.review, cls.memory = synthetic_case(Path(cls.temp.name), documents=1)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def execute_scenario(self, scenario):
        mode, variant, expected = scenario["mode"], scenario["variant"], scenario["expected"]
        if mode == "intake":
            with tempfile.TemporaryDirectory() as temporary:
                out = Path(temporary)
                receive_accounts(out, {"schema_version":"1.0","entries":[{"id":"C1","text":"Relato sintético.","conversation_reference":"fixture"}]})
                if variant == "empty_docs":
                    self.assertEqual(update_memory(out)["documents"], [])
                    self.assertTrue((out / "memoria_processual.md").is_file())
                else:
                    entry = {"id":"C1" if variant == "reused_id" else "C2","text":"Novo relato.","conversation_reference":"fixture"}
                    if variant in {"missing_predecessor","correction"}:
                        entry["supersedes"] = "missing" if variant == "missing_predecessor" else "C1"
                    if expected == "rejected":
                        with self.assertRaises(ValueError):
                            receive_accounts(out, {"schema_version":"1.0","entries":[entry]})
                    else:
                        receive_accounts(out, {"schema_version":"1.0","entries":[entry]})
                        self.assertEqual(len(load_accounts(out)), 2)
                        self.assertIn("Retifica", (out / "relato_cliente.md").read_text(encoding="utf-8"))
        elif mode == "workflow":
            r = copy.deepcopy(self.review); w = r["labor_review"]["workflow"]; c = w["claim_reviews"][0]
            if variant == "verified_account": c["requirements"][0]["status"] = "verified"
            elif variant == "missing_material": c["requirements"][0]["status"] = "missing_material"
            elif variant == "question":
                w["material_questions"] = [{"id":"Q1","claim_review_id":"CLAIM1","field":"period","question":"Qual período?",
                    "impact":"Impede delimitação.","status":"open","answer_fact_ids":[],"reason":"Dado material."}]
            elif variant == "omitted_requirement": c["requirements"].pop()
            elif variant == "foreign_proof": w["proof_plan"][0]["issue_id"] = "OTHER"
            elif variant == "proof_received": w["proof_plan"][0]["status"] = "received"
            elif variant == "exhibition": w["proof_plan"][0].update(method="exhibition",norm_ids=[])
            elif variant == "unknown_client": w["client_record_ids"] = ["invented"]
            elif variant == "document_status": w["document_availability"] = "none"
            elif variant in {"amount_agreement","actor_agreement"}:
                a = copy.deepcopy(r["assertion_reviews"][0]["atoms"])
                a["amount"] = "900.00" if variant == "amount_agreement" else "2200.00"
                if variant == "actor_agreement": a["actor"] = "Outra pessoa"
                r["assertion_reviews"][1]["atoms"] = a
                w["reconciliations"] = [{"id":"REC1","issue_id":"I1","relationship_id":"REL1","period_ids":["PER1"],
                    "atom":"amount","left_fact_id":"F1","right_fact_id":"F2","status":"agrees","reason":"Comparação de teste."}]
            elif variant == "temporal":
                r["labor_review"]["contract_periods"][0].update(start="2019-01-01",end="2019-12-31")
                w["temporal_checks"] = [{"id":"TIME1","issue_id":"I1","period_id":"PER1","norm_id":"N1","reviewed_until":None,
                                         "status":"applicable","reason":"Regra começa só em 2020."}]
            elif variant in {"authority_pending","authority_cancelled"}:
                w["authority_checks"] = [{"id":"AUTH1","issue_ids":["I1"],"norm_id":"N1","status_norm_ids":[],"checked_on":"2026-09-06",
                    "status":"pending" if variant == "authority_pending" else "cancelled",
                    "use":"merit_support" if variant == "authority_pending" else "historical",
                    "scope_analysis":"Situação sintética.","temporal_reason":"Fonte não fornecida."}]
            elif variant == "expert_answer":
                w["instruction_questions"] = [{"id":"EX1","issue_id":"I1","proof_plan_id":"PROOF1","method":"expert",
                    "question":"Qual a metodologia?","controversy":"Prova técnica.","status":"answered","answer_fact_ids":[],"reason":"Sem resposta recebida."}]
            elif variant == "unknown_sector":
                w["sector_selections"] = [{"id":"SEC1","sector_id":"invented","fact_ids":["F1"],"regime_analysis":"Teste.","reason":"Teste."}]
            elif variant == "exclusive_options":
                w["strategy_options"] = [{"id":"OPT1","thesis_id":"T1","exclusive_with":["OPT2"],"scenario_id":"SAME","selected":True,"reason":"Incompatível."},
                                          {"id":"OPT2","thesis_id":"T1","exclusive_with":["OPT1"],"scenario_id":"SAME","selected":True,"reason":"Incompatível."}]
            elif variant in {"appeal_response","appeal_quote"}:
                source = r["facts"][1]["sources"][0]["quote"]
                w["appeal_chapters"] = [{"id":"AP1","issue_id":"I1","act_fact_id":"F2",
                    "decision_excerpt":source if variant == "appeal_response" else "Decisão inventada",
                    "measure_catalog_id":"recurso_ordinario_trabalhista","grounds":[{"id":"G1","excerpt":source,
                    "response_paragraph_ids":[],"status":"challenged","norm_ids":["N1"],"reason":"Resposta ausente."}],
                    "requested_effect":"Reformar.","reason":"Teste de capítulo."}]
            errors = validate_workflow(r, self.memory)
            self.assertEqual(bool(errors), expected == "rejected", errors)
        elif mode == "window":
            window = {"anchor_date":"2024-02-29","unit":"years","quantity":1,"direction":"forward",
                      "leap_policy":"strict" if variant == "strict" else "last_valid_day","adjustments":[],
                      "expected_date":"2025-03-01" if variant == "wrong" else "2025-02-28"}
            if expected == "rejected":
                with self.assertRaises(ValueError): count_date_window(window)
            else: self.assertEqual(count_date_window(window)["date"], expected)
        elif mode == "routing":
            context = resolve_context("chatgpt","petition",labor_claims=["overtime"],labor_sectors=["banking"],labor_intake=True)
            paths = [r["path"] for r in context["references"]]
            self.assertTrue(any("labor_sectors/banking.md" in p for p in paths))
            self.assertFalse(any("labor_sectors/domestic.md" in p for p in paths))
            self.assertEqual(context["labor_sectors"][0]["id"], expected)
        else:
            payload = ledger_fixture(); day = payload["days"][0]; rule = payload["rules"][0]
            if variant == "overnight":
                day["intervals"] = [{"start":"2026-06-01T22:00:00-03:00","end":"2026-06-02T06:00:00-03:00"}]
            elif variant == "overlap": day["intervals"].append(copy.deepcopy(day["intervals"][0]))
            elif variant == "unknown": day.update(day_status="unknown",intervals=[])
            elif variant == "competing":
                other = copy.deepcopy(rule); other["id"] = "RULE2"; payload["rules"].append(other)
            elif variant in {"daily_weekly","weekly"}:
                payload["days"] = []
                for n in range(7):
                    d = date(2026,6,1) + timedelta(days=n)
                    hours = 9 if variant == "daily_weekly" and n < 5 else 8 if n < 5 else 5 if variant == "weekly" and n == 5 else 0
                    payload["days"].append({**day,"id":"DAY"+str(n),"date":d.isoformat(),"day_status":"worked" if hours else "rest",
                        "intervals":[{"start":d.isoformat()+"T09:00:00-03:00","end":d.isoformat()+f"T{9+hours:02d}:00:00-03:00"}] if hours else []})
            elif variant == "night":
                rule.update(night_window={"start":"22:00","end":"05:00","unit_minutes":"30"},night_reduction=True,limit_basis="legal")
                day["intervals"] = [{"start":"2026-06-01T22:00:00-03:00","end":"2026-06-02T00:00:00-03:00"}]
            elif variant in {"double_payment","confirmation","salary_conflict","missing_payment"}:
                row = {"id":"PAY1","relationship_id":"REL1","competence":"2026-06","rubric":"RUBRIC","kind":"due","payment_id":None,
                       "amount":"100","origin":"document","fact_ids":["F2"],"reason":"SINTÉTICO."}
                payload["payroll"] = [row]
                if variant in {"double_payment","confirmation"}:
                    payment = {**row,"id":"PAY2","kind":"payment","payment_id":"P1"}
                    payload["payroll"].append(payment)
                    payload["payroll"].append({**payment,"id":"PAY3","kind":"payment" if variant == "double_payment" else "payment_confirmation"})
                if variant == "salary_conflict":
                    payload["payroll"] = [{**row,"kind":"salary_parameter"},{**row,"id":"PAY2","kind":"salary_parameter","amount":"200"}]
            if expected == "rejected":
                with self.assertRaises(ValueError): apportion_workdays(payload)
            else:
                result = apportion_workdays(payload)
                value = result["days"][0]["physical_minutes"] if variant == "overnight" else result["days"][0]["legal_minutes"] if variant == "night" else (
                    result["weeks"][0]["total_excess_without_double_count"] if variant in {"daily_weekly","weekly"} else
                    result["payroll"][0]["payments_recorded"] if variant == "confirmation" else
                    result["payroll"][0]["salary_conflict"] if variant == "salary_conflict" else
                    result["payroll"][0]["difference_recorded"] if variant == "missing_payment" else result["status"])
                self.assertEqual(value, expected)


def scenario_method(scenario):
    return lambda self: self.execute_scenario(scenario)

for scenario in SUITE["scenarios"]:
    setattr(LaborScenarios, "test_" + scenario["id"], scenario_method(scenario))


class IntegralLaborCases(unittest.TestCase):
    def execute_case(self, case):
        with tempfile.TemporaryDirectory() as temporary:
            output, review, memory = synthetic_case(Path(temporary), documents=case["documents"], claim_id=case["claim"],
                                                   text=case["text"], sector=case["sector"])
            self.assertEqual(validate_labor(review, memory), [])
            path = Path(temporary) / "review.json"
            atomic_json(path, review)
            result = finalize(output, path)
            self.assertEqual(result["errors"], [], result)
            self.assertEqual(result["draft_status"], "ready_for_review", result)
            self.assertEqual(result["analysis_status"], "qualified")
            self.assertTrue((output / "minuta_peca.md").is_file())
            self.assertNotIn("MINUTA PARCIAL", (output / "minuta_peca.md").read_text(encoding="utf-8"))
            self.assertTrue((output / "desenvolvimento_trabalhista.md").is_file())
            self.assertTrue((output / "processo_completo.zip").is_file())
            self.assertEqual(validate_links(output), [])
            self.assertFalse(result["can_issue_final_legal_conclusion"])
            if not case["documents"]:
                self.assertEqual(memory["documents"], [])
                manifest = json.loads((output / "intake_manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["document_pages"], 0)


class LaborContinuity(unittest.TestCase):
    def test_common_appeal_is_allowed_but_initial_is_not_an_appeal(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, review, memory = synthetic_case(Path(temporary),documents=1)
            quote = review["facts"][1]["sources"][0]["quote"]
            row = {"id":"AP1","issue_id":"I1","act_fact_id":"F2","decision_excerpt":quote,
                   "measure_catalog_id":"embargos_declaracao","grounds":[{"id":"G1","excerpt":quote,
                   "response_paragraph_ids":["P-fundamentos"],"status":"challenged","norm_ids":["N1"],"reason":"Resposta ligada à questão."}],
                   "requested_effect":"Sanar vício indicado.","reason":"Catálogo comum compatível com trabalho."}
            review["labor_review"]["workflow"]["appeal_chapters"] = [row]
            self.assertEqual(validate_workflow(review,memory),[])
            row["measure_catalog_id"] = "reclamacao_trabalhista"
            self.assertTrue(any("instrumento incompatível" in e for e in validate_workflow(review,memory)))

    def test_equivalent_decimal_forms_do_not_create_false_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, review, memory = synthetic_case(Path(temporary),documents=1)
            atom = copy.deepcopy(review["assertion_reviews"][0]["atoms"])
            atom["amount"] = "2200.0"
            review["assertion_reviews"][1]["atoms"] = atom
            review["labor_review"]["workflow"]["reconciliations"] = [{"id":"REC1","issue_id":"I1","relationship_id":"REL1",
                "period_ids":["PER1"],"atom":"amount","left_fact_id":"F1","right_fact_id":"F2","status":"agrees",
                "reason":"Mesma quantia em representações decimais diferentes."}]
            self.assertEqual(validate_workflow(review,memory),[])

    def test_bounded_account_reading_keeps_every_character(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            texts = ["Texto sintético extenso. " * 1300, "Retificação sintética. " * 300]
            receive_accounts(output, {"schema_version":"1.0","entries":[
                {"id":"C1","text":texts[0],"conversation_reference":"fixture"},
                {"id":"C2","text":texts[1],"conversation_reference":"fixture","supersedes":"C1"}]})
            offset, rebuilt = 0, ""
            while True:
                packet = account_packet(output, offset=offset, max_chars=127)
                rebuilt += "".join(s["text"] for s in packet["segments"])
                self.assertLessEqual(sum(len(s["text"]) for s in packet["segments"]),127)
                if packet["next_offset"] is None:
                    break
                offset = packet["next_offset"]
            self.assertEqual(rebuilt, "".join(texts))
            self.assertEqual(search_client_records(output,"retificação")["records"][0]["id"],"C2")

    def test_account_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            receive_accounts(output, {"schema_version":"1.0","entries":[{"id":"C1","text":"Original.","conversation_reference":"fixture"}]})
            data = json.loads((output / "client_records.json").read_text(encoding="utf-8"))
            data["entries"][0]["text"] = "Alterado sem retificação."
            atomic_json(output / "client_records.json",data)
            with self.assertRaises(ValueError):
                load_accounts(output)

    def test_tampered_received_account_cannot_keep_approved_draft(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, review, _ = synthetic_case(root)
            path = root / "review.json"; atomic_json(path,review)
            self.assertEqual(finalize(output,path)["errors"],[])
            received = json.loads((output / "client_records.json").read_text(encoding="utf-8"))
            received["entries"][0]["text"] = "Conteúdo alterado sem versão."
            atomic_json(output / "client_records.json",received)
            result = finalize(output,path)
            self.assertEqual(result["draft_status"],"blocked")
            self.assertTrue(any("Relatos persistidos" in e for e in result["errors"]))

    def test_client_contradiction_preserves_origin_and_actual_document(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, review, _ = synthetic_case(root,documents=1,
                document_text="COMPROVANTE INTEIRAMENTE SINTÉTICO. O salário recebido de EMP1 foi 1800.00.")
            review["facts"][0]["sources"] = copy.deepcopy(review["facts"][1]["sources"])
            contrary_atoms = {"actor":"Parte do cenário","action":"receber","object":"salário","polarity":"affirmed",
                              "scope":"remuneração narrada","amount":"1800.00","currency":"BRL"}
            review["assertion_reviews"][1].update(atoms=contrary_atoms,critical_checks=[
                {"field":"amount","source_index":0,"method":"text_crosscheck","result":"confirmed",
                 "basis":"Número literal no comprovante sintético."}])
            review["assertion_reviews"][1]["evidence"][0]["source_atoms"] = contrary_atoms
            assertion = review["assertion_reviews"][0]
            assertion["atoms"].update(action="receber",object="salário",scope="remuneração narrada")
            assertion["evidence_status"] = "disputed"
            assertion["evidence"] = [{"source_index":0,"relation":"contradicts","source_atoms":contrary_atoms,
                                     "context":"Documento adverso recebido, sem apagar o relato."}]
            for check in review["labor_review"]["workflow"]["claim_reviews"][0]["requirements"]:
                check["status"] = "disputed"
            review["labor_review"]["workflow"]["claim_reviews"][0]["merit_status"] = "contested"
            path = root / "review.json"; atomic_json(path,review)
            self.assertEqual(finalize(output,path)["errors"],[])
            # A fictitious contrary quote is rejected even on a client-origin fact.
            review["facts"][0]["sources"][0]["quote"] = "Trecho adverso que não existe no arquivo."
            atomic_json(path,review)
            self.assertTrue(any("trecho não encontrado" in e for e in finalize(output,path)["errors"]))

    def test_retification_reopens_claim_and_preserves_draft(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, review, memory = synthetic_case(root)
            path = root / "review.json"; atomic_json(path,review)
            self.assertEqual(finalize(output,path)["errors"],[])
            original = (output / "minuta_peca.md").read_bytes()
            result = receive_accounts(output, {"schema_version":"1.0","entries":[{
                "id":"C2","text":"Retifico o período anteriormente narrado.","conversation_reference":"fixture-new","supersedes":"C1"}]})
            self.assertIn("I1",result["update"]["impacted_elements"]["issue_ids"])
            self.assertTrue(result["update"]["requires_legal_reassessment"])
            self.assertTrue((output / "minuta_peca.md").read_text(encoding="utf-8").startswith("> **ENTREGA ANTERIOR"))
            archives = list((output / "legal_reviews/superseded").glob("*/minuta_peca.md"))
            self.assertTrue(any(p.read_bytes() == original for p in archives))
            self.assertEqual(len(load_accounts(output)),2)

    def test_late_upload_keeps_account_and_all_documents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, _, before = synthetic_case(root)
            source = root / "novo.txt"
            source.write_text("COMPROVANTE SINTÉTICO NOVO.",encoding="utf-8")
            run_ingest(source,output,task="analyze")
            after = update_memory(output)
            self.assertEqual(len(after["client_records"]),1)
            self.assertEqual(len(after["documents"]),1)
            self.assertNotEqual(before["corpus_revision"],after["corpus_revision"])
            self.assertEqual(search_client_records(output,"salário")["total"],1)

    def test_completed_versions_remain_recoverable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, review, _ = synthetic_case(root)
            path = root / "review.json"; atomic_json(path,review)
            self.assertEqual(finalize(output,path)["errors"],[])
            previous = (output / "minuta_peca.md").read_bytes()
            review["paragraphs"][0]["text"] += " Revisão editorial sintética."
            atomic_json(path,review)
            self.assertEqual(finalize(output,path)["errors"],[])
            self.assertTrue(any(p.read_bytes() == previous for p in (output / "legal_reviews/history").glob("*/minuta_peca.md")))

for case in SUITE["integral_cases"]:
    setattr(IntegralLaborCases, "test_" + case["id"], lambda self, case=case: self.execute_case(case))


if __name__ == "__main__":
    unittest.main()
