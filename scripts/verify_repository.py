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
    labor_path = ROOT / router["labor_topics"]
    topics = json.loads(labor_path.read_text(encoding="utf-8"))["topics"]
    assert len({item["id"] for item in topics}) == len(topics), "duplicate labor topic"
    module_ids = {module["id"] for module in modules}
    for topic in topics:
        assert topic["specialization_id"] in module_ids, topic["specialization_id"]
        assert (labor_path.parent / topic["reference"]).is_file(), topic["reference"]
        assert len(set(topic["checks"])) == len(topic["checks"]), "duplicate labor check"
    claims = json.loads((ROOT / router["labor_claims"]).read_text(encoding="utf-8"))["claims"]
    sectors = json.loads((ROOT / router["labor_sectors"]).read_text(encoding="utf-8"))["sectors"]
    assert len({c["id"] for c in claims}) == len(claims), "duplicate claim"
    assert len({s["id"] for s in sectors}) == len(sectors), "duplicate sector"
    for claim in claims:
        assert claim["topic_id"] in {t["id"] for t in topics}
        assert len(set(claim["requirements"])) == len(claim["requirements"])
        if claim.get("reference"):
            assert (labor_path.parent / claim["reference"]).is_file(), claim["reference"]
    assert len(claims) == 44
    profiles = json.loads((labor_path.parent / "labor_parameter_profiles.json").read_text(encoding="utf-8"))["profiles"]
    assert len(profiles) == len({p["id"] for p in profiles}) == 8
    for profile in profiles:
        assert (labor_path.parent / profile["reference"]).is_file()
        assert profile["source_requirements"] and profile["expression"]
    assert (labor_path.parent / "local_response_workflow.md").is_file()
    for task in ("analyze", "petition", "audit", "evidence", "deadlines"):
        assert "response_research" in router["tasks"][task]["automatic_triggers"]
    for sector in sectors:
        assert (labor_path.parent / sector["reference"]).is_file(), sector["reference"]
        assert set(sector["claim_ids"]) <= {c["id"] for c in claims}
    scenario_suite = json.loads((ROOT / "evaluation/labor_workflow_cases.json").read_text(encoding="utf-8"))
    assert len(scenario_suite["scenarios"]) == 40 and len(scenario_suite["integral_cases"]) == 10
    assert len({c["id"] for c in scenario_suite["scenarios"]}) == 40
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
