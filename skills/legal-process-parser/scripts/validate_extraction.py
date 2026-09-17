from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from .validate_links import validate_links
except ImportError:  # direct execution
    from validate_links import validate_links  # type: ignore


def validate(output: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = output / "manifest.json"
    if not manifest_path.exists():
        return ["manifest.json não encontrado"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return [f"manifest.json inválido: {exc}"]
    coverage = manifest.get("coverage", {})
    total = coverage.get("pages_total", 0)
    processed = coverage.get("pages_processed", 0)
    pages_path = output / "processo_estruturado.md"
    page_headers = re.findall(r"^## \[Página PDF (\d+)\]", pages_path.read_text(encoding="utf-8-sig"), flags=re.M) if pages_path.exists() else []
    numbers = [int(item) for item in page_headers]
    if processed != len(numbers):
        errors.append(f"manifesto informa {processed} páginas, Markdown contém {len(numbers)}")
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append("sequência de páginas do Markdown não é contínua")
    if processed != total:
        errors.append(f"processamento incompleto: {processed}/{total} páginas")
    generated_files = manifest.get("generated_files")
    required_files = (
        [name for name in generated_files if isinstance(name, str) and not name.endswith("/")]
        if isinstance(generated_files, list)
        else [
            "index.jsonl",
            "indice_pecas.md",
            "cronologia.md",
            "matriz_controversias.md",
            "relatorio_auditoria.md",
            "image_inventory.json",
            "legal_basis.json",
            "base_legal.md",
            "quality_gate.json",
            "legal_narrative.json",
            "analise_juridica.md",
            "relatorio_processual.md",
            "andamento_processual.json",
            "relatorio_andamento.md",
            "pendencias_e_prazos.md",
            "matriz_documental.md",
            "mapa_provas.md",
            "checklist_manifestacao.md",
            "minuta_peca.md",
            "relatorio_conformidade.md",
        ]
    )
    for required in required_files:
        if not (output / required).exists():
            errors.append(f"arquivo ausente: {required}")
    if pages_path.exists():
        markdown = pages_path.read_text(encoding="utf-8-sig")
        if markdown.count("### Resumo sem") < processed:
            errors.append("Markdown sem resumo semântico para todas as páginas")
            visual_sections = markdown.count("### Imagens e elementos visuais") + markdown.count("### Imagens visuais relevantes")
            if visual_sections < processed:
                errors.append("Markdown sem seção visual para todas as páginas")
    procedural_path = output / "andamento_processual.json"
    if procedural_path.exists():
        try:
            procedural = json.loads(procedural_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            errors.append("andamento_processual.json inválido")
        else:
            for collection in ("events", "deadlines", "evidence", "pending_pages", "tasks"):
                if not isinstance(procedural.get(collection), list):
                    errors.append(f"andamento_processual.json sem lista {collection}")
    pages_jsonl = output / "pages.jsonl"
    if pages_jsonl.exists():
        page_records: list[dict] = []
        for line_number, line in enumerate(pages_jsonl.read_text(encoding="utf-8-sig").splitlines(), start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"pages.jsonl linha {line_number} inválida")
                continue
            page_records.append(record)
            for key in ("summary", "entities", "keywords", "content_blocks", "visuals"):
                if key not in record:
                    errors.append(f"pages.jsonl linha {line_number} sem campo {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida cobertura e artefatos sem interpretar o mérito jurídico.")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    errors = validate(args.output.resolve())
    if errors:
        print("\n".join(f"ERRO: {error}" for error in errors))
        return 1
    print("OK: cobertura, sequência e artefatos básicos válidos")
    return 0


_validate_legacy = validate


def validate(output: Path) -> list[str]:
    errors = _validate_legacy(output)
    manifest_path = output / "manifest.json"
    pages_path = output / "pages.jsonl"
    if not manifest_path.exists() or not pages_path.exists():
        return errors
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        records = [json.loads(line) for line in pages_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError):
        return errors
    for index, record in enumerate(records, start=1):
        if record.get("status") == "COMPLETE":
            render = record.get("render", {})
            vision = record.get("vision", {})
            if render.get("required") and not render.get("validated"):
                errors.append(f"pages.jsonl linha {index} marca COMPLETE sem renderização validada")
            if vision.get("required") and not vision.get("semantic_checked"):
                errors.append(f"pages.jsonl linha {index} marca COMPLETE sem visão semântica")
    if manifest.get("coverage", {}).get("full_conversion_complete") and any(record.get("status") != "COMPLETE" for record in records):
        errors.append("manifesto marca conversão integral com páginas não COMPLETE")
    quality_path = output / "quality_gate.json"
    if quality_path.exists():
        try:
            quality_gate = json.loads(quality_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            errors.append("quality_gate.json inválido")
        else:
            if quality_gate.get("status") == "passed" and quality_gate.get("blocking_gates"):
                errors.append("quality_gate.json marca passed com gates bloqueadores")
            if quality_gate.get("can_issue_final_legal_conclusion") and quality_gate.get("gates", {}).get("legal_verification", {}).get("status") != "passed":
                errors.append("quality_gate.json permite conclusão final sem verificação legal aprovada")
    matrix_path = output / "matriz_fato_prova_norma_pedido.json"
    if matrix_path.exists():
        try:
            matrix = json.loads(matrix_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            errors.append("matriz_fato_prova_norma_pedido.json inválida")
        else:
            rows = matrix.get("rows", [])
            if not isinstance(rows, list):
                errors.append("matriz fato-prova-norma-pedido sem lista rows")
            elif any(not row.get("fact", {}).get("source", {}).get("document_id") for row in rows):
                errors.append("matriz fato-prova-norma-pedido contém linha sem proveniência")
    narrative_path = output / "legal_narrative.json"
    if narrative_path.exists():
        try:
            narrative = json.loads(narrative_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            errors.append("legal_narrative.json inválido")
        else:
            paragraphs = narrative.get("paragraphs", [])
            if narrative.get("style") != "affirmative_legal_narrative":
                errors.append("legal_narrative.json sem estilo afirmativo legal")
            if not isinstance(paragraphs, list):
                errors.append("legal_narrative.json sem lista paragraphs")
            else:
                expected = manifest.get("coverage", {}).get("pages_processed")
                represented_pages = {item.get("page_pdf") for item in paragraphs if isinstance(item, dict)}
                if expected is not None and represented_pages != set(range(1, int(expected) + 1)):
                    errors.append("legal_narrative.json não representa todas as páginas processadas")
                for paragraph in paragraphs:
                    if not paragraph.get("text") or not paragraph.get("source", {}).get("document_id"):
                        errors.append("legal_narrative.json contém parágrafo sem texto ou proveniência")
                        break
            phrase_check = narrative.get("prohibited_phrase_check", {})
            if phrase_check.get("passed") is False and phrase_check.get("findings"):
                errors.append("legal_narrative.json contém formulação de estilo proibida")
            markdown_path = output / "analise_juridica.md"
            if markdown_path.exists() and not markdown_path.read_text(encoding="utf-8-sig").lstrip().startswith("# "):
                errors.append("analise_juridica.md sem título de narrativa jurídica")
    errors.extend(validate_links(output))
    return errors


if __name__ == "__main__":
    raise SystemExit(main())

