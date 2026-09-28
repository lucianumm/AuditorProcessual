"""Synthetic regression suite: no client documents or live legal conclusions."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.case_memory import atomic_json, checkpoint, identity, page_revision, query_memory, update_memory
from scripts.case_graph import affected_elements, build_case_graph
from scripts.case_search import search_memory
from scripts.ingest_document import run_ingest, resolve_vision_configuration
from scripts.legal_review import finalize, validate_review, style_findings
from scripts.piece_validation import initial_voice_findings
from scripts.validate_links import validate_links
from scripts.validate_extraction import validate


def fixture(output):
    memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8"))
    doc = memory["documents"][0]
    page = doc["pages"][0]
    quote = page["text"]
    receipt = {"url": "https://www.planalto.gov.br/test-fixture", "accessed_on": "2026-09-06",
               "text": "Texto normativo sintético para testar o contrato, não usar como lei.", "method": "official_http_capture"}
    receipt["text_hash"] = hashlib.sha256(receipt["text"].encode()).hexdigest()
    receipt["raw_content_hash"] = receipt["text_hash"]
    receipt["capture_id"] = identity(receipt)
    atomic_json(output / "research_sources" / (receipt["capture_id"] + ".json"), receipt)
    (output / "research_sources" / (receipt["capture_id"] + ".source")).write_bytes(receipt["text"].encode())
    norm = dict(id="N1", kind="statute", url=receipt["url"], accessed_on=receipt["accessed_on"], title="Fonte sintética",
                provision="Regra de teste", quote=receipt["text"], official_text=receipt["text"], temporal_analysis="Cenário sintético datado",
                jurisdiction="Cenário civil", hierarchy="Teste", case_fit="Obrigação descrita na fonte sintética", reviewed_by="test-fixture",
                status="verified", capture_id=receipt["capture_id"])
    review = {"corpus_revision": memory["corpus_revision"], "task": "analyze", "title": "Análise jurídica",
        "strategy": {"objective": "Examinar pagamento", "jurisdiction": "cível", "domain": "civil", "phase": "conhecimento"},
        "reviewed_pages": [doc["sha256"] + ":1"],
        "page_reviews": [{"page_id": doc["sha256"] + ":1", "content_revision": page_revision(page), "relevance": "relevant",
                          "findings": "Pagamento indicado expressamente na única frase.", "fact_ids": ["F1"], "reviewed_by": "test-fixture"}],
        "facts": [{"id": "F1", "text": quote, "nature": "fato", "origin": "document", "sources": [{"source_sha256": doc["sha256"],
                   "pdf_page": 1, "document_id": page["document_id"], "quote": quote}],
                   "support": {"assessment": "direct", "reason": "Mesma proposição literal", "reviewed_by": "test-fixture"}}],
        "norms": [norm], "client_records": [], "requests": [], "issues": [{"id": "I1", "fact_ids": ["F1"], "norm_ids": ["N1"],
            "question": "O pagamento está registrado?", "subsumption": "A frase registra o pagamento no cenário sintético.",
            "counterargument": "Pode haver obrigação distinta.", "response": "Esta análise se limita à obrigação descrita.",
            "conclusion": "Pagamento registrado, sujeito à conferência profissional.", "evidence_assessment": "Registro textual, não autenticação.",
            "requirements": [{"rule": "Pagamento", "assessment": "supported", "reason": "Fonte expressa", "fact_ids": ["F1"]}],
            "research": {key: "Examinado no cenário sintético; não é orientação jurídica." for key in ("material_law", "procedure", "temporal_scope", "jurisdiction", "contrary_authorities", "closure_reason")}}],
        "paragraphs": [{"id": "P1", "section": "fatos", "text": quote, "fact_ids": ["F1"], "norm_ids": ["N1"], "issue_ids": ["I1"], "request_ids": []}],
        "research_closure": {"searched_topics": ["Pagamento"], "stop_reason": "Cenário sintético restrito"}, "unresolved": []}
    return review, memory


def v3_fixture(review):
    review = copy.deepcopy(review)
    review["schema_version"] = "3.0"
    review["piece_assessment"] = {
        "status": "outside_scope", "process_stage": "análise sintética",
        "triggering_act": "nenhum ato pendente", "represented_party": "Parte sintética",
        "objective": "analisar o registro", "selected_piece": None, "drafted_piece_type": None,
        "selection_reason": "Não foi solicitada minuta", "alternatives_considered": [],
        "admissibility_checks": [],
        "deadline": {"status": "not_applicable", "calculation_or_limitation": "Sem prazo neste caso sintético",
                     "fact_ids": [], "norm_ids": []},
        "fact_ids": ["F1"], "norm_ids": ["N1"],
    }
    review["norm_applications"] = [{
        "id": "A1", "issue_id": "I1", "norm_id": "N1", "method": "direct",
        "basis_for_use": "Regra do caso sintético", "gap_or_remission": "Não aplicável",
        "similarities": [], "differences": [], "compatibility_analysis": "Compatível no cenário",
        "limits_and_contrary_authorities": "Cenário sintético restrito",
        "temporal_fit": "Período sintético", "result": "applied",
    }]
    review["theses"] = [{
        "id": "T1", "issue_id": "I1", "characterization": "consolidated", "role": "principal",
        "proposition": "O registro contém a proposição sintética", "fact_ids": ["F1"],
        "norm_ids": ["N1"], "norm_application_ids": ["A1"], "request_ids": [],
        "requirements_analysis": "Cenário sintético", "strongest_objection": "Fato não autentica documento",
        "response": "Conclusão limitada ao conteúdo literal", "procedural_compatibility": "Análise",
        "evidential_limits": "Fonte sintética", "expected_effect": "Descrever o registro",
    }]
    return review


class ReleaseIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "fonte.txt"
        self.source.write_text("O pagamento foi realizado.", encoding="utf-8")
        self.output = self.root / "saida"
        run_ingest(self.source, self.output, task="analyze")

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_review_is_technical_only_and_schema_valid(self):
        from scripts.contracts import validate_contract
        review, memory = fixture(self.output)
        path = self.root / "review.json"
        atomic_json(path, review)
        result = finalize(self.output, path)
        self.assertEqual(result["errors"], [])
        gate = json.loads((self.output / "quality_gate.json").read_text())
        self.assertEqual(validate_contract(gate, "quality_gate.schema.json"), [])
        self.assertFalse(gate["can_issue_final_legal_conclusion"])
        self.assertEqual(gate["gates"]["official_source_integrity"]["status"], "passed")
        self.assertEqual(gate["gates"]["legal_applicability"]["status"], "not_machine_verified")
        self.assertEqual(validate(self.output), [])
        rendered = (self.output / "analise_juridica.md").read_text(encoding="utf-8")
        self.assertIn("PDF p. 1", rendered)
        self.assertIn("fonte.txt", rendered)
        self.assertNotIn(memory["documents"][0]["sha256"], rendered)

    def test_independent_issue_survives_scoped_decisive_gap(self):
        review, _ = fixture(self.output)
        second = copy.deepcopy(review["issues"][0])
        second.update(id="I2", question="A entrega foi comprovada?", conclusion="Não é possível concluir sem a prova de entrega.")
        review["issues"].append(second)
        review["findings"] = [{
            "id": "GAP-I2", "code": "EVIDENCE_MISSING", "category": "evidence",
            "severity": "material", "status": "open", "scope": "issue", "target_ids": ["I2"],
            "description": "Comprovante de entrega não localizado.",
            "impact": "A questão da entrega permanece sem premissa decisiva.",
            "delivery_effect": "blocks_issue", "required_action": "Localizar comprovante de entrega.",
            "attempt_ids": [], "resolution": None,
        }]
        path = self.root / "partial_review.json"
        atomic_json(path, review)
        result = finalize(self.output, path)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["status"], "partial_for_professional_review")
        self.assertEqual(result["analysis_status"], "qualified")
        states = {item["id"]: item["analysis_status"] for item in result["issue_statuses"]}
        self.assertEqual(states, {"I1": "concluded", "I2": "undetermined"})
        text = (self.output / "analise_juridica.md").read_text(encoding="utf-8")
        self.assertIn("O pagamento foi realizado.", text)
        self.assertIn("Comprovante de entrega não localizado", text)

    def test_contradictory_quote_and_missing_requirement_rejected(self):
        review, memory = fixture(self.output)
        review["facts"][0]["text"] = "O pagamento não foi realizado."
        self.assertTrue(any("negação" in e for e in validate_review(review, memory)))
        review["issues"][0]["requirements"][0].update(assessment="missing", fact_ids=[])
        self.assertTrue(any("estratégia" in e for e in validate_review(review, memory)))

    def test_v3_rejected_analogy_cannot_support_an_active_thesis(self):
        review, memory = fixture(self.output)
        review = v3_fixture(review)
        review["norm_applications"][0].update(
            method="analogy", result="rejected",
            similarities=["Situação funcionalmente semelhante"],
            differences=["Regime especial incompatível"],
        )
        review["theses"][0].update(
            characterization="analogical_proposal",
            proposition="Aplicar a regra por analogia",
        )
        errors = validate_review(review, memory)
        self.assertTrue(any("aplicação normativa rejeitada" in error for error in errors), errors)
        self.assertTrue(any("analogia sustentada" in error for error in errors), errors)

    def test_v3_measure_with_unsatisfied_admissibility_cannot_be_selected(self):
        review, memory = fixture(self.output)
        review = v3_fixture(review)
        review["piece_assessment"].update(
            status="selected", selected_piece="Medida sintética",
            fact_ids=["F1"], norm_ids=["N1"],
            admissibility_checks=[{
                "requirement": "Cabimento", "status": "unsatisfied",
                "reason": "A hipótese processual sintética não prevê a medida",
                "fact_ids": ["F1"], "norm_ids": ["N1"],
            }],
        )
        errors = validate_review(review, memory)
        self.assertTrue(any("marcado não atendido" in error for error in errors), errors)

    def test_initial_quote_is_exempt_from_authorial_style_lint(self):
        text = 'A ré declarou: "A autora alega inadimplemento." O pagamento venceu.'
        self.assertEqual(style_findings(text, initial=True), [])
        self.assertEqual(initial_voice_findings({"section": "fatos", "text": text}), [])

    def test_full_page_read_is_explicit_and_contains_the_end_of_long_pages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "longa.txt"
            source.write_text(
                "INÍCIO. " + "Conteúdo integral da página. " * 300 + "MARCADOR_FINAL_DA_PAGINA.",
                encoding="utf-8",
            )
            output = root / "case"
            run_ingest(source, output, task="ingest")
            excerpt = search_memory(output, limit=1)
            complete = search_memory(output, limit=1, include_full_pages=True)
            self.assertNotIn("MARCADOR_FINAL_DA_PAGINA", excerpt["pages"][0]["snippet"])
            self.assertIn("MARCADOR_FINAL_DA_PAGINA", complete["pages"][0]["text"])

    def test_case_graph_propagates_page_changes_to_v3_theses_and_applications(self):
        review, memory = fixture(self.output)
        graph = build_case_graph(v3_fixture(review))
        changed_page = review["reviewed_pages"][0]
        impact = affected_elements(graph, [changed_page])
        self.assertEqual(impact["thesis_ids"], ["T1"])
        self.assertEqual(impact["norm_application_ids"], ["A1"])

    def test_invalid_current_review_marks_and_preserves_previous_deliverable(self):
        review, _ = fixture(self.output)
        path = self.root / "review.json"
        atomic_json(path, review)
        self.assertEqual(finalize(self.output, path)["errors"], [])
        deliverable = self.output / "analise_juridica.md"
        accepted = deliverable.read_bytes()
        invalid = copy.deepcopy(review)
        invalid["paragraphs"][0]["fact_ids"] = ["F-INEXISTENTE"]
        atomic_json(path, invalid)
        report = finalize(self.output, path)
        self.assertEqual(report["status"], "review_required")
        self.assertIn("ENTREGA ANTERIOR — NÃO UTILIZAR", deliverable.read_text(encoding="utf-8"))
        archived = list((self.output / "legal_reviews" / "superseded").rglob("analise_juridica.md"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].read_bytes(), accepted)
        manifest = json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn(manifest["superseded_deliverable"]["path"], manifest["generated_files"])

    def test_page_assertion_without_ledger_rejected(self):
        review, memory = fixture(self.output)
        review["page_reviews"] = []
        self.assertTrue(any("page_reviews" in e for e in validate_review(review, memory)))

    def test_failure_gate_schema_and_markdown_are_current(self):
        from scripts.contracts import validate_contract
        path = self.root / "review.json"
        atomic_json(path, {})
        self.assertTrue(finalize(self.output, path)["errors"])
        gate = json.loads((self.output / "quality_gate.json").read_text())
        self.assertEqual(validate_contract(gate, "quality_gate.schema.json"), [])
        self.assertIn("PENDENTE", (self.output / "quality_gate.md").read_text(encoding="utf-8"))

    def test_malformed_review_returns_failure_instead_of_traceback(self):
        path = self.root / "malformed.json"
        atomic_json(path, {"task": "analyze", "facts": "not a list", "issues": ["not an issue"],
                           "norms": ["not a norm"], "findings": "not a list"})
        result = finalize(self.output, path)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["execution_status"], "failed")
        self.assertTrue(result["errors"])

    def test_in_output_input_preserved_and_stale_review_recorded(self):
        review, memory = fixture(self.output)
        path = self.output / "legal_review.json"
        atomic_json(path, review)
        self.assertEqual(run_ingest(self.source, self.output, task="analyze", legal_review=path)["manifest"]["legal_review"]["errors"], [])
        self.assertTrue(list((self.output / "review_inputs").glob("*.json")))
        second = self.root / "novo.txt"
        second.write_text("Há uma obrigação distinta.", encoding="utf-8")
        result = run_ingest(second, self.output)
        self.assertEqual(result["manifest"]["legal_review"]["status"], "stale")

    def test_visual_content_changes_revision_and_search(self):
        old = json.loads((self.output / "case_memory.json").read_text())
        page = json.loads((self.output / "pages.jsonl").read_text())
        page["vision"] = {"description": "fotografia singularXYZ"}
        (self.output / "pages.jsonl").write_text(json.dumps(page) + "\n")
        memory = update_memory(self.output)
        self.assertNotEqual(old["corpus_revision"], memory["corpus_revision"])
        self.assertTrue(memory["update"]["requires_legal_reassessment"])
        self.assertEqual(len(query_memory(self.output, "singularXYZ")), 1)

    def test_wrong_source_vision_rejected_before_mutation(self):
        sidecar = self.root / "vision.json"
        atomic_json(sidecar, {"source_sha256": "f" * 64, "pages": {"1": {"semantic_description": "Outra página", "description_source": "human_review"}}})
        with self.assertRaisesRegex(ValueError, "source_sha256"):
            resolve_vision_configuration(self.source, self.output, "required", "sidecar", sidecar, None)

    def test_cumulative_zip_has_all_local_links(self):
        for number in range(3):
            source = self.root / f"adicional{number}.txt"
            source.write_text(f"Nova página {number}")
            run_ingest(source, self.output)
        unpacked = self.root / "unpacked"
        with zipfile.ZipFile(self.output / "processo_completo.zip") as z:
            z.extractall(unpacked)
            self.assertTrue(any(n.startswith("versions/") for n in z.namelist()))
            self.assertFalse(any(n.endswith(".zip") for n in z.namelist()))
        self.assertEqual(validate_links(unpacked), [])

    def test_initial_voice_plural_and_party(self):
        for text in ("A parte autora sustenta que pagou.", "Os autores alegam inadimplemento."):
            self.assertTrue(style_findings(text, initial=True))
        self.assertFalse(style_findings("O réu deixou de pagar a parcela.", initial=True))

    def test_checkpoint_failure_and_corruption_resume(self):
        cache = self.root / "cache"
        with self.assertRaises(RuntimeError):
            checkpoint(cache, "native", "one", lambda: (_ for _ in ()).throw(RuntimeError("interruption")))
        self.assertEqual(checkpoint(cache, "native", "one", lambda: "recovered"), "recovered")
        next(cache.rglob("*.json")).write_text("corrupted")
        self.assertEqual(checkpoint(cache, "native", "one", lambda: "recomputed"), "recomputed")

    def test_ingest_does_not_build_legal_narrative(self):
        with patch("scripts.ingest_document.build_legal_narrative", side_effect=AssertionError("unnecessary work")):
            run_ingest(self.source, self.root / "minimal", task="ingest")

    def test_changed_number_rejected(self):
        review, memory = fixture(self.output)
        review["facts"][0]["text"] = "O pagamento foi de R$ 200."
        review["facts"][0]["sources"][0]["quote"] = "O pagamento foi de R$ 100."
        self.assertTrue(any("valores/datas" in e for e in validate_review(review, memory)))

    def test_raw_capture_tampering_rejected(self):
        review, _ = fixture(self.output)
        next((self.output / "research_sources").glob("*.source")).write_bytes(b"altered")
        path = self.root / "review.json"
        atomic_json(path, review)
        self.assertTrue(any("resposta oficial bruta" in e for e in finalize(self.output, path)["errors"]))

    def test_asset_tampering_prevents_reuse(self):
        asset = self.output / "assets/pages/probe.png"
        asset.write_bytes(b"changed")
        manifest_path = self.output / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["artifact_hashes"]["assets/pages/probe.png"] = "a" * 64
        atomic_json(manifest_path, manifest)
        self.assertEqual(run_ingest(self.source, self.output, task="analyze")["status"], "processed")

    def capture_fixture(self, content_type, raw):
        from email.message import Message
        from unittest.mock import MagicMock
        from scripts.research_sources import capture
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = "https://www.planalto.gov.br/test-fixture"
        response.headers = Message()
        response.headers["Content-Type"] = content_type
        response.read.return_value = raw
        opener = MagicMock()
        opener.open.return_value = response
        with patch("scripts.research_sources.build_opener", return_value=opener):
            return capture(response.geturl(), self.output)

    def test_official_html_capture_encoding_and_raw_receipt(self):
        receipt = self.capture_fixture("text/html", "<p>Obrigação</p>".encode("cp1252"))
        self.assertIn("Obrigação", receipt["text"])
        self.assertEqual(receipt["encoding"], "cp1252")
        self.assertTrue((self.output / "research_sources" / (receipt["capture_id"] + ".source")).exists())

    def test_official_pdf_extraction_adapter_keeps_page_locator(self):
        from types import SimpleNamespace
        pdf = SimpleNamespace(PdfReader=lambda _: SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda: "Regra PDF <texto literal>")]))
        with patch.dict(sys.modules, {"pypdf": pdf}):
            receipt = self.capture_fixture("application/pdf", b"%PDF-synthetic-adapter-fixture")
        self.assertIn("[PDF p. 1]", receipt["text"])
        self.assertIn("<texto literal>", receipt["text"])


if __name__ == "__main__":
    unittest.main()
