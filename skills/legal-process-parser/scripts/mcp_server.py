"""Servidor Model Context Protocol (MCP) JSON-RPC 2.0 sobre stdio (apenas biblioteca padrão).

Suporta automaticamente enquadramento JSON-RPC delimitado por linha (MCP 2024-11-05 / 2025-03-26)
e enquadramento com cabeçalho `Content-Length:` a partir do primeiro byte útil de cada mensagem.
Nunca executa comandos de shell arbitrários; valida caminhos de arquivo e encapsula falhas em
respostas estruturadas com `isError: true`.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import io
import json
import re
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, BinaryIO, Callable

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS_DIR.parent
REPO_ROOT = SKILL_ROOT.parents[1]

if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

SUPPORTED_PROTOCOL_VERSIONS = ("2025-03-26", "2024-11-05")
DEFAULT_PROTOCOL_VERSION = "2024-11-05"
MAX_MESSAGE_BYTES = 32 * 1024 * 1024
FORBIDDEN_SYSTEM_PREFIXES = ("/etc/", "/proc/", "/sys/", "/dev/", "/boot/", "/root/.ssh")


def _detect_server_version() -> str:
    pyproject = REPO_ROOT / "pyproject.toml"
    if pyproject.is_file():
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    return "1.0.0"


def _json_default(value: Any) -> Any:
    if isinstance(value, (Decimal, Path, date, datetime)):
        return str(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Tipo não serializável em JSON: {type(value).__name__}")


def _dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=_json_default)


def _safe_path(raw: Any, *, must_exist: bool = False, expect_dir: bool = False) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Caminho de arquivo obrigatório e deve ser texto não vazio")
    if "\x00" in raw or "://" in raw:
        raise ValueError("Caminho de arquivo inválido")
    resolved = Path(raw).expanduser().resolve()
    posix = resolved.as_posix()
    if any(posix == p.rstrip("/") or posix.startswith(p) for p in FORBIDDEN_SYSTEM_PREFIXES) or "/.ssh/" in posix:
        raise ValueError("Acesso a diretório sensível do sistema bloqueado")
    if must_exist:
        if expect_dir and not resolved.is_dir():
            raise FileNotFoundError(f"Diretório não encontrado: {resolved}")
        if not expect_dir and not resolved.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {resolved}")
    return resolved


def _load_script_module(module_name: str) -> Any:
    try:
        if __package__:
            return importlib.import_module(f".{module_name}", package=__package__)
        return importlib.import_module(f"scripts.{module_name}")
    except ImportError:
        return importlib.import_module(module_name)


def _call_dynamic_function(
    module_name: str,
    candidate_functions: tuple[str, ...],
    arguments: dict[str, Any],
    aliases: dict[str, tuple[str, ...]] | None = None,
) -> Any:
    try:
        mod = _load_script_module(module_name)
    except ImportError as exc:
        raise RuntimeError(f"Módulo '{module_name}' indisponível no momento: {exc}") from exc

    fn: Callable[..., Any] | None = None
    for name in candidate_functions:
        attr = getattr(mod, name, None)
        if callable(attr):
            fn = attr
            break
    if fn is None:
        for name, attr in vars(mod).items():
            if (
                callable(attr)
                and not name.startswith("_")
                and getattr(attr, "__module__", "") == mod.__name__
                and name.startswith(("calculate_", "compute_", "evaluate_", "check_", "pseudonymize_", "redact_"))
            ):
                fn = attr
                break
    if fn is None:
        raise RuntimeError(f"Nenhuma função pública compatível localizada em '{module_name}'")

    sig = inspect.signature(fn)
    explicit_params = [
        p for p in sig.parameters.values()
        if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]
    if len(explicit_params) == 1 and explicit_params[0].name in {"spec", "payload", "data", "config", "request", "input_data"}:
        pname = explicit_params[0].name
        spec_val = dict(arguments[pname]) if isinstance(arguments.get(pname), dict) else dict(arguments)
        if aliases:
            for canonical_param, alt_names in aliases.items():
                if canonical_param not in spec_val:
                    for alt in alt_names:
                        if alt in spec_val:
                            spec_val[canonical_param] = spec_val[alt]
                            break
        result = fn(spec_val)
        return {"result": result[0], "metadata": result[1]} if isinstance(result, tuple) and len(result) == 2 else result

    accepts_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    normalized_args = dict(arguments)
    if aliases:
        for canonical_param, alt_names in aliases.items():
            if canonical_param not in normalized_args and canonical_param in sig.parameters:
                for alt in alt_names:
                    if alt in normalized_args:
                        normalized_args[canonical_param] = normalized_args.pop(alt)
                        break

    call_kwargs: dict[str, Any] = {}
    for pname, param in sig.parameters.items():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if pname in normalized_args:
            val = normalized_args[pname]
            ann = str(param.annotation)
            if isinstance(val, str) and "Path" in ann:
                val = _safe_path(val)
            elif isinstance(val, (int, float, str)) and "Decimal" in ann:
                val = Decimal(str(val))
            call_kwargs[pname] = val

    if accepts_var_kw:
        for k, v in normalized_args.items():
            if k not in call_kwargs:
                call_kwargs[k] = v

    result = fn(**call_kwargs)
    if isinstance(result, tuple) and len(result) == 2:
        return {"result": result[0], "metadata": result[1]}
    return result


# --- Handlers das 16 ferramentas determinísticas ---

def _tool_ingest_process(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("ingest_document")
    source = _safe_path(args.get("source_path"), must_exist=True)
    output = _safe_path(args.get("output_dir"))
    task = str(args.get("task") or "ingest")
    force = bool(args.get("force", False))
    use_ocr = bool(args.get("use_ocr", False))
    vision_mode = str(args.get("vision_mode") or "never")
    return mod.run_ingest(
        source,
        output,
        task=task,
        force=force,
        use_ocr=use_ocr,
        vision_mode=vision_mode,
    )


def _tool_read_case_batch(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("case_packet")
    output = _safe_path(args.get("output_dir"), must_exist=True, expect_dir=True)
    offset = int(args.get("offset", 0))
    max_chars = int(args.get("max_chars", 12000))
    return mod.reading_packet(output, offset=offset, max_chars=max_chars)


def _tool_search_case_records(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("case_search")
    output = _safe_path(args.get("output_dir"), must_exist=True, expect_dir=True)
    if args.get("client_accounts"):
        return mod.search_client_records(
            output,
            str(args.get("query") or ""),
            offset=int(args.get("offset", 0)),
            limit=int(args.get("limit", 20)),
        )
    return mod.search_memory(
        output,
        str(args.get("query") or ""),
        offset=int(args.get("offset", 0)),
        limit=int(args.get("limit", 20)),
        mode=str(args.get("mode") or "tokens"),
        source_sha256=args.get("source_sha256"),
        document_id=args.get("document_id"),
        document=args.get("document"),
        piece=args.get("piece"),
        person=args.get("person"),
        date_from=args.get("date_from"),
        date_to=args.get("date_to"),
        amount=args.get("amount"),
        entity_type=args.get("entity_type"),
        include_full_pages=bool(args.get("include_full_pages", False)),
        context_chars=int(args.get("context_chars", 500)),
        context_window=int(args.get("context_window", 0)),
    )


def _tool_search_legal_claims(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("claim_search")
    query = str(args.get("query") or "")
    limit = int(args.get("limit", 8))
    domain = args.get("domain")
    polo = args.get("polo")
    return mod.search(query, limit=limit, domain=domain, polo=polo)


def _tool_get_domain_claim_brief(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("domain_catalog")
    claim_ids = args.get("claim_ids") or []
    if isinstance(claim_ids, str):
        claim_ids = [claim_ids]
    if not claim_ids:
        raise ValueError("Informe ao menos um identificador em claim_ids")
    polo = str(args.get("polo") or "ambos")
    domain = args.get("domain")
    as_markdown = bool(args.get("markdown", False))
    if as_markdown:
        return {"markdown": mod.thesis_map_markdown(list(claim_ids), polo=polo, domain=domain), "polo": polo}
    return mod.claim_brief(list(claim_ids), polo=polo, domain=domain)


def _tool_get_labor_claim_brief(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("labor_catalog")
    claim_ids = args.get("claim_ids") or []
    if isinstance(claim_ids, str):
        claim_ids = [claim_ids]
    if not claim_ids:
        raise ValueError("Informe ao menos um identificador em claim_ids")
    polo = str(args.get("polo") or "ambos")
    as_markdown = bool(args.get("markdown", False))
    if as_markdown:
        return {"markdown": mod.thesis_map_markdown(list(claim_ids), polo=polo), "polo": polo}
    return mod.claim_brief(list(claim_ids), polo=polo)


def _tool_list_procedural_pieces(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("procedural_catalog")
    domain = str(args.get("domain") or "")
    phase = str(args.get("phase") or "")
    if not domain or not phase:
        raise ValueError("Parâmetros obrigatórios: domain e phase")
    return mod.candidates(domain, phase, args.get("family"))


def _tool_lookup_official_indices(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("official_indices")
    if args.get("selic_points") and args.get("ipca_points") and hasattr(mod, "compute_lei_14905_interest"):
        return mod.compute_lei_14905_interest(args["selic_points"], args["ipca_points"])
    if not args.get("series") or args.get("list_only"):
        return {"known_series": dict(mod.KNOWN_SERIES), "count": len(mod.KNOWN_SERIES)}
    if not args.get("output_dir") or not args.get("start") or not args.get("end"):
        raise ValueError("Para captura BCB/SGS informe output_dir, series, start e end (ou list_only=true)")
    output = _safe_path(args["output_dir"])
    result = mod.fetch_series(output, str(args["series"]), str(args["start"]), str(args["end"]))
    if args.get("accumulate"):
        result["accumulated"] = mod.accumulate(result["points"], mode=str(args["accumulate"]))
    return result


def _tool_verify_official_citation(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("citation_check")
    provision = str(args.get("provision") or "")
    if not provision:
        raise ValueError("Informe o dispositivo em 'provision' (ex.: 'Art. 186', 'Súmula 338')")
    quote = str(args.get("quote") or "")
    fact_dates = list(args.get("fact_dates") or [])
    if args.get("record_path"):
        rec_path = _safe_path(args["record_path"], must_exist=True)
        record = json.loads(rec_path.read_text(encoding="utf-8-sig"))
        return mod.check_record(record, provision, quote, fact_dates=fact_dates)
    source_text = str(args.get("source_text") or "")
    if not source_text:
        raise ValueError("Informe 'source_text' (texto oficial capturado) ou 'record_path'")
    return mod.check_citation(source_text, provision, quote, fact_dates=fact_dates)


def _tool_export_forensic_docx(args: dict[str, Any]) -> dict[str, Any]:
    mod = _load_script_module("docx_exporter")
    output_docx = _safe_path(args.get("output_path"))
    title = str(args.get("title") or "Minuta Jurídica")
    draft_banner = bool(args.get("draft_banner", True))
    metadata = args.get("metadata") if isinstance(args.get("metadata"), dict) else None
    if args.get("markdown_path"):
        md_source: str | Path = _safe_path(args["markdown_path"], must_exist=True)
    elif args.get("markdown_text") is not None:
        md_source = str(args["markdown_text"])
    else:
        raise ValueError("Informe 'markdown_text' ou 'markdown_path'")
    return mod.export_markdown_to_docx(
        md_source,
        output_docx,
        title=title,
        draft_banner=draft_banner,
        metadata=metadata,
    )


def _tool_calculate_procedural_deadline(args: dict[str, Any]) -> Any:
    return _call_dynamic_function(
        "deadline_calculator",
        ("calculate_deadline", "compute_deadline", "evaluate_deadline"),
        args,
        aliases={
            "base_date": ("start_date", "publication_date", "availability_date", "intimation_date"),
            "publication_date": ("base_date", "start_date"),
            "start_date": ("base_date", "publication_date"),
            "days": ("deadline_days", "term_days"),
            "deadline_days": ("days", "term_days"),
        },
    )


def _tool_calculate_monetary_update(args: dict[str, Any]) -> Any:
    return _call_dynamic_function(
        "civil_monetary_engine",
        ("calculate_monetary_update", "compute_monetary_update", "update_amount"),
        args,
        aliases={
            "principal": ("amount", "value"),
            "amount": ("principal", "value"),
        },
    )


def _tool_calculate_social_security_time(args: dict[str, Any]) -> Any:
    return _call_dynamic_function(
        "social_security_calc",
        ("evaluate_rgps_eligibility", "calculate_contribution_time", "calculate_social_security_time"),
        args,
    )


def _tool_calculate_penal_dosimetry(args: dict[str, Any]) -> Any:
    return _call_dynamic_function(
        "penal_dosimetry",
        ("calculate_dosimetry", "calculate_penal_dosimetry", "compute_dosimetry", "evaluate_dosimetry"),
        args,
    )


def _tool_check_limitation_timeline(args: dict[str, Any]) -> Any:
    return _call_dynamic_function(
        "limitation_checker",
        ("check_limitation", "check_limitation_timeline", "evaluate_limitation", "calculate_limitation"),
        args,
    )


def _tool_pseudonymize_lgpd(args: dict[str, Any]) -> Any:
    mod = _load_script_module("privacy_redactor")
    if args.get("case_dir") and hasattr(mod, "build_cnj615_audit_record"):
        case_dir = _safe_path(args["case_dir"], must_exist=True, expect_dir=True)
        return mod.build_cnj615_audit_record(
            case_dir,
            model_info=str(args.get("model_info") or "unspecified"),
            human_reviewer=args.get("human_reviewer"),
        )
    if args.get("rehydrate") and hasattr(mod, "rehydrate_text"):
        vault = args.get("vault")
        if not isinstance(vault, dict):
            raise ValueError("Para reidratação informe o dicionário 'vault'")
        return {"restored_text": mod.rehydrate_text(str(args.get("text") or ""), vault)}
    text = str(args.get("text") or "")
    custom_names = list(args.get("custom_names") or [])
    vault_in = args.get("vault") if isinstance(args.get("vault"), dict) else None
    redacted, vault_out = mod.pseudonymize_text(text, vault=vault_in, custom_names=custom_names)
    return {
        "redacted_text": redacted,
        "counts": vault_out.get("counts", {}),
        "vault": vault_out,
    }


TOOL_SPECS: tuple[dict[str, Any], ...] = (
    {
        "name": "ingest_process",
        "description": "Ingere e indexa autos ou documentos (.pdf, .docx, .xlsx, .txt, .md) gerando memória paginada e recibos SHA-256.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_path": {"type": "string", "description": "Caminho do arquivo original a ingerir"},
                "output_dir": {"type": "string", "description": "Diretório de saída do caso processado"},
                "task": {"type": "string", "enum": ["ingest", "analyze", "petition", "deadlines", "evidence", "audit"], "default": "ingest"},
                "force": {"type": "boolean", "default": False},
                "use_ocr": {"type": "boolean", "default": False},
                "vision_mode": {"type": "string", "enum": ["always", "auto", "never"], "default": "never"},
            },
            "required": ["source_path", "output_dir"],
        },
        "handler": _tool_ingest_process,
    },
    {
        "name": "read_case_batch",
        "description": "Lê um lote sequencial sem perdas do corpus processual com recibo criptográfico de leitura.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_dir": {"type": "string", "description": "Diretório do caso contendo case_memory.json"},
                "offset": {"type": "integer", "default": 0, "minimum": 0},
                "max_chars": {"type": "integer", "default": 12000, "minimum": 512, "maximum": 64000},
            },
            "required": ["output_dir"],
        },
        "handler": _tool_read_case_batch,
    },
    {
        "name": "search_case_records",
        "description": "Busca nos autos indexados (insensível a acentos/OCR) com filtros por peça, datas, entidades (money, date, cnj, cpf_cnpj, citation) e janela de páginas adjacentes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_dir": {"type": "string", "description": "Diretório do caso indexado"},
                "query": {"type": "string", "default": ""},
                "offset": {"type": "integer", "default": 0},
                "limit": {"type": "integer", "default": 20},
                "mode": {"type": "string", "enum": ["tokens", "substring"], "default": "tokens"},
                "piece": {"type": "string", "description": "Filtro por nome/subtrecho da peça (ex.: Sentença)"},
                "person": {"type": "string"},
                "amount": {"type": "string"},
                "date_from": {"type": "string", "description": "Data ISO YYYY-MM-DD"},
                "date_to": {"type": "string", "description": "Data ISO YYYY-MM-DD"},
                "entity_type": {"type": "string", "enum": ["money", "date", "cnj", "cpf_cnpj", "citation", "all"]},
                "context_window": {"type": "integer", "default": 0, "minimum": 0, "maximum": 5},
                "include_full_pages": {"type": "boolean", "default": False},
                "client_accounts": {"type": "boolean", "default": False},
            },
            "required": ["output_dir"],
        },
        "handler": _tool_search_case_records,
    },
    {
        "name": "search_legal_claims",
        "description": "Localiza pretensões candidatas nos catálogos trabalhista e de 20+ ramos do Direito a partir de fatos coloquiais ou técnicos (BM25 + sinônimos).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Descrição fática ou jurídica da pretensão"},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 50},
                "domain": {"type": "string", "description": "Ramo opcional (ex.: trabalhista, consumidor, bancario, previdenciario)"},
                "polo": {"type": "string", "enum": ["ativo", "passivo", "ambos", "reclamante", "reclamada"]},
            },
            "required": ["query"],
        },
        "handler": _tool_search_legal_claims,
    },
    {
        "name": "get_domain_claim_brief",
        "description": "Abre o checklist completo de requisitos, teses dos dois polos, autoridades candidatas e marcos temporais de pretensões cíveis/públicas/penais.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_ids": {"type": "array", "items": {"type": "string"}, "description": "IDs das pretensões (ex.: ['banc_fraud', 'cons_credit_bureau'])"},
                "polo": {"type": "string", "enum": ["ativo", "passivo", "ambos"], "default": "ambos"},
                "domain": {"type": "string"},
                "markdown": {"type": "boolean", "default": False},
            },
            "required": ["claim_ids"],
        },
        "handler": _tool_get_domain_claim_brief,
    },
    {
        "name": "get_labor_claim_brief",
        "description": "Abre o checklist completo de requisitos, teses do reclamante/reclamada, perfis de cálculo e autoridades candidatas no catálogo trabalhista.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_ids": {"type": "array", "items": {"type": "string"}, "description": "IDs trabalhistas (ex.: ['social_security_limbo', 'overtime'])"},
                "polo": {"type": "string", "enum": ["reclamante", "reclamada", "ambos"], "default": "ambos"},
                "markdown": {"type": "boolean", "default": False},
            },
            "required": ["claim_ids"],
        },
        "handler": _tool_get_labor_claim_brief,
    },
    {
        "name": "list_procedural_pieces",
        "description": "Lista peças processuais candidatas e verificações obrigatórias de cabimento por ramo e fase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Ramo do Direito (ex.: civil, trabalhista, penal, tributario)"},
                "phase": {"type": "string", "description": "Fase processual (ex.: preprocessual, conhecimento, recursal, execucao, administrativo)"},
                "family": {"type": "string"},
            },
            "required": ["domain", "phase"],
        },
        "handler": _tool_list_procedural_pieces,
    },
    {
        "name": "lookup_official_indices",
        "description": "Lista códigos oficiais BCB/SGS, captura séries econômicas oficiais com recibo ou calcula a Taxa Legal da Lei 14.905/2024 (SELIC - IPCA).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_only": {"type": "boolean", "default": False},
                "output_dir": {"type": "string"},
                "series": {"type": "string", "description": "Código SGS (ex.: 4390 SELIC mensal, 433 IPCA)"},
                "start": {"type": "string", "description": "Data inicial ISO YYYY-MM-DD"},
                "end": {"type": "string", "description": "Data final ISO YYYY-MM-DD"},
                "accumulate": {"type": "string", "enum": ["compound", "simple"]},
                "selic_points": {"type": "array", "items": {"type": "object"}},
                "ipca_points": {"type": "array", "items": {"type": "object"}},
            },
        },
        "handler": _tool_lookup_official_indices,
    },
    {
        "name": "verify_official_citation",
        "description": "Confere estruturalmente artigo, parágrafo, súmula, OJ ou Tema no texto oficial capturado, detectando revogações, texto riscado e alterações pós-fatos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provision": {"type": "string", "description": "Dispositivo citado (ex.: 'Art. 71, § 4º', 'Súmula 338')"},
                "source_text": {"type": "string", "description": "Texto oficial capturado para verificação"},
                "record_path": {"type": "string", "description": "Alternativa: caminho para research_sources/<id>.json"},
                "quote": {"type": "string", "default": ""},
                "fact_dates": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["provision"],
        },
        "handler": _tool_verify_official_citation,
    },
    {
        "name": "export_forensic_docx",
        "description": "Exporta minuta ou relatório Markdown para arquivo OOXML .docx no padrão forense brasileiro (A4, margens 3/3/2/2cm, citação 4cm, tabelas e aviso CNJ 332/2020 e 615/2025).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Caminho de destino .docx"},
                "markdown_text": {"type": "string", "description": "Conteúdo Markdown da minuta"},
                "markdown_path": {"type": "string", "description": "Alternativa: caminho para arquivo .md"},
                "title": {"type": "string", "default": "Minuta Jurídica"},
                "draft_banner": {"type": "boolean", "default": True},
                "metadata": {"type": "object"},
            },
            "required": ["output_path"],
        },
        "handler": _tool_export_forensic_docx,
    },
    {
        "name": "calculate_procedural_deadline",
        "description": "Calcula prazos processuais (CPC, CLT, CPP, JEC/JEF) considerando dias úteis/corridos, recesso forense (art. 220 CPC), feriados e prerrogativas de prazo em dobro.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "base_date": {"type": "string", "description": "Data base ISO YYYY-MM-DD (disponibilização DJe, remessa portal ou ciência)"},
                "days": {"type": "integer", "description": "Quantidade de dias do prazo"},
                "rito": {"type": "string", "description": "civel, trabalhista, jec, jef, penal, execucao_penal, recuperacao_judicial, eleitoral"},
                "intimation_mode": {"type": "string", "enum": ["dje", "portal_eletronico", "djen_citacao", "in_person_or_hearing", "juntada"], "default": "dje"},
            },
            "required": ["days"],
        },
        "handler": _tool_calculate_procedural_deadline,
    },
    {
        "name": "calculate_monetary_update",
        "description": "Executa atualização monetária e juros cíveis/públicos por fases temporais (EC 113/2021, Lei 14.905/2024, condenações da Fazenda Pública).",
        "inputSchema": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "principal": {"type": "string", "description": "Valor principal em string decimal exata (ex.: '1000.00')"},
                "start_date": {"type": "string", "description": "Data inicial ISO YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "Data final ISO YYYY-MM-DD"},
                "regime": {"type": "string", "description": "civil_lei_14905, fazenda_ec113, tributario_selic, fgts_adi5090, custom"},
            },
        },
        "handler": _tool_calculate_monetary_update,
    },
    {
        "name": "calculate_social_security_time",
        "description": "Soma vínculos contributivos (CNIS) sem dupla contagem em concomitância e avalia elegibilidade e regras de transição da EC 103/2019 no RGPS.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "periods": {"type": "array", "items": {"type": "object"}, "description": "Períodos contributivos {start, end, special_grade}"},
                "sex": {"type": "string", "enum": ["M", "F"]},
                "birth_date": {"type": "string", "description": "Data de nascimento ISO YYYY-MM-DD"},
                "reference_date": {"type": "string", "description": "Data de referência/DER ISO YYYY-MM-DD"},
                "car_months": {"type": "integer", "description": "Meses de carência cumpridos"},
            },
        },
        "handler": _tool_calculate_social_security_time,
    },
    {
        "name": "calculate_penal_dosimetry",
        "description": "Calcula dosimetria trifásica da pena (CP, art. 68), frações, regime inicial (art. 33), substituição por PRD (art. 44) e progressão de regime (Lei 7.210/1984).",
        "inputSchema": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "min_penalty": {"type": ["object", "integer"], "description": "Pena mínima abstrata (ex.: {'years': 1, 'months': 0})"},
                "max_penalty": {"type": ["object", "integer"], "description": "Pena máxima abstrata (ex.: {'years': 4, 'months': 0})"},
                "unfavorable_circumstances_count": {"type": "integer", "default": 0},
            },
        },
        "handler": _tool_calculate_penal_dosimetry,
    },
    {
        "name": "check_limitation_timeline",
        "description": "Avalia marcos de prescrição, decadência e prescrição intercorrente (CC, CDC, CLT, CTN/LEF, Fazenda Pública e Improbidade).",
        "inputSchema": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "profile": {"type": "string", "description": "Perfil legal (ex.: cpc_art921_intercorrente, lef_art40_intercorrente_1mais5)"},
                "start_date": {"type": "string", "description": "Termo inicial ISO YYYY-MM-DD"},
                "reference_date": {"type": "string", "description": "Data de referência/ajuizamento ISO YYYY-MM-DD"},
            },
        },
        "handler": _tool_check_limitation_timeline,
    },
    {
        "name": "pseudonymize_lgpd",
        "description": "Pseudonimiza dados pessoais (CPF, CNPJ, OAB, e-mail, telefone, conta, partes) com cofre reversível local (LGPD) ou gera relatório de governança CNJ Res. 332/2020 e 615/2025.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a pseudonimizar ou reidratar"},
                "custom_names": {"type": "array", "items": {"type": "string"}},
                "vault": {"type": "object"},
                "rehydrate": {"type": "boolean", "default": False},
                "case_dir": {"type": "string", "description": "Se informado, gera registro de auditoria CNJ 615/2025 do caso"},
                "model_info": {"type": "string"},
                "human_reviewer": {"type": "string"},
            },
        },
        "handler": _tool_pseudonymize_lgpd,
    },
)

RESOURCES: tuple[dict[str, Any], ...] = (
    {
        "uri": "auditor://entrypoint",
        "name": "AI Entrypoint",
        "description": "Ponto de entrada universal e regras de carregamento seletivo do AuditorProcessual.",
        "mimeType": "text/markdown",
        "path": REPO_ROOT / "AI_ENTRYPOINT.md",
    },
    {
        "uri": "auditor://routing/task-router",
        "name": "Task Router",
        "description": "Roteador determinístico de tarefas, gatilhos e orçamento de contexto.",
        "mimeType": "application/json",
        "path": REPO_ROOT / "routing" / "task-router.json",
    },
    {
        "uri": "auditor://references/labor-claims-index",
        "name": "Índice de Pretensões Trabalhistas",
        "description": "Índice leve das pretensões trabalhistas catalogadas.",
        "mimeType": "text/markdown",
        "path": SKILL_ROOT / "references" / "labor_claims_index.md",
    },
    {
        "uri": "auditor://references/domain-claims-index",
        "name": "Índice de Pretensões por Ramo",
        "description": "Índice geral das pretensões cíveis, públicas, penais e empresariais.",
        "mimeType": "text/markdown",
        "path": SKILL_ROOT / "references" / "domain_claims_index.md",
    },
    {
        "uri": "auditor://references/citation-verification-rules",
        "name": "Regras de Verificação de Citações",
        "description": "Protocolo obrigatório de conferência de vigência e redação em fonte oficial.",
        "mimeType": "text/markdown",
        "path": SKILL_ROOT / "references" / "citation_verification_rules.md",
    },
    {
        "uri": "auditor://references/procedural-catalog",
        "name": "Catálogo de Peças Processuais",
        "description": "Peças processuais candidatas por ramo, fase e requisitos de cabimento.",
        "mimeType": "application/json",
        "path": SKILL_ROOT / "references" / "procedural_catalog.json",
    },
    {
        "uri": "auditor://references/official-source-registry",
        "name": "Registro de Portais Jurídicos Oficiais",
        "description": "Portais oficiais brasileiros para consulta legislativa, jurisprudencial e econômica.",
        "mimeType": "application/json",
        "path": SKILL_ROOT / "references" / "official_source_registry.json",
    },
)


class MCPServer:
    """Servidor MCP JSON-RPC 2.0 determinístico e sem estado externo oculto."""

    def __init__(self) -> None:
        self.version = _detect_server_version()
        self.initialized = False
        self._tools = {spec["name"]: spec for spec in TOOL_SPECS}
        self._resources = {res["uri"]: res for res in RESOURCES if res["path"].is_file()}

    def list_tools_metadata(self) -> list[dict[str, Any]]:
        return [
            {
                "name": spec["name"],
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
            }
            for spec in TOOL_SPECS
        ]

    def list_resources_metadata(self) -> list[dict[str, Any]]:
        return [
            {
                "uri": res["uri"],
                "name": res["name"],
                "description": res["description"],
                "mimeType": res["mimeType"],
            }
            for res in self._resources.values()
        ]

    @staticmethod
    def _ok(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error(req_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
        err: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            err["data"] = data
        return {"jsonrpc": "2.0", "id": req_id, "error": err}

    def handle_request(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            req_id = msg.get("id") if isinstance(msg, dict) else None
            return self._error(req_id, -32600, "Requisição JSON-RPC 2.0 inválida")

        method = msg.get("method")
        is_notification = "id" not in msg
        req_id = msg.get("id")
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}

        if not isinstance(method, str) or not method:
            return None if is_notification else self._error(req_id, -32600, "Campo 'method' ausente ou inválido")

        # Notificações JSON-RPC não geram resposta no transporte
        if is_notification or method.startswith("notifications/"):
            if method == "notifications/initialized":
                self.initialized = True
            return None

        if method == "initialize":
            client_version = str(params.get("protocolVersion") or "")
            negotiated = client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
            self.initialized = True
            return self._ok(req_id, {
                "protocolVersion": negotiated,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                },
                "serverInfo": {
                    "name": "auditor-processual",
                    "version": self.version,
                },
                "instructions": (
                    "AuditorProcessual MCP: ferramentas determinísticas de ingestão documental, busca processual, "
                    "catálogos de pretensões e peças, conferência de citações em texto oficial, cálculos forenses, "
                    "pseudonimização LGPD e exportação forense DOCX. Toda saída exige revisão advocatícia humana "
                    "(Res. CNJ 332/2020 e 615/2025)."
                ),
            })

        if method == "ping":
            return self._ok(req_id, {})

        if method == "tools/list":
            return self._ok(req_id, {"tools": self.list_tools_metadata()})

        if method == "tools/call":
            tool_name = params.get("name")
            if not isinstance(tool_name, str) or not tool_name:
                return self._error(req_id, -32602, "Parâmetro 'name' da ferramenta é obrigatório")
            spec = self._tools.get(tool_name)
            if spec is None:
                return self._ok(req_id, {
                    "content": [{"type": "text", "text": _dumps({"error": f"Ferramenta desconhecida: {tool_name}"})}],
                    "isError": True,
                })
            tool_args = params.get("arguments")
            if tool_args is None:
                tool_args = {}
            if not isinstance(tool_args, dict):
                return self._ok(req_id, {
                    "content": [{"type": "text", "text": _dumps({"error": "Campo 'arguments' deve ser um objeto JSON"})}],
                    "isError": True,
                })
            try:
                payload = spec["handler"](tool_args)
                return self._ok(req_id, {
                    "content": [{"type": "text", "text": _dumps(payload)}],
                    "isError": False,
                })
            except Exception as exc:
                return self._ok(req_id, {
                    "content": [{"type": "text", "text": _dumps({"error": str(exc), "tool": tool_name})}],
                    "isError": True,
                })

        if method == "resources/list":
            return self._ok(req_id, {"resources": self.list_resources_metadata()})

        if method == "resources/read":
            uri = params.get("uri")
            if not isinstance(uri, str) or uri not in self._resources:
                return self._error(req_id, -32602, f"Recurso desconhecido ou indisponível: {uri!r}")
            res = self._resources[uri]
            text = res["path"].read_text(encoding="utf-8-sig")
            return self._ok(req_id, {
                "contents": [{
                    "uri": res["uri"],
                    "mimeType": res["mimeType"],
                    "text": text,
                }],
            })

        return self._error(req_id, -32601, f"Método MCP não suportado: {method}")


_DEFAULT_SERVER = MCPServer()


def handle_request(msg: dict[str, Any]) -> dict[str, Any] | None:
    """Função de conveniência para despacho direto de uma mensagem JSON-RPC 2.0."""
    return _DEFAULT_SERVER.handle_request(msg)


def _read_exact(stream: BinaryIO, length: int) -> bytes:
    chunks = []
    remaining = length
    while remaining > 0:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _write_framed(stream: BinaryIO, payload: dict[str, Any] | list[Any], mode: str) -> None:
    encoded = _dumps(payload).encode("utf-8")
    if mode == "content-length":
        header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
        stream.write(header + encoded)
    else:
        stream.write(encoded + b"\n")
    stream.flush()


def serve_stdio(stdin: BinaryIO | None = None, stdout: BinaryIO | None = None, server: MCPServer | None = None) -> None:
    """Loop principal stdio com detecção automática de linha JSON vs Content-Length."""
    reader = stdin if stdin is not None else sys.stdin.buffer
    writer = stdout if stdout is not None else sys.stdout.buffer
    mcp = server or MCPServer()

    while True:
        line = reader.readline()
        if not line:
            break
        stripped = line.lstrip()
        if not stripped:
            continue

        framing = "line"
        raw_json: bytes
        if stripped[:1] in (b"{", b"["):
            framing = "line"
            raw_json = stripped.strip()
        elif stripped.lower().startswith(b"content-length:"):
            framing = "content-length"
            try:
                content_length = int(stripped.split(b":", 1)[1].strip())
            except ValueError:
                _write_framed(writer, MCPServer._error(None, -32700, "Cabeçalho Content-Length inválido"), framing)
                continue
            if not 0 < content_length <= MAX_MESSAGE_BYTES:
                _write_framed(writer, MCPServer._error(None, -32600, "Content-Length fora do limite seguro"), framing)
                continue
            # Consome demais cabeçalhos até a linha em branco
            while True:
                hdr_line = reader.readline()
                if not hdr_line or hdr_line in (b"\r\n", b"\n"):
                    break
            raw_json = _read_exact(reader, content_length)
            if len(raw_json) < content_length:
                break
        else:
            _write_framed(writer, MCPServer._error(None, -32700, "Entrada não reconhecida como JSON-RPC"), "line")
            continue

        try:
            decoded = json.loads(raw_json.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _write_framed(writer, MCPServer._error(None, -32700, f"JSON malformado: {exc}"), framing)
            continue

        if isinstance(decoded, list):
            responses = [resp for item in decoded if (resp := mcp.handle_request(item)) is not None]
            if responses:
                _write_framed(writer, responses, framing)
        else:
            response = mcp.handle_request(decoded)
            if response is not None:
                _write_framed(writer, response, framing)


def run_self_test() -> dict[str, Any]:
    """Executa autoteste offline de protocolo (ambos os enquadramentos) e ferramentas essenciais."""
    mcp = MCPServer()
    init_resp = mcp.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "self-test", "version": "1.0"}},
    })
    assert init_resp and init_resp["result"]["serverInfo"]["name"] == "auditor-processual"
    assert mcp.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None

    tools_resp = mcp.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = tools_resp["result"]["tools"] if tools_resp else []
    assert len(tools) >= 16

    res_list = mcp.handle_request({"jsonrpc": "2.0", "id": 3, "method": "resources/list"})
    resources = res_list["result"]["resources"] if res_list else []
    assert resources

    claim_call = mcp.handle_request({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "search_legal_claims", "arguments": {"query": "golpe do pix", "limit": 2}},
    })
    assert claim_call and not claim_call["result"]["isError"]

    # Testa transporte stdio tanto em linha quanto em Content-Length
    line_req = b'{"jsonrpc":"2.0","id":10,"method":"ping"}\n'
    cl_body = b'{"jsonrpc":"2.0","id":11,"method":"ping"}'
    cl_req = f"Content-Length: {len(cl_body)}\r\n\r\n".encode("ascii") + cl_body
    in_buf = io.BytesIO(line_req + cl_req)
    out_buf = io.BytesIO()
    serve_stdio(stdin=in_buf, stdout=out_buf, server=mcp)
    wire_out = out_buf.getvalue().decode("utf-8")
    assert '"id": 10' in wire_out and "Content-Length:" in wire_out and '"id": 11' in wire_out

    return {
        "ok": True,
        "server": init_resp["result"]["serverInfo"],
        "tools_count": len(tools),
        "resources_count": len(resources),
        "transports_verified": ["line-delimited-json", "content-length-framed"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Servidor MCP stdio do AuditorProcessual (JSON-RPC 2.0)")
    parser.add_argument("--list-tools", action="store_true", help="Imprime o catálogo JSON de ferramentas MCP e encerra")
    parser.add_argument("--self-test", action="store_true", help="Executa autoteste de protocolo e ferramentas e encerra")
    args = parser.parse_args(argv)

    if args.list_tools:
        srv = MCPServer()
        print(_dumps({"server": "auditor-processual", "version": srv.version, "tools": srv.list_tools_metadata()}))
        return 0
    if args.self_test:
        result = run_self_test()
        print(_dumps(result))
        return 0 if result.get("ok") else 1

    serve_stdio()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
