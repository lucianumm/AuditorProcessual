"""Cliente opcional da API Pública Oficial DataJud/CNJ (api-publica.datajud.cnj.jus.br) com recibo SHA-256.

Inclui roteamento determinístico offline do número único CNJ (Res. CNJ 65/2008) para o endpoint
exato do tribunal e parser estruturado de classes, assuntos TPU, órgão julgador e movimentos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from .case_memory import atomic_bytes, atomic_json, identity
    from .helpers import CNJ_UF, parse_cnj_numbers
    from .research_memory import register_source_record
    from .research_sources import USER_AGENT
except ImportError:
    from case_memory import atomic_bytes, atomic_json, identity
    from helpers import CNJ_UF, parse_cnj_numbers
    from research_memory import register_source_record
    from research_sources import USER_AGENT

DATAJUD_BASE = "https://api-publica.datajud.cnj.jus.br/api_publica_{alias}/_search"

STATE_MILITARY_ALIASES = {"13": "tjmmg", "21": "tjmrs", "26": "tjmsp"}


def _alias_for_segment_and_court(segment: str, court_code: str) -> str:
    if segment == "3":
        return "stj"
    if segment == "4":
        reg = int(court_code)
        if 1 <= reg <= 6:
            return f"trf{reg}"
        raise ValueError(f"Código de TRF inválido para DataJud: {court_code}")
    if segment == "5":
        if court_code == "00":
            return "tst"
        reg = int(court_code)
        if 1 <= reg <= 24:
            return f"trt{reg}"
        raise ValueError(f"Código de TRT inválido para DataJud: {court_code}")
    if segment == "6":
        if court_code == "00":
            return "tse"
        uf = CNJ_UF.get(court_code)
        if not uf:
            raise ValueError(f"Código de TRE inválido para DataJud: {court_code}")
        return "tre-dft" if uf == "DF" else f"tre-{uf.lower()}"
    if segment == "7":
        return "stm"
    if segment == "8":
        uf = CNJ_UF.get(court_code)
        if not uf:
            raise ValueError(f"Código de TJ inválido para DataJud: {court_code}")
        return "tjdft" if uf == "DF" else f"tj{uf.lower()}"
    if segment == "9":
        alias = STATE_MILITARY_ALIASES.get(court_code)
        if not alias:
            raise ValueError(f"Código de TJM estadual sem endpoint público DataJud: {court_code}")
        return alias
    raise ValueError(
        f"Segmento CNJ '{segment}' não possui endpoint público no DataJud (STF e CNJ utilizam portais próprios)."
    )


def build_query_payload(cnj_number: str, *, size: int = 10, validate_digits: bool = True) -> dict:
    """Constrói o payload oficial de consulta Elasticsearch do DataJud para um número CNJ."""
    found = parse_cnj_numbers(cnj_number)
    if not found:
        raise ValueError(f"Número único CNJ inválido ou não reconhecido: {cnj_number!r}")
    item = found[0]
    if validate_digits and not item["check_digits_valid"]:
        raise ValueError(f"Dígitos verificadores inválidos (ISO 7064 mod 97) no processo: {item['number']}")
    digits20 = re.sub(r"\D", "", item["number"])
    return {"size": int(size), "query": {"match": {"numeroProcesso": digits20}}}


def resolve_endpoint(cnj_number: str, *, validate_digits: bool = True) -> dict:
    """Resolve offline o número CNJ para o alias e URL oficial da API Pública DataJud."""
    found = parse_cnj_numbers(cnj_number)
    if not found:
        raise ValueError(f"Número único CNJ inválido ou não reconhecido: {cnj_number!r}")
    item = found[0]
    if validate_digits and not item["check_digits_valid"]:
        raise ValueError(f"Dígitos verificadores inválidos (ISO 7064 mod 97) no processo: {item['number']}")
    alias = _alias_for_segment_and_court(item["segment"], item["court_code"])
    digits20 = re.sub(r"\D", "", item["number"])
    endpoint_url = DATAJUD_BASE.format(alias=alias)
    return {
        "cnj_number": item["number"],
        "numero_processo_digits": digits20,
        "segment": item["segment"],
        "justice": item["justice"],
        "court_code": item["court_code"],
        "court": item["court"],
        "origin": item["origin"],
        "year": item["year"],
        "check_digits_valid": item["check_digits_valid"],
        "alias": alias,
        "endpoint_url": endpoint_url,
        "query_payload": {"size": 10, "query": {"match": {"numeroProcesso": digits20}}},
    }


def _flatten_assuntos(raw_assuntos: object) -> list[dict]:
    items: list[dict] = []
    if not isinstance(raw_assuntos, list):
        return items
    for entry in raw_assuntos:
        if isinstance(entry, list):
            items.extend(_flatten_assuntos(entry))
        elif isinstance(entry, dict):
            items.append({
                "codigo": entry.get("codigo"),
                "nome": entry.get("nome"),
            })
    return items


def parse_datajud_hit(payload: dict) -> dict:
    """Extrai metadados TPU (classe, assuntos, órgão julgador, dataAjuizamento e movimentos cronológicos)."""
    if not isinstance(payload, dict):
        raise ValueError("Payload DataJud deve ser um objeto JSON")
    if "hits" in payload and isinstance(payload["hits"], dict):
        hit_list = payload["hits"].get("hits") or []
        if not hit_list:
            return {
                "found": False,
                "hits_count": 0,
                "legal_status": "process_not_found_in_datajud_public_index",
            }
        source = hit_list[0].get("_source") if isinstance(hit_list[0], dict) else None
        hits_count = len(hit_list)
    elif "_source" in payload and isinstance(payload["_source"], dict):
        source = payload["_source"]
        hits_count = 1
    else:
        source = payload
        hits_count = 1

    if not isinstance(source, dict):
        raise ValueError("Estrutura _source ausente ou inválida no retorno do DataJud")

    classe_raw = source.get("classe") if isinstance(source.get("classe"), dict) else {}
    orgao_raw = source.get("orgaoJulgador") if isinstance(source.get("orgaoJulgador"), dict) else {}
    sistema_raw = source.get("sistema") if isinstance(source.get("sistema"), dict) else {}
    formato_raw = source.get("formato") if isinstance(source.get("formato"), dict) else {}

    movs_raw = source.get("movimentos") if isinstance(source.get("movimentos"), list) else []
    movimentos: list[dict] = []
    for mov in movs_raw:
        if not isinstance(mov, dict):
            continue
        comps = mov.get("complementosTabelados") if isinstance(mov.get("complementosTabelados"), list) else []
        movimentos.append({
            "codigo": mov.get("codigo"),
            "nome": mov.get("nome"),
            "data_hora": mov.get("dataHora"),
            "complementos_tabelados": [
                {
                    "codigo": c.get("codigo"),
                    "nome": c.get("nome"),
                    "valor": c.get("valor"),
                    "descricao": c.get("descricao"),
                }
                for c in comps if isinstance(c, dict)
            ],
        })
    movimentos.sort(key=lambda m: str(m.get("data_hora") or ""))

    return {
        "found": True,
        "hits_count": hits_count,
        "numero_processo": source.get("numeroProcesso"),
        "tribunal": source.get("tribunal"),
        "grau": source.get("grau"),
        "nivel_sigilo": source.get("nivelSigilo"),
        "data_ajuizamento": source.get("dataAjuizamento"),
        "data_hora_ultima_atualizacao": source.get("dataHoraUltimaAtualizacao"),
        "classe": {"codigo": classe_raw.get("codigo"), "nome": classe_raw.get("nome")},
        "assuntos": _flatten_assuntos(source.get("assuntos")),
        "orgao_julgador": {
            "codigo": orgao_raw.get("codigo"),
            "nome": orgao_raw.get("nome"),
            "codigo_municipio_ibge": orgao_raw.get("codigoMunicipioIBGE"),
        },
        "sistema": {"codigo": sistema_raw.get("codigo"), "nome": sistema_raw.get("nome")},
        "formato": {"codigo": formato_raw.get("codigo"), "nome": formato_raw.get("nome")},
        "movimentos_count": len(movimentos),
        "movimentos": movimentos,
        "legal_status": "metadata_procedural_tpu_verify_full_case_records",
    }


def _normalize_auth_header(api_key: str) -> str:
    cleaned = api_key.strip()
    if not cleaned:
        raise ValueError("Chave da API Pública DataJud vazia")
    if cleaned.lower().startswith("apikey "):
        return "APIKey " + cleaned[7:].strip()
    return f"APIKey {cleaned}"


def lookup_process(
    cnj_number: str,
    *,
    output: Path | None = None,
    api_key: str | None = None,
    timeout: int = 30,
) -> dict:
    """Consulta a API Pública DataJud via HTTPS POST e, quando informado output, preserva recibo SHA-256."""
    resolved = resolve_endpoint(cnj_number)
    effective_key = api_key or os.environ.get("DATAJUD_API_KEY")
    if not effective_key:
        raise ValueError(
            "Chave da API Pública DataJud ausente: informe --api-key ou defina a variável de ambiente DATAJUD_API_KEY"
        )

    body = json.dumps(resolved["query_payload"]).encode("utf-8")
    headers = {
        "Authorization": _normalize_auth_header(effective_key),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    req = Request(resolved["endpoint_url"], data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError("Resposta DataJud excede limite de 8 MiB")
            encoding = response.headers.get_content_charset() or "utf-8"
    except (HTTPError, URLError, HTTPException, TimeoutError) as error:
        raise OSError(f"Falha na consulta à API Pública DataJud: {type(error).__name__}: {error}") from error

    text = raw.decode(encoding)
    payload = json.loads(text)
    parsed = parse_datajud_hit(payload)

    result: dict = {
        "endpoint": resolved,
        "process": parsed,
    }

    if output is not None:
        out_dir = Path(output).resolve()
        captured_at = datetime.now(timezone.utc)
        receipt = {
            "requested_url": resolved["endpoint_url"],
            "url": resolved["endpoint_url"],
            "accessed_on": captured_at.date().isoformat(),
            "captured_at": captured_at.isoformat(),
            "text": text,
            "raw_content_hash": hashlib.sha256(raw).hexdigest(),
            "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "content_type": "application/json",
            "encoding": encoding,
            "method": "official_http_capture",
        }
        receipt["capture_id"] = identity(receipt)
        atomic_bytes(out_dir / "research_sources" / (receipt["capture_id"] + ".source"), raw)
        atomic_json(out_dir / "research_sources" / (receipt["capture_id"] + ".json"), receipt)
        register_source_record(out_dir, receipt)
        result["receipt"] = {
            k: receipt[k]
            for k in ("capture_id", "url", "accessed_on", "raw_content_hash", "text_hash", "method")
        }

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cliente da API Pública Oficial DataJud/CNJ com recibo SHA-256")
    parser.add_argument("--cnj", help="Número único CNJ do processo")
    parser.add_argument("--resolve-only", action="store_true", help="Resolve apenas o endpoint e payload offline, sem rede")
    parser.add_argument("--parse-file", type=Path, help="Analisa offline um arquivo JSON de resposta do DataJud")
    parser.add_argument("--output", type=Path, help="Diretório do caso para gravar recibo em research_sources/")
    parser.add_argument("--api-key", help="Chave da API Pública DataJud (ou use DATAJUD_API_KEY)")
    args = parser.parse_args(argv)
    try:
        if args.parse_file:
            payload = json.loads(args.parse_file.read_text(encoding="utf-8"))
            result = parse_datajud_hit(payload)
        elif args.cnj and args.resolve_only:
            result = resolve_endpoint(args.cnj)
        elif args.cnj:
            result = lookup_process(args.cnj, output=args.output, api_key=args.api_key)
        else:
            parser.error("Informe --cnj NUMERO (com ou sem --resolve-only) ou --parse-file ARQUIVO.json")
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
