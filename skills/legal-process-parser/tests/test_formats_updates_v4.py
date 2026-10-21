"""Office extraction and cumulative update tests using generated synthetic files."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))

from scripts.case_memory import atomic_json, update_memory
from scripts.document_formats import extract_office, inspect_format
from scripts.document_relations import record_relation
from scripts.helpers import extract_pages
from scripts.ingest_document import run_ingest
from scripts.legal_review import finalize
from scripts.research_memory import register_source_record, research_revision, changed_authorities
from scripts.validate_links import validate_links
from tests.test_precision_v4 import v4_fixture


class FormatsAndUpdatesV4(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def _docx(self, media=False):
        path = self.root / "prova.docx"
        with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml",'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
              <w:p><w:r><w:t>A autora recebeu R$ 100,00 em 01/09/2026.</w:t></w:r></w:p>
              <w:sdt><w:sdtContent><w:p><w:r><w:t>Fato em controle de conteúdo.</w:t></w:r></w:p></w:sdtContent></w:sdt>
              <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Contrato</w:t></w:r></w:p><w:p><w:r><w:t>Especial</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
              <w:p><w:del><w:r><w:delText>Redação anterior.</w:delText></w:r></w:del><w:ins><w:r><w:t>Redação nova.</w:t></w:r></w:ins></w:p>
            </w:body></w:document>''')
            archive.writestr("word/header1.xml",'<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Identificação do contrato</w:t></w:r></w:p></w:hdr>')
            if media:
                archive.writestr("word/media/photo.png",b"synthetic-not-a-real-image")
        return path

    def test_docx_body_tables_controls_headers_and_revisions(self):
        texts,warnings = extract_office(self._docx())
        self.assertIn("01/09/2026",texts[0])
        self.assertIn("Fato em controle",texts[0])
        self.assertIn("Contrato Especial",texts[0])
        self.assertIn("Identificação",texts[0])
        self.assertTrue(any("Revisões controladas" in warning for warning in warnings))
        self.assertFalse(texts[0].startswith("PK"))

    def test_office_embedded_visual_is_not_declared_complete(self):
        output = self.root / "saida"
        run_ingest(self._docx(media=True),output,task="ingest")
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["coverage"]["full_conversion_complete"])
        self.assertTrue(manifest["coverage"]["office_visual_review_pending"])
        self.assertEqual(manifest["source"]["page_unit"],"logical_segment")
        self.assertEqual(validate_links(output),[])
        markdown = (output / "processo_completo.md").read_text(encoding="utf-8")
        self.assertIn("Segmento lógico 1 da peça", markdown)
        self.assertNotIn("Página PDF 1 da peça", markdown)

    def test_xlsx_all_rows_hidden_sheet_and_formula_are_preserved(self):
        path = self.root / "extrato.xlsx"
        with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml",'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Extrato" state="hidden" sheetId="1" r:id="r1"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels",'<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
            rows = ''.join(f'<row r="{i}"><c r="A{i}" t="inlineStr"><is><t>Transação {i}</t></is></c></row>' for i in range(1,1501))
            archive.writestr("xl/worksheets/sheet1.xml",'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+rows+'<row r="1501"><c r="B1501"><f>SUM(B1:B1500)</f><v>100</v></c></row></sheetData></worksheet>')
        texts,warnings = extract_office(path)
        self.assertIn("Transação 1500",texts[0])
        self.assertIn("estado: hidden",texts[0])
        self.assertIn("fórmula SUM",texts[0])
        self.assertTrue(any("não executadas" in warning for warning in warnings))

    def test_unknown_binary_and_masquerading_text_are_rejected(self):
        for name,content in (("foto.png",b"\x89PNG"),("prova.txt",b"PK\x03\x04\x00"),("falso.pdf",b"just text")):
            path = self.root / name
            path.write_bytes(content)
            with self.assertRaises(ValueError):
                inspect_format(path)

    def test_entities_and_macros_are_not_executed(self):
        path = self.root / "malformed.docx"
        with zipfile.ZipFile(path,"w") as archive:
            archive.writestr("word/document.xml",'<!DOCTYPE x [<!ENTITY data "danger">]><x>&data;</x>')
        with self.assertRaises(ValueError):
            extract_office(path)
        with zipfile.ZipFile(path,"a") as archive:
            archive.writestr("word/vbaProject.bin",b"never-execute")
        with self.assertRaisesRegex(ValueError,"macros"):
            extract_office(path)

    def test_utf16_bom_is_not_mistaken_for_binary(self):
        path = self.root / "prova.txt"
        path.write_bytes("A parte recebeu o salário.".encode("utf-16"))
        texts,_ = extract_pages(path)
        self.assertEqual(texts,["A parte recebeu o salário."])

    def _accepted_review(self):
        source = self.root / "fonte.txt"
        source.write_text("O pagamento foi realizado.",encoding="utf-8")
        output = self.root / "saida"
        run_ingest(source,output,task="analyze")
        review,memory = v4_fixture(output)
        path = self.root / "review.json"
        atomic_json(path,review)
        self.assertEqual(finalize(output,path)["errors"],[])
        return output,review,memory

    def test_authority_change_without_new_upload_invalidates_only_dependencies(self):
        output,review,memory = self._accepted_review()
        norm = review["norms"][0]
        path = output / "research_sources" / (norm["capture_id"] + ".json")
        previous = json.loads(path.read_text(encoding="utf-8"))
        current = dict(previous,text="Texto consultado modificado no cenário sintético.",capture_id="f"*64)
        register_source_record(output,current)
        self.assertNotEqual(review["research_revision"],research_revision(output))
        self.assertEqual(changed_authorities(review,output),["N1"])
        self.assertEqual(json.loads((output / "case_memory.json").read_text(encoding="utf-8"))["corpus_revision"],memory["corpus_revision"])
        self.assertIn("ENTREGA ANTERIOR",(output / "analise_juridica.md").read_text(encoding="utf-8"))
        updates = json.loads((output / "legal_source_updates.json").read_text(encoding="utf-8"))
        self.assertIn("T1",updates["impacted_elements"]["thesis_ids"])
        self.assertEqual(json.loads((output / "quality_gate.json").read_text(encoding="utf-8"))["status"],"review_required")
        self.assertTrue(path.exists())

    def test_same_authority_text_recapture_does_not_change_revision(self):
        output,review,_ = self._accepted_review()
        norm = review["norms"][0]
        original = json.loads((output / "research_sources" / (norm["capture_id"]+".json")).read_text(encoding="utf-8"))
        result = register_source_record(output,{**original,"capture_id":"e"*64,"accessed_on":"2026-10-10"})
        self.assertFalse(result["changed"])
        self.assertEqual(review["research_revision"],research_revision(output))

    def test_relations_change_revision_keep_originals_and_reject_cycles(self):
        output,_,_ = self._accepted_review()
        another = self.root / "retificacao.txt"
        another.write_text("A transação corrigida refere-se a outro período.",encoding="utf-8")
        run_ingest(another,output,task="ingest")
        memory = json.loads((output / "case_memory.json").read_text(encoding="utf-8"))
        older,newer = [doc["sha256"] for doc in memory["documents"]]
        kwargs = dict(older=older,newer=newer,relation="supersedes",reason="Retificação expressa sintética",recorded_by="test")
        record_relation(output,**kwargs)
        updated = json.loads((output / "case_memory.json").read_text(encoding="utf-8"))
        self.assertNotEqual(updated["corpus_revision"],memory["corpus_revision"])
        self.assertEqual(len(updated["documents"]),2)
        with self.assertRaisesRegex(ValueError,"circular"):
            record_relation(output,older=newer,newer=older,relation="supersedes",reason="ciclo",recorded_by="test")
        revision = updated["corpus_revision"]
        record_relation(output,**kwargs)
        self.assertEqual(update_memory(output)["corpus_revision"],revision)
        self.assertEqual(validate_links(output),[])

    def test_missing_markdown_anchor_is_reported(self):
        page = self.root / "indice.md"
        page.write_text("[Item](#inexistente)\n",encoding="utf-8")
        self.assertTrue(any("âncora ausente" in error for error in validate_links(self.root)))


if __name__ == "__main__":
    unittest.main()
