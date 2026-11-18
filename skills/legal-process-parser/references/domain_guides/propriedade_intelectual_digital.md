# Propriedade Intelectual, Inovação e Direito Digital

Catálogo: `domain_catalogs/propriedade_intelectual_digital.json`.

## Enquadramento e escopo
Rege marcas, patentes, desenhos industriais, *trade dress*, concorrência desleal e segredo industrial (Lei 9.279/1996 — LPI), direitos autorais e conexos (Lei 9.610/1998), software e SaaS (Lei 9.609/1998), franquias (Lei 13.966/2019), nomes de domínio `.br`, plataformas digitais (Lei 12.965/2014) e conflitos de IA, *scraping* e mídia sintética. Pretensões: `pid_trademark_infringement_collision`, `pid_trademark_nullity_forfeiture`, `pid_trade_dress_unfair_competition`, `pid_patents_industrial_design`, `pid_copyright_plagiarism_image`, `pid_software_saas_licensing`, `pid_domain_names_saci_cybersquatting`, `pid_platform_liability_content_removal`, `pid_trade_secret_knowhow_nda`, `pid_franchising_cof_annulment`, `pid_ai_scraping_deepfake_synthetic`, `pid_tech_transfer_inpi_royalties` e `pid_keyword_advertising_parasitic_search`.

## Polo ativo (titular, autor, franqueado ou ofendido digital)
- **PI, *trade dress* e franquia:** comprove certificado no INPI (ou precedência de 6 meses — art. 129, § 1º, LPI), risco de confusão/parasitismo (inclusive *keyword advertising*) e postule tutela inibitória (art. 209, § 1º) e lucros cessantes pelo critério mais favorável do art. 210. Em franquia sem entrega da COF com 10 dias de antecedência, requeira anulação e restituição integral (Lei 13.966/2019, art. 2º, § 2º).
- **Autoral, software, IA e plataformas:** indique URLs exatas para remoção (Lei 12.965/2014, art. 19, § 1º; salvo nudez privada do art. 21 e deveres do Tema 987 STF). Invoque dano *in re ipsa* no uso comercial de imagem (Súmula 403 STJ), titularidade do contratante sobre software (Lei 9.609/1998, art. 4º) e proteção contra *deepfakes* e segredo violado (LPI, art. 206).

## Polo passivo (concorrente, plataforma, franqueador ou usuário)
- **Limites da exclusividade:** oponha especialidade de classes, expressões comuns/descritivas (LPI, art. 124, VI), exaustão de direitos (art. 132), exceção Bolar (art. 43, VII) ou nulidade patentária incidental como matéria de defesa na Justiça Estadual (art. 56, § 1º).
- **Autoral e internet:** sustente desenvolvimento independente de código, limitações autorais de citação/paródia (Lei 9.610/1998, arts. 46–48), falta de URL específica, guarda limitada a 6 meses dos registros de aplicação (Lei 12.965/2014, art. 15) e prescrição trienal (CC, art. 206, § 3º, V) ou quinquenal (LPI, art. 225; art. 174 salvo má-fé da CUP, art. 6º bis).

## Magistratura e gabinete (CPC, art. 489, § 1º)
- Separar a **competência da Justiça Federal** nas ações de nulidade de registro com o INPI (CF, art. 109, I; LPI, arts. 57 e 175) da **Justiça Estadual** nas ações de infração, *trade dress* e indenização entre particulares. Evitar juízo puramente visual sem perícia técnica em patentes, código-fonte ou *trade dress* controvertido e resguardar segredo industrial (LPI, art. 206).

## Marcos intertemporais
- **Lei 12.965/2014 e Temas 533 e 987 STF:** responsabilidade civil de provedores de aplicações (conferir tese e modulação no portal do STF).
- **Lei 13.966/2019 (vigência em 27/03/2020):** novo marco de franquias e COF.
- **ADI 5529 STF (12/05/2021):** inconstitucionalidade do parágrafo único do art. 40 da LPI com modulação setorial.

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** certificado/carta-patente no INPI, ata notarial com URLs e hashes (CPC, art. 384), amostras comparativas ou COF com recibo datado.
- **Prova futura/instrutória:** perícia de engenharia/química (patentes), comparação pericial de código-fonte, pesquisa mercadológica e liquidação contábil do art. 210 da LPI.

## Integração com os motores determinísticos
Acione `domain_catalog.py --domain propriedade_intelectual_digital`, selecione peças (`oposicao_nulidade_administrativa_inpi`, `ata_notarial`, `producao_antecipada_provas`) em `procedural_catalog.py`, confira prescrição em `limitation_checker.py`, calcule *royalties* e lucros cessantes em `civil_monetary_engine.py` e valide citações em `response_research.py`.
