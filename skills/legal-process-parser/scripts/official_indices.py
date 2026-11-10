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
KNOWN_SERIES = {"4390": "SELIC acumulada no mês (% a.m.)", "11": "SELIC diária (% a.d.)", "10764": "IPCA-E (% a.m.)", "433": "IPCA (% a.m.)"}


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Captura séries oficiais do BCB/SGS com recibo; não escolhe índice jurídico")
    parser.add_argument("output", type=Path)
    parser.add_argument("--series", required=True, help="Código SGS (ex.: 4390 SELIC mensal, 10764 IPCA-E)")
    parser.add_argument("--start", required=True, help="Data inicial ISO")
    parser.add_argument("--end", required=True, help="Data final ISO")
    parser.add_argument("--accumulate", choices=["compound", "simple"])
    args = parser.parse_args()
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
