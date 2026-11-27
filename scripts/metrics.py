"""Fonte única das contagens citadas na documentação (pretensões, teses, autoridades, peças, MCP).

    python scripts/metrics.py            # regrava metrics.json
    python scripts/metrics.py --check    # falha se metrics.json ou os documentos divergirem

A checagem dos documentos procura frases "N pretensões" nos textos vigentes (não no
CHANGELOG, que é histórico) e exige que N seja uma contagem atual.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "skills" / "legal-process-parser"
DOCS = ["README.md", "SKILL.md", "AI_ENTRYPOINT.md", "llms.txt", "docs/TECHNICAL_GUIDE.md", "docs/RESPONSE_WORKFLOW.md",
        "skills/legal-process-parser/SKILL.md"]


def compute() -> dict:
    sys.path.insert(0, str(CORE))
    from scripts.domain_catalog import catalogs
    from scripts.mcp_server import TOOL_SPECS
    labor = json.loads((CORE / "references" / "labor_claims.json").read_text(encoding="utf-8"))["claims"]
    domains = catalogs()
    domain_claims = [c for d in domains.values() for c in d["claims"]]
    authorities = {name: json.loads((CORE / "references" / f"{name}_authorities.json").read_text(encoding="utf-8"))["authorities"]
                   for name in ("labor", "domain")}
    pending = {name: sum(1 for a in rows if a["status"] == "pendente_conferencia_oficial") for name, rows in authorities.items()}
    pieces = json.loads((CORE / "references" / "procedural_catalog.json").read_text(encoding="utf-8"))["entries"]
    theses = sum(len(c.get("claimant_theses", [])) + len(c.get("defense_theses", [])) for c in labor)
    theses += sum(len(c[f]) for c in domain_claims for f in ("claimant_theses", "defense_theses"))
    return {"labor_claims": len(labor), "domain_branches": len(domains), "domain_claims": len(domain_claims),
            "total_claims": len(labor) + len(domain_claims), "branches_total": len(domains) + 1, "theses": theses,
            "labor_authorities": len(authorities["labor"]), "domain_authorities": len(authorities["domain"]),
            "pending_labor_authorities": pending["labor"], "pending_domain_authorities": pending["domain"],
            "procedural_pieces": len(pieces), "mcp_tools": len(TOOL_SPECS)}


def doc_errors(metrics: dict) -> list[str]:
    per_branch = {len(d["claims"]) for d in __import__("scripts.domain_catalog", fromlist=["catalogs"]).catalogs().values()}
    allowed = {metrics["labor_claims"], metrics["domain_claims"], metrics["total_claims"]} | per_branch
    errors = []
    for name in DOCS:
        path = ROOT / name
        if not path.is_file():
            continue
        for match in re.finditer(r"\b(\d{1,3}(?:\.\d{3})*|\d+)\s+pretens(?:ões|oes)", path.read_text(encoding="utf-8")):
            value = int(match.group(1).replace(".", ""))
            if value not in allowed:
                errors.append(f"{name}: '{match.group(0)}' não corresponde às contagens atuais")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Contagens do projeto em fonte única")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    metrics = compute()
    path = ROOT / "metrics.json"
    text = json.dumps(metrics, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        errors = [] if path.is_file() and path.read_text(encoding="utf-8") == text else ["metrics.json desatualizado: rodar scripts/metrics.py"]
        errors += doc_errors(metrics)
        print(json.dumps({"metrics": metrics, "errors": errors}, ensure_ascii=False, indent=2))
        return 1 if errors else 0
    path.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
