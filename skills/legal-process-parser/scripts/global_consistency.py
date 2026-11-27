"""Material coherence across every selected chapter of a pleading.

Each chapter is validated against its own slice of the analysis; this module
compares the prose of all chapters with one another and with the analysis:
parameters (salary, working hours, divisors, rates), single-occurrence events
(admission, dismissal), identifiers (CNJ, CPF, CNPJ), request coverage,
double counting in the calculation set, naming of the parties and internal
cross-references. Findings are observable mismatches, not a merit review.
"""
from __future__ import annotations

import argparse
import json
import re
from decimal import InvalidOperation
from pathlib import Path

try:
    from .numeric_criteria import fold, parse_number
    from .prose_dates import find_dates
except ImportError:
    from numeric_criteria import fold, parse_number
    from prose_dates import find_dates

BLOCKING, WARNING = "blocking", "warning"
SENTENCE = re.compile(r"(?:[^.;!?\n]|\.(?=\d))+[.;!?]?")
MONEY = r"r\$\s*(?P<v>\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:,\d{1,2})?)"
NUMBER = r"(?P<v>\d+(?:[.,]\d+)?)"
PARAMETERS = [
    ("salario", re.compile(r"\b(?:salari[oa]s?|remuneracao)(?:\s+(?:base|contratual|mensal|inicial|final|fixo|registrad[oa]|anotad[oa]))?"
                           r"[^.;\d]{0,40}?" + MONEY)),
    ("jornada", re.compile(r"\bjornada(?:\s+[a-z]+){0,3}?\s+de\s+" + NUMBER + r"\s*h(?:oras?)?\b(?P<q>\s*(?:semana(?:is|l)|diari[ao]s?|mensa(?:is|l)|por\s+(?:dia|semana|mes)))?")),
    ("divisor", re.compile(r"\bdivisor\s+(?:de\s+)?" + NUMBER + r"\b")),
    ("adicional", re.compile(r"\badicional\s+(?:de\s+)?(?P<q>noturno|insalubridade|periculosidade|horas?\s+extras?|transferencia)?"
                             r"\s*(?:de|em|no\s+percentual\s+de|equivalente\s+a)?\s*" + NUMBER + r"\s*%")),
]
QUALIFIERS = (("paradigma", r"\bparadigma|\bmodelo\b"), ("piso", r"\bpiso\b|\bnormativ|\bcategoria\b"), ("minimo", r"\bminimo\b"))
EVENTS = [
    ("admissao", re.compile(r"\b(?:admitid[oa]s?|admissao|contratad[oa]s?\s+em|data\s+de\s+admissao)\b")),
    ("dispensa", re.compile(r"\b(?:dispensad[oa]s?|demitid[oa]s?|despedid[oa]s?|desligad[oa]s?|dispensa|demissao|despedida|"
                            r"desligamento|rescisao\s+(?:do\s+contrato|contratual)|extincao\s+do\s+contrato)\b")),
]
IDENTIFIERS = {"processo (CNJ)": re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b"),
               "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
               "CNPJ": re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")}
ROLE_FAMILIES = {
    "polo ativo": {"reclamante": r"\breclamantes?\b", "autor(a)": r"\b(?:parte\s+)?autor(?:a|es|as)?\b",
                   "requerente": r"\brequerentes?\b", "demandante": r"\bdemandantes?\b"},
    "polo passivo": {"reclamada": r"\breclamad[ao]s?\b", "ré/réu": r"(?<!\w)(?:ré|rés|réu|réus)(?!\w)",
                     "requerida": r"\brequerid[ao]s?\b", "demandada": r"\bdemandad[ao]s?\b"},
}
CROSS_REF = re.compile(r"\b(?:item|itens|topico|capitulo|secao)\s+(?P<n>\d+(?:\.\d+)*)", re.I)


def _decimal(value: str) -> str | None:
    try:
        return format(parse_number(value).normalize(), "f")
    except (InvalidOperation, ValueError, KeyError):
        return None


def _prose(text: str) -> str:
    # Block quotations reproduce the source; they are not the author's assertions.
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))


def _mentions(chapters: list[dict]):
    for chapter in chapters:
        for paragraph in chapter["paragraphs"]:
            text = _prose(paragraph["text"])
            yield chapter["id"], paragraph["id"], text


def _sentences(text: str):
    for match in SENTENCE.finditer(text):
        if match.group(0).strip():
            yield match.start(), match.group(0)


def _finding(kind, severity, detail, places, values=None) -> dict:
    row = {"kind": kind, "severity": severity, "detail": detail,
           "chapters": sorted({c for c, _ in places}), "paragraphs": sorted({c + "--" + p for c, p in places})}
    if values is not None:
        row["values"] = values
    return row


def _period_dates(sentence: str) -> tuple:
    """Dates qualifying a period; event dates (admission, dismissal) do not delimit a parameter."""
    events = [m.end() for _, rx in EVENTS for m in rx.finditer(sentence)]
    return tuple(sorted({d["value"] for d in find_dates(sentence)
                         if not any(0 <= d["start"] - end < 30 for end in events)}))


