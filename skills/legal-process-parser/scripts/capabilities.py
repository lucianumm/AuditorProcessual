"""Read-only diagnostics: report installed resources without reading credentials."""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from urllib.request import Request, urlopen

PROBE_URL = "https://www.planalto.gov.br/ccivil_03/leis/l0605.htm"


def inspect_capabilities() -> dict:
    modules = {name: importlib.util.find_spec(name) is not None for name in ("pypdf", "pdf2image", "pytesseract", "PIL", "docx", "jsonschema")}
    binaries = {name: shutil.which(name) is not None for name in ("pdftoppm", "pdfinfo", "tesseract")}
    return {"python_execution": True, "modules": modules, "binaries": binaries,
            "pdf_text": modules["pypdf"], "render": modules["pdf2image"] and binaries["pdftoppm"] and binaries["pdfinfo"],
            "ocr": modules["pytesseract"] and binaries["tesseract"] and binaries["pdftoppm"],
            "host_vision": "must_be_observed_in_current_session", "host_browsing": "must_be_observed_in_current_session",
            "local_http": "not_tested", "official_source_methods": ["official_http_capture", "browser_observation", "source_unavailable"],
            "persistent_memory": "requires_access_to_output_directory", "cross_platform_calls": False}


def probe_local_http(url: str = PROBE_URL, *, timeout: int = 15) -> dict:
    """Observe outbound HTTPS to an official portal; no case content is sent."""
    try:
        from .research_sources import USER_AGENT
    except ImportError:
        from research_sources import USER_AGENT
    try:
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout) as response:
            status = getattr(response, "status", None)
            sample = response.read(2048)
        ok = status == 200 and bool(sample.strip())
        return {"local_http": ok, "status": status, "url": url,
                "meaning": "Captura local observada nesta execução." if ok else "Portal respondeu sem conteúdo utilizável."}
    except (OSError, ValueError) as error:
        return {"local_http": False, "status": None, "url": url, "reason": type(error).__name__,
                "meaning": "Sem captura local nesta execução; usar navegador da IA ou registrar limitação."}


def select_source_route(*, local_http: bool | None = None, host_browsing: bool | None = None, url: str | None = None) -> dict:
    """Choose a source route from observed capabilities, not installed packages.

    Passing None means the capability was not tested in this execution. This
    routine does not probe the network or infer host tools from Python modules.
    """
    tier = None
    if url:
        try:
            from .source_registry import access_tier
        except ImportError:
            from source_registry import access_tier
        tier = access_tier(url)
    if local_http is True and tier != "browser_only":
        return {"method": "official_http_capture", "status": "available", "reason": "Captura HTTPS local disponível nesta execução."}
    if host_browsing is True:
        return {"method": "browser_observation", "status": "available", "reason": "Consulta pelo navegador da IA observada nesta execução; registrar a referência real da ferramenta."}
    if tier == "browser_only":
        return {"method": "source_unavailable", "status": "unavailable",
                "reason": "Portal recusa clientes automatizados; usar navegador da IA ou arquivo oficial enviado e registrar a tentativa."}
    return {"method": "source_unavailable", "status": "unavailable", "reason": "Nenhuma via de consulta oficial foi observada nesta execução."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostica recursos locais sem acessar chaves ou autos.")
    parser.add_argument("--probe-http", action="store_true", help="Testa captura HTTPS em portal oficial (sem enviar autos)")
    args = parser.parse_args()
    result = inspect_capabilities()
    if args.probe_http:
        probe = probe_local_http()
        result.update(local_http=probe["local_http"], local_http_probe=probe)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
