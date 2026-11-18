"""LGPD & judicial secrecy reversible pseudonymizer and CNJ Res. 332/2020 & 615/2025 AI Governance audit builder.

Pure Python standard library implementation. Keeps rehydration vaults strictly
local and emits auditable AI supervision records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CNPJ_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|(?<=\bCPF\s)[:\s]*\d{11}\b", re.I)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
OAB_RE = re.compile(
    r"\bOAB\s*(?:/\s*[A-Z]{2}|-[A-Z]{2}|\s+[A-Z]{2})\s*(?:n[ºo°.]?\s*)?\d{1,3}(?:\.?\d{3})*(?:-[A-Za-z0-9])?\b",
    re.I,
)
BANK_ACCOUNT_RE = re.compile(
    r"\b(?:ag[êe]ncia|ag\.?)\s*:?\s*\d{3,5}(?:-[0-9Xx])?\s*(?:[,;/\s-]+)?"
    r"(?:conta(?:\s+corrente|\s+poupan[çc]a)?|c/?c|c/?p)\s*:?\s*\d{3,12}(?:-[0-9Xx])?\b",
    re.I,
)
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+55\s*)?(?:\(\d{2}\)\s*|\b\d{2}\s+)9?\d{4}[-\s]\d{4}\b"
)
CEP_RE = re.compile(
    r"(?<!\d)(?:CEP\s*:?\s*)?(?:\d{2}\.\d{3}-\d{3}|\b\d{5}-\d{3})\b(?!\.)"
)
TOKEN_RE = re.compile(r"\[([A-Z_]+_\d{3,})\]")


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _init_vault(vault: dict[str, Any] | None) -> dict[str, Any]:
    if vault is None:
        return {
            "schema_version": "1.0",
            "created_at": _now_utc(),
            "tokens_to_values": {},
            "values_to_tokens": {},
            "counts": {},
        }
    return {
        "schema_version": str(vault.get("schema_version", "1.0")),
        "created_at": str(vault.get("created_at") or _now_utc()),
        "tokens_to_values": dict(vault.get("tokens_to_values", {})),
        "values_to_tokens": dict(vault.get("values_to_tokens", {})),
        "counts": dict(vault.get("counts", {})),
    }


def _assign_token(category: str, original: str, state: dict[str, Any]) -> str:
    lookup_key = f"{category}::{original}"
    existing = state["values_to_tokens"].get(lookup_key)
    if existing:
        return existing
    next_index = int(state["counts"].get(category, 0)) + 1
    token = f"[{category}_{next_index:03d}]"
    while token in state["tokens_to_values"]:
        next_index += 1
        token = f"[{category}_{next_index:03d}]"
    state["counts"][category] = next_index
    state["tokens_to_values"][token] = original
    state["values_to_tokens"][lookup_key] = token
    return token


def pseudonymize_text(
    text: str,
    vault: dict[str, Any] | None = None,
    custom_names: list[str] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Mask Brazilian PII and custom party names into deterministic reversible tokens."""
    state = _init_vault(vault)
    result = text or ""

    if custom_names:
        cleaned_names = sorted(
            {name.strip() for name in custom_names if isinstance(name, str) and name.strip()},
            key=len,
            reverse=True,
        )
        for name in cleaned_names:
            pattern = re.compile(r"(?<!\w)" + re.escape(name) + r"(?!\w)", re.I)
            result = pattern.sub(lambda m: _assign_token("PARTE", m.group(0), state), result)

    rules: list[tuple[str, re.Pattern[str]]] = [
        ("CNPJ", CNPJ_RE),
        ("CPF", CPF_RE),
        ("EMAIL", EMAIL_RE),
        ("OAB", OAB_RE),
        ("CONTA", BANK_ACCOUNT_RE),
        ("TELEFONE", PHONE_RE),
        ("CEP", CEP_RE),
    ]
    for category, regex in rules:
        result = regex.sub(lambda m, cat=category: _assign_token(cat, m.group(0), state), result)

    state["updated_at"] = _now_utc()
    return result, state


def rehydrate_text(text: str, vault: dict[str, Any]) -> str:
    """Restore exact original PII values locally from a pseudonymization vault."""
    if not text or not vault:
        return text or ""
    mapping = vault.get("tokens_to_values") if isinstance(vault.get("tokens_to_values"), dict) else vault
    return TOKEN_RE.sub(lambda m: str(mapping.get(m.group(0), m.group(0))), text)


