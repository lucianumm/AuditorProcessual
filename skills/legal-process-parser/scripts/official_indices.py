"""Capture official economic series (BCB/SGS) with receipts; no index table is embedded.

Which series, phase and compounding apply to a labor debt is a legal question
answered by the title and current official sources, not by this module.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

try:
    from .research_sources import capture
    from .labor_calculations import decimal_value
except ImportError:
    from research_sources import capture
    from labor_calculations import decimal_value

SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series}/dados?formato=json&dataInicial={start}&dataFinal={end}"
# Series codes documented in references/official_source_registry.json; confirm before use.
KNOWN_SERIES = {
    # Índices monetários, inflacionários e referenciais
    "4390": "SELIC acumulada no mês (% a.m.)",
    "11": "SELIC diária (% a.d.)",
    "10764": "IPCA-E (% a.m.)",
    "433": "IPCA (% a.m.)",
    "7478": "IPCA-15 (% a.m.)",
    "188": "INPC (% a.m.)",
    "189": "IGP-M (% a.m.)",
    "226": "TR — Taxa Referencial (% a.m.)",
    "12": "CDI diário (% a.d.)",
    "4391": "CDI acumulado no mês (% a.m.)",
    "196": "Poupança — rendimento mensal (% a.m.)",
    # Taxas médias de mercado de operações de crédito — BCB (STJ Temas 24–27 / Súmula 530)
    "25464": "Taxa média — Crédito pessoal consignado privado — PF (% a.m.)",
    "25463": "Taxa média — Crédito pessoal consignado público — PF (% a.m.)",
    "25470": "Taxa média — Crédito pessoal consignado INSS — PF (% a.m.)",
    "25462": "Taxa média — Crédito pessoal consignado total — PF (% a.m.)",
    "25461": "Taxa média — Crédito pessoal não consignado — PF (% a.m.)",
    "20714": "Taxa média — Crédito pessoal não consignado — PF (% a.a.)",
    "22022": "Taxa média — Cartão de crédito rotativo regular — PF (% a.m.)",
    "25471": "Taxa média — Aquisição de veículos — PF (% a.m.)",
    "20749": "Taxa média — Aquisição de veículos — PF (% a.a.)",
    "20724": "Taxa média — Capital de giro total — PJ (% a.a.)",
}


def br_date(value: str) -> str:
    day = date.fromisoformat(value)
    return day.strftime("%d/%m/%Y")


def fetch_series(output: Path, series: str, start: str, end: str) -> dict:
    """Capture one SGS series for a closed period and parse it from the preserved text."""
    if not series.isdigit():
        raise ValueError("Código de série SGS inválido")
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise ValueError("Período da série invertido")
    record = capture(SGS_URL.format(series=series, start=br_date(start), end=br_date(end)), output)
    rows = parse_series(record["text"])
    return {"series": series, "label": KNOWN_SERIES.get(series, "série SGS informada"), "start": start, "end": end,
            "capture_id": record["capture_id"], "url": record["url"], "accessed_on": record["accessed_on"],
            "points": rows, "status": "captured_official_series_not_legal_selection"}


def parse_series(text: str) -> list[dict]:
    data = json.loads(text)
    if not isinstance(data, list) or not data:
        raise ValueError("Série oficial vazia ou em formato inesperado")
    rows = []
    for item in data:
        day, month, year = item["data"].split("/")
        rows.append({"date": f"{year}-{month}-{day}", "value": str(decimal_value(str(item["valor"]).replace(",", ".")))})
    return rows


def accumulate(points: list[dict], *, mode: str) -> dict:
    """Accumulated factor of monthly percentage points: compound or simple, as chosen by the author."""
    if mode not in {"compound", "simple"}:
        raise ValueError("Escolher acumulação compound ou simple conforme título e fonte oficial")
    with localcontext() as context:
        context.prec = 50
        factor = Decimal(1)
        total = Decimal(0)
        for point in points:
            rate = decimal_value(point["value"]) / 100
            factor *= 1 + rate
            total += rate
        result = factor if mode == "compound" else 1 + total
    return {"mode": mode, "factor": str(result.quantize(Decimal("0.000000000001"))), "points": len(points),
            "first": points[0]["date"] if points else None, "last": points[-1]["date"] if points else None}


def _competence_key(raw_date: str) -> str:
    if not isinstance(raw_date, str) or len(raw_date) < 7:
        raise ValueError("Data de competência inválida na série fornecida")
    comp = raw_date[:7]
    parts = comp.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2 or not (parts[0].isdigit() and parts[1].isdigit()):
        raise ValueError(f"Competência fora do padrão YYYY-MM: {raw_date}")
    month = int(parts[1])
    if month < 1 or month > 12:
        raise ValueError(f"Mês inválido na competência: {raw_date}")
    return comp


def _series_by_competence(points: list[dict], name: str) -> dict[str, Decimal]:
    if not isinstance(points, list) or not points:
        raise ValueError(f"Série obrigatória vazia ou ausente: {name}")
    mapped: dict[str, Decimal] = {}
    for point in points:
        if not isinstance(point, dict) or "date" not in point or "value" not in point:
            raise ValueError(f"Ponto inválido na série {name}: esperado dict com 'date' e 'value'")
        comp = _competence_key(str(point["date"]))
        if comp in mapped:
            raise ValueError(f"Competência duplicada ({comp}) na série {name}")
        mapped[comp] = decimal_value(str(point["value"]).replace(",", "."))
    return mapped


def compute_lei_14905_interest(selic_points: list[dict], ipca_points: list[dict]) -> dict:
    """Calcula a Taxa Legal (CC, art. 406, §§ 1º e 3º; Lei 14.905/2024; Res. CMN 5.171/2024).

    Por mês m: taxa_legal_m = max(0, selic_m - ipca_m), em acumulação simples (art. 3º da Res. CMN 5.171/2024).
    """
    selic_map = _series_by_competence(selic_points, "SELIC")
    ipca_map = _series_by_competence(ipca_points, "IPCA")
    missing_ipca = sorted(set(selic_map) - set(ipca_map))
    missing_selic = sorted(set(ipca_map) - set(selic_map))
    if missing_ipca or missing_selic:
        details = []
        if missing_ipca:
            details.append("IPCA ausente em " + ", ".join(missing_ipca))
        if missing_selic:
            details.append("SELIC ausente em " + ", ".join(missing_selic))
        raise ValueError("Divergência de competências entre SELIC e IPCA: " + "; ".join(details))
    competences = sorted(selic_map)
    monthly = []
    with localcontext() as context:
        context.prec = 50
        total_pct = Decimal("0")
        for comp in competences:
            selic_m = selic_map[comp]
            ipca_m = ipca_map[comp]
            raw_diff = selic_m - ipca_m
            floor_applied = raw_diff < Decimal("0")
            taxa_m = Decimal("0") if floor_applied else raw_diff
            total_pct += taxa_m
            monthly.append({
                "competence": comp,
                "selic_pct": str(selic_m),
                "ipca_pct": str(ipca_m),
                "raw_diff_pct": str(raw_diff),
                "taxa_legal_pct": str(taxa_m),
                "floor_zero_applied": floor_applied,
            })
        factor = Decimal("1") + (total_pct / Decimal("100"))
    return {
        "normative_basis": "CC, art. 406, §§ 1º e 3º (Lei 14.905/2024); Resolução CMN 5.171/2024, arts. 2º e 3º",
        "accumulation_mode": "simple",
        "months": len(monthly),
        "first_competence": competences[0],
        "last_competence": competences[-1],
        "accumulated_pct": str(total_pct.quantize(Decimal("0.000001"))),
        "factor": str(factor.quantize(Decimal("0.000000000001"))),
        "monthly_breakdown": monthly,
        "legal_status": "calculated_from_supplied_series",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Captura séries oficiais do BCB/SGS com recibo; não escolhe índice jurídico")
    parser.add_argument("output", type=Path, nargs="?", help="Diretório de saída para recibos")
    parser.add_argument("--series", help="Código SGS (ex.: 4390 SELIC mensal, 10764 IPCA-E)")
    parser.add_argument("--start", help="Data inicial ISO")
    parser.add_argument("--end", help="Data final ISO")
    parser.add_argument("--accumulate", choices=["compound", "simple"])
    parser.add_argument("--list-series", action="store_true", help="Lista as séries SGS catalogadas e encerra")
    args = parser.parse_args(argv)
    if args.list_series:
        print(json.dumps({"series": KNOWN_SERIES, "count": len(KNOWN_SERIES)}, ensure_ascii=False, indent=2))
        return 0
    missing = [flag for flag, val in (("output", args.output), ("--series", args.series), ("--start", args.start), ("--end", args.end)) if not val]
    if missing:
        parser.error("argumentos obrigatórios ausentes: " + ", ".join(missing))
    try:
        result = fetch_series(args.output.resolve(), args.series, args.start, args.end)
        if args.accumulate:
            result["accumulated"] = accumulate(result["points"], mode=args.accumulate)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
