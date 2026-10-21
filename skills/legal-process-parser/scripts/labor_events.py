"""Preserve dated or uncertain client events without inventing an exact anchor."""
from __future__ import annotations

import argparse
import calendar
import json
import re
from datetime import date
from pathlib import Path

try:
    from .case_memory import atomic_json, atomic_text, identity
    from .client_intake import load_accounts
    from .contracts import validate_contract
    from .artifact_tracking import track_artifacts
    from .legal_index import safe_text
except ImportError:
    from case_memory import atomic_json, atomic_text, identity
    from client_intake import load_accounts
    from contracts import validate_contract
    from artifact_tracking import track_artifacts
    from legal_index import safe_text


def date_bounds(value: dict) -> dict:
    precision, raw = value["precision"], value["value"]
    if precision == "unknown":
        if raw is not None or value["end"] is not None:
            raise ValueError("Data desconhecida não recebe marco inventado")
        return {"earliest": None, "latest": None, "exact": False}
    if precision == "month":
        if not isinstance(raw, str) or not re.fullmatch(r"\d{4}-\d{2}", raw) or value["end"] is not None:
            raise ValueError("Mês aproximado exige YYYY-MM sem dia presumido")
        year, month = map(int, raw.split("-"))
        first = date(year, month, 1)
        last = date(year, month, calendar.monthrange(year, month)[1])
    elif precision in {"exact", "range"}:
        first = date.fromisoformat(raw)
        last = date.fromisoformat(value["end"]) if precision == "range" else first
        if precision == "exact" and value["end"] is not None or last < first:
            raise ValueError("Intervalo de data incoerente")
    else:
        raise ValueError("Precisão de data desconhecida")
    return {"earliest": first.isoformat(), "latest": last.isoformat(), "exact": precision == "exact"}


def receive_events(output: Path, payload: dict) -> dict:
    errors = validate_contract(payload, "labor_events.schema.json")
    if errors:
        raise ValueError("; ".join(errors))
    accounts = {r["id"]: r for r in load_accounts(output)}
    path = output / "intake_events.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"schema_version": "1.0", "events": []}
    if old["events"] and old.get("revision") != identity(old["events"]):
        raise ValueError("Cronologia de relatos adulterada ou sem revisão")
    by_id = {e["id"]: e for e in old["events"]}
    incoming = set()
    for entry in payload["events"]:
        if entry["id"] in incoming:
            raise ValueError("Evento duplicado no envio")
        incoming.add(entry["id"])
        record = accounts.get(entry["client_record_id"])
        if not record or not entry["quote"].strip() or entry["quote"] not in record["text"]:
            raise ValueError("Evento exige trecho literal do relato recebido")
        item = dict(entry, bounds=date_bounds(entry["happened"]), account_hash=record["sha256"])
        if item.get("supersedes") and item["supersedes"] not in by_id:
            raise ValueError("Retificação de evento exige predecessor existente")
        if item["id"] in by_id and by_id[item["id"]] != item:
            raise ValueError("Preservar o evento anterior; retificar com novo ID")
        by_id[item["id"]] = item
    events = list(by_id.values())
    result = {"schema_version": "1.0", "events": events, "revision": identity(events),
              "meaning": "Limites de datas narradas; não escolhem marco legal nem confirmam prova documental."}
    names = ["intake_events.json", "cronologia_relato.md"]
    if path.is_file() and old != result:
        name = "intake_event_history/" + identity(old) + ".json"
        atomic_json(output / name, old)
        names.append(name)
    atomic_json(path, result)
    lines = ["# CRONOLOGIA DO RELATO", "", "Datas aproximadas permanecem aproximadas; conferir marcos jurídicos por pretensão.", ""]
    for event in events:
        bounds = event["bounds"]
        lines += ["## " + safe_text(event["id"]), "", safe_text(event["description"]), "",
                  "Relato: " + safe_text(event["client_record_id"]) + ". Precisão: " + event["happened"]["precision"] + ".",
                  "Limites narrados: " + str(bounds["earliest"]) + " a " + str(bounds["latest"]) + ".", ""]
        if event.get("supersedes"):
            lines += ["Retifica " + safe_text(event["supersedes"]) + "; versão anterior preservada.", ""]
    atomic_text(output / "cronologia_relato.md", "\n".join(lines))
    report = output / "relatorio_processual.md"
    if report.is_file():
        text = report.read_text(encoding="utf-8")
        link = "[Cronologia e incertezas do relato](cronologia_relato.md)"
        if link not in text:
            atomic_text(report, text.rstrip() + "\n\n" + link + ".\n")
            names.append("relatorio_processual.md")
    track_artifacts(output, names, bundle=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Registra eventos atribuídos e datas aproximadas")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = receive_events(args.output.resolve(), json.loads(args.input.read_text(encoding="utf-8-sig")))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
