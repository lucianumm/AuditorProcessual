"""Adversarial v4 contract tests. All facts/authorities are synthetic, not law."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))

from scripts.case_memory import atomic_json, page_revision
from scripts.case_packet import check_reading_coverage, reading_packet, layer_text
from scripts.contracts import validate_contract
from scripts.ingest_document import run_ingest
from scripts.legal_review import finalize, validate_review
from scripts.precision_validation import validate_precision
from scripts.research_memory import register_source_record, research_revision
from scripts.review_skeleton import skeleton
from scripts.procedural_catalog import candidates, validate_catalog_selection
from scripts.task_context import resolve_context
from scripts.validate_links import validate_links
from tests.test_release_integrity import fixture, v3_fixture


def v4_fixture(output: Path):
    old, memory = fixture(output)
    review = v3_fixture(old)
    review["schema_version"] = "4.0"
    review["strategy"].update(subdomain="pagamento_sintetico",regime="civil_sintetico")
    packet = reading_packet(output)
    source_id = review["norms"][0]["capture_id"]
    register_source_record(output,json.loads((output / "research_sources" / (source_id + ".json")).read_text(encoding="utf-8")))
    review["research_revision"] = research_revision(output)
    review["execution_context"] = {"platform":"synthetic-test","mode":"local","capabilities":{
        key:{"status":"not_tested"} for key in ("vision","browsing","code_execution","persistence")}}
    review["reading_coverage"] = [{"page_id":part["page_id"], "content_revision":part["content_revision"],
        "layer":part["layer"],"intervals":[[part["start"],part["end"]]],"method":"local_receipt","receipt_ids":[packet["receipt_id"]]}
        for part in packet["segments"]]
    atoms = {"actor":"Parte do cenário", "action":"pagar", "object":"obrigação sintética", "polarity":"affirmed", "scope":"pagamento registrado"}
    review["assertion_reviews"] = [{"fact_id":"F1","issue_ids":["I1"],"atoms":atoms,"evidence_status":"supported",
        "evidence":[{"source_index":0,"relation":"supports","source_atoms":dict(atoms),"context":"Única frase literal, não autenticação."}],
        "critical_checks":[],"treatment":"Conclusão limitada ao registro sintético."}]
    review["normative_map"] = [{"norm_id":"N1","issue_ids":["I1"],"full_context":"Regra sintética restrita",
        "requirements":["Pagamento"],"exceptions":[],"consequences":"Descrição do registro, não orientação jurídica",
        "effective_from":"2020-01-01","effective_until":None,"relevant_dates":[{"date":"2026-09-06","reason":"Marco sintético","fact_ids":["F1"]}],
        "transition_norm_ids":[],"temporal_status":"applicable","temporal_reason":"Vigência fictícia do cenário"}]
    review["precedent_comparisons"] = []
    review["thesis_reviews"] = [{"thesis_id":"T1","evidential_strength":"strong","normative_strength":"direct","procedural_fit":"satisfied",
        "requirement_checks":[{"requirement_index":0,"assessment":"supported","fact_ids":["F1"],"reason":"Registro literal"}],
        "contrary_norm_ids":[],"strongest_objection":"Autenticidade não conferida","response":"Limitar ao conteúdo",
        "selection_reason":"Questão única do cenário","residual_risk":"Não extrapolar a fonte sintética"}]
    return review, memory


class PrecisionV4(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / "fonte.txt"
        source.write_text("O pagamento foi realizado.",encoding="utf-8")
        self.output = self.root / "saida"
        run_ingest(source,self.output,task="analyze")
        self.review,self.memory = v4_fixture(self.output)

    def test_complete_v4_end_to_end_is_not_merit_certification(self):
        self.assertEqual(validate_contract(self.review,"legal_review.schema.json"),[])
        self.assertEqual(validate_precision(self.review,self.memory,self.output),[])
        self.assertEqual(validate_review(self.review,self.memory),[])
        path = self.root / "review.json"
        atomic_json(path,self.review)
        result = finalize(self.output,path)
        self.assertEqual(result["errors"],[])
        self.assertFalse(result["can_issue_final_legal_conclusion"])
        self.assertEqual(validate_links(self.output),[])
        self.assertIn("fonte.txt",(self.output / "indice_juridico.md").read_text(encoding="utf-8"))
        self.assertIn("fonte.txt",(self.output / "analise_juridica.md").read_text(encoding="utf-8"))

    def test_actor_polarity_period_amount_and_scope_mismatches(self):
        for field,value in (("actor","Outra parte"),("polarity","negated"),("scope","quitação total"),("date","2026-10-01"),("amount","900.00"),("period_start","2020-01-01")):
            with self.subTest(field=field):
                review = copy.deepcopy(self.review)
                review["assertion_reviews"][0]["atoms"][field] = value
                self.assertTrue(any(field in error for error in validate_precision(review,self.memory)))

    def test_contrary_evidence_cannot_be_hidden_as_supported(self):
        self.review["assertion_reviews"][0]["evidence"][0]["relation"] = "contradicts"
        self.assertTrue(any("contrária" in error for error in validate_precision(self.review,self.memory)))

    def test_critical_ocr_number_requires_region_and_confirmation(self):
        record = self.review["assertion_reviews"][0]
        record["atoms"]["amount"] = "100.00"
        record["evidence"][0]["source_atoms"]["amount"] = "100.00"
        self.assertTrue(any("reconferência" in error for error in validate_precision(self.review,self.memory)))
        record["critical_checks"] = [{"field":"amount","source_index":0,"method":"ocr_crosscheck","result":"confirmed","basis":"Número comparado"}]
        self.assertTrue(any("região" in error for error in validate_precision(self.review,self.memory)))
        record["critical_checks"][0]["region"] = "valor na terceira linha"
        self.review["execution_context"]["capabilities"]["vision"] = {"status":"available","observed_reference":"synthetic-test-crop-only"}
        self.assertEqual(validate_precision(self.review,self.memory),[])

    def test_precedent_needs_fact_comparison_and_exact_holding(self):
        norm = self.review["norms"][0]
        norm["kind"] = "precedent"
        self.assertTrue(any("precedent_comparisons" in error for error in validate_precision(self.review,self.memory)))
        self.review["precedent_comparisons"] = [{"norm_id":"N1","issue_ids":["I1"],"facts_of_precedent":"Cenário diverso",
            "holding_excerpt":"Fundamento inventado","case_comparison":"Diferenças decisivas","current_status_analysis":"Somente cenário sintético"}]
        self.assertTrue(any("fundamento determinante" in error for error in validate_precision(self.review,self.memory)))

    def test_thesis_request_cannot_point_to_different_issue(self):
        self.review["requests"] = [{"id":"R1","issue_ids":["OTHER"],"fact_ids":["F1"],"origin":"proposed","text":"Pedido sintético","compatibility":"Sem base na questão"}]
        self.review["theses"][0]["request_ids"] = ["R1"]
        self.assertTrue(any("pedido da tese" in error for error in validate_review(self.review,self.memory)))

    def test_future_norm_cannot_apply_without_transition(self):
        self.review["normative_map"][0]["effective_from"] = "2030-01-01"
        self.assertTrue(any("fora da vigência" in error for error in validate_precision(self.review,self.memory)))

    def test_pending_application_cannot_sustain_consolidated_thesis(self):
        self.review["norm_applications"][0]["result"] = "pending"
        self.assertTrue(any("pendente" in error for error in validate_review(self.review,self.memory)))

    def test_unknown_capability_and_probabilities_are_rejected(self):
        self.review["execution_context"]["capabilities"]["vision"] = {"status":"available"}
        self.review["thesis_reviews"][0]["success_probability"] = 99
        self.assertTrue(validate_contract(self.review,"legal_review.schema.json"))
        self.assertTrue(any("não observada" in error for error in validate_precision(self.review,self.memory)))

    def test_skeleton_does_not_mark_pages_or_sources_reviewed(self):
        pending = skeleton(self.output)
        self.assertFalse(pending["reviewed_pages"])
        self.assertFalse(pending["reading_coverage"])
        self.assertTrue(validate_contract(pending,"legal_review.schema.json"))

    def test_forged_receipt_and_missing_page_are_rejected(self):
        record = self.review["reading_coverage"][0]
        self.assertEqual(check_reading_coverage(self.review,self.memory,self.output),[])
        record["receipt_ids"] = ["0" * 64]
        self.assertTrue(any("recibo" in error for error in check_reading_coverage(self.review,self.memory,self.output)))
        self.review["reading_coverage"] = []
        self.assertTrue(check_reading_coverage(self.review,self.memory,self.output))

    def test_incomplete_and_malformed_reading_spans(self):
        record = self.review["reading_coverage"][0]
        for span in ([[1,5]],[["bad",3]], [[]]):
            record["intervals"] = span
            self.assertTrue(check_reading_coverage(self.review,self.memory))

    def test_full_text_batches_are_lossless_for_large_page(self):
        page = self.memory["documents"][0]["pages"][0]
        page["text"] = "abcd" * 10000 + "FATO CRÍTICO NO FINAL"
        atomic_json(self.output / "case_memory.json",self.memory)
        offset,parts = 0,[]
        while True:
            packet = reading_packet(self.output,offset=offset,max_chars=1000)
            self.assertLessEqual(packet["characters"],1000)
            parts += [item["text"] for item in packet["segments"]]
            if packet["next_offset"] is None:
                break
            offset = packet["next_offset"]
        self.assertEqual("".join(parts),page["text"])

    def test_all_246_pages_remain_represented_and_exported(self):
        source = self.root / "grande.txt"
        texts = [f"Página sintética {i}: contexto e fato próprio do segmento." for i in range(1,247)]
        source.write_text("\f".join(texts),encoding="utf-8")
        output = self.root / "grande"
        run_ingest(source,output,task="ingest")
        memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8"))
        offset,seen,parts = 0,set(),[]
        while True:
            packet = reading_packet(output,offset=offset,max_chars=1000)
            for segment in packet["segments"]:
                seen.add(segment["page_id"])
                parts.append(segment["text"])
            if packet["next_offset"] is None:
                break
            offset = packet["next_offset"]
        self.assertEqual(len(seen),246)
        self.assertEqual("".join(parts),"".join(texts))
        self.assertEqual(len(memory["documents"][0]["pages"]),246)
        self.assertEqual(validate_links(output),[])

    def test_selected_piece_checks_catalog_and_family(self):
        self.review["piece_assessment"].update(status="selected",catalog_id="apelacao_civel",selected_piece="Apelação")
        self.assertTrue(any("admissibilidade" in error for error in validate_catalog_selection(self.review)))
        found = candidates("trabalhista","sentenca","recurso")["candidates"]
        self.assertIn("recurso_ordinario_trabalhista",{item["id"] for item in found})
        self.assertNotIn("apelacao_civel",{item["id"] for item in found})

    def test_platform_routing_is_selective_and_does_not_assume_vision(self):
        context = resolve_context("gemini_gem","analyze",specialization_ids=["assistencia_bpc"])
        self.assertIn("gemini",context["adapter"])
        self.assertFalse(any("chatgpt" in item["path"] for item in context["references"]))
        self.assertEqual(context["capabilities"]["vision"],"not_tested")
        self.assertLess(context["reference_characters"],22000)
        with self.assertRaises(ValueError):
            resolve_context("generic","analyze",triggers=["invented"])


if __name__ == "__main__":
    unittest.main()
