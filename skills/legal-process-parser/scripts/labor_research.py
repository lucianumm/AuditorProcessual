"""Selective official research agenda and real, explicitly requested recaptures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .labor_catalog import select_claims, select_sectors
    from .source_records import official_url
    from .research_sources import capture
    from .research_memory import load_registry
except ImportError:
    from labor_catalog import select_claims, select_sectors
    from source_records import official_url
    from research_sources import capture
    from research_memory import load_registry

PORTALS = {
    "legislation": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm",
    "tst": "https://www.tst.jus.br/indice-tematico-precedentes-trabalhistas-stf-tst",
    "stf": "https://portal.stf.jus.br/jurisprudencia/",
    "collective": "https://www.gov.br/trabalho-e-emprego/pt-br/servicos/empregador/mediacao/registro-de-convencoes-e-acordo-coletivo-de-trabalho",
    "sst": "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/seguranca-e-saude-no-trabalho/normas-regulamentadoras",
}


def research_agenda(claim_ids: list[str], sector_ids: list[str], trt: str = "", *, question: str = "", context: dict | None = None) -> dict:
    claims, sectors = select_claims(claim_ids), select_sectors(sector_ids)
    if trt and (not trt.isdigit() or not 1 <= int(trt) <= 24):
        raise ValueError("Indicar o número do TRT confirmado, entre 1 e 24")
    portals = dict(PORTALS)
    if trt:
        portals["regional"] = "https://www.trt" + str(int(trt)) + ".jus.br/"
    context = context or {}
    from datetime import date
    for key in ("period_start", "period_end"):
        if context.get(key):
            date.fromisoformat(context[key])
    if context.get("period_start") and context.get("period_end") and context["period_start"] > context["period_end"]:
        raise ValueError("Período da pesquisa invertido")
    terms = " ".join([question] + [str(context[k]) for k in ("activity", "job", "category", "territory", "period_start", "period_end") if context.get(k)]).strip()
    return {"schema_version": "1.0", "status": "research_plan_not_executed", "portals": portals, "context": context,
            "specific_question": question,
            "targeted_queries": ["site:" + domain + " " + terms for domain in ("planalto.gov.br", "tst.jus.br", "stf.jus.br", "mediador.trabalho.gov.br")]
                                if terms else [],
            "response_requirement": "Consulta efetiva nova e revisão vinculada antes da resposta jurídica; agenda não satisfaz o requisito.",
            "queries": [{"claim_id": c["id"], "question": c["label"], "requirements": c["requirements"],
                         "official_queries": ["site:tst.jus.br " + c["label"] + " precedentes",
                                              "site:stf.jus.br " + c["label"] + " repercussão geral"],
                         "check": ["inteiro_teor", "fatos_determinantes", "redacao_por_periodo", "fontes_contrarias",
                                   "situacao_processual", "efeito_da_tese", "modulacao", "pedido_concreto"]} for c in claims],
            "sector_ids": [s["id"] for s in sectors],
            "collective_lookup": {"required_fields": ["atividade", "funcao", "empregador", "categoria", "territorio", "periodo"],
                                  "meaning": "Pesquisar com âmbito confirmado; resultado vazio não demonstra inexistência."},
            "meaning": "Roteiro sem consulta simulada; portais e consultas genéricas não são citações que sustentam a tese."}


def renew_sources(output: Path, urls: list[str] | None = None) -> list[dict]:
    targets = urls if urls is not None else [r["url"] for r in load_registry(output)["sources"].values()
                                            if r["method"] == "official_http_capture"]
    if any(not official_url(url) for url in targets):
        raise ValueError("Usar somente URLs oficiais verificáveis")
    results = []
    for url in dict.fromkeys(targets):
        try:
            record = capture(url, output)
            results.append({"url": url, "status": "captured", "capture_id": record["capture_id"],
                            "text_hash": record["text_hash"], "accessed_on": record["accessed_on"]})
        except (OSError, ValueError) as error:
            results.append({"url": url, "status": "unavailable", "reason": str(error),
                            "next_step": "Consultar a fonte oficial com navegação disponível; delimitar a questão dependente."})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Pesquisa trabalhista seletiva; recaptura somente quando solicitada")
    parser.add_argument("--claim", action="append", default=[])
    parser.add_argument("--sector", action="append", default=[])
    parser.add_argument("--trt", default="")
    parser.add_argument("--refresh", type=Path)
    parser.add_argument("--url", action="append")
    parser.add_argument("--discover", type=Path, help="Captura índices oficiais e localiza candidatos pertinentes")
    parser.add_argument("--question", default="")
    for field in ("period-start", "period-end", "employer", "activity", "job", "category", "territory"):
        parser.add_argument("--" + field, default="")
    args = parser.parse_args()
    try:
        if args.refresh and args.discover:
            raise ValueError("Selecionar descoberta ou recaptura")
        if args.discover:
            try:
                from .research_locator import discover_candidates
            except ImportError:
                from research_locator import discover_candidates
            result = discover_candidates(args.discover.resolve(), args.url or [], args.question)
        else:
            context = {k: getattr(args, k) for k in ("period_start", "period_end", "employer", "activity", "job", "category", "territory") if getattr(args, k)}
            result = renew_sources(args.refresh.resolve(), args.url) if args.refresh else research_agenda(args.claim, args.sector, args.trt, question=args.question, context=context)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
