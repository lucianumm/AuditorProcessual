"""Pautas de pesquisa por ramo do direito fora do trabalhista: pretensões, teses dos dois polos e autoridades candidatas.

O catálogo localiza candidatos; não confirma cabimento, vigência nem incidência. Cada autoridade
registra como e quando foi conferida no catálogo; a resposta jurídica exige consulta nova.
"""
from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
REFS = CORE / "references"
CATALOG_DIR = REFS / "domain_catalogs"
AUTHORITIES = REFS / "domain_authorities.json"
POLOS = {"ativo": ("claimant_theses",), "passivo": ("defense_theses",), "ambos": ("claimant_theses", "defense_theses")}
STATUS_LABELS = {"localizado_no_texto_oficial": "texto oficial localizado", "revogado": "revogado", "vigente": "sem cancelamento na fonte oficial",
                 "alterada": "redação alterada", "cancelada": "cancelada", "tese_firmada": "tese firmada", "julgado_com_modulacao": "julgado com modulação",
                 "merito_pendente": "mérito pendente", "pendente_conferencia_oficial": "pendente de conferência no portal oficial",
                 "sem_vigencia": "sem vigência no portal oficial"}


@lru_cache(maxsize=1)
def catalogs() -> dict:
    return {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in sorted(CATALOG_DIR.glob("*.json"))}


@lru_cache(maxsize=1)
def authority_catalog() -> dict:
    data = json.loads(AUTHORITIES.read_text(encoding="utf-8"))
    return {"authorities": {a["id"]: a for a in data["authorities"]}, "markers": {m["id"]: m for m in data["temporal_markers"]}, "policy": data["policy"]}


def claim_catalog(domain: str | None = None) -> dict:
    rows = {}
    for key, catalog in catalogs().items():
        if domain and key != domain:
            continue
        for claim in catalog["claims"]:
            rows[claim["id"]] = {**claim, "domain": key}
    return rows


def select_claims(identifiers: list[str], domain: str | None = None) -> list[dict]:
    if domain and domain not in catalogs():
        raise ValueError("Ramo sem catálogo: " + domain)
    known = claim_catalog(domain)
    unknown = set(identifiers) - set(known)
    if unknown:
        raise ValueError("Pretensão desconhecida: " + ", ".join(sorted(unknown)))
    return [known[key] for key in dict.fromkeys(identifiers)]


def claim_brief(identifiers: list[str], polo: str = "ambos", domain: str | None = None) -> dict:
    if polo not in POLOS:
        raise ValueError("Polo deve ser ativo, passivo ou ambos")
    refs = authority_catalog()
    out = []
    for claim in select_claims(identifiers, domain):
        labels = catalogs()[claim["domain"]]["polo_labels"]
        row = {k: claim[k] for k in ("id", "domain", "label", "requirements", "typical_requests", "evidence", "piece_ids", "related_claims", "limitation")}
        for field in POLOS[polo]:
            row[field] = {"label": labels[field],
                          "theses": [{**t, "authorities": [refs["authorities"][a] for a in t["authority_ids"]]} for t in claim[field]]}
        row["temporal_markers"] = [refs["markers"][m] for m in claim["temporal_marker_ids"]]
        out.append(row)
    return {"claims": out, "polo": polo, "policy": refs["policy"], "legal_status": "candidate_authorities_require_current_verification"}


def thesis_map_markdown(identifiers: list[str], polo: str = "ambos", domain: str | None = None) -> str:
    try:
        from .legal_index import safe_text
    except ImportError:
        from legal_index import safe_text
    brief = claim_brief(identifiers, polo, domain)
    lines = ["# MAPA DE TESES CANDIDATAS", "",
             "Teses e autoridades do catálogo são candidatas: conferir dispositivo, redação do período e situação na consulta da própria resposta.", ""]
    for claim in brief["claims"]:
        lines += [f"## {safe_text(claim['label'])} (`{claim['id']}`, {claim['domain']})", "",
                  "Requisitos a examinar: " + ", ".join(claim["requirements"]) + ".", ""]
        for field in POLOS[polo]:
            lines += ["### " + safe_text(claim[field]["label"]), ""]
            for thesis in claim[field]["theses"]:
                cites = "; ".join(f"[{safe_text(a['label'])}]({a['official_url']}) — {STATUS_LABELS.get(a['status'], a['status'])} (catálogo {a['verified']['on']})"
                                  for a in thesis["authorities"])
                lines.append("- " + safe_text(thesis["label"]) + (" · " + cites if cites else " · pesquisar fonte própria"))
            lines.append("")
        if claim["temporal_markers"]:
            lines += ["Marcos temporais: " + "; ".join(f"{m['date']} — {safe_text(m['effect'])}" for m in claim["temporal_markers"]), ""]
        if claim["typical_requests"]:
            lines += ["Pedidos típicos: " + "; ".join(safe_text(r) for r in claim["typical_requests"]) + ".", ""]
        if claim["evidence"]:
            lines += ["Prova típica: " + "; ".join(safe_text(e) for e in claim["evidence"]) + ".", ""]
        lines += ["Peças candidatas: " + ", ".join(f"`{p}`" for p in claim["piece_ids"]) + ".", "", "Prazo: " + safe_text(claim["limitation"]) + ".", ""]
    return "\n".join(lines).rstrip() + "\n"


