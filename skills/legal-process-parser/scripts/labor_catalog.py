"""Select labor claim checklists and sector references without loading all guides."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]

def catalog(name: str, field: str) -> dict:
    return {item["id"]: item for item in json.loads((CORE / "references" / name).read_text(encoding="utf-8"))[field]}

def claim_catalog() -> dict:
    return catalog("labor_claims.json", "claims")

def sector_catalog() -> dict:
    return catalog("labor_sectors.json", "sectors")

def select_claims(identifiers: list[str]) -> list[dict]:
    known = claim_catalog()
    if set(identifiers) - set(known):
        raise ValueError("Pretensão trabalhista desconhecida")
    return [known[key] for key in dict.fromkeys(identifiers)]

def select_sectors(identifiers: list[str]) -> list[dict]:
    known = sector_catalog()
    if set(identifiers) - set(known):
        raise ValueError("Setor trabalhista desconhecido")
    return [known[key] for key in dict.fromkeys(identifiers)]

def main() -> int:
    parser = argparse.ArgumentParser(description="Pautas de pesquisa por pretensão e setor, não confirmação de direito")
    parser.add_argument("--claim", action="append", default=[])
    parser.add_argument("--sector", action="append", default=[])
    args = parser.parse_args()
    try:
        print(json.dumps({"claims": select_claims(args.claim), "sectors": select_sectors(args.sector),
                          "legal_status": "research_checklists_only"}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
