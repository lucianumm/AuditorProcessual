"""Localiza pretensões candidatas nos catálogos trabalhista e dos demais ramos a partir de palavras dos fatos.

A busca compara termos sem acento com rótulos, requisitos, teses, pedidos típicos e prova típica,
e devolve apenas pontos de partida: cabimento, vigência e incidência continuam a depender da
leitura dos autos e da consulta oficial da resposta.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from functools import lru_cache

try:
    from .domain_catalog import catalogs as domain_catalogs
    from .labor_catalog import claim_catalog as labor_claims
except ImportError:
    from domain_catalog import catalogs as domain_catalogs
    from labor_catalog import claim_catalog as labor_claims

STOPWORDS = set("""a o e de da do das dos em no na nos nas um uma uns umas para por com sem ao aos as os que se sua seu
suas seus ou ate apos sobre entre pela pelo pelas pelos mais menos como quando sob nao sim foi ser ter tem ha""".split())
FIELD_WEIGHTS = {"label": 3.0, "requirements": 1.5, "theses": 1.0, "typical_requests": 1.0, "evidence": 0.6}
PREFIX = 5


def fold(text: str) -> str:
    plain = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", plain.lower()).strip()


def terms(text: str) -> list[str]:
    """Radicais simples: prefixo de cinco letras, sem palavras vazias; números ficam inteiros."""
    out = []
    for word in fold(text).split():
        if word in STOPWORDS or (len(word) < 3 and not word.isdigit()):
            continue
        out.append(word if word.isdigit() else word[:PREFIX])
    return out


def _claim_fields(claim: dict) -> dict[str, str]:
    return {
        "label": claim["label"],
        "requirements": " ".join(r.replace("_", " ") for r in claim.get("requirements", [])),
        "theses": " ".join(t["label"] for t in claim.get("claimant_theses", []) + claim.get("defense_theses", [])),
        "typical_requests": " ".join(claim.get("typical_requests", [])),
        "evidence": " ".join(claim.get("evidence", [])),
    }


@lru_cache(maxsize=1)
def search_index() -> list[dict]:
    rows = []
    for claim in labor_claims().values():
        rows.append({"id": claim["id"], "catalog": "trabalhista", "domain": "trabalhista", "label": claim["label"],
                     "fields": {k: set(terms(v)) for k, v in _claim_fields(claim).items()},
                     "open": f"labor_catalog.py --claim {claim['id']} --markdown"})
    for key, catalog in domain_catalogs().items():
        for claim in catalog["claims"]:
            rows.append({"id": claim["id"], "catalog": "ramos", "domain": key, "label": claim["label"],
                         "fields": {k: set(terms(v)) for k, v in _claim_fields(claim).items()},
                         "open": f"domain_catalog.py --claim {claim['id']} --markdown"})
    return rows


def search(query: str, *, limit: int = 8, domain: str | None = None) -> dict:
    wanted = list(dict.fromkeys(terms(query)))
    if not wanted:
        raise ValueError("Consulta sem termos pesquisáveis")
    results = []
    for row in search_index():
        if domain and row["domain"] != domain:
            continue
        score, matched = 0.0, set()
        for term in wanted:
            hits = [FIELD_WEIGHTS[name] for name, bag in row["fields"].items() if term in bag]
            if hits:
                score += max(hits)
                matched.add(term)
        if matched:
            coverage = len(matched) / len(wanted)
            results.append({"id": row["id"], "domain": row["domain"], "label": row["label"],
                            "score": round(score * (0.5 + coverage), 2), "matched_terms": sorted(matched), "open": row["open"]})
    results.sort(key=lambda r: (-r["score"], r["id"]))
    return {"query": query, "terms": wanted, "results": results[:max(1, limit)],
            "legal_status": "candidate_claims_only",
            "note": "Lista de partida por semelhança de palavras; confirmar ramo, fatos e cabimento antes de abrir as pretensões."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca pretensões candidatas nos catálogos a partir de palavras dos fatos")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--domain", help="trabalhista ou chave do ramo (ex.: consumidor)")
    args = parser.parse_args()
    try:
        print(json.dumps(search(args.query, limit=args.limit, domain=args.domain), ensure_ascii=False, indent=2))
        return 0
    except ValueError as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
