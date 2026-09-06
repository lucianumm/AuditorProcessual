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
from scripts.ingest_document import run_ingest, resolve_vision_configuration
from scripts.legal_review import finalize, validate_review, style_findings
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
        self.assertEqual(validate(self.output), [])
        self.assertIn(memory["documents"][0]["sha256"], (self.output / "analise_juridica.md").read_text(encoding="utf-8"))

    def test_contradictory_quote_and_missing_requirement_rejected(self):
        review, memory = fixture(self.output)
        review["facts"][0]["text"] = "O pagamento não foi realizado."
        self.assertTrue(any("negação" in e for e in validate_review(review, memory)))
        review["issues"][0]["requirements"][0].update(assessment="missing", fact_ids=[])
        self.assertTrue(any("estratégia" in e for e in validate_review(review, memory)))

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