def _domain_table(key: str, catalog: dict, level: str = "##") -> list[str]:
    labels = catalog["polo_labels"]
    lines = [f"{level} {catalog['label']} (`{key}`)", "", f"Guia: `{catalog['guide']}` · catálogo: `domain_catalogs/{key}.json`", "",
             f"| ID | Pretensão | {labels['claimant_theses']} / {labels['defense_theses']} |", "|---|---|---|"]
    lines += [f"| `{c['id']}` | {c['label']} | {len(c['claimant_theses'])}/{len(c['defense_theses'])} |" for c in catalog["claims"]]
    return lines + [""]


def index_markdown() -> str:
    """Índice de todos os ramos: usar quando o ramo ainda não estiver confirmado."""
    lines = ["# Índice das pretensões por ramo (fora do trabalhista)", "",
             "Selecionar pelos fatos e abrir somente o catálogo do ramo confirmado em `domain_catalogs/`",
             "(com código: `domain_catalog.py --claim ID --markdown`). Teses e autoridades são candidatas.", ""]
    for key, catalog in catalogs().items():
        lines += _domain_table(key, catalog)
    return "\n".join(lines).rstrip() + "\n"


def domain_index_markdown(key: str) -> str:
    """Índice de um só ramo, carregado pelo roteador quando o ramo já foi identificado."""
    if key not in catalogs():
        raise ValueError("Ramo sem catálogo: " + key)
    lines = ["# Pretensões do catálogo", "", "Teses e autoridades são candidatas: abrir só as entradas escolhidas (`domain_catalog.py --claim ID --markdown`).", ""]
    return "\n".join(lines + _domain_table(key, catalogs()[key], "##")).rstrip() + "\n"


def index_files() -> dict[Path, str]:
    """Arquivos gerados que devem coincidir com o catálogo (conferidos por verify_repository.py)."""
    files = {REFS / "domain_claims_index.md": index_markdown()}
    files.update({CATALOG_DIR / f"{key}_index.md": domain_index_markdown(key) for key in catalogs()})
    return files


def integrity_errors() -> list[str]:
    """Vínculos internos: autoridades, marcos, pretensões relacionadas, peças, guias e perfis de domínio."""
    errors = []
    refs = authority_catalog()
    pieces = {e["id"]: e for e in json.loads((REFS / "procedural_catalog.json").read_text(encoding="utf-8"))["entries"]}
    profiles = {d["key"] for d in json.loads((REFS / "legal_domain_profiles.json").read_text(encoding="utf-8"))["domains"]}
    all_claims = claim_catalog()
    seen = set()
    for key, catalog in catalogs().items():
        if catalog["domain"] != key:
            errors.append(f"{key}: domínio diverge do nome do arquivo")
        if key not in profiles:
            errors.append(f"{key}: sem perfil em legal_domain_profiles.json")
        if not (REFS / catalog["guide"]).is_file():
            errors.append(f"{key}: guia ausente {catalog['guide']}")
        for claim in catalog["claims"]:
            if claim["id"] in seen:
                errors.append("pretensão duplicada: " + claim["id"])
            seen.add(claim["id"])
            for thesis in claim["claimant_theses"] + claim["defense_theses"]:
                errors += [f"{thesis['id']}: autoridade desconhecida {a}" for a in thesis["authority_ids"] if a not in refs["authorities"]]
            errors += [f"{claim['id']}: marco desconhecido {m}" for m in claim["temporal_marker_ids"] if m not in refs["markers"]]
            errors += [f"{claim['id']}: pretensão relacionada desconhecida {r}" for r in claim["related_claims"] if r not in all_claims]
            for piece in claim["piece_ids"]:
                entry = pieces.get(piece)
                if entry is None:
                    errors.append(f"{claim['id']}: peça desconhecida {piece}")
                elif key in entry.get("excluded_domains", []) or ("*" not in entry["domains"] and key not in entry["domains"]):
                    errors.append(f"{claim['id']}: peça {piece} não lista o ramo {key}")
    for marker in refs["markers"].values():
        errors += [f"marco {marker['id']}: autoridade desconhecida {a}" for a in marker["authority_ids"] if a not in refs["authorities"]]
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Pautas de pesquisa por ramo do direito; não confirmam direito, vigência ou cabimento")
    parser.add_argument("--domain")
    parser.add_argument("--claim", action="append", default=[])
    parser.add_argument("--polo", default="ambos", choices=sorted(POLOS))
    parser.add_argument("--brief", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--index", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            errors = integrity_errors()
            print(json.dumps({"errors": errors, "ok": not errors}, ensure_ascii=False, indent=2))
            return 1 if errors else 0
        if args.index:
            print(domain_index_markdown(args.domain) if args.domain else index_markdown(), end="")
            return 0
        if args.markdown:
            print(thesis_map_markdown(args.claim, args.polo, args.domain), end="")
            return 0
        if args.brief:
            print(json.dumps(claim_brief(args.claim, args.polo, args.domain), ensure_ascii=False, indent=2))
            return 0
        rows = list(claim_catalog(args.domain).values()) if not args.claim else select_claims(args.claim, args.domain)
        print(json.dumps({"claims": [{"id": c["id"], "domain": c["domain"], "label": c["label"]} for c in rows],
                          "legal_status": "research_checklists_only"}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
