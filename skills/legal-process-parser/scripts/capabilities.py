"""Read-only diagnostics: report installed resources without reading credentials."""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil


def inspect_capabilities() -> dict:
    modules = {name: importlib.util.find_spec(name) is not None for name in ("pypdf", "pdf2image", "pytesseract", "PIL", "docx", "jsonschema")}
    binaries = {name: shutil.which(name) is not None for name in ("pdftoppm", "pdfinfo", "tesseract")}
    return {"python_execution": True, "modules": modules, "binaries": binaries,
            "pdf_text": modules["pypdf"], "render": modules["pdf2image"] and binaries["pdftoppm"] and binaries["pdfinfo"],
            "ocr": modules["pytesseract"] and binaries["tesseract"] and binaries["pdftoppm"],
            "host_vision": "must_be_observed_in_current_session", "host_browsing": "must_be_observed_in_current_session",
            "persistent_memory": "requires_access_to_output_directory", "cross_platform_calls": False}


def main() -> int:
    argparse.ArgumentParser(description="Diagnostica recursos locais sem acessar chaves ou autos.").parse_args()
    print(json.dumps(inspect_capabilities(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
