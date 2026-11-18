"""Localiza pretensões candidatas nos catálogos trabalhista e dos demais ramos a partir de palavras dos fatos.

Combina normalização morfológica em português + prefixos de 5 caracteres, ponderação BM25/IDF sobre o
catálogo dinâmico e expansão controlada de vocabulário coloquial/técnico (peso 1.0 para termos diretos da
consulta e 0.55 para sinônimos expandidos). Devolve apenas pontos de partida: cabimento, vigência e
incidência continuam a depender da leitura dos autos e da consulta oficial da resposta.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

try:
    from .domain_catalog import CATALOG_DIR, catalogs as domain_catalogs
    from .labor_catalog import claim_catalog as labor_claims
except ImportError:
    from domain_catalog import CATALOG_DIR, catalogs as domain_catalogs
    from labor_catalog import claim_catalog as labor_claims

STOPWORDS = set("""a o e de da do das dos em no na nos nas um uma uns umas para por com sem ao aos as os que se sua seu
suas seus ou ate apos sobre entre pela pelo pelas pelos mais menos como quando sob nao sim foi ser ter tem ha meu minha
meus minhas ele ela eles elas isso isto esse essa este esta num numa pro pra lhe lhes me te nos vos ja so bem mal""".split())

ALLOW_SHORT_TOKENS = {"pj", "rj", "hc", "ms", "os", "pi", "ti"} - STOPWORDS
PRESERVE_S_TOKENS = {
    "inss", "loas", "fgts", "icms", "iss", "pis", "cofins", "sus", "ans", "ibs", "cbs",
    "simples", "haveres", "alimentos", "ferias", "juros", "custas", "autos", "bens", "pais",
}

FIELD_WEIGHTS = {
    "label": 3.2,
    "requirements": 1.6,
    "theses": 1.0,
    "typical_requests": 1.1,
    "evidence": 0.65,
}
POLO_ALIASES = {
    "ativo": "claimant_theses",
    "reclamante": "claimant_theses",
    "autor": "claimant_theses",
    "passivo": "defense_theses",
    "reclamada": "defense_theses",
    "reu": "defense_theses",
    "ambos": "both",
}
PREFIX = 5
DIRECT_WEIGHT = 1.0
SYNONYM_WEIGHT = 0.55
BM25_K1 = 1.2
BM25_B = 0.55

# 82 grupos curados de equivalência entre fala coloquial do cliente, siglas forenses e terminologia dos catálogos.
# Entradas de palavra única só são incluídas quando forem siglas/termos juridicamente específicos (evita poluição).
SYNONYM_GROUPS: tuple[tuple[str, ...], ...] = (
    # Consumidor e Bancário
    ("serasa", "spc", "scpc", "boa vista", "nome sujo", "sujaram meu nome", "negativacao", "cadastros credito", "protesto indevido"),
    ("pix", "golpe", "fraude bancaria", "engenharia social", "central falsa", "motoboy cartao", "transacoes nao reconhecidas", "fortuito interno", "boleto falso"),
    ("rmc", "rcc", "cartao consignado", "reserva margem", "emprestimo consignado", "consignacao folha", "desconto aposentadoria"),
    ("juros abusivos", "anatocismo", "capitalizacao juros", "taxa media", "tarifas bancarias", "venda casada"),
    ("busca apreensao veiculo", "financiamento veiculo", "alienacao fiduciaria veiculo", "purgacao mora veiculo", "retomada carro"),
    ("cheque especial", "limite conta", "encargos conta corrente", "rotativo cartao"),
    ("superendividamento", "minimo existencial", "repactuacao dividas", "consumidor superendividado"),
    ("cobranca indevida", "repeticao indebito", "devolucao dobro", "cobrado duas vezes"),
    ("voo atrasado", "cancelamento voo", "overbooking", "pretericao embarque", "extravio bagagem", "transporte aereo"),
    ("corte luz", "corte agua", "suspensao energia", "recuperacao consumo", "toi", "servicos essenciais"),
    ("compra internet", "compra distancia", "direito arrependimento", "produto nao entregue", "estorno compra"),
    ("produto defeito", "vicio produto", "vicio oculto", "assistencia tecnica", "acidente consumo", "fato produto"),
    ("propaganda enganosa", "publicidade enganosa", "descumprimento oferta", "oferta vinculante"),
    # Saúde Suplementar e Pública
    ("home care", "internacao domiciliar", "plano de saude", "negativa cobertura", "rol ans", "terapia aba", "tea", "urgencia emergencia"),
    ("reajuste plano saude", "faixa etaria plano", "reajuste sinistralidade", "rescisao unilateral plano"),
    ("remedio alto custo", "medicamento nao incorporado", "fornecimento medicamento", "rename", "conitec", "acesso medicamento sus"),
    ("fila regulacao", "vaga uti", "leito hospitalar", "cirurgia sus", "exame sus"),
    ("tratamento oncologico", "quimioterapia", "radioterapia", "lei sessenta dias", "neoplasia maligna"),
    ("internacao psiquiatrica", "internacao compulsoria", "dependencia quimica", "saude mental"),
    # Previdenciário e Previdência Complementar
    ("inss", "encostado", "auxilio doenca", "incapacidade temporaria", "incapacidade permanente", "aposentadoria invalidez", "pericia medica"),
    ("limbo previdenciario", "alta inss", "recusa retorno", "inapto retorno trabalho"),
    ("loas", "bpc", "beneficio assistencial", "prestacao continuada", "baixa renda", "miserabilidade", "autismo"),
    ("auxilio acidente", "sequela definitiva", "reducao capacidade laboral"),
    ("ppp", "ltcat", "aposentadoria especial", "tempo especial", "agente nocivo", "insalubridade previdenciaria"),
    ("aposentadoria rural", "segurado especial", "economia familiar", "lavrador", "aposentadoria hibrida"),
    ("pensao por morte", "dependente falecido", "obito segurado", "qualidade segurado"),
    ("salario maternidade", "gestante desempregada", "periodo graca maternidade"),
    ("acrescimo 25", "grande invalidez", "assistencia permanente", "cuidador permanente"),
    ("auxilio reclusao", "segurado preso", "dependente recluso"),
    ("revisao vida toda", "revisao beneficio", "decadencia previdenciaria", "erro calculo beneficio"),
    ("rpps", "aposentadoria servidor", "abono permanencia", "paridade integralidade"),
    ("previdencia complementar", "fundo pensao", "equacionamento deficit", "contribuicao extraordinaria", "patrocinio publico"),
    # Família e Sucessões
    ("pensao atrasada", "alimentos", "prisao civil", "execucao alimentos", "cumprimento alimentos"),
    ("exoneracao alimentos", "revisao alimentos", "reduzir pensao", "aumentar pensao", "maioridade alimentar"),
    ("alimentos gravidicos", "alimentos avoengos", "pensao avos", "gestacao alimentos"),
    ("divorcio", "partilha bens", "comunhao parcial", "comunhao universal", "separacao bens"),
    ("guarda compartilhada", "guarda unilateral", "convivencia familiar", "alienacao parental", "regulamentacao visitas"),
    ("uniao estavel", "morando junto", "companheiro", "dissolucao uniao", "concubinato"),
    ("maria da penha", "violencia domestica", "medida protetiva", "descumprimento protetiva"),
    ("inventario", "heranca", "partilha sucessoria", "espolio", "sobrepartilha"),
    ("testamento", "legitima", "colacao", "doacao inoficiosa", "herdeiro necessario"),
    ("investigacao paternidade", "exame dna", "paternidade socioafetiva", "multiparentalidade", "negatoria paternidade"),
    ("curatela", "interdicao", "tomada decisao apoiada", "incapacidade civil"),
    # Imobiliário, Agrário e Civil
    ("chaves", "atraso obra", "na planta", "incorporadora", "atraso entrega imovel", "lucros cessantes", "juros obra"),
    ("distrato", "desistencia imovel", "retencao parcelas", "rescisao promessa compra"),
    ("vicios construtivos", "infiltracao", "rachadura", "defeito construcao", "solidez seguranca obra"),
    ("usucapiao", "posse mansa", "prescricao aquisitiva", "sem escritura", "reurb"),
    ("adjudicacao compulsoria", "contrato gaveta", "outorga escritura", "promessa quitada"),
    ("despejo", "aluguel atrasado", "locacao", "fiador", "caucao locaticia", "benfeitorias"),
    ("acao renovatoria", "revisional aluguel", "ponto comercial", "locacao comercial"),
    ("condominio atrasado", "debito condominial", "propter rem", "cota condominial"),
    ("leilao imovel", "consolidacao propriedade", "alienacao fiduciaria imovel", "purgacao mora imovel"),
    ("erro medico", "responsabilidade medica", "responsabilidade hospitalar", "negligencia medica", "erro odontologico"),
    ("sinistro", "seguradora", "apolice", "indenizacao securitaria", "negativa cobertura seguro", "agravamento risco"),
    ("arrendamento rural", "parceria rural", "despejo rural", "estatuto terra", "credito rural", "cedula produto rural"),
    # Trabalhista
    ("pejotizacao", "pj", "vinculo empregaticio", "subordinacao", "mei", "sem carteira assinada", "reconhecimento vinculo"),
    ("motorista aplicativo", "entregador aplicativo", "uber", "ifood", "plataformas digitais"),
    ("justa causa", "reversao", "falta grave", "abandono emprego", "desidia"),
    ("rescisao indireta", "falta grave empregador", "atraso reiterado salario", "ausencia deposito fgts"),
    ("hora extra", "horas extras", "banco de horas", "cartao ponto", "jornada trabalho", "sobrejornada"),
    ("intervalo intrajornada", "horario almoco", "pausa refeicao", "supressao intervalo"),
    ("adicional noturno", "trabalho noturno", "hora noturna reduzida", "prorrogacao jornada noturna"),
    ("insalubridade", "periculosidade", "epi", "agente insalubre", "risco acentuado", "inflamaveis", "eletricidade"),
    ("burnout", "doenca ocupacional", "acidente trabalho", "ler dort", "nexo concausal", "cat"),
    ("assedio moral", "assedio sexual", "dano extrapatrimonial", "metas abusivas", "dispensa discriminatoria"),
    ("estabilidade gestante", "gravida dispensada", "garantia gestacao", "estabilidade acidentaria", "cipa"),
    ("salario por fora", "salario extrafolha", "pagamento por fora", "comissoes extrafolha"),
    ("equiparacao salarial", "paradigma salarial", "identidade funcao", "diferencas salariais"),
    ("acumulo funcao", "desvio funcao", "diferencas funcionais", "plus salarial"),
    ("verbas rescisorias", "multa 477", "multa 467", "acerto rescisorio", "baixa ctps"),
    ("teletrabalho", "home office", "ajuda custo internet", "controle jornada remota"),
    # Execução, Tributário e Empresarial
    ("sisbajud", "bacenjud", "penhora", "bloqueio judicial", "conta salario", "impenhorabilidade", "bem de familia"),
    ("cda", "execucao fiscal", "prescricao intercorrente", "excecao pre executividade", "divida ativa"),
    ("redirecionamento socio", "dissolucao irregular", "artigo 135", "responsabilidade tributaria socio"),
    ("simples nacional", "exclusao simples", "reforma tributaria", "ibs", "cbs", "compensacao tributaria"),
    ("recuperacao judicial", "trava bancaria", "stay period", "essencialidade", "bem capital", "falencia"),
    ("idpj", "desconsideracao personalidade", "confusao patrimonial", "desvio finalidade", "grupo economico"),
    ("apuracao haveres", "dissolucao parcial", "exclusao socio", "conflito societario"),
    ("marca", "inpi", "colidencia", "propriedade industrial", "concorrencia desleal", "patente", "direito autoral"),
    ("demurrage", "sobreestadia", "conteiner", "porto", "aduaneiro", "perdimento mercadoria", "transporte maritimo"),
    # Penal, Digital, Administrativo, Ambiental, Infância e Desportivo
    ("whatsapp", "cadeia custodia", "print", "prova digital", "espelhamento", "extracao celular", "nulidade prova"),
    ("busca domiciliar", "busca pessoal", "sem mandado", "invasao domicilio", "reconhecimento fotografico", "reconhecimento pessoas"),
    ("prisao preventiva", "flagrante", "audiencia custodia", "liberdade provisoria", "excesso prazo", "habeas corpus"),
    ("trafico privilegiado", "pequena quantidade", "uso pessoal drogas", "dosimetria pena", "regime inicial"),
    ("anpp", "acordo nao persecucao", "progressao regime", "remicao pena", "execucao penal"),
    ("lgpd", "vazamento dados", "incidente seguranca", "dados pessoais", "dados sensiveis", "anpd", "remocao conteudo"),
    ("concurso publico", "cadastro reserva", "pretericao", "pad", "processo disciplinar", "improbidade administrativa", "licitacao"),
    ("multa ambiental", "ibama", "auto infracao ambiental", "embargo ambiental", "app", "reserva legal", "car"),
    ("eca", "medida socioeducativa", "ato infracional", "vaga creche", "destituicao poder familiar"),
    ("justica desportiva", "atleta profissional", "direito arena", "clausula indenizatoria desportiva", "doping"),
)


def fold(text: str) -> str:
    plain = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", plain.lower()).strip()


def stem_pt(word: str) -> str:
    """Normalização morfológica leve para português jurídico, preservando radicais discriminantes."""
    if word.isdigit() or len(word) <= 3:
        return word
    w = word
    if w.endswith("mente") and len(w) > 7:
        w = w[:-5]
    # Plural normalization before derivational suffixes
    if w not in PRESERVE_S_TOKENS:
        if w.endswith("coes") and len(w) > 6:
            w = w[:-4] + "cao"
        elif w.endswith("soes") and len(w) > 6:
            w = w[:-4] + "sao"
        elif w.endswith("oes") and len(w) > 5:
            w = w[:-3] + "ao"
        elif w.endswith("ais") and len(w) > 5:
            w = w[:-3] + "al"
        elif w.endswith("eis") and len(w) > 5:
            w = w[:-3] + "el"
        elif w.endswith("ois") and len(w) > 5:
            w = w[:-3] + "ol"
        elif w.endswith("ns") and len(w) > 4:
            w = w[:-2] + "m"
        elif w.endswith("res") and len(w) > 5:
            w = w[:-2]
        elif w.endswith("is") and len(w) > 5:
            w = w[:-2] + "il"
        elif w.endswith("s") and len(w) > 3:
            w = w[:-1]
    # Derivational suffixes
    for suffix in (
        "amento", "imento", "mento",
        "acoes", "icoes", "acao", "icao", "cao", "sao",
        "idades", "idade", "dade",
        "abilidades", "abilidade", "ibilidade",
        "arios", "arias", "ario", "aria",
        "istas", "ista", "ismos", "ismo",
        "adores", "adoras", "ador", "adora",
        "ancias", "ancia", "encias", "encia",
        "aveis", "avel", "iveis", "ivel",
        "icos", "icas", "ico", "ica",
    ):
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            w = w[: -len(suffix)]
            break
    # Final thematic vowel strip so "banco"/"bancario" -> "banc" and "atrasou"/"atraso" -> "atras"
    for ending in ("aram", "eram", "iram", "ando", "endo", "indo", "ado", "ido", "ou", "am", "em", "ar", "er", "ir", "o", "a", "e"):
        if w.endswith(ending) and len(w) - len(ending) >= 4:
            w = w[: -len(ending)]
            break
    return w


def _raw_words(text: str) -> list[str]:
    out = []
    for word in fold(text).split():
        if word in STOPWORDS:
            continue
        if len(word) < 3 and not word.isdigit() and word not in ALLOW_SHORT_TOKENS:
            continue
        out.append(word)
    return out


def _token_variants(word: str) -> set[str]:
    if word.isdigit():
        return {word}
    stem = stem_pt(word)
    variants = {word, stem}
    if len(word) >= PREFIX:
        variants.add(word[:PREFIX])
    if len(stem) >= PREFIX:
        variants.add(stem[:PREFIX])
    return variants


def terms(text: str) -> list[str]:
    """Radicais normalizados em português sem palavras vazias; números ficam inteiros."""
    out = []
    for word in _raw_words(text):
        if word.isdigit():
            out.append(word)
        else:
            stem = stem_pt(word)
            out.append(stem if len(stem) <= PREFIX else stem[:PREFIX] if len(word) >= PREFIX and stem == word else stem)
    return out


@lru_cache(maxsize=1)
def _compiled_synonyms() -> list[list[tuple[str, tuple[str, ...], tuple[str, ...]]]]:
    """Pré-compila cada grupo em entradas (frase_folded, raw_words, stems)."""
    compiled = []
    for group in SYNONYM_GROUPS:
        entries = []
        for phrase in group:
            folded = fold(phrase)
            words = tuple(_raw_words(folded))
            stems = tuple(stem_pt(w) for w in words)
            if words:
                entries.append((folded, words, stems))
        if entries:
            compiled.append(entries)
    return compiled


def _expand_synonyms(query_folded: str, query_words: set[str], query_stems: set[str]) -> list[tuple[str, list[str]]]:
    """Retorna clusters acionados pela consulta como pares (gatilho, lista_de_termos_expandidos)."""
    padded = f" {query_folded} "
    triggered: list[tuple[str, list[str]]] = []
    for entries in _compiled_synonyms():
        matched_trigger = None
        for folded, words, stems in entries:
            if len(words) == 1:
                if words[0] in query_words or (len(stems[0]) >= 4 and stems[0] in query_stems):
                    matched_trigger = folded
                    break
            else:
                if f" {folded} " in padded or all(s in query_stems or w in query_words for w, s in zip(words, stems)):
                    matched_trigger = folded
                    break
        if matched_trigger is not None:
            expanded = []
            for _, words, _ in entries:
                for w in words:
                    if w not in query_words and stem_pt(w) not in query_stems:
                        expanded.append(w)
            if expanded:
                triggered.append((matched_trigger, list(dict.fromkeys(expanded))))
    return triggered


def _claim_fields(claim: dict) -> dict[str, str]:
    claimant = " ".join(t["label"] for t in claim.get("claimant_theses", []))
    defense = " ".join(t["label"] for t in claim.get("defense_theses", []))
    return {
        "label": claim["label"],
        "requirements": " ".join(r.replace("_", " ") for r in claim.get("requirements", [])),
        "theses": f"{claimant} {defense}".strip(),
        "claimant_theses": claimant,
        "defense_theses": defense,
        "typical_requests": " ".join(claim.get("typical_requests", [])),
        "evidence": " ".join(claim.get("evidence", [])),
    }


def _catalog_signature() -> tuple[int, tuple[str, ...]]:
    domain_files = tuple(sorted(p.name for p in Path(CATALOG_DIR).glob("*.json"))) if Path(CATALOG_DIR).is_dir() else ()
    return (len(domain_files), domain_files)


@lru_cache(maxsize=2)
def _indexed_corpus(sig: tuple[int, tuple[str, ...]]) -> dict:
    if hasattr(domain_catalogs, "cache_clear"):
        current_keys = tuple(sorted(f"{k}.json" for k in domain_catalogs().keys()))
        if current_keys != sig[1]:
            domain_catalogs.cache_clear()

    raw_rows = []
    for claim in labor_claims().values():
        raw_rows.append((claim["id"], "trabalhista", "trabalhista", claim["label"], _claim_fields(claim),
                         f"labor_catalog.py --claim {claim['id']} --markdown"))
    for key, catalog in domain_catalogs().items():
        for claim in catalog["claims"]:
            raw_rows.append((claim["id"], "ramos", key, claim["label"], _claim_fields(claim),
                             f"domain_catalog.py --claim {claim['id']} --markdown"))

    rows = []
    df: Counter[str] = Counter()
    field_lengths: dict[str, list[int]] = {k: [] for k in ("label", "requirements", "theses", "claimant_theses", "defense_theses", "typical_requests", "evidence")}

    for cid, cat_type, dom, label, fields_text, open_cmd in raw_rows:
        field_tf: dict[str, Counter[str]] = {}
        field_bags: dict[str, set[str]] = {}
        doc_tokens: set[str] = set()
        for fname, text in fields_text.items():
            words = _raw_words(text)
            tf: Counter[str] = Counter()
            bag: set[str] = set()
            for w in words:
                variants = _token_variants(w)
                bag.update(variants)
                for v in variants:
                    tf[v] += 1
            field_tf[fname] = tf
            field_bags[fname] = bag
            field_lengths[fname].append(max(1, len(words)))
            if fname in FIELD_WEIGHTS:
                doc_tokens.update(bag)
        for tok in doc_tokens:
            df[tok] += 1
        rows.append({
            "id": cid,
            "catalog": cat_type,
            "domain": dom,
            "label": label,
            "fields": {k: field_bags[k] for k in FIELD_WEIGHTS},
            "field_tf": field_tf,
            "field_len": {k: max(1, len(_raw_words(fields_text[k]))) for k in field_tf},
            "open": open_cmd,
        })

    total_docs = max(1, len(rows))
    avgdl = {fname: (sum(lengths) / len(lengths) if lengths else 1.0) for fname, lengths in field_lengths.items()}
    idf = {
        tok: math.log(1.0 + (total_docs - freq + 0.5) / (freq + 0.5))
        for tok, freq in df.items()
    }
    default_idf = math.log(1.0 + (total_docs + 0.5) / 0.5)
    return {"rows": rows, "idf": idf, "avgdl": avgdl, "default_idf": default_idf, "total_docs": total_docs}


def clear_cache() -> None:
    """Limpa caches em memória para refletir alterações dinâmicas nos catálogos JSON."""
    _indexed_corpus.cache_clear()
    _compiled_synonyms.cache_clear()
    if hasattr(domain_catalogs, "cache_clear"):
        domain_catalogs.cache_clear()


def search_index() -> list[dict]:
    return _indexed_corpus(_catalog_signature())["rows"]


def _word_hit_score(word: str, row: dict, corpus: dict, polo_target: str | None) -> float:
    variants = _token_variants(word)
    best = 0.0
    idf_map = corpus["idf"]
    avgdl_map = corpus["avgdl"]
    for fname, base_weight in FIELD_WEIGHTS.items():
        bag = row["fields"][fname]
        matched_variants = bag.intersection(variants)
        if not matched_variants:
            continue
        tf = max(row["field_tf"][fname][v] for v in matched_variants)
        dl = row["field_len"][fname]
        avgdl = avgdl_map[fname]
        bm25_tf = (tf * (BM25_K1 + 1.0)) / (tf + BM25_K1 * (1.0 - BM25_B + BM25_B * (dl / avgdl)))
        # Prefer the most specific variant that actually exists in the document
        tok_idf = max(idf_map.get(v, 1.0) for v in matched_variants)
        weight = base_weight
        if fname == "theses" and polo_target in ("claimant_theses", "defense_theses"):
            if row["field_tf"][polo_target] and any(row["field_tf"][polo_target][v] > 0 for v in matched_variants):
                weight *= 1.35
        score = weight * bm25_tf * tok_idf
        if score > best:
            best = score
    return best


def search(query: str, *, limit: int = 8, domain: str | None = None, polo: str | None = None) -> dict:
    raw_query_words = list(dict.fromkeys(_raw_words(query)))
    wanted = list(dict.fromkeys(terms(query)))
    if not raw_query_words or not wanted:
        raise ValueError("Consulta sem termos pesquisáveis")
    polo_target = None
    if polo is not None:
        key = fold(polo)
        if key not in POLO_ALIASES:
            raise ValueError("Polo deve ser ativo, passivo, ambos, reclamante ou reclamada")
        polo_target = POLO_ALIASES[key]

    corpus = _indexed_corpus(_catalog_signature())
    query_folded = fold(query)
    query_word_set = set(raw_query_words)
    query_stem_set = {stem_pt(w) for w in raw_query_words}
    synonym_clusters = _expand_synonyms(query_folded, query_word_set, query_stem_set)
    expanded_vocab = sorted({w for _, words in synonym_clusters for w in words})

    results = []
    for row in corpus["rows"]:
        if domain and row["domain"] != domain:
            continue
        score = 0.0
        matched_direct: set[str] = set()
        matched_synonyms: set[str] = set()

        for word in raw_query_words:
            hit = _word_hit_score(word, row, corpus, polo_target)
            if hit > 0.0:
                score += DIRECT_WEIGHT * hit
                matched_direct.add(stem_pt(word) if not word.isdigit() else word)

        for _, syn_words in synonym_clusters:
            cluster_hits = []
            seen_syn_stems: set[str] = set()
            for sw in syn_words:
                s_stem = stem_pt(sw)
                if s_stem in seen_syn_stems or s_stem in matched_direct:
                    continue
                seen_syn_stems.add(s_stem)
                sh = _word_hit_score(sw, row, corpus, polo_target)
                if sh > 0.0:
                    cluster_hits.append((sh, sw))
            if cluster_hits:
                cluster_hits.sort(reverse=True)
                # Usa até os 2 melhores termos distintos do grupo com peso 0.55 (termos diretos têm peso 1.0)
                for idx, (sh, sw) in enumerate(cluster_hits[:2]):
                    decay = 1.0 if idx == 0 else 0.5
                    score += SYNONYM_WEIGHT * decay * sh
                    matched_synonyms.add(sw)

        if matched_direct or matched_synonyms:
            direct_coverage = len(matched_direct) / len(raw_query_words)
            syn_coverage = min(0.55, 0.25 * len(matched_synonyms))
            effective_coverage = max(direct_coverage, syn_coverage) if not matched_direct else min(1.0, direct_coverage + 0.15 * len(matched_synonyms))
            final_score = round(score * (0.5 + effective_coverage), 2)
            matched_all = sorted(matched_direct | {f"~{s}" for s in matched_synonyms}) if not matched_direct else sorted(matched_direct)
            entry = {
                "id": row["id"],
                "domain": row["domain"],
                "label": row["label"],
                "score": final_score,
                "matched_terms": matched_all,
                "open": row["open"],
            }
            if matched_synonyms:
                entry["synonym_matches"] = sorted(matched_synonyms)
            results.append(entry)

    results.sort(key=lambda r: (-r["score"], r["id"]))
    top = results[: max(1, limit)]
    domains_represented = list(dict.fromkeys(r["domain"] for r in top))
    out = {
        "query": query,
        "terms": wanted,
        "expanded_terms": expanded_vocab,
        "domains_represented": domains_represented,
        "results": top,
        "legal_status": "candidate_claims_only",
        "note": "Lista de partida por semelhança de palavras; confirmar ramo, fatos e cabimento antes de abrir as pretensões.",
    }
    if polo is not None:
        out["polo"] = fold(polo)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca pretensões candidatas nos catálogos a partir de palavras dos fatos")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--domain", help="trabalhista ou chave do ramo (ex.: consumidor)")
    parser.add_argument("--polo", help="ativo, passivo, ambos, reclamante ou reclamada")
    args = parser.parse_args()
    try:
        print(json.dumps(search(args.query, limit=args.limit, domain=args.domain, polo=args.polo), ensure_ascii=False, indent=2))
        return 0
    except ValueError as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
