"""Reconfere no texto oficial as autoridades legislativas pendentes do catálogo de ramos.

Uso de manutenção (não é carregado pela skill em atendimento):

    python scripts/catalog_recheck.py --cache .intake-cache --report conferencia.json [--apply] [--limit N]

Para cada autoridade `pendente_conferencia_oficial` de lei, código, decreto ou da
Constituição, a norma é resolvida nos dados abertos do Senado, o texto compilado é
capturado no normas.leg.br com recibo (mesma via de `catalog_intake.py`), o artigo é
localizado fora de redação riscada e o assunto curado precisa encontrar apoio no
próprio artigo (palavras significativas do assunto presentes no texto do artigo).
Só então a entrada passa a `localizado_no_texto_oficial` (ou `revogado`/`sem_vigencia`
quando o portal assim indicar). O que falha continua pendente e vai para o relatório
com o motivo. A localização não certifica vigência na data dos fatos nem incidência.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from catalog_intake import article_text, fold, load_act, ORIGINAL_NOTE, RECENT_MARKER_YEAR  # noqa: E402

sys.path.insert(0, str(ROOT / "skills" / "legal-process-parser"))
from scripts.legislation_lookup import article_report  # noqa: E402

CATALOG = ROOT / "skills" / "legal-process-parser" / "references" / "domain_authorities.json"
NAMED = {"codigo civil": "LEI:10406:2002", "codigo de processo civil": "LEI:13105:2015", "codigo tributario nacional": "LEI:5172:1966",
         "codigo de defesa do consumidor": "LEI:8078:1990", "constituicao federal": "CF", "codigo penal": "DL:2848:1940",
         "codigo de processo penal": "DL:3689:1941", "consolidacao das leis do trabalho": "DL:5452:1943"}
ACT = re.compile(r"(lei complementar|decreto-lei|decreto|medida provisoria|lei)\s+(?:n[.ºo°]*\s*)?([\d.]+(?:-\d+)?)\s*/\s*(\d{4})")
KIND = {"lei complementar": "LC", "decreto-lei": "DL", "decreto": "DEC", "medida provisoria": "MPV", "lei": "LEI"}
STOP = set("a ao aos as com como da das de do dos e em entre na nas no nos o os ou para pela pelas pelo pelos por "
           "que se sem sob sobre um uma regras regra hipoteses hipotese casos caso efeitos efeito".split())


def act_for(law: str) -> str | None:
    folded = fold(law)
    match = ACT.search(folded)
    if match:
        return f"{KIND[match.group(1)]}:{match.group(2).replace('.', '')}:{match.group(3)}"
    return next((act for name, act in NAMED.items() if folded.startswith(name)), None)


def article_of(provision: str) -> str | None:
    match = re.match(r"\s*art\.?\s*(\d+(?:\.\d+)?)(?:\s*[-–]\s*([A-Za-z]{1,2}))?", provision or "", re.I)
    if not match:
        return None
    return match.group(1).replace(".", "") + ("-" + match.group(2).upper() if match.group(2) else "")


# Words present in almost every article; they never confirm the subject by themselves.
GENERIC = {"direi", "pesso", "prazo", "legal", "norma", "previs", "aplic", "regim", "geral", "publi", "jurid",
           "efeit", "hipot", "proce", "dispo", "termo", "forma", "auton", "compe", "obrig", "dever"}


def subject_support(subject: str, body: str) -> tuple[list[str], list[str]]:
    words = [w for w in re.findall(r"[a-z]+", fold(subject)) if len(w) >= 5 and w not in STOP]
    stems = list(dict.fromkeys(w[:max(5, len(w) - 3)] for w in words))
    text = fold(body)
    found = [s for s in stems if s in text]
    return found, stems


def subject_confirmed(found: list[str], stems: list[str]) -> bool:
    specific = [s for s in found if s[:5] not in GENERIC]
    return len(found) >= (1 if len(stems) <= 2 else 2) and bool(specific)


def recheck(entry: dict, cache: Path) -> tuple[dict | None, dict | None]:
    act, article = act_for(entry.get("law", "")), article_of(entry.get("provision", ""))
    if not act or not article:
        return None, {"id": entry["id"], "problem": "norma_ou_artigo_nao_identificado", "law": entry.get("law"), "provision": entry.get("provision")}
    try:
        record = load_act(cache, act)
    except (OSError, ValueError, KeyError) as error:
        return None, {"id": entry["id"], "problem": "norma_nao_capturada", "detail": f"{act}: {error}"}
    body = article_text(record["text"], article)
    if body is None:
        return None, {"id": entry["id"], "problem": "artigo_nao_localizado", "detail": f"{act} art. {article}"}
    found, stems = subject_support(entry.get("subject", ""), body)
    if not subject_confirmed(found, stems):
        return None, {"id": entry["id"], "problem": "assunto_nao_confere", "subject": entry.get("subject"),
                      "matched": found, "found": re.sub(r"\s+", " ", body)[:300]}
    meta = record["meta"]
    report = article_report(record["text"], article)
    if meta.get("legal_force") == "NotInForce" or meta.get("revoked_by"):
        status, note = "sem_vigencia", "Norma marcada sem vigência no normas.leg.br; usar somente para fatos anteriores, com análise intertemporal."
    elif report.get("whole_article_revoked_or_vetoed"):
        status, note = "revogado", None
    else:
        status, note = "localizado_no_texto_oficial", (ORIGINAL_NOTE if (meta.get("text_version") or "") != "Current" else None)
    recent = list(dict.fromkeys(m["text"] for m in report.get("markers", [])
                                if m.get("year") and int(m["year"]) >= RECENT_MARKER_YEAR))[:4]
    updated = dict(entry, status=status, status_note=note, recent_wording_markers=recent, official_url=meta.get("page_url") or entry["official_url"],
                   verified={"method": "normas_leg_br_http_capture", "on": record["accessed_on"], "located": True,
                             "source_url": record["source_url"], "capture_text_hash": record["text_hash"],
                             "legal_force": meta.get("legal_force"), "text_version": meta.get("text_version"),
                             "subject_terms_matched": found})
    return updated, None


def revalidate(cache: Path, report: Path) -> dict:
    """Offline second pass over entries confirmed by this script, with the stricter subject rule."""
    import subprocess
    original = {a["id"]: a for a in json.loads(subprocess.run(
        ["git", "show", "HEAD:" + CATALOG.relative_to(ROOT).as_posix()], cwd=ROOT, capture_output=True, text=True, check=True).stdout)["authorities"]}
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    reverted = []
    for index, entry in enumerate(data["authorities"]):
        matched = entry.get("verified", {}).get("subject_terms_matched")
        if matched is None or original.get(entry["id"], {}).get("status") != "pendente_conferencia_oficial":
            continue
        record = load_act(cache, act_for(entry["law"]))
        body = article_text(record["text"], article_of(entry["provision"])) or ""
        found, stems = subject_support(entry.get("subject", ""), body)
        if not subject_confirmed(found, stems):
            data["authorities"][index] = original[entry["id"]]
            reverted.append({"id": entry["id"], "subject": entry.get("subject"), "matched": found})
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"reverted_to_pending": reverted}
    report.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconfere autoridades legislativas pendentes no texto oficial")
    parser.add_argument("--cache", type=Path, default=Path(".intake-cache"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="grava as entradas conferidas no catálogo")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--revalidate", action="store_true", help="segunda passagem offline (cache) com a regra de assunto estrita")
    args = parser.parse_args()
    if args.revalidate:
        print(json.dumps({"reverted": len(revalidate(args.cache.resolve(), args.report)["reverted_to_pending"])}))
        return 0
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    pending = [a for a in data["authorities"] if a["status"] == "pendente_conferencia_oficial"
               and a["kind"] in {"statute", "constitution", "regulation", "constitutional_amendment"}][:args.limit]
    updates, problems = {}, []
    for index, entry in enumerate(pending, 1):
        updated, problem = recheck(entry, args.cache.resolve())
        if updated:
            updates[entry["id"]] = updated
        else:
            problems.append(problem)
        if index % 25 == 0:
            print(f"{index}/{len(pending)} conferidas: {len(updates)} localizadas, {len(problems)} pendentes", file=sys.stderr)
    if args.apply and updates:
        data["authorities"] = [updates.get(a["id"], a) for a in data["authorities"]]
        CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"checked_on": date.today().isoformat(), "examined": len(pending), "located": len(updates),
              "still_pending": len(problems), "problems": problems}
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "problems"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
