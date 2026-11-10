"""Localiza norma federal e captura o texto compilado vigente por via oficial do Congresso.

Rota alternativa ao Planalto quando o portal recusa o acesso automatizado:

1. Dados abertos do Senado (legis.senado.leg.br/dadosabertos) resolvem tipo,
   número e ano na data de assinatura e no identificador URN LexML.
2. normas.leg.br (Senado e Câmara) fornece metadados (data, DOU, ementa) e a
   "Compilação Monovigente" da Câmara, com marcas como "(Revogado pela Lei...)",
   "(Artigo acrescido pela...)" e "(... com redação dada pela...)".
3. O texto é capturado por research_sources.capture, que preserva bytes e recibo.

A compilação é texto de referência ("UnofficialLegalValue" no próprio portal);
o valor oficial é o da publicação no DOU. A localização de um artigo sem marca de
revogação não certifica vigência na data dos fatos nem incidência no caso.
"""
from __future__ import annotations

import argparse
import json
import re
from http.client import HTTPException
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from .research_sources import USER_AGENT, capture
    from .citation_check import segment_articles, units, version_markers, normalize
except ImportError:
    from research_sources import USER_AGENT, capture
    from citation_check import segment_articles, units, version_markers, normalize

SENADO_LIST = "https://legis.senado.leg.br/dadosabertos/legislacao/lista?tipo={kind}&numero={number}&ano={year}"
SENADO_CONSTITUTION = "https://legis.senado.leg.br/dadosabertos/legislacao/lista?tipo=CON&ano=1988"
NORMAS_DETAIL = "https://normas.leg.br/api/public/normas?urn={urn}&tipo_documento=maior-detalhe"
NORMAS_PAGE = "https://normas.leg.br/?urn={urn}"
# Siglas do Senado → tipo LexML.
KINDS = {"LEI": "lei", "LCP": "lei.complementar", "DEL": "decreto.lei", "DEC": "decreto",
         "EMC": "emenda.constitucional", "MPV": "medida.provisoria"}
ALIASES = {"LC": "LCP", "DL": "DEL", "EC": "EMC", "MP": "MPV", "DECRETO": "DEC"}


def _get_json(url: str, timeout: int = 60, attempts: int = 3) -> dict:
    """Lê JSON oficial; repete a leitura quando a resposta chega truncada (metadados grandes do normas.leg.br)."""
    last: Exception | None = None
    for _ in range(max(1, attempts)):
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}), timeout=timeout) as response:
                return json.loads(response.read())
        except (HTTPException, TimeoutError, json.JSONDecodeError) as error:
            last = error
    raise OSError("Resposta incompleta do portal oficial: " + type(last).__name__)


def parse_act(value: str) -> tuple[str, str, str]:
    """'LEI:14647:2023', 'LC:150:2015' ou 'CF'."""
    if value.strip().upper() in {"CF", "CON", "CF/1988"}:
        return "CON", "", "1988"
    parts = [part.strip() for part in value.split(":")]
    if len(parts) != 3 or not parts[1].isdigit() or not re.fullmatch(r"\d{4}", parts[2]):
        raise ValueError("Ato no formato TIPO:NUMERO:ANO (ex.: LEI:14647:2023) ou CF")
    kind = ALIASES.get(parts[0].upper(), parts[0].upper())
    if kind not in KINDS:
        raise ValueError("Tipo não suportado: " + parts[0])
    return kind, parts[1], parts[2]


def resolve(kind: str, number: str, year: str) -> dict:
    """Tipo, número e ano → data de assinatura e URN, pelos dados abertos do Senado."""
    url = SENADO_CONSTITUTION if kind == "CON" else SENADO_LIST.format(kind=kind, number=number, year=year)
    payload = _get_json(url)
    docs = payload.get("ListaDocumento", {}).get("documentos", {}).get("documento", [])
    docs = [docs] if isinstance(docs, dict) else docs
    if kind == "CON":
        docs = [doc for doc in docs if str(doc.get("tipo", "")).startswith("CON-v")] or docs
    if not docs:
        raise ValueError("Ato não localizado nos dados abertos do Senado")
    doc = docs[0]
    match = re.search(r"(\d{4}-\d{2}-\d{2})$", doc.get("norma", ""))
    if not match:
        raise ValueError("Identificador sem data de assinatura")
    signed = match.group(1)
    urn = ("urn:lex:br:federal:constituicao:1988-10-05;1988" if kind == "CON"
           else "urn:lex:br:federal:" + KINDS[kind] + ":" + signed + ";" + number)
    return {"kind": kind, "number": number, "year": year, "signed_on": signed, "urn": urn,
            "name": doc.get("normaNome"), "summary": doc.get("ementa"), "senado_id": doc.get("id"),
            "resolver_url": url}


