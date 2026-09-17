"""Build provider-specific packages without duplicating the legal-process core."""

from __future__ import annotations

import argparse
import zipfile
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = REPO_ROOT / "skills" / "legal-process-parser"


def is_ignored(path: Path) -> bool:
    relative = path.relative_to(REPO_ROOT)
    return any(
        part in {".git", "__pycache__", ".pytest_cache", "build", "dist", "outputs", ".ci-artifacts", ".cache"}
        or part.endswith(".egg-info")
        for part in relative.parts
    ) or path.suffix in {".pyc", ".zip", ".skill", ".whl"}


def core_files(include_tests: bool = False) -> list[Path]:
    files: list[Path] = []
    for path in sorted(CORE_ROOT.rglob("*")):
        if not path.is_file() or is_ignored(path):
            continue
        if not include_tests and "tests" in path.relative_to(CORE_ROOT).parts:
            continue
        files.append(path)
    return files


def add_file(archive: zipfile.ZipFile, source: Path, target: str) -> None:
    archive.write(source, target.replace("\\", "/"))


def write_zip(destination: Path, files: list[tuple[Path, str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(REPO_ROOT / "LICENSE", "LICENSE")
        for source, target in sorted(files, key=lambda item: item[1]):
            if target == "LICENSE":
                continue
            if target == "routing/task-router.json" and any(t == "scripts/legal_review.py" for _, t in files):
                import json
                router = json.loads(source.read_text(encoding="utf-8"))
                router["load_order"] = ["SKILL.md", "routing/task-router.json", "the_selected_task_reference", "the_user_corpus_or_generated_indexes"]
                router["platforms"] = {}
                archive.writestr(target, json.dumps(router, ensure_ascii=False, indent=2).replace("skills/legal-process-parser/", ""))
                continue
            if target in {"INSTRUCTIONS.md", "CLAUDE_INSTRUCTIONS.md", "SYSTEM_INSTRUCTIONS.md"}:
                content = source.read_text(encoding="utf-8").replace("skills/legal-process-parser/", "")
                archive.writestr(target, content)
                continue
            add_file(archive, source, target)


def files_under(directory: Path, prefix: str = "") -> list[tuple[Path, str]]:
    if not directory.exists():
        return []
    return [
        (path, f"{prefix}{path.relative_to(directory).as_posix()}")
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not is_ignored(path)
    ]


def core_at_root() -> list[tuple[Path, str]]:
    return [(path, path.relative_to(CORE_ROOT).as_posix()) for path in core_files()]


def repository_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--cached"], cwd=REPO_ROOT).decode("utf-8").split("\0")
    for path in sorted(REPO_ROOT / name for name in tracked if name):
        if path.is_file() and not is_ignored(path):
            relative = path.relative_to(REPO_ROOT).as_posix()
            files.append((path, f"auditor-processual/{relative}"))
    return files


def universal_context() -> list[tuple[Path, str]]:
    names = ("AI_ENTRYPOINT.md", "llms.txt", "routing/task-router.json")
    return [(REPO_ROOT / name, name) for name in names]


def build_packages(output: Path) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    generic = [(path, f"legal-process-parser/{path.relative_to(CORE_ROOT).as_posix()}") for path in core_files()]
    generic.append((REPO_ROOT / "LICENSE", "legal-process-parser/LICENSE"))
    generic_destination = output / "legal-process-parser.zip"
    write_zip(generic_destination, generic)
    created.append(generic_destination)

    plugin_destination = output / "auditor-processual-plugin.zip"
    write_zip(plugin_destination, repository_files())
    created.append(plugin_destination)

    chatgpt_files = core_at_root() + [
        (REPO_ROOT / "adapters/chatgpt/INSTRUCTIONS.md", "INSTRUCTIONS.md"),
        (REPO_ROOT / "routing/task-router.json", "routing/task-router.json"),
    ]
    for filename in ("legal-process-parser-chatgpt.skill", "legal-process-parser-chatgpt.zip"):
        destination = output / filename
        write_zip(destination, chatgpt_files)
        created.append(destination)

    claude_files = core_at_root() + [
        (REPO_ROOT / "adapters/claude/CLAUDE_INSTRUCTIONS.md", "CLAUDE_INSTRUCTIONS.md"),
        (REPO_ROOT / "routing/task-router.json", "routing/task-router.json"),
    ]
    claude_destination = output / "auditor-processual-claude.zip"
    write_zip(claude_destination, claude_files)
    created.append(claude_destination)

    manus_files = universal_context() + [
        (REPO_ROOT / "SKILL.md", "SKILL.md"),
        *files_under(REPO_ROOT / "adapters/manus", "adapters/manus/"),
        *[(p, "skills/legal-process-parser/" + p.relative_to(CORE_ROOT).as_posix()) for p in core_files()],
    ]
    for filename in ("auditor-processual-manus.skill", "auditor-processual-manus.zip"):
        destination = output / filename
        write_zip(destination, manus_files)
        created.append(destination)

    gemini_files = universal_context() + [
        (REPO_ROOT / "gemini-extension.json", "gemini-extension.json"),
        (REPO_ROOT / "GEMINI.md", "GEMINI.md"),
        *files_under(REPO_ROOT / "adapters/gemini", "adapters/gemini/"),
        *[(p, "skills/legal-process-parser/" + p.relative_to(CORE_ROOT).as_posix()) for p in core_files()],
    ]
    gemini_destination = output / "auditor-processual-gemini-cli.zip"
    write_zip(gemini_destination, gemini_files)
    created.append(gemini_destination)
    gem_instructions = output / "auditor-processual-gemini-gem.md"
    gem_instructions.write_text(
        (REPO_ROOT / "adapters/gemini/GEM_INSTRUCTIONS.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    created.append(gem_instructions)

    # Executable tools must carry their complete import graph, not four selected modules.
    grok_files = core_at_root() + [
        (REPO_ROOT / "adapters/grok/SYSTEM_INSTRUCTIONS.md", "SYSTEM_INSTRUCTIONS.md"),
        (REPO_ROOT / "adapters/grok/README.md", "README.md"),
        (REPO_ROOT / "routing/task-router.json", "routing/task-router.json"),
    ]
    grok_destination = output / "auditor-processual-grok.zip"
    write_zip(grok_destination, grok_files)
    created.append(grok_destination)

    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera pacotes mínimos por plataforma.")
    parser.add_argument("--output", type=Path, default=REPO_ROOT.parent.parent / "outputs")
    args = parser.parse_args()
    created = build_packages(args.output.resolve())
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
