"""Select labor claim checklists and sector references without loading all guides."""
from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
POLOS = {"reclamante": ("claimant_theses",), "reclamada": ("defense_theses",), "ambos": ("claimant_theses", "defense_theses")}
STATUS_LABELS = {"localizado_no_texto_oficial": "texto oficial localizado", "revogado": "revogado", "vigente": "sem cancelamento conhecido",
                 "alterada": "alterada", "cancelada": "cancelada", "tese_firmada": "tese firmada",
                 "julgado_com_modulacao": "julgado com modulação", "merito_pendente": "mérito pendente"}

def catalog(name: str, field: str) -> dict:
    return {item["id"]: item for item in json.loads((CORE / "references" / name).read_text(encoding="utf-8"))[field]}

def claim_catalog() -> dict:
    return catalog("labor_claims.json", "claims")

def sector_catalog() -> dict:
    return catalog("labor_sectors.json", "sectors")

@lru_cache(maxsize=1)
def authority_catalog() -> dict:
    data = json.loads((CORE / "references" / "labor_authorities.json").read_text(encoding="utf-8"))
    return {"authorities": {a["id"]: a for a in data["authorities"]},
            "markers": {m["id"]: m for m in data["temporal_markers"]}, "policy": data["policy"]}

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

def claim_brief(identifiers: list[str], polo: str = "ambos") -> dict:
    """Selected claims with their candidate authorities resolved; still to be verified per response."""
    if polo not in POLOS:
        raise ValueError("Polo deve ser reclamante, reclamada ou ambos")
    refs = authority_catalog()
    claims = []
    for claim in select_claims(identifiers):
        row = {k: claim[k] for k in ("id", "label", "topic_id", "requirements", "typical_requests", "evidence",
                                     "calculation_profiles", "related_claims", "prescription") if k in claim}
        for field in POLOS[polo]:
            row[field] = [{**t, "authorities": [refs["authorities"][a] for a in t["authority_ids"]]} for t in claim.get(field, [])]
        row["temporal_markers"] = [refs["markers"][m] for m in claim.get("temporal_marker_ids", [])]
        claims.append(row)
    return {"claims": claims, "polo": polo, "policy": refs["policy"], "legal_status": "candidate_authorities_require_current_verification"}

def thesis_map_markdown(identifiers: list[str], polo: str = "ambos") -> str:
    """Candidate thesis map for the selected claims; a research plan, not a conclusion."""
    try:
        from .legal_index import safe_text
    except ImportError:
        from legal_index import safe_text
    brief = claim_brief(identifiers, polo)
    lines = ["# MAPA DE TESES CANDIDATAS", "",
             "Teses e autoridades do catálogo são candidatas: conferir dispositivo, redação do período e situação na consulta da própria resposta.", ""]
    titles = {"claimant_theses": "Teses do trabalhador", "defense_theses": "Teses da defesa"}
    for claim in brief["claims"]:
        lines += ["## " + safe_text(claim["label"]) + " (`" + claim["id"] + "`)", "",
                  "Requisitos a examinar: " + ", ".join(claim["requirements"]) + ".", ""]
        for field in POLOS[polo]:
            lines += ["### " + titles[field], ""]
            for thesis in claim.get(field, []):
                cites = "; ".join(f"[{safe_text(a['label'])}]({a['official_url']}) — {STATUS_LABELS.get(a['status'], a['status'])} "
                                  f"(catálogo {a['verified']['on']})" for a in thesis["authorities"])
                lines.append("- " + safe_text(thesis["label"]) + (" · " + cites if cites else " · pesquisar fonte própria"))
            lines.append("")
        if claim["temporal_markers"]:
            lines += ["Marcos temporais: " + "; ".join(f"{m['date']} — {safe_text(m['effect'])}" for m in claim["temporal_markers"]), ""]
        if claim.get("typical_requests"):
            lines += ["Pedidos típicos: " + "; ".join(safe_text(r) for r in claim["typical_requests"]) + ".", ""]
        if claim.get("evidence"):
            lines += ["Prova típica: " + "; ".join(safe_text(e) for e in claim["evidence"]) + ".", ""]
    return "\n".join(lines).rstrip() + "\n"

def index_markdown() -> str:
    """Lightweight selection index; the full entry is loaded only for chosen claims."""
    lines = ["# Índice das pretensões trabalhistas", "",
             "Selecionar pelos fatos e abrir somente as entradas escolhidas em `labor_claims.json`",
             "(com código: `labor_catalog.py --claim ID --brief`). Teses e autoridades são candidatas.", "",
             "| ID | Pretensão | Tema | Teses (trab./defesa) |", "|---|---|---|---|"]
    for claim in claim_catalog().values():
        lines.append(f"| `{claim['id']}` | {claim['label']} | {claim['topic_id']} | "
                     f"{len(claim.get('claimant_theses', []))}/{len(claim.get('defense_theses', []))} |")
    return "\n".join(lines) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description="Pautas de pesquisa por pretensão e setor, não confirmação de direito")
    parser.add_argument("--claim", action="append", default=[])
    parser.add_argument("--sector", action="append", default=[])
    parser.add_argument("--brief", action="store_true", help="Resolve teses e autoridades candidatas das pretensões")
    parser.add_argument("--polo", default="ambos", choices=sorted(POLOS))
    parser.add_argument("--markdown", action="store_true", help="Mapa de teses candidatas em Markdown")
    args = parser.parse_args()
    try:
        if args.markdown:
            print(thesis_map_markdown(args.claim, args.polo))
            return 0
        if args.brief:
            result = dict(claim_brief(args.claim, args.polo), sectors=select_sectors(args.sector))
        else:
            result = {"claims": select_claims(args.claim), "sectors": select_sectors(args.sector),
                      "legal_status": "research_checklists_only"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