def parameter_findings(chapters: list[dict], review: dict) -> list[dict]:
    groups: dict[tuple, dict[str, set]] = {}
    for cid, pid, text in _mentions(chapters):
        folded = fold(text)
        for index, (_, sentence) in enumerate(_sentences(folded)):
            dates = _period_dates(sentence)
            for name, pattern in PARAMETERS:
                for match in pattern.finditer(sentence):
                    value = _decimal(match.group("v"))
                    if value is None:
                        continue
                    qualifier = (match.groupdict().get("q") or "").strip()
                    qualifier = re.sub(r"\s+", " ", qualifier)
                    if name == "salario":
                        near = sentence[max(0, match.start() - 20):match.end()]
                        qualifier = next((label for label, rx in QUALIFIERS if re.search(rx, near)), "")
                    key = (name, qualifier, dates)
                    groups.setdefault(key, {}).setdefault(value, set()).add((cid, pid, index))
    findings = []
    for (name, qualifier, dates), values in groups.items():
        if len(values) < 2:
            continue
        # Values compared inside one sentence ("pago R$ X e devido R$ Y") are a comparison, not a conflict.
        sentences = {(c, p, i) for places in values.values() for c, p, i in places}
        if len(sentences) < 2:
            continue
        label = name + (" " + qualifier if qualifier else "") + (" (" + ", ".join(dates) + ")" if dates else " (sem período indicado)")
        places = [(c, p) for c, p, _ in sentences]
        findings.append(_finding("parameter", BLOCKING,
            "Parâmetro com valores diferentes na peça: " + label + " = " + " × ".join(sorted(values)) +
            ". Unificar o valor ou indicar na frase o período de cada um.", places, sorted(values)))
    return findings


def event_findings(chapters: list[dict], review: dict) -> list[dict]:
    relations = review.get("labor_review", {}).get("relationships", [])
    severity = WARNING if len(relations) > 1 else BLOCKING
    seen: dict[str, dict[str, set]] = {}
    for cid, pid, text in _mentions(chapters):
        for _, sentence in _sentences(fold(text)):
            for name, pattern in EVENTS:
                for match in pattern.finditer(sentence):
                    window = sentence[match.end():match.end() + 45]
                    dates = find_dates(window)
                    if dates and dates[0]["start"] < 30:
                        seen.setdefault(name, {}).setdefault(dates[0]["value"], set()).add((cid, pid))
    findings = []
    for name, values in seen.items():
        # A month date compatible with a full date of the same month is the same event, less precise.
        distinct = {v for v in values if not (len(v) == 7 and any(o.startswith(v + "-") for o in values))}
        if len(distinct) > 1:
            places = [place for v in values for place in values[v]]
            findings.append(_finding("event_date", severity,
                "Data de " + name + " diferente entre trechos: " + " × ".join(sorted(distinct)) +
                (". Há mais de um vínculo: indicar a qual se refere cada data." if severity == WARNING else ". Unificar com a fonte."),
                places, sorted(distinct)))
    return findings


def known_identifiers(review: dict, extra_texts: list[str] | None = None) -> str:
    base = {k: v for k, v in review.items() if k != "paragraphs"}
    return json.dumps(base, ensure_ascii=False) + "\n".join(extra_texts or [])


def identifier_findings(chapters: list[dict], review: dict, extra_texts: list[str] | None = None) -> list[dict]:
    known = known_identifiers(review, extra_texts)
    unknown: dict[tuple, set] = {}
    for cid, pid, text in _mentions(chapters):
        for label, pattern in IDENTIFIERS.items():
            for match in pattern.finditer(text):
                if match.group(0) not in known:
                    unknown.setdefault((label, match.group(0)), set()).add((cid, pid))
    return [_finding("entity", BLOCKING, label + " na prosa sem correspondência nas fontes do caso: " + value +
                     ". Conferir o número na fonte; não corrigir de memória.", sorted(places), [value])
            for (label, value), places in sorted(unknown.items())]


def coverage_findings(chapters: list[dict], review: dict) -> list[dict]:
    findings = []
    requests = {r["id"]: r for r in review.get("requests", [])}
    issues = {i for c in chapters for i in c["issue_ids"]}
    covered = {r for c in chapters for r in c["request_ids"]}
    for chapter in chapters:
        for rid in chapter["request_ids"]:
            grounded = [p for p in chapter["paragraphs"] if rid in p["request_ids"] and (p["fact_ids"] or p["norm_ids"])]
            if not grounded:
                findings.append(_finding("coverage", BLOCKING, "Pedido " + rid + " sem causa de pedir desenvolvida: nenhum parágrafo "
                                         "que o sustenta vincula fato ou norma.", [(chapter["id"], "-")], [rid]))
    for rid, request in sorted(requests.items()):
        if rid not in covered and request.get("issue_ids") and set(request["issue_ids"]) <= issues:
            findings.append(_finding("coverage", BLOCKING, "Causa de pedir desenvolvida sem o pedido " + rid +
                                     " da análise. Incluir o pedido em um capítulo ou registrar na análise a sua retirada.",
                                     [(c["id"], "-") for c in chapters if set(c["issue_ids"]) & set(request["issue_ids"])], [rid]))
    for rid in sorted(covered):
        request = requests.get(rid, {})
        if request.get("priority") in {"subsidiary", "alternative"} and not request.get("condition"):
            findings.append(_finding("coverage", BLOCKING, "Pedido " + rid + " subsidiário/alternativo sem condição de apreciação.",
                                     [(c["id"], "-") for c in chapters if rid in c["request_ids"]], [rid]))
    return findings