def _load_json_safe(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def build_cnj615_audit_record(
    case_dir: Path,
    model_info: str = "unspecified",
    human_reviewer: str | None = None,
) -> dict[str, Any]:
    """Generate an AI governance & supervision audit record per CNJ Res. 332/2020 & 615/2025."""
    case_dir = case_dir.resolve()
    manifest = _load_json_safe(case_dir / "manifest.json")
    quality_gate = _load_json_safe(case_dir / "quality_gate.json")
    recovery = _load_json_safe(case_dir / "recovery_findings.json")
    memory = _load_json_safe(case_dir / "case_memory.json")
    vault = _load_json_safe(case_dir / "privacy_vault.json")

    preserved_sources: list[dict[str, Any]] = []
    source_meta = manifest.get("source")
    if isinstance(source_meta, dict) and source_meta.get("sha256"):
        preserved_sources.append({
            "name": source_meta.get("name"),
            "sha256": source_meta.get("sha256"),
            "pages": source_meta.get("pages"),
            "preserved_path": source_meta.get("preserved_path"),
        })
    for doc in memory.get("documents", []) if isinstance(memory.get("documents"), list) else []:
        if isinstance(doc, dict) and doc.get("sha256") and not any(s.get("sha256") == doc.get("sha256") for s in preserved_sources):
            preserved_sources.append({
                "name": doc.get("name"),
                "sha256": doc.get("sha256"),
                "pages": len(doc.get("pages", [])) if isinstance(doc.get("pages"), list) else None,
                "folder": doc.get("folder"),
            })

    unexecuted_checks: list[str] = [
        "Verificação criptográfica de cadeias ICP-Brasil (.p7s) não executada localmente.",
        "Vigência material, direito intertemporal e subsunção normativa exigem validação jurídica humana.",
    ]
    coverage = manifest.get("coverage", {}) if isinstance(manifest.get("coverage"), dict) else {}
    if coverage.get("semantic_vision_unavailable", 0):
        unexecuted_checks.append("Visão semântica multimodal pendente em uma ou mais páginas/segmentos.")
    if not manifest.get("ocr_requested", False):
        unexecuted_checks.append("OCR local não foi solicitado na execução atual.")
    for warning in manifest.get("warnings", []) if isinstance(manifest.get("warnings"), list) else []:
        if isinstance(warning, str) and warning not in unexecuted_checks:
            unexecuted_checks.append(warning)

    reviewer_clean = human_reviewer.strip() if isinstance(human_reviewer, str) and human_reviewer.strip() else None
    vault_present = bool(vault.get("tokens_to_values"))
    confidentiality = str(manifest.get("confidentiality", "normal"))

    return {
        "schema_version": "1.0",
        "generated_at": _now_utc(),
        "normative_framework": [
            "Resolução CNJ nº 332/2020 (Ética, transparência e governança em IA no Poder Judiciário)",
            "Resolução CNJ nº 615/2025 (Governança, auditabilidade e supervisão humana de IA)",
            "Lei nº 13.709/2018 (LGPD — Proteção de Dados Pessoais)",
        ],
        "case_directory": str(case_dir),
        "process_id": manifest.get("process_id", "Não identificado nos autos"),
        "ai_system": {
            "engine_version": manifest.get("engine_version", "unknown"),
            "execution_fingerprint": manifest.get("execution_fingerprint"),
            "model_info": model_info or "unspecified",
            "task": manifest.get("task", "unspecified"),
            "autonomous_decision_making": False,
        },
        "human_supervision": {
            "required": True,
            "human_reviewer": reviewer_clean,
            "supervision_status": "reviewer_assigned" if reviewer_clean else "pending_human_review",
            "ready_for_unreviewed_filing": False,
        },
        "preserved_sources": preserved_sources,
        "artifact_hashes_count": len(manifest.get("artifact_hashes", {})) if isinstance(manifest.get("artifact_hashes"), dict) else 0,
        "privacy_governance": {
            "confidentiality_level": confidentiality,
            "pseudonymization_mode": "vault_active" if vault_present else "not_applied",
            "redacted_counts": vault.get("counts", {}) if vault_present else {},
            "judicial_secrecy_alert": confidentiality == "restricted",
        },
        "unexecuted_local_checks": unexecuted_checks,
        "quality_gate": {
            "status": quality_gate.get("status", manifest.get("quality_gate", {}).get("status", "review_required")),
            "blocking_gates": quality_gate.get("blocking_gates", manifest.get("quality_gate", {}).get("blocking_gates", [])),
            "recovery_status": recovery.get("status", manifest.get("recovery", {}).get("status", "unknown")),
        },
        "mandatory_lawyer_review_notice": (
            "AVISO OBRIGATÓRIO (Resolução CNJ nº 332/2020 e Resolução CNJ nº 615/2025): "
            "Os artefatos gerados constituem apoio técnico-documental automatizado sob estrita "
            "supervisão humana. É vedado o protocolo ou uso decisório sem conferência integral "
            "dos autos originais, das citações normativas/jurisprudenciais em fonte oficial e "
            "validação por advogado(a) ou profissional juridicamente habilitado(a)."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pseudonimização reversível (LGPD) e registro de auditoria CNJ Res. 332/2020 & 615/2025."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    redact_cmd = sub.add_parser("redact", help="Pseudonimiza PII em arquivo de texto com cofre local reversível.")
    redact_cmd.add_argument("input", type=Path, help="Arquivo de entrada (UTF-8)")
    redact_cmd.add_argument("--output", type=Path, required=True, help="Arquivo pseudonimizado de saída")
    redact_cmd.add_argument("--vault", type=Path, help="Caminho do cofre JSON local (padrão: <output>.vault.json)")
    redact_cmd.add_argument("--name", action="append", default=[], dest="names", help="Nome próprio adicional a mascarar")

    rehydrate_cmd = sub.add_parser("rehydrate", help="Restaura valores originais localmente usando o cofre JSON.")
    rehydrate_cmd.add_argument("input", type=Path, help="Arquivo pseudonimizado")
    rehydrate_cmd.add_argument("--vault", type=Path, required=True, help="Cofre JSON gerado pelo comando redact")
    rehydrate_cmd.add_argument("--output", type=Path, required=True, help="Arquivo reidratado de saída")

    audit_cmd = sub.add_parser("cnj-audit", help="Gera registro de governança de IA (Res. CNJ 332/2020 e 615/2025).")
    audit_cmd.add_argument("case_dir", type=Path, help="Diretório do caso processado (contendo manifest.json)")
    audit_cmd.add_argument("--model-info", default="unspecified", help="Identificação do modelo de IA utilizado")
    audit_cmd.add_argument("--human-reviewer", help="Nome/OAB do(a) revisor(a) humano(a) responsável")
    audit_cmd.add_argument("--output", type=Path, help="Arquivo JSON de saída (padrão: <case_dir>/cnj615_audit.json)")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "redact":
            raw_text = args.input.read_text(encoding="utf-8-sig")
            vault_path = args.vault or Path(f"{args.output}.vault.json")
            existing_vault = _load_json_safe(vault_path) if vault_path.is_file() else None
            redacted, vault = pseudonymize_text(raw_text, vault=existing_vault, custom_names=args.names)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            vault_path.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(redacted, encoding="utf-8")
            vault_path.write_text(json.dumps(vault, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({
                "status": "redacted",
                "output": str(args.output),
                "vault": str(vault_path),
                "counts": vault["counts"],
                "input_sha256": _sha256_file(args.input),
            }, ensure_ascii=False, indent=2))
            return 0

        if args.command == "rehydrate":
            redacted_text = args.input.read_text(encoding="utf-8-sig")
            if not args.vault.is_file():
                raise FileNotFoundError(f"Cofre não encontrado: {args.vault}")
            vault = json.loads(args.vault.read_text(encoding="utf-8-sig"))
            restored = rehydrate_text(redacted_text, vault)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(restored, encoding="utf-8")
            print(json.dumps({
                "status": "rehydrated",
                "output": str(args.output),
            }, ensure_ascii=False, indent=2))
            return 0

        if args.command == "cnj-audit":
            record = build_cnj615_audit_record(
                args.case_dir,
                model_info=args.model_info,
                human_reviewer=args.human_reviewer,
            )
            out_path = args.output or (args.case_dir.resolve() / "cnj615_audit.json")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(record, ensure_ascii=False, indent=2))
            return 0

        return 2
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
