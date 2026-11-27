"""Calendar dates and periods written in Portuguese prose, normalised to ISO.

Recognising a date does not establish which event it marks. Only full dates
(day, month, year) and month dates (month, year) are read; bare years and
statute numbers are left alone so they never become a matching date.
"""
from __future__ import annotations

import calendar
import json
import re

try:
    from .numeric_criteria import fold
except ImportError:
    from numeric_criteria import fold

MONTHS = {"janeiro": 1, "jan": 1, "fevereiro": 2, "fev": 2, "marco": 3, "mar": 3, "abril": 4, "abr": 4,
          "maio": 5, "mai": 5, "junho": 6, "jun": 6, "julho": 7, "jul": 7, "agosto": 8, "ago": 8,
          "setembro": 9, "set": 9, "outubro": 10, "out": 10, "novembro": 11, "nov": 11, "dezembro": 12, "dez": 12}
MONTH = "(?:" + "|".join(sorted(MONTHS, key=len, reverse=True)) + ")"
# Identifiers whose digits look like dates are masked before reading dates.
MASKS = (re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b"),
         re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
         re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"))
FULL = [
    (re.compile(r"(?<![\w/.-])(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})(?![\w/-])"), "ymd"),
    (re.compile(r"(?<![\w/.-])(?P<d>\d{1,2})[/.-](?P<m>\d{1,2})[/.-](?P<y>\d{4}|\d{2})(?![\w/-]|\.\d)"), "dmy"),
    (re.compile(r"(?<!\w)(?P<d>\d{1,2})(?:º|o|°)?\s+de\s+(?P<mn>" + MONTH + r")\.?\s+de\s+(?P<y>\d{4})(?!\w)"), "named"),
]
PARTIAL = [
    (re.compile(r"(?<![\w/.-])(?P<y>\d{4})-(?P<m>\d{1,2})(?![\w/-])"), "ym"),
    (re.compile(r"(?<![\w/.-])(?P<m>\d{1,2})/(?P<y>\d{4})(?![\w/-])"), "my"),
    (re.compile(r"(?<!\w)(?P<mn>" + MONTH + r")\.?\s*(?:/|de|\s)\s*(?P<y>\d{4})(?!\w)"), "named_month"),
]
# Dates inside a statute or precedent name ("Lei 13.467, de 13 de julho de 2017") are citations, not facts.
CITATION_PREFIX = re.compile(r"(?:\blei\b|\bdecreto|\bconstitui|\bemenda|\bresolu|\bportaria|\binstru[cç]|\bmedida provis|"
                             r"\bmp\b|\blc\b|\bsumula|\btema\b|\boj\b|\borienta|\badi\b|\badc\b|\badpf\b|\bresp\b|\bre\s*n?[ºo°.]*\s*\d|"
                             r"\bnr\b|\bnorma regulamentadora)(?:[^.;:!?\n]|(?<=\d)\.(?=\d)|(?<=\bn)\.|(?<=art)\.){0,45}$")


def _year(value: str) -> int:
    year = int(value)
    return year + (2000 if year < 50 else 1900) if len(value) == 2 else year


def _iso(year: int, month: int, day: int | None) -> str | None:
    if not 1 <= month <= 12 or not 1000 <= year <= 2999:
        return None
    if day is None:
        return f"{year:04d}-{month:02d}"
    if not 1 <= day <= calendar.monthrange(year, month)[1]:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _masked(text: str) -> str:
    for pattern in MASKS:
        text = pattern.sub(lambda m: "#" * len(m.group(0)), text)
    return text


def find_dates(text: str, *, skip_citations: bool = True) -> list[dict]:
    """Return dates with literal span, ISO value and precision (day or month)."""
    folded = _masked(fold(text))
    taken: list[tuple[int, int]] = []
    found = []
    for patterns, precision in ((FULL, "day"), (PARTIAL, "month")):
        for pattern, kind in patterns:
            for match in pattern.finditer(folded):
                if any(match.start() < end and start < match.end() for start, end in taken):
                    continue
                groups = match.groupdict()
                month = MONTHS[groups["mn"]] if groups.get("mn") else int(groups["m"])
                value = _iso(_year(groups["y"]), month, int(groups["d"]) if precision == "day" else None)
                if value is None:
                    continue
                taken.append((match.start(), match.end()))
                citation = bool(CITATION_PREFIX.search(folded[max(0, match.start() - 60):match.start()]))
                if skip_citations and citation:
                    continue
                found.append({"text": text[match.start():match.end()], "start": match.start(), "end": match.end(),
                              "value": value, "precision": precision})
    return sorted(found, key=lambda d: d["start"])


PERIOD_LINK = re.compile(r"^\s*(?:a|ate|e|ao|à|-|–)\s*$")


def find_periods(text: str) -> list[dict]:
    """Pairs written as "de X a Y", "entre X e Y" or "X a Y"."""
    dates = find_dates(text)
    folded = fold(text)
    periods = []
    for left, right in zip(dates, dates[1:]):
        between = folded[left["end"]:right["start"]]
        before = folded[max(0, left["start"] - 12):left["start"]]
        if PERIOD_LINK.match(between) and (re.search(r"(?:\bde|\bentre|\bdesde|\bperiodo|\bno|\bem)\s*$", before) or between.strip() in {"a", "ate"}):
            periods.append({"start": left, "end": right, "text": text[left["start"]:right["end"]]})
    return periods


def harvest(value) -> set[str]:
    """ISO dates and month dates found anywhere inside structured source records."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return {d["value"] for d in find_dates(text, skip_citations=False)}


def date_supported(value: str, allowed: set[str]) -> str | None:
    """None when supported; otherwise the reason the prose date lacks support."""
    if value in allowed:
        return None
    if len(value) == 7:
        if any(a.startswith(value) for a in allowed):
            return None
        return "data na prosa sem suporte vinculado"
    if value[:7] in allowed and not any(a.startswith(value[:7] + "-") for a in allowed):
        return "data aproximada (mês/ano) tornada exata na prosa"
    return "data na prosa sem suporte vinculado"
