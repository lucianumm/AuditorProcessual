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
            "local_http": "not_tested", "official_source_methods": ["official_http_capture", "browser_observation", "source_unavailable"],
            "persistent_memory": "requires_access_to_output_directory", "cross_platform_calls": False}


def select_source_route(*, local_http: bool | None = None, host_browsing: bool | None = None) -> dict:
    """Choose a source route from observed capabilities, not installed packages.

    Passing None means the capability was not tested in this execution. This
    routine does not probe the network or infer host tools from Python modules.
    """
    if local_http is True:
        return {"method": "official_http_capture", "status": "available", "reason": "Captura HTTPS local disponível nesta execução."}
    if host_browsing is True:
        return {"method": "browser_observation", "status": "available", "reason": "Consulta pelo navegador da IA observada nesta execução; registrar a referência real da ferramenta."}
    return {"method": "source_unavailable", "status": "unavailable", "reason": "Nenhuma via de consulta oficial foi observada nesta execução."}


def main() -> int:
    argparse.ArgumentParser(description="Diagnostica recursos locais sem acessar chaves ou autos.").parse_args()
    print(json.dumps(inspect_capabilities(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
