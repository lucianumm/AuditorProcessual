"""Preserve attributed client accounts, including cases without uploads."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .case_memory import atomic_json, atomic_text, identity, update_memory
    from .contracts import validate_contract
    from .legal_index import anchor, safe_text
except ImportError:
    from case_memory import atomic_json, atomic_text, identity, update_memory
    from contracts import validate_contract
    from legal_index import anchor, safe_text


def load_accounts(output: Path) -> list[dict]:
    path = output / "client_records.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    entries = data.get("entries", [])
    raw = [{k: v for k, v in entry.items() if k != "sha256"} for entry in entries]
    errors = validate_contract({"schema_version": "1.0", "entries": raw}, "client_intake.schema.json")
    known = set()
    for entry, original in zip(entries, raw):
        if entry.get("id") in known or entry.get("sha256") != identity(original):
            errors.append("Relato duplicado ou alterado; preservar a origem e usar novo ID")
        if original.get("supersedes") and original["supersedes"] not in known:
            errors.append("Retificação aponta para relato anterior inexistente")
        known.add(entry.get("id"))
    if errors or data.get("revision") != identity(entries):
        raise ValueError("; ".join(errors or ["Revisão do relato alterada"]))
    return entries


def render_accounts(output: Path, entries: list[dict]) -> None:
    lines = ["# RELATOS DO CLIENTE", "", "Origem declarada; relato não equivale a prova documental.", ""]
    for entry in entries:
        lines += [f'<a id="{anchor("client", entry["id"])}"></a>',
                  "## " + safe_text(entry["id"]), "",
                  "Referência: " + safe_text(entry["conversation_reference"]), ""]
        if entry.get("supersedes"):
            lines += ["Retifica o relato " + safe_text(entry["supersedes"]) + "; ambas as versões permanecem preservadas.", ""]
        lines += [safe_text(entry["text"]), ""]
    atomic_text(output / "relato_cliente.md", "\n".join(lines))
    # Refresh only the account section; preserve the rest of an existing report.
    report = output / "relatorio_processual.md"
    old = report.read_text(encoding="utf-8-sig") if report.is_file() else "# RELATÓRIO PROCESSUAL\n\n"
    marker = "<!-- client-accounts:start -->"
    end = "<!-- client-accounts:end -->"
    block = marker + "\n\n## Relatos recebidos\n\n"
    block += "[Relatos e retificações preservados](relato_cliente.md). A disponibilidade de documentos e a suficiência da prova são avaliadas por questão.\n\n" + end
    if marker in old and end in old:
        start, finish = old.index(marker), old.index(end) + len(end)
        new = old[:start] + block + old[finish:]
    else:
        new = old.rstrip() + "\n\n" + block + "\n"
    if new != old and report.is_file():
        atomic_text(output / "intake_history" / identity(old) / "relatorio_processual.md", old)
    atomic_text(report, new)


def receive_accounts(output: Path, payload: dict) -> dict:
    errors = validate_contract(payload, "client_intake.schema.json")
    if errors:
        raise ValueError("; ".join(errors))
    output.mkdir(parents=True, exist_ok=True)
    previous = load_accounts(output)
    merged = list(previous)
    known = {entry["id"]: entry for entry in previous}
    for original in payload["entries"]:
        entry = {**original, "sha256": identity(original)}
        if entry["id"] in known:
            if entry != known[entry["id"]]:
                raise ValueError("ID de relato já recebido; usar novo ID e supersedes para retificação")
            continue
        if entry.get("supersedes") and entry["supersedes"] not in known:
            raise ValueError("Retificação exige relato anterior recebido")
        merged.append(entry)
        known[entry["id"]] = entry
    record = {"schema_version": "1.0", "revision": identity(merged), "entries": merged}
    if previous:
        atomic_json(output / "intake_history" / identity(previous) / "client_records.json",
                    {"schema_version": "1.0", "revision": identity(previous), "entries": previous})
    atomic_json(output / "client_records.json", record)
    atomic_json(output / "intake_history" / record["revision"] / "client_records.json", record)
    render_accounts(output, merged)
    memory = update_memory(output)
    if memory["update"]["requires_legal_reassessment"]:
        try:
            from .artifact_tracking import invalidate_legal_delivery
        except ImportError:
            from artifact_tracking import invalidate_legal_delivery
        invalidate_legal_delivery(output, memory["corpus_revision"], "Novo relato/retificação recebido; conferir fatos e conclusões dependentes.")
    try:
        from .artifact_tracking import track_artifacts
    except ImportError:
        from artifact_tracking import track_artifacts
    track_artifacts(output, ["client_records.json", "relato_cliente.md", "relatorio_processual.md",
                             "case_memory.json", "memoria_processual.md", "indice_juridico.md", "indice_juridico.json"], bundle=True)
    return {"corpus_revision": memory["corpus_revision"], "received_records": len(merged),
            "documents": len(memory["documents"]), "update": memory["update"],
            "evidence_status": "client_account_not_documentary_confirmation"}


def account_packet(output: Path, *, offset: int = 0, max_chars: int = 12000) -> dict:
    if offset < 0 or not 1 <= max_chars <= 100000:
        raise ValueError("offset >= 0 e max_chars entre 1 e 100000")
    entries = load_accounts(output)
    total = sum(len(entry["text"]) for entry in entries)
    if offset > total:
        raise ValueError("Offset posterior ao conteúdo dos relatos")
    position, remaining, segments = 0, max_chars, []
    consumed = offset
    for entry in entries:
        length = len(entry["text"])
        if position + length <= offset:
            position += length
            continue
        start = max(0, offset - position)
        end = min(length, start + remaining)
        if end > start:
            segments.append({"record_id": entry["id"], "source_revision": entry["sha256"],
                             "conversation_reference": entry["conversation_reference"], "start": start, "end": end,
                             "length": length, "text": entry["text"][start:end], "source_kind": "client_account"})
            remaining -= end - start
            consumed = position + end
        position += length
        if remaining == 0:
            break
    return {"offset": offset, "next_offset": consumed if consumed < total else None,
            "total_characters": total, "segments": segments, "meaning": "Conteúdo disponibilizado; não certifica compreensão."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Preserva relatos e retificações; permite iniciar caso sem anexos")
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--read", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args()
    try:
        if args.read:
            result = account_packet(args.output, offset=args.offset, max_chars=args.max_chars)
        elif args.input:
            result = receive_accounts(args.output, json.loads(args.input.read_text(encoding="utf-8-sig")))
        else:
            raise ValueError("Indicar relato.json ou --read")
        print(json.dumps(result,
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
