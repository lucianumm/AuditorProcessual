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
UNIT = r"%|por\s+cento|percentuais?|horas?|minutos?|segundos?|dias?|mes(?:es)?|anos?|reais?|vez(?:es)?|avos?"
# Fractions written out in statutes ("um terço", "metade"); never read as the bare number 1.
FRACTIONS = {"meio": (1, 2), "metade": (1, 2), "terco": (1, 3), "tercos": (None, 3), "quarto": (1, 4), "quartos": (None, 4),
             "quinto": (1, 5), "quintos": (None, 5), "sexto": (1, 6), "decimo": (1, 10), "decimos": (None, 10)}
FRACTION = re.compile(r"(?<!\w)(?:(?P<count>um|uma|dois|duas|tres|quatro)\s+(?P<part>tercos?|quartos?|quintos?|sexto|decimos?)|(?P<half>metade|meio))(?!\w)")
FRACTION_STEP = Decimal("0.000000000001")
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


def _relation(normalized: str, start: int, end: int) -> str:
    prefix = normalized[max(0, start - 65):start]
    suffix = normalized[end:end + 45]
    if re.search(r"(?<![a-z])(?:no minimo|minimo de|pelo menos|nao inferior a|igual ou superior a)[,\s]*(?:(?:em|de|a|o|com)\s+)?$", prefix) \
            or re.match(r"^\s*(?:\([^()]*\)\s*)?,?\s*(?:no minimo|pelo menos)(?![a-z])", suffix):
        return "minimum"
    if re.search(r"(?<![a-z])(?:no maximo|maximo de|ate|nao superior a|limitad[oa] a)[,\s]*(?:(?:em|de|a|o)\s+)?$", prefix) \
            or re.match(r"^\s*(?:\([^()]*\)\s*)?,?\s*no maximo(?![a-z])", suffix):
        return "maximum"
    if re.search(r"(?<![a-z])(?:mais de|superior a)\s*$", prefix):
        return "greater_than"
    if re.search(r"(?<![a-z])(?:menos de|inferior a)\s*$", prefix):
        return "less_than"
    return "exact"


def quantities(text: str) -> list[dict]:
    normalized = fold(text)
    rows = []
    fraction_spans = []
    for match in FRACTION.finditer(normalized):
        if match["half"]:
            numerator, denominator = FRACTIONS[match["half"]]
        else:
            numerator = WORDS[match["count"]]
            denominator = FRACTIONS[match["part"]][1]
        fraction_spans.append((match.start(), match.end()))
        rows.append({"value": str((Decimal(numerator) / Decimal(denominator)).quantize(FRACTION_STEP)), "unit": "fraction",
                     "numerator": numerator, "denominator": denominator,
                     "relation": _relation(normalized, match.start(), match.end()),
                     "start": match.start(), "end": match.end(), "text": text[match.start():match.end()]})
    for match in QUANTITY.finditer(normalized):
        if any(a <= match.start() < b for a, b in fraction_spans):
            continue
        try:
            value = parse_number(match["number"])
        except (ValueError, KeyError, ArithmeticError):
            continue
        token = match["unit"] or ""
        unit = next((u for pattern, u in (
            (r"%|por\s+cento|percentu", "percent"), (r"hora", "hours"), (r"minuto", "minutes"), (r"segundo", "seconds"),
            (r"dia", "days"), (r"mes", "months"), (r"ano", "years"), (r"rea", "money"),
            (r"vez", "factor"), (r"avo", "fraction_denominator")) if re.match(pattern, token)), "number")
        if re.search(r"r\$\s*$", normalized[:match.start()]):
            unit = "money"
        rows.append({"value": str(value), "unit": unit, "relation": _relation(normalized, match.start(), match.end()),
                     "start": match.start(), "end": match.end(), "text": text[match.start():match.end()]})
    # A parenthetical spelling repeats the preceding quantity; it shares its bound.
    ordered = sorted(rows, key=lambda r: r["start"])
    for first, second in zip(ordered, ordered[1:]):
        if (first["value"], first["unit"]) == (second["value"], second["unit"]) \
                and re.fullmatch(r"\s*\(\s*", normalized[first["end"]:second["start"]]) \
                and re.match(r"\s*\)", normalized[second["end"]:]):
            second["relation"] = first["relation"] if first["relation"] != "exact" else second["relation"]
            first["relation"] = second["relation"] if second["relation"] != "exact" else first["relation"]
    # "52 minutos e 30 segundos" is one duration of 52.5 minutes.
    ordered = sorted((r for r in rows if r["unit"] in {"minutes", "seconds"}), key=lambda r: r["start"])
    for first, second in zip(ordered, ordered[1:]):
        if first["unit"] == "minutes" and second["unit"] == "seconds" and re.fullmatch(r"\s*e\s*", normalized[first["end"]:second["start"]]):
            rows.append({"value": str(Decimal(first["value"]) + Decimal(second["value"]) / 60), "unit": "minutes",
                         "relation": first["relation"], "start": first["start"], "end": second["end"],
                         "text": text[first["start"]:second["end"]], "composite": True})
    return sorted(rows, key=lambda r: (r["start"], r["end"]))


def same_value(found: str, declared: str) -> bool:
    """Exact match, or a non-terminating value rounded at the declared precision (6+ decimals)."""
    exact, given = Decimal(found), Decimal(declared)
    if exact == given:
        return True
    places = -given.as_tuple().exponent
    return places >= 6 and exact.quantize(Decimal(1).scaleb(-places)) == given


def criterion_matches(row: dict, parameter: dict) -> list[dict]:
    method = row["transform"]
    needed = {"percent_to_fraction": "percent", "percent_to_factor": "percent", "minutes_to_hours": "minutes"}.get(method)
    declared = row.get("source_unit")
    if declared and needed and declared != needed:
        return []
    if method == "identity":
        compatible = {"count": {"number", "fraction_denominator"}, "factor": {"factor", "number", "fraction"},
                      "index": {"factor", "number"}}.get(parameter["unit"], {parameter["unit"]})
        allowed = {declared} if declared else compatible
        if not allowed <= compatible:
            return []
    elif {"percent_to_factor": "factor", "percent_to_fraction": "factor", "minutes_to_hours": "hours"}.get(method) != parameter["unit"]:
        return []
    else:
        allowed = {needed}
    return [q for q in quantities(row["quote"]) if same_value(q["value"], row["source_value"])
            and q["unit"] in allowed and (not row.get("source_relation") or q["relation"] == row["source_relation"])]
