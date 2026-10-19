"""Conservative Portuguese quantities with units, bounds and literal spans.

Recognising a quantity does not establish which legal condition governs a case.
Unsupported forms remain unresolved instead of becoming a bare matching number.
"""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn")


WORDS = dict(zip(
    "zero um uma dois duas tres quatro cinco seis sete oito nove dez onze doze treze quatorze catorze quinze dezesseis dezassete dezessete dezoito dezenove".split(),
    [0, 1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14, 15, 16, 17, 17, 18, 19]))
WORDS.update(dict(zip("vinte trinta quarenta cinquenta sessenta setenta oitenta noventa cem cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos mil".split(),
                      [20, 30, 40, 50, 60, 70, 80, 90, 100, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])))
WORDS.update({word[:-2] + "as": value for word, value in list(WORDS.items()) if word.endswith("tos")})
WORD = "(?:" + "|".join(sorted(WORDS, key=len, reverse=True)) + ")"
NUMBER = r"-?\d+(?:[.,]\d+)*"
UNIT = r"%|por\s+cento|percentuais?|horas?|minutos?|dias?|mes(?:es)?|anos?|reais?|vez(?:es)?|avos?"
QUANTITY = re.compile(r"(?<!\w)(?P<number>" + NUMBER + "|" + WORD + r"(?:(?:\s+e)?\s+" + WORD + r")*(?:\s+virgula\s+" + WORD + r")?)(?!\w)(?P<gap>\s*(?:\([^()]*\)\s*)?)(?P<unit>" + UNIT + r")?(?!\w)")


def parse_number(value: str) -> Decimal:
    value = fold(value.strip())
    if re.fullmatch(NUMBER, value):
        if "," in value:
            value = value.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", value):
            value = value.replace(".", "")
        return Decimal(value)
    whole, sep, fraction = value.partition(" virgula ")
    total = group = 0
    previous = None
    for word in whole.split():
        if word == "e":
            continue
        number = WORDS[word]
        # Two adjacent units or tens are two quantities, not a valid spelling.
        if previous is not None and (number == previous == 1000 or number < 1000 and (previous < 20 or 20 <= previous < 100 and number >= 10)):
            raise ValueError("Número por extenso ambíguo")
        if number == 1000:
            total += (group or 1) * 1000
            group = 0
        else:
            group += number
        previous = number
    result = Decimal(total + group)
    if sep:
        digits = "".join(str(WORDS[w]) for w in fraction.split() if w != "e")
        if not digits or any(WORDS[w] > 9 for w in fraction.split() if w != "e"):
            raise ValueError("Decimal por extenso não suportado; delimitar o trecho")
        result += Decimal("0." + digits)
    return result


def quantities(text: str) -> list[dict]:
    normalized = fold(text)
    rows = []
    for match in QUANTITY.finditer(normalized):
        try:
            value = parse_number(match["number"])
        except (ValueError, KeyError, ArithmeticError):
            continue
        token = match["unit"] or ""
        unit = next((u for pattern, u in (
            (r"%|por\s+cento|percentu", "percent"), (r"hora", "hours"), (r"minuto", "minutes"),
            (r"dia", "days"), (r"mes", "months"), (r"ano", "years"), (r"rea", "money"),
            (r"vez", "factor"), (r"avo", "fraction_denominator")) if re.match(pattern, token)), "number")
        if re.search(r"r\$\s*$", normalized[:match.start()]):
            unit = "money"
        prefix = normalized[max(0, match.start() - 65):match.start()]
        relation = "exact"
        if re.search(r"(?:no minimo|minimo de|pelo menos|nao inferior a|igual ou superior a)\s*$", prefix):
            relation = "minimum"
        elif re.search(r"(?:no maximo|maximo de|ate|nao superior a|limitad[oa] a)\s*$", prefix):
            relation = "maximum"
        elif re.search(r"(?:mais de|superior a)\s*$", prefix):
            relation = "greater_than"
        elif re.search(r"(?:menos de|inferior a)\s*$", prefix):
            relation = "less_than"
        rows.append({"value": str(value), "unit": unit, "relation": relation,
                     "start": match.start(), "end": match.end(), "text": text[match.start():match.end()]})
    return rows


def criterion_matches(row: dict, parameter: dict) -> list[dict]:
    method = row["transform"]
    expected = {"percent_to_fraction": "percent", "percent_to_factor": "percent", "minutes_to_hours": "minutes"}.get(method)
    if row.get("source_unit") and expected and row["source_unit"] != expected:
        return []
    expected = expected or row.get("source_unit") or parameter["unit"]
    if method == "identity":
        compatible = {"count": {"number", "fraction_denominator"}, "factor": {"factor", "number"}, "index": {"factor", "number"}}.get(parameter["unit"], {parameter["unit"]})
        if expected not in compatible:
            return []
    elif {"percent_to_factor": "factor", "percent_to_fraction": "factor", "minutes_to_hours": "hours"}.get(method) != parameter["unit"]:
        return []
    if expected in {"count", "factor", "fraction", "money_per_hour", "money_per_day"} and not row.get("source_unit"):
        expected = "number" if expected == "count" else expected
    return [q for q in quantities(row["quote"]) if Decimal(q["value"]) == Decimal(row["source_value"])
            and q["unit"] == expected and (not row.get("source_relation") or q["relation"] == row["source_relation"])]
