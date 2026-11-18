# Prática recursal e tribunais superiores: admissibilidade e dialeticidade

Guia aplicável à análise de cabimento, interposição ou contrarrazões de recursos e ações autônomas de impugnação (`apelacao_civel`, `agravo_instrumento`, `embargos_declaracao`, `agravo_interno_civel`, `recurso_inominado`, `recurso_especial`, `recurso_extraordinario`, `reclamacao_constitucional` e `acao_rescisoria`).

## 1. Decomposição estrutural da decisão recorrida
Decomponha o pronunciamento por capítulos independentes no `legal_review.json` antes de redigir:
1. **Natureza e via adequada:** separe despacho irrecorrível (CPC, art. 1.001), interlocutória agravável pelo rol legal ou por taxatividade mitigada diante da inutilidade do julgamento diferido (art. 1.015; Tema 988 STJ), decisão parcial de mérito (art. 356, § 5º — agravável sob pena de coisa julgada), sentença (art. 1.009, incluindo preliminares contra interlocutórias não preclusas do § 1º) e acórdão.
2. **Inventário de fundamentos autônomos:** liste todos os fundamentos suficientes, por si sós, para manter cada capítulo decisório. Omitir ataque específico a qualquer fundamento autônomo inviabiliza o conhecimento por violação à dialeticidade (CPC, arts. 932, III, 1.010, III, e 1.021, § 1º; Súmulas 283 e 284 STF; Súmula 182 STJ).

## 2. Pressupostos de admissibilidade e efeito suspensivo
- **Tempestividade e preparo:** valide intimação, prazo e calendário em `deadline_calculator.py`. Exija documento oficial de feriado local ou indisponibilidade eletrônica no ato da interposição (CPC, art. 1.003, § 6º) e confira preparo, dispensa legal ou recolhimento em dobro (art. 1.007, §§ 2º e 4º).
- **Efeito suspensivo (`ope legis` vs. `ope judicis`):** fora do art. 1.012, *caput*, do CPC, formule pedido autônomo (arts. 995, parágrafo único, 1.012, § 4º, 1.019, I, e 1.029, § 5º) demonstrando probabilidade de provimento e risco concreto de dano grave.

## 3. Embargos de declaração e prequestionamento (CPC, arts. 1.022–1.026)
- Restrinja aclaratórios a **obscuridade, contradição interna** (entre premissas e dispositivo da própria decisão), **omissão** (incluindo os vícios do art. 489, § 1º, e precedentes do art. 927 do CPC) ou **erro material**.
- **Prequestionamento ficto (art. 1.025):** persistindo omissão relevante no tribunal local após aclaratórios, suscite preliminar de violação ao art. 1.022 c/c art. 1.025 no REsp para habilitar o exame da tese federal no STJ (observada a Súmula 356 no STF). Alerte sobre multa protelatória (art. 1.026, §§ 2º–3º).

## 4. Filtros estritos de Recurso Especial (STJ) e Extraordinário (STF)
1. **Relevância federal (CF, art. 105, §§ 2º–3º — EC 125/2022) e Repercussão Geral (CPC, art. 1.035):** abra preliminar específica demonstrando transcendência jurídica, econômica, social ou política.
2. **Óbices sumulares:** diferencie **revaloração jurídica de fatos incontroversos descritos no acórdão** (admissível) de **reexame fático-probatório ou contratual** (vedado pelas Súmulas 5 e 7 STJ e 279 e 454 STF). No dissídio, realize cotejo analítico e supere a Súmula 83 do STJ.
3. **Bifurcação contra inadmissão na origem (arts. 1.030 e 1.042):** contra negativa fundada em Tema de Repercussão Geral ou Repetitivo (art. 1.030, I), cabe **exclusivamente agravo interno** na origem (§ 2º) demonstrando *distinguishing*; contra óbices comuns (art. 1.030, V), cabe **agravo em REsp/RE** (art. 1.042), configurando erro grosseiro a troca das vias.

## 5. Reforma vs. cassação e contrarrazões
- Vincule `error in procedendo` a pedido de **anulação/cassação** (salvo causa madura — art. 1.013, § 3º) e `error in judicando` a **reforma**, atento aos honorários recursais (art. 85, § 11).
- Nas **contrarrazões**, argua preliminares de não conhecimento (intempestividade, deserção, ausência de dialeticidade, inovação recursal, Súmulas 5/7/83/279/283), avalie recurso adesivo (art. 997) e valide citações em `response_research.py` e `citation_check.py`.