def detail(urn: str) -> dict:
    payload = _get_json(NORMAS_DETAIL.format(urn=quote(urn, safe=":;-.")), timeout=120)
    encodings = payload.get("encoding") or []
    encodings = [encodings] if isinstance(encodings, dict) else [item for item in encodings if isinstance(item, dict)]
    with_text = [item for item in encodings if item.get("contentUrl")]
    current = next((item for item in with_text if item.get("version") == "Current"), None)
    original = next((item for item in with_text if item.get("version") == "Original"), None)
    chosen = current or original or (with_text[0] if with_text else None)
    content = (chosen or {}).get("contentUrl")
    if content:
        content = content.replace("/api/binario/", "/api/public/binario/")
    reverse = payload.get("@reverse") if isinstance(payload.get("@reverse"), dict) else {}
    repealers = reverse.get("legislationRepeals") or []
    repealers = [repealers] if isinstance(repealers, dict) else repealers
    revoked_by = [str(item.get("@id", "")).split("urn=")[-1] for item in repealers if isinstance(item, dict)]
    force = payload.get("legislationLegalForce")
    if chosen is None:
        text_note = "Portal sem texto disponível; conferir a publicação no DOU ou outra fonte oficial."
    elif (chosen.get("version") or "") != "Current":
        text_note = ("Texto da publicação original: alterações e revogações posteriores não aparecem nele; "
                     "conferir legal_force, revoked_by e a compilação atualizada.")
    else:
        text_note = "Compilação de referência; valor oficial é o da publicação no DOU. Pode não refletir alteração recente."
    return {"urn": urn, "headline": payload.get("headline"), "signed_on": payload.get("legislationDate"),
            "dou_published_on": payload.get("datePublished"), "summary": payload.get("abstract"),
            # "NotInForce" no portal indica norma sem vigência (ex.: revogada), mesmo que o texto compilado não traga a marca.
            "legal_force": force, "revoked_by": revoked_by,
            "text_version": (chosen or {}).get("version"),
            "text_kind": (chosen or {}).get("additionalType") or (chosen or {}).get("name"),
            "legal_value_note": text_note, "portal_updated_on": payload.get("sdDatePublished"),
            "content_url": content, "page_url": NORMAS_PAGE.format(urn=urn)}


def article_report(text: str, article: str) -> dict:
    """Localiza o artigo e lista as marcas de versão do caput e dos parágrafos."""
    wanted = article.replace("º", "").replace("°", "").replace(".", "").strip().upper()
    for segment in segment_articles(text):
        if segment["number"].upper() != wanted or segment["struck"]:
            continue
        body = text[segment["start"]:segment["end"]]
        rows = units(body)
        caput = rows[0][1]
        whole_revoked = bool(re.match(r"^Art\.?\s*[\d.]+[º°]?(?:-[A-Z]{1,2})?\s*[.\-–—]?\s*\((?:Revogad|Vetad)", normalize(body), re.I))
        return {"article": article, "located": True, "whole_article_revoked_or_vetoed": whole_revoked,
                "caput_excerpt": caput[:240],
                "markers": [dict(marker, unit=label) for label, unit in rows for marker in version_markers(unit)]}
    return {"article": article, "located": False}


def lookup(output: Path, act: str, articles: list[str] | None = None, *, capture_text: bool = True) -> dict:
    kind, number, year = parse_act(act)
    resolved = resolve(kind, number, year)
    meta = detail(resolved["urn"])
    result = {"resolved": resolved, "normas": meta}
    if meta.get("legal_force") == "NotInForce" or meta.get("revoked_by"):
        result["warning"] = ("Norma marcada sem vigência ou revogada no portal (" + ", ".join(meta.get("revoked_by") or ["sem ato indicado"]) +
                             "); usar somente para fatos anteriores, com análise intertemporal.")
    if capture_text and meta.get("content_url"):
        receipt = capture(meta["content_url"], output)
        result["capture"] = {key: receipt[key] for key in ("capture_id", "url", "accessed_on", "raw_content_hash", "text_hash", "method")}
        result["articles"] = [article_report(receipt["text"], item) for item in (articles or [])]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve e captura norma federal por via oficial do Congresso (normas.leg.br)")
    parser.add_argument("output", type=Path)
    parser.add_argument("--act", required=True, help="TIPO:NUMERO:ANO (LEI, LC, DL, DEC, EC, MP) ou CF")
    parser.add_argument("--article", action="append", default=[], help="Artigo a localizar (ex.: 442, 59-A)")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    try:
        result = lookup(args.output.resolve(), args.act, args.article, capture_text=not args.metadata_only)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
