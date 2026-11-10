"""Validate local Markdown/assets links in a generated process bundle."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote


LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")


def markdown_anchors(text: str) -> set[str]:
    anchors = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', text))
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")
        count = counts.get(slug, 0)
        anchors.add(slug + (f"-{count}" if count else ""))
        counts[slug] = count + 1
    return anchors


def validate_links(root: Path) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    for markdown_path in sorted(root.rglob("*.md")):
        try:
            text = markdown_path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            errors.append(f"{markdown_path.relative_to(root)}: leitura falhou ({exc})")
            continue
        for target in LINK_RE.findall(text):
            target = target.strip()
            if target.startswith("<") and ">" in target:
                target = target[1:target.index(">")]
            if not target or target.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            path_part, _, fragment = target.partition("#")
            path_part = unquote(path_part.strip())
            candidate = (markdown_path.parent / path_part.replace("\\", "/")).resolve() if path_part else markdown_path.resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{markdown_path.relative_to(root)}: link fora do pacote: {target}")
                continue
            if not candidate.exists():
                errors.append(f"{markdown_path.relative_to(root)}: asset ausente: {target}")
            elif fragment and candidate.suffix.lower() == ".md":
                try:
                    if candidate not in anchor_cache:
                        anchor_cache[candidate] = markdown_anchors(candidate.read_text(encoding="utf-8-sig"))
                    anchors = anchor_cache[candidate]
                    if unquote(fragment) not in anchors:
                        errors.append(f"{markdown_path.relative_to(root)}: âncora ausente: {target}")
                except (OSError, UnicodeError) as exc:
                    errors.append(f"{markdown_path.relative_to(root)}: destino ilegível: {exc}")

    image_index_path = root / "images" / "index.json"
    if image_index_path.is_file():
        try:
            index = json.loads(image_index_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"images/index.json inválido: {exc}")
        else:
            for item in index.get("unique_images", []):
                for field in ("relative_path", "zoom_relative_path"):
                    relative = item.get(field)
                    if not relative:
                        continue
                    candidate = (root / str(relative)).resolve()
                    try:
                        candidate.relative_to(root.resolve())
                    except ValueError:
                        errors.append(f"images/index.json: caminho fora do pacote: {relative}")
                        continue
                    if not candidate.exists():
                        errors.append(f"images/index.json: asset ausente: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida links Markdown e assets locais do pacote processual.")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    errors = validate_links(args.root.resolve())
    if errors:
        print("\n".join(f"ERRO: {error}" for error in errors))
        return 1
    print("OK: links Markdown e assets locais válidos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
