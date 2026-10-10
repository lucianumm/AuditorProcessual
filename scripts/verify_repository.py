"""Check skill metadata, routing and JSON schemas on Windows and Linux."""
from __future__ import annotations

import json
import re
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def verify() -> None:
    skill_path = ROOT / "skills" / "legal-process-parser" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+)\n---\n", text)
    assert match and len(match.group(1)) <= 64 and match.group(2).strip(), "invalid SKILL.md frontmatter"
    router = json.loads((ROOT / "routing" / "task-router.json").read_text(encoding="utf-8"))
    assert set(router["tasks"]) == {"ingest", "analyze", "petition", "deadlines", "evidence", "audit"}
    for task in router["tasks"].values():
        cost = 0
        for reference in task["references"]:
            assert (ROOT / reference).is_file(), f"missing task reference: {reference}"
            cost += len((ROOT / reference).read_text(encoding="utf-8-sig"))
        assert cost <= router["context_budget"]["mandatory_reference_max_chars"], f"mandatory instructions too large: {cost}"
    for item in router.get("conditional_references", []):
        for reference in item["references"]:
            assert (ROOT / reference).is_file(), f"missing conditional reference: {reference}"
    modules_path = ROOT / router["specializations"]
    modules = json.loads(modules_path.read_text(encoding="utf-8"))["modules"]
    assert len({m["id"] for m in modules}) == len(modules), "duplicate specialization"
    for module in modules:
        assert (modules_path.parent / module["reference"]).is_file(), module["reference"]
    for name in ("AI_ENTRYPOINT.md", "llms.txt"):
        assert (ROOT / name).is_file(), name
    schema_dir = skill_path.parent / "schemas"
    for path in schema_dir.glob("*.json"):
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    for directory in (ROOT / "scripts", skill_path.parent / "scripts"):
        for path in directory.glob("*.py"):
            ast.parse(path.read_text(encoding="utf-8-sig"),filename=str(path))
    version = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
    for path in (ROOT / "gemini-extension.json", ROOT / ".codex-plugin/plugin.json"):
        assert json.loads(path.read_text(encoding="utf-8"))["version"] == version, f"version mismatch: {path.name}"
    print("Skill metadata, selective routing, schema contracts, Python syntax and versions valid")


if __name__ == "__main__":
    verify()
