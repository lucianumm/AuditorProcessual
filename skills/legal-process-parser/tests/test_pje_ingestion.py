"""PJe records: case number, signature footer and pieces by document id.

Synthetic texts only: names, numbers, ids and dates are invented.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from scripts.helpers import (
    build_pages,
    classify_process,
    identify_pieces,
    identify_process_number,
    pje_footer,
    strip_pje_footer,
)
from scripts.ingest_document import run_ingest

CASE = "0001234-56.2026.5.99.0001"
PRECEDENT = "1000001-11.2019.5.99.0002"


def first_degree(text: str, doc_id: str, folio: int, signer: str = "FULANA DE TAL SINTÉTICA") -> str:
    return (
        f"{text}\n"
        f"Documento assinado eletronicamente por {signer}, em 05/03/2026, às 10:11:12 - {doc_id}\n"
        f"https://pje.trt99.jus.br/pjekz/validacao/26030510111200000000099999?instancia=1\n"
        f"Número do processo: {CASE}\n"
        "Número do documento: 26030510111200000000099999\n"
        f"Fls.: {folio}"
    )


def second_degree(text: str, doc_id: str, folio: int, page: int) -> str:
    return (
        f"{text}\n"
        f"Assinado eletronicamente por: BELTRANO RELATOR SINTÉTICO - 20/08/2026 14:15:16 - {doc_id}\n"
        "https://pje.trt99.jus.br/segundograu/Processo/ConsultaDocumento/listView.seam?nd=26082014151600000000088888\n"
        f"Número do processo: {CASE}\n"
        "Número do documento: 26082014151600000000088888\n"
        f"ID. {doc_id} - Pág. {page}\n"
        f"Fls.: {folio}"
    )


INITIAL = (
    "EXCELENTÍSSIMO SENHOR JUIZ DA VARA DO TRABALHO SINTÉTICA\n"
    "PETIÇÃO INICIAL\n"
    "A reclamante, trabalhadora fictícia, propõe a presente ação. Em caso semelhante "
    f"(processo {PRECEDENT}) o tribunal deferiu horas extras. Requer o pagamento das verbas rescisórias."
)
INITIAL_2 = "Dos pedidos: aviso prévio, férias com um terço, décimo terceiro e FGTS com multa de quarenta por cento."
SENTENCE = (
    "PODER JUDICIÁRIO - JUSTIÇA DO TRABALHO\n"
    "SENTENÇA\n"
    "Relatório: a reclamante ajuizou a ação conforme a petição inicial; a reclamada apresentou contestação. "
    "Fundamentação: provas documentais e testemunhais examinadas. Dispositivo: julgo procedentes em parte os pedidos."
)
DECISION = (
    "ACÓRDÃO\n"
    "Recurso ordinário da reclamada conhecido e desprovido. A sentença fica mantida pelos próprios fundamentos, "
    "com a observação de que os cálculos seguem os parâmetros fixados."
)


def synthetic_records() -> list[str]:
    return [
        first_degree(INITIAL, "a1b2c3d", 1),
        first_degree(INITIAL_2, "a1b2c3d", 2),
        first_degree("", "b2c3d4e", 3, signer="ADVOGADO FICTÍCIO"),
        first_degree("", "b2c3d4e", 4, signer="ADVOGADO FICTÍCIO"),
        first_degree(SENTENCE, "c3d4e5f", 5, signer="JUÍZA SINTÉTICA"),
        first_degree("Dispositivo (continuação): custas pela reclamada, calculadas sobre o valor da condenação.", "c3d4e5f", 6, signer="JUÍZA SINTÉTICA"),
        second_degree(DECISION, "d4e5f60", 7, 1),
        second_degree("Ante o exposto, nego provimento ao recurso, nos termos da fundamentação sintética.", "d4e5f60", 8, 2),
    ]


class ProcessNumber(unittest.TestCase):
    def test_most_frequent_number_wins_over_first_cited_precedent(self):
        text = f"Cita-se o precedente {PRECEDENT}.\n" + "\n".join(f"Autos {CASE}, página {n}." for n in range(5))
        result = identify_process_number(text)
        self.assertEqual(result["numero"], CASE)
        self.assertEqual(result["criterio"], "mais_frequente")
        self.assertEqual(result["citados"], [{"numero": PRECEDENT, "ocorrencias": 1}])

    def test_pje_footer_number_wins_even_when_precedent_is_more_cited(self):
        text = (f"{PRECEDENT} {PRECEDENT} {PRECEDENT}\n" f"Número do processo: {CASE}\n")
        result = identify_process_number(text)
        self.assertEqual((result["numero"], result["criterio"]), (CASE, "pje_rodape"))
        self.assertEqual(result["citados"], [{"numero": PRECEDENT, "ocorrencias": 3}])

    def test_classification_records_cited_numbers(self):
        pages, _ = build_pages(synthetic_records())
        classification = classify_process(pages)
        self.assertEqual(classification["numero_processo"], CASE)
        self.assertEqual(classification["numeros_processo_citados"], [{"numero": PRECEDENT, "ocorrencias": 1}])

    def test_without_any_number(self):
        self.assertEqual(identify_process_number("sem número")["numero"], None)


class Footer(unittest.TestCase):
    def test_footer_is_read_in_both_degrees(self):
        self.assertEqual(pje_footer(first_degree("texto", "a1b2c3d", 12)),
                         {"document_id": "a1b2c3d", "document_page": None, "court_page": 12})
        self.assertEqual(pje_footer(second_degree("texto", "d4e5f60", 40, 3)),
                         {"document_id": "d4e5f60", "document_page": 3, "court_page": 40})

    def test_footer_only_page_has_no_content(self):
        self.assertEqual(strip_pje_footer(first_degree("", "b2c3d4e", 3)), "")
        self.assertEqual(strip_pje_footer(second_degree("12", "d4e5f60", 7, 1)), "")
        self.assertIn("verbas rescisórias", strip_pje_footer(first_degree(INITIAL, "a1b2c3d", 1)))
        self.assertNotIn("assinado", strip_pje_footer(first_degree(INITIAL, "a1b2c3d", 1)).lower())

    def test_text_without_pje_footer_is_untouched(self):
        text = "Página comum.\n12\nfls. 3 dos autos"
        self.assertEqual(strip_pje_footer(text), text)

    def test_footer_only_page_goes_to_ocr_or_vision(self):
        pages, _ = build_pages(synthetic_records(), source_kind=".pdf", vision_policy="off")
        scanned = [page for page in pages if page.pdf_page in {3, 4}]
        self.assertTrue(all(page.source == "needs_ocr_or_vision" for page in scanned))
        self.assertTrue(all(page.quality == "unreadable" for page in scanned))
        self.assertTrue(all(page.status == "PARTIAL" for page in scanned))
        self.assertTrue(all(page.ocr["required"] for page in scanned))
        self.assertTrue(all(page.source == "native_text" and page.quality == "high"
                            for page in pages if page.pdf_page not in {3, 4}))
        # The footer stays in the preserved page text.
        self.assertIn("b2c3d4e", scanned[0].text)


class Pieces(unittest.TestCase):
    def test_pieces_follow_pje_document_id_and_folios(self):
        pages, _ = build_pages(synthetic_records())
        self.assertEqual([page.court_page for page in pages], list(range(1, 9)))
        pieces = identify_pieces(pages)
        summary = [(p["pje_document_id"], p["piece"], p["pdf_page_start"], p["pdf_page_end"],
                    p["court_page_start"], p["court_page_end"]) for p in pieces]
        self.assertEqual(summary, [
            ("a1b2c3d", "Petição Inicial", 1, 2, 1, 2),
            ("b2c3d4e", "Não identificado", 3, 4, 3, 4),
            ("c3d4e5f", "Sentença", 5, 6, 5, 6),
            ("d4e5f60", "Acórdão", 7, 8, 7, 8),
        ])
        self.assertEqual([page.piece for page in pages][2:6],
                         ["Não identificado", "Não identificado", "Sentença", "Sentença"])

    def test_same_label_in_two_documents_stays_two_pieces(self):
        records = [first_degree("MANIFESTAÇÃO\nA reclamante se manifesta sobre os documentos juntados.", doc, n)
                   for n, doc in enumerate(("e5f6071", "f607182"), start=1)]
        pieces = identify_pieces(build_pages(records)[0])
        self.assertEqual([(p["piece"], p["pje_document_id"]) for p in pieces],
                         [("Manifestação", "e5f6071"), ("Manifestação", "f607182")])

    def test_without_pje_footer_keeps_keyword_segmentation(self):
        pieces = identify_pieces(build_pages(["CONTESTAÇÃO\nA reclamada contesta.", "Continua a defesa."])[0])
        self.assertEqual([(p["piece"], p["pdf_page_start"], p["pdf_page_end"]) for p in pieces],
                         [("Contestação", 1, 2)])
        self.assertNotIn("pje_document_id", pieces[0])


def text_pdf(pages: list[str]) -> bytes:
    """Minimal PDF with one Helvetica text line per input line (WinAnsi)."""
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", None,
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    kids = []
    for text in pages:
        lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in text.split("\n")]
        stream = "BT /F1 9 Tf 40 800 Td 12 TL " + " ".join(f"({line}) '" for line in lines) + " ET"
        data = stream.encode("cp1252")
        objects.append(f"<< /Length {len(data)} >>\nstream\n".encode("ascii") + data + b"\nendstream")
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {len(objects)} 0 R >>")
        kids.append(f"{len(objects)} 0 R")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("ascii") + (body if isinstance(body, bytes) else body.encode("ascii")) + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii")
    out += "".join(f"{offset:010d} 00000 n \n" for offset in offsets).encode("ascii")
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    return bytes(out)


class Ingestion(unittest.TestCase):
    def test_footer_only_pdf_page_is_sent_to_ocr(self):
        try:
            import pypdf  # noqa: F401
        except ImportError:
            self.skipTest("pypdf não instalado")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "autos_sinteticos.pdf"
            source.write_bytes(text_pdf([first_degree(INITIAL, "a1b2c3d", 1), first_degree("", "b2c3d4e", 2)]))
            output = Path(tmp) / "saida"
            manifest = run_ingest(source, output, use_ocr=True, vision_policy="off")["manifest"]
            pages = [json.loads(line) for line in (output / "pages.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([page["pje_document_id"] for page in pages], ["a1b2c3d", "b2c3d4e"])
        self.assertEqual([page["court_page"] for page in pages], [1, 2])
        self.assertEqual(pages[0]["source"], "native_text")
        # Without Tesseract the OCR stays pending, but it was attempted on the
        # footer-only page and not on the page with its own text.
        if pages[1]["source"] != "ocr":
            self.assertEqual(pages[1]["source"], "needs_ocr_or_vision")
            self.assertTrue(any(w.startswith("PDF p. 2: OCR pendente") for w in manifest["warnings"]))
        self.assertFalse(any(w.startswith("PDF p. 1:") for w in manifest["warnings"]))


    def test_manifest_and_schemas(self):
        from jsonschema import Draft202012Validator

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "autos_sinteticos.txt"
            source.write_text("\f".join(synthetic_records()), encoding="utf-8")
            manifest = run_ingest(source, Path(tmp) / "saida", task="ingest")["manifest"]
            self.assertEqual(manifest["process_id"], CASE)
            self.assertEqual(manifest["process_id_criterion"], "pje_rodape")
            self.assertEqual(manifest["cited_process_ids"], [{"numero": PRECEDENT, "ocorrencias": 1}])
            self.assertEqual([p["piece"] for p in manifest["pieces"]],
                             ["Petição Inicial", "Não identificado", "Sentença", "Acórdão"])
            schemas = CORE / "schemas"
            piece_schema = json.loads((schemas / "document_piece.schema.json").read_text(encoding="utf-8"))
            manifest_schema = json.loads((schemas / "process_manifest.schema.json").read_text(encoding="utf-8"))
            for piece in manifest["pieces"]:
                Draft202012Validator(piece_schema).validate(piece)
            Draft202012Validator(manifest_schema).validate(manifest)


if __name__ == "__main__":
    unittest.main()
