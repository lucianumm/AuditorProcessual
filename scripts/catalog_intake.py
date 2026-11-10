"""Confere dispositivos candidatos no texto oficial antes de entrarem nos catálogos de autoridades.

Uso de manutenção (não é carregado pela skill em atendimento):

    python scripts/catalog_intake.py spec.json --cache .intake-cache --out conferidos.json

`spec.json` é uma lista de itens:

    {"id": "cc_art476", "act": "LEI:10406:2002", "article": "476",
     "law": "Código Civil (Lei 10.406/2002)", "short": "CC",
     "subject": "Exceção de contrato não cumprido.", "expect": ["antes de cumprida", "obrigação"]}

Cada item só vira autoridade quando (1) a norma é resolvida nos dados abertos do
Senado, (2) o texto compilado é capturado no normas.leg.br com recibo, (3) o artigo
é localizado fora de redação riscada e (4) todas as expressões de `expect` aparecem
no próprio artigo. A quarta checagem impede que um número de artigo lembrado de
memória entre no catálogo apontando para outro assunto. O que falha é listado em
`problems` com o trecho encontrado e não gera entrada.

A entrada conferida registra a localização no catálogo; não certifica vigência na
data dos fatos nem incidência no caso — a resposta jurídica refaz a consulta.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from http.client import HTTPException
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "legal-process-parser"))
from scripts.citation_check import segment_articles  # noqa: E402
from scripts.legislation_lookup import article_report, detail, parse_act, resolve  # noqa: E402
from scripts.research_sources import capture  # noqa: E402

ORIGINAL_NOTE = ("Conferido na publicação original (normas.leg.br): alterações posteriores não aparecem no texto; "
                 "conferir a compilação atual.")
RECENT_MARKER_YEAR = 2017


def fold(text: str) -> str:
    """Minúsculas, sem acentos e com espaços simples, para comparar expressões com o texto oficial."""
    plain = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", plain).lower()


def article_label(article: str) -> str:
    match = re.fullmatch(r"(\d+)(?:-?([A-Za-z]{1,2}))?", article.replace(".", "").strip())
    if not match:
        raise ValueError("Artigo inválido: " + article)
    number, suffix = match.group(1), (match.group(2) or "").upper()
    return f"{number}-{suffix}" if suffix else (number + "º" if int(number) < 10 else number)


def kind_for(act: str) -> str:
    kind = parse_act(act)[0]
    return {"CON": "constitution", "EMC": "constitutional_amendment", "DEC": "regulation"}.get(kind, "statute")


def load_act(cache: Path, act: str) -> dict:
    """Resolve, lê os metadados e captura o texto uma vez por norma; reutiliza o que já está em `cache`."""
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (re.sub(r"[^A-Za-z0-9]+", "_", act.upper()) + ".json")
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    kind, number, year = parse_act(act)
    meta = detail(resolve(kind, number, year)["urn"])
    if not meta.get("content_url"):
        raise ValueError("Portal sem texto disponível para " + act)
    receipt = None
    for attempt in range(3):
        try:
            receipt = capture(meta["content_url"], cache / "captures")
            break
        except HTTPException as error:  # leitura truncada do texto compilado: repetir
            if attempt == 2:
                raise OSError("Captura incompleta de " + act + ": " + type(error).__name__) from error
    record = {"act": act, "meta": meta, "text": receipt["text"], "text_hash": receipt["text_hash"],
              "accessed_on": receipt["accessed_on"], "source_url": receipt["url"]}
    path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    return record


def article_text(text: str, article: str) -> str | None:
    wanted = article.replace("º", "").replace("°", "").replace(".", "").replace("-", "").strip().upper()
    for segment in segment_articles(text):
        if segment["number"].upper().replace("-", "") == wanted and not segment["struck"]:
            return text[segment["start"]:segment["end"]]
    return None


def verify(item: dict, cache: Path) -> tuple[dict | None, dict | None]:
    """Devolve (entrada conferida, None) ou (None, problema)."""
    try:
        record = load_act(cache, item["act"])
    except (OSError, ValueError) as error:
        return None, {"id": item["id"], "problem": "norma_nao_capturada", "detail": str(error)}
    body = article_text(record["text"], item["article"])
    if body is None:
        return None, {"id": item["id"], "problem": "artigo_nao_localizado", "detail": item["act"] + " art. " + item["article"]}
    folded = fold(body)
    missing = [term for term in item.get("expect", []) if fold(term) not in folded]
    if missing:
        return None, {"id": item["id"], "problem": "assunto_nao_confere", "missing": missing, "found": re.sub(r"\s+", " ", body)[:420]}
    report = article_report(record["text"], article_label(item["article"]))
    meta = record["meta"]
    original = (meta.get("text_version") or "") != "Current"
    if meta.get("legal_force") == "NotInForce" or meta.get("revoked_by"):
        status, note = "sem_vigencia", "Norma marcada sem vigência no normas.leg.br; usar somente para fatos anteriores, com análise intertemporal."
    elif report.get("whole_article_revoked_or_vetoed"):
        status, note = "revogado", None
    else:
        status, note = "localizado_no_texto_oficial", (ORIGINAL_NOTE if original else None)
    recent = []
    for marker in report.get("markers", []):
        if marker.get("year") and int(marker["year"]) >= RECENT_MARKER_YEAR and marker["text"] not in recent:
            recent.append(marker["text"])
    label = article_label(item["article"])
    entry = {"id": item["id"], "kind": item.get("kind") or kind_for(item["act"]), "label": f"{item['short']}, art. {label}",
             "provision": "art. " + label, "law": item["law"], "subject": item["subject"], "official_url": meta["page_url"],
             "access_tier": "http_capture", "status": status, "status_note": note, "recent_wording_markers": recent[:4],
             "verified": {"method": "normas_leg_br_http_capture", "on": record["accessed_on"], "located": True,
                          "source_url": record["source_url"], "capture_text_hash": record["text_hash"],
                          "legal_force": meta.get("legal_force"), "text_version": meta.get("text_version")}}
    return entry, None


def run(items: list[dict], cache: Path) -> dict:
    entries, problems = [], []
    for item in items:
        entry, problem = verify(item, cache)
        (entries if entry else problems).append(entry or problem)
    return {"checked_on": date.today().isoformat(), "entries": entries, "problems": problems}


def main() -> int:
    parser = argparse.ArgumentParser(description="Confere dispositivos candidatos no texto oficial (normas.leg.br)")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--cache", type=Path, default=Path(".intake-cache"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(json.loads(args.spec.read_text(encoding="utf-8")), args.cache.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=1)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(json.dumps({"entries": len(result["entries"]), "problems": result["problems"]}, ensure_ascii=False, indent=1))
    else:
        print(text)
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
