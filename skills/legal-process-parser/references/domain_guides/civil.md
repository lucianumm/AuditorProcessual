# Direito Civil — Obrigações, Contratos, Responsabilidade e Posse

Catálogo: `domain_catalogs/civil.json`.

## 1. Regime e competência
- Rege relações paritárias e civis sob o Código Civil (Lei 10.406/2002), afastando-se a inversão ope legis ou facilitada do CDC quando ausente relação de consumo (interpretação dos negócios empresariais e paritários conforme usos, boa-fé e alocação de riscos — CC, arts. 113 e 421-A, Lei 13.874/2019). Competência da Justiça Estadual (ou JEC até 40 SM sem perícia complexa — Lei 9.099/1995).

## 2. Teses do credor, lesado ou possuidor
- **Inadimplemento, resolução e revisão:** exija perdas e danos, cláusula penal ou execução específica (CC, arts. 389, 408 e 475), oponha exceção de contrato não cumprido (art. 476) e postule resolução ou revisão por onerosidade excessiva decorrente de evento extraordinário e imprevisível (arts. 317 e 478).
- **Responsabilidade civil, posse e crédito:** demonstre conduta ilícita ou atividade de risco habitual (CC, arts. 186, 187 e 927, parágrafo único), dano emergente, lucros cessantes, pensão por redução da capacidade laborativa (art. 950, inclusive em parcela única com redutor prudencial) e dano moral/estético cumuláveis (Súmula 387 STJ). Proteja a posse com liminar de força nova dentro de ano e dia (CPC, art. 558), cobre títulos prescritos via ação monitória (CPC, art. 700; Súmulas 299 e 503 STJ) e reprima fraude contra credores ou à execução (CC, art. 158; Súmula 375 STJ) e abuso da personalidade jurídica (CC, art. 50; CPC, arts. 133–137).

## 3. Teses do devedor ou demandado
- **Excludentes, alocação de riscos e redução equitativa:** sustente fortuito/força maior (CC, art. 393), culpa exclusiva ou concorrente da vítima (art. 945), adimplemento substancial que veda a resolução drástica, validade da matriz contratual de riscos (art. 421-A) e **redução equitativa obrigatória** da cláusula penal manifestamente excessiva ou parcialmente cumprida (art. 413) e da indenização desproporcional ao grau de culpa (art. 944, parágrafo único).
- **Prescrição, impenhorabilidade e IDPJ:** oponha prescrição trienal para reparação civil e enriquecimento sem causa (CC, art. 206, § 3º, IV e V) e quinquenal para dívidas líquidas em instrumento (art. 206, § 5º, I), impenhorabilidade do bem de família e de verbas alimentares (Lei 8.009/1990; CPC, art. 833) e ausência de desvio de finalidade ou confusão patrimonial específica para afastar o IDPJ na Teoria Maior (CC, art. 50).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Separar termo inicial dos juros de mora e da correção monetária: responsabilidade extracontratual com juros desde o evento danoso (Súmula 54 STJ), contratual desde a citação (CC, art. 405) e correção do dano moral desde o arbitramento (Súmula 362 STJ). Em conflito possessório coletivo ou de força velha, observar audiência de mediação e inspeção (CPC, art. 565; ADPF 828 STF).

## 5. Marcos intertemporais e motores
- **20/09/2019 (Lei 13.874/2019 — Liberdade Econômica: arts. 50, 113 e 421-A CC)** · **26/08/2021 (Lei 14.195/2021 — prescrição intercorrente art. 921 CPC)** · **14/07/2023 (Lei 14.620/2023 — título executivo eletrônico sem testemunhas, art. 784, § 4º, CPC)** · **30/08/2024 (Lei 14.905/2024 — IPCA + taxa legal `SELIC - IPCA` com piso zero, arts. 389 e 406 CC)**.
- Motores: `civil_monetary_engine.py` (`civil_lei_14905`), `limitation_checker.py`, `deadline_calculator.py`, `domain_catalog.py` e `citation_check.py`.
