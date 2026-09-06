"""Restartable per-page text/OCR and rendering. Cache contains no API credentials."""
from __future__ import annotations

import importlib.metadata
import shutil
import hashlib
from pathlib import Path

try:
    from .case_memory import checkpoint, identity
except ImportError:
    from case_memory import checkpoint, identity


def dependency_versions() -> dict:
    result = {}
    for name in ("pypdf", "PyPDF2", "pdf2image", "pytesseract", "Pillow"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def extract(path: Path, cache: Path, use_ocr: bool, language: str, dpi: int) -> tuple:
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return [], ["PDF sem extrator disponível; instale pypdf."], []
    reader = PdfReader(str(path))
    texts, warnings, ocr_pages = [], [], []
    for number, page in enumerate(reader.pages, 1):
        key = identity(number, dependency_versions())
        try:
            text = checkpoint(cache, "native", key, lambda page=page: page.extract_text() or "")
        except Exception as exc:
            text = ""
            warnings.append(f"PDF p. {number}: extração falhou ({type(exc).__name__}); nova tentativa necessária.")
        if use_ocr and len(text.strip()) < 30:
            def recognise() -> str:
                from pdf2image import convert_from_path
                import pytesseract
                images = convert_from_path(str(path), dpi=dpi, first_page=number, last_page=number)
                result = pytesseract.image_to_string(images[0], lang=language) if images else ""
                if not result.strip():
                    raise ValueError("OCR vazio")
                return result
            try:
                ocr_text = checkpoint(cache, "ocr", identity(key, language, dpi), recognise)
                text = text + "\n\n[Camada OCR complementar]\n" + ocr_text if text.strip() and text.strip() != ocr_text.strip() else ocr_text
                ocr_pages.append(number)
            except Exception as exc:
                warnings.append(f"PDF p. {number}: OCR pendente ({type(exc).__name__}).")
        texts.append(text)
    return texts, warnings, ocr_pages


def render(path: Path, output: Path, cache: Path, dpi: int) -> tuple:
    try:
        from pdf2image import convert_from_path, pdfinfo_from_path
        from PIL import Image
    except ImportError:
        return {}, ["Renderização pendente: pdf2image/Pillow indisponíveis."]
    try:
        count = int(pdfinfo_from_path(str(path))["Pages"])
    except Exception as exc:
        return {}, [f"Renderização pendente: {type(exc).__name__}."]
    output.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    records, warnings = {}, []
    for number in range(1, count + 1):
        cached = cache / f"{identity(number, dpi, dependency_versions())}.png"
        target = output / f"page-{number:06d}.png"
        try:
            valid = False
            if cached.exists():
                try:
                    with Image.open(cached) as im:
                        im.verify()
                    valid = True
                except Exception:
                    pass
            if not valid:
                images = convert_from_path(str(path), dpi=dpi, first_page=number, last_page=number, fmt="png")
                if not images:
                    raise ValueError("Sem página renderizada")
                temporary = cached.with_suffix(".tmp.png")
                images[0].save(temporary, format="PNG")
                temporary.replace(cached)
            shutil.copy2(cached, target)
            records[number] = {"created": True, "validated": True, "path": str(target),
                               "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                               "relative_path": f"rendered_pages/{target.name}", "provider": "pdf2image/Poppler", "dpi": dpi}
        except Exception as exc:
            warnings.append(f"PDF p. {number}: renderização pendente ({type(exc).__name__}).")
    return records, warnings