def bis_in_idem_findings(chapters: list[dict], review: dict) -> list[dict]:
    selected = {r for c in chapters for r in c["request_ids"]}
    priority = {r["id"]: r.get("priority", "principal") for r in review.get("requests", [])}
    owner = {r: c["id"] for c in chapters for r in c["request_ids"]}
    items = review.get("labor_review", {}).get("calculation_set", {}).get("items", [])
    groups: dict[tuple, set] = {}
    for item in items:
        if item.get("kind") not in {"principal", "difference"} or not item.get("include_in_total", True):
            continue
        rids = [r for r in item.get("request_ids", []) if r in selected and priority.get(r, "principal") == "principal"]
        if rids:
            key = (item.get("relationship_id"), item.get("competence"), item.get("claim_type"), item.get("segment"))
            groups.setdefault(key, set()).add(tuple(sorted(rids)))
    findings = []
    for (relation, competence, claim, segment), owners in sorted(groups.items(), key=lambda kv: tuple(map(str, kv[0]))):
        rids = sorted({r for group in owners for r in group})
        if len(owners) > 1:
            findings.append(_finding("bis_in_idem", BLOCKING, "Mesma rubrica e competência somada em pedidos principais distintos: " +
                                     str(claim) + "/" + str(segment) + " em " + str(competence) + " (" + ", ".join(rids) +
                                     "). Tornar um pedido subsidiário ou excluir a sobreposição no cálculo.",
                                     [(owner[r], "-") for r in rids], rids))
    return findings


def glossary_findings(chapters: list[dict]) -> list[dict]:
    findings = []
    text = "\n".join(t for _, _, t in _mentions(chapters))
    lowered = text.lower()
    for family, terms in ROLE_FAMILIES.items():
        used = sorted(label for label, rx in terms.items() if re.search(rx, lowered if "é" in rx or "ú" in rx else fold(text)))
        if len(used) > 1:
            findings.append({"kind": "glossary", "severity": WARNING, "chapters": [c["id"] for c in chapters], "paragraphs": [],
                             "detail": "Designações alternadas para o " + family + ": " + ", ".join(used) +
                                       ". Usar um termo único em toda a peça.", "values": used})
    return findings


def cross_reference_findings(chapters: list[dict], sections: set[str] | None) -> list[dict]:
    findings = []
    for cid, pid, text in _mentions(chapters):
        for match in CROSS_REF.finditer(fold(text)):
            target = match.group("n")
            if sections is None or target not in sections:
                findings.append(_finding("cross_reference", WARNING, "Remissão interna sem seção correspondente na consolidação: " +
                                         match.group(0) + ".", [(cid, pid)], [target]))
    return findings


def check_consistency(chapters: list[dict], review: dict, *, extra_texts: list[str] | None = None,
                      sections: set[str] | None = None) -> dict:
    findings = (parameter_findings(chapters, review) + event_findings(chapters, review) +
                identifier_findings(chapters, review, extra_texts) + coverage_findings(chapters, review) +
                bis_in_idem_findings(chapters, review) + glossary_findings(chapters) +
                cross_reference_findings(chapters, sections))
    blocking = [f for f in findings if f["severity"] == BLOCKING]
    return {"status": "blocked" if blocking else "warnings" if findings else "consistent",
            "findings": findings, "blocking_count": len(blocking),
            "controls": ["consistency.parameters", "consistency.event_dates", "consistency.entities",
                         "consistency.request_coverage", "consistency.bis_in_idem", "consistency.glossary",
                         "consistency.cross_refs"],
            "scope": "Divergências observáveis na prosa e nos vínculos; não certifica a correção jurídica nem a prova."}


def summary(report: dict) -> str:
    return "; ".join(f["detail"] for f in report["findings"] if f["severity"] == BLOCKING)


def main() -> int:
    parser = argparse.ArgumentParser(description="Coerência material entre capítulos já salvos")
    parser.add_argument("output", type=Path)
    parser.add_argument("--chapter", action="append", default=[], help="capítulos a comparar; omitido: todos")
    args = parser.parse_args()
    try:
        try:
            from .petition_workspace import load_workspace, chapter_record
        except ImportError:
            from petition_workspace import load_workspace, chapter_record
        state, review = load_workspace(args.output.resolve())
        ids = args.chapter or sorted(state["chapters"])
        chapters = [chapter_record(args.output.resolve(), state["chapters"][cid]) for cid in ids]
        print(json.dumps(check_consistency(chapters, review), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
