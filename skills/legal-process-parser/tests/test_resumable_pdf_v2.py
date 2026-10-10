from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts import resumable_pdf  # noqa: E402


class ResumablePdfTests(unittest.TestCase):
    def test_text_checkpoint_is_bound_to_pdf_bytes_and_corrupt_cache_is_retried(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.pdf"
            cache = root / "cache"
            calls: list[str] = []

            class Page:
                def __init__(self, text: str) -> None:
                    self.text = text

                def extract_text(self) -> str:
                    calls.append(self.text)
                    return self.text

            def reader(name: str) -> object:
                return types.SimpleNamespace(pages=[Page(Path(name).read_text(encoding="utf-8"))])

            with patch("pypdf.PdfReader", side_effect=reader):
                source.write_text("Primeiro texto", encoding="utf-8")
                self.assertEqual(resumable_pdf.extract(source, cache, False, "por", 200)[0], ["Primeiro texto"])
                self.assertEqual(resumable_pdf.extract(source, cache, False, "por", 200)[0], ["Primeiro texto"])
                self.assertEqual(calls, ["Primeiro texto"])

                source.write_text("Segundo texto", encoding="utf-8")
                self.assertEqual(resumable_pdf.extract(source, cache, False, "por", 200)[0], ["Segundo texto"])
                self.assertEqual(calls, ["Primeiro texto", "Segundo texto"])

                for checkpoint in (cache / "native").glob("*.json"):
                    checkpoint.write_text("corrupt", encoding="utf-8")
                self.assertEqual(resumable_pdf.extract(source, cache, False, "por", 200)[0], ["Segundo texto"])
                self.assertEqual(calls[-1], "Segundo texto")
                self.assertEqual(len(calls), 3)

    def test_failed_ocr_preserves_native_text_and_retry_adds_separate_layer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.pdf"
            source.write_bytes(b"a-pdf-fixture")
            cache = root / "cache"

            fake_reader = lambda _name: types.SimpleNamespace(pages=[types.SimpleNamespace(extract_text=lambda: "Ato")])
            fake_pdf2image = types.ModuleType("pdf2image")
            fake_pdf2image.convert_from_path = lambda *_args, **_kwargs: [object()]
            fake_ocr = types.ModuleType("pytesseract")
            attempts = [RuntimeError("OCR interrompido"), "Ato processual completo com detalhes relevantes"]

            def recognise(*_args: object, **_kwargs: object) -> str:
                result = attempts.pop(0)
                if isinstance(result, Exception):
                    raise result
                return result

            fake_ocr.image_to_string = recognise
            with patch("pypdf.PdfReader", side_effect=fake_reader), patch.dict(
                sys.modules, {"pdf2image": fake_pdf2image, "pytesseract": fake_ocr}
            ):
                texts, warnings, ocr_pages = resumable_pdf.extract(source, cache, True, "por", 200)
                self.assertEqual(texts, ["Ato"])
                self.assertEqual(ocr_pages, [])
                self.assertIn("OCR pendente", warnings[0])

                texts, warnings, ocr_pages = resumable_pdf.extract(source, cache, True, "por", 200)
                self.assertFalse(warnings)
                self.assertEqual(ocr_pages, [1])
                self.assertIn("Ato\n\n[Camada OCR complementar]\nAto processual", texts[0])

    def test_render_resumes_failed_page_and_repairs_corrupt_image(self) -> None:
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow não instalado")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.pdf"
            source.write_bytes(b"pdf-one")
            output = root / "pages"
            cache = root / "cache"
            calls: list[int] = []
            fail_second = [True]

            def convert(_source: str, *, first_page: int, **_kwargs: object) -> list:
                calls.append(first_page)
                if first_page == 2 and fail_second[0]:
                    fail_second[0] = False
                    raise RuntimeError("Interrupção simulada")
                return [Image.new("RGB", (2, 2), "red" if first_page == 1 else "blue")]

            fake_pdf2image = types.ModuleType("pdf2image")
            fake_pdf2image.pdfinfo_from_path = lambda _source: {"Pages": 2}
            fake_pdf2image.convert_from_path = convert
            with patch.dict(sys.modules, {"pdf2image": fake_pdf2image}):
                records, warnings = resumable_pdf.render(source, output, cache, 100)
                self.assertEqual(set(records), {1})
                self.assertIn("PDF p. 2: renderização pendente", warnings[0])

                records, warnings = resumable_pdf.render(source, output, cache, 100)
                self.assertFalse(warnings)
                self.assertEqual(set(records), {1, 2})
                self.assertEqual(calls, [1, 2, 2])

                cached_first = next(p for p in cache.glob("*.png") if p.read_bytes() == (output / "page-000001.png").read_bytes())
                cached_first.write_bytes(b"invalid-image")
                records, warnings = resumable_pdf.render(source, output, cache, 100)
                self.assertFalse(warnings)
                self.assertEqual(set(records), {1, 2})
                self.assertEqual(calls, [1, 2, 2, 1])
                self.assertFalse(list(output.glob(".page-*")))
                self.assertFalse(list(cache.glob(".render-*")))

                prior = (output / "page-000001.png").read_bytes()

                def interrupted_copy(input_file: object, output_file: object) -> None:
                    output_file.write(input_file.read(8))
                    raise OSError("Cópia interrompida")

                with patch.object(resumable_pdf.shutil, "copyfileobj", side_effect=interrupted_copy):
                    records, warnings = resumable_pdf.render(source, output, cache, 100)
                self.assertFalse(records)
                self.assertEqual(len(warnings), 2)
                self.assertEqual((output / "page-000001.png").read_bytes(), prior)
                self.assertFalse(list(output.glob(".page-*")))


if __name__ == "__main__":
    unittest.main()
