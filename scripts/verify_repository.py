"""Check skill metadata, routing and JSON schemas on Windows and Linux."""
from __future__ import annotations

import json
import re
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
        for reference in task["references"]:
            assert (ROOT / reference).is_file(), f"missing task reference: {reference}"
    for name in ("AI_ENTRYPOINT.md", "llms.txt"):
        assert (ROOT / name).is_file(), name
    schema_dir = skill_path.parent / "schemas"
    for path in schema_dir.glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    print("Skill metadata, routing and schemas valid")


if __name__ == "__main__":
    verify()
