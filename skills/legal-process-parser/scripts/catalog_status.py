"""Freshness of catalogued authorities and the backlog of pending official checks.

The catalogue records when each authority was last checked (``verified.on``).
This module applies a time-to-live per kind of source: past it, the entry is
only a research pointer and the response cycle must consult the official
source again before using it. Freshness never upgrades an unchecked entry.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
CATALOGS = {"labor": CORE / "references" / "labor_authorities.json",
            "domain": CORE / "references" / "domain_authorities.json"}
PENDING = "pendente_conferencia_oficial"
# Days a check stays usable as a pointer; the response cycle still consults the source.
TTL_DAYS = {"pending_merit": 15, "precedent": 90, "recent_statute": 60, "stable": 180, "treaty": 365}
PRECEDENT_KINDS = {"sumula_stj", "sumula_tst", "sumula_vinculante", "sumula_tnu", "sumula_tse", "sumula_carf", "sumula_tcu",
                   "oj_tst", "sdi1_tst", "tema_stf", "tema_stj", "irr_tst"}
CONTROL_KINDS = {"adi", "adc", "adpf"}
SETTLED = {"tese_firmada", "julgado_com_modulacao", "cancelada", "sem_vigencia", "revogado"}
RISK = {"sumula_vinculante": 5, "tema_stf": 5, "adi": 5, "adc": 5, "adpf": 5, "tema_stj": 4, "irr_tst": 4,
        "sumula_stj": 3, "sumula_tst": 3, "oj_tst": 3, "sdi1_tst": 3, "constitution": 3, "constitutional_amendment": 3}


def ttl_class(authority: dict) -> str:
    kind, status = authority.get("kind", ""), authority.get("status", "")
    if kind in CONTROL_KINDS or kind in {"tema_stf", "tema_stj", "irr_tst"} and status not in SETTLED:
        return "pending_merit"
    if kind in PRECEDENT_KINDS:
        return "precedent"
    if kind == "ilo_convention":
        return "treaty"
    if status == "alterada" or authority.get("recent_wording_markers"):
        return "recent_statute"
    return "stable"


def freshness(authority: dict, today: date | None = None) -> dict:
    today = today or date.today()
    verified = authority.get("verified", {})
    klass = ttl_class(authority)
    days = TTL_DAYS[klass]
    row = {"id": authority.get("id"), "kind": authority.get("kind"), "status": authority.get("status"),
           "ttl_class": klass, "ttl_days": days, "verified_on": verified.get("on"), "method": verified.get("method")}
    if authority.get("status") == PENDING or verified.get("method") == "curated_pending_official_check":
        return dict(row, state="never_verified", expires_on=None,
                    action="Conferir no portal oficial antes de qualquer uso; o catálogo é só ponto de pesquisa.")
    try:
        checked = date.fromisoformat(str(verified.get("on")))
    except ValueError:
        return dict(row, state="never_verified", expires_on=None, action="Data de conferência ausente ou inválida.")
    expires = checked + timedelta(days=days)
    expired = today > expires
    return dict(row, state="expired" if expired else "fresh", expires_on=expires.isoformat(),
                action=("Conferência vencida: nova consulta oficial obrigatória antes do uso." if expired else
                        "Dentro da validade como ponto de pesquisa; a resposta ainda exige consulta atual."))


def load(name: str) -> list[dict]:
    return json.loads(CATALOGS[name].read_text(encoding="utf-8"))["authorities"]


def usage() -> dict[str, int]:
    """How many catalogued theses or markers cite each authority."""
    counts: dict[str, int] = {}
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "authority_ids" and isinstance(item, list):
                    for aid in item:
                        counts[aid] = counts.get(aid, 0) + 1
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    paths = [CORE / "references" / "labor_claims.json", *sorted((CORE / "references" / "domain_catalogs").glob("*.json"))]
    for path in paths:
        if path.is_file():
            walk(json.loads(path.read_text(encoding="utf-8")))
    return counts


def report(today: date | None = None, *, pending_only: bool = False, by_usage: bool = False, limit: int | None = None) -> dict:
    today = today or date.today()
    uses = usage() if by_usage else {}
    summary, rows = {}, []
    for name in CATALOGS:
        authorities = load(name)
        states = [freshness(a, today) for a in authorities]
        summary[name] = {"total": len(states), **{s: sum(1 for r in states if r["state"] == s)
                                                  for s in ("fresh", "expired", "never_verified")}}
        summary[name]["pending_share"] = round(summary[name]["never_verified"] / max(1, len(states)), 4)
        for row in states:
            if pending_only and row["state"] == "fresh":
                continue
            row = dict(row, catalog=name)
            if by_usage:
                row.update(usage=uses.get(row["id"], 0), risk=RISK.get(row["kind"], 1))
            rows.append(row)
    if by_usage:
        rows.sort(key=lambda r: (-r["usage"] * r["risk"], -r["risk"], r["id"]))
    return {"checked_on": today.isoformat(), "summary": summary, "ttl_days": TTL_DAYS,
            "authorities": rows[:limit] if limit else rows,
            "meaning": "Validade da conferência como ponto de pesquisa; nunca substitui a consulta oficial da resposta."}


def annotate(authorities: list[dict], today: date | None = None) -> list[dict]:
    """Copies of catalogue entries with their freshness, for briefs shown to the model."""
    return [{**a, "freshness": freshness(a, today)} for a in authorities]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validade das conferências do catálogo e fila de autoridades pendentes")
    parser.add_argument("--pending", action="store_true", help="só vencidas ou nunca conferidas")
    parser.add_argument("--by-usage", action="store_true", help="ordenar por uso nas pretensões × risco do tipo")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--today", help="data de referência AAAA-MM-DD")
    parser.add_argument("--id", help="validade de uma autoridade")
    args = parser.parse_args()
    today = date.fromisoformat(args.today) if args.today else None
    if args.id:
        for name in CATALOGS:
            match = [a for a in load(name) if a["id"] == args.id]
            if match:
                print(json.dumps(dict(freshness(match[0], today), catalog=name), ensure_ascii=False, indent=2))
                return 0
        print(json.dumps({"error": "Autoridade não catalogada: " + args.id}, ensure_ascii=False))
        return 1
    print(json.dumps(report(today, pending_only=args.pending, by_usage=args.by_usage, limit=args.limit), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
