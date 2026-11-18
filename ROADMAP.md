# Arquitetura e Plano Diretor — AuditorProcessual (`v1.0.0`)

Este documento registra a arquitetura consolidada na versão `1.0.0` do **AuditorProcessual (`legal-process-parser`)** e as diretrizes contínuas de evolução, verificação oficial e governança ética para análise de autos e elaboração de peças jurídicas rastreáveis no Direito brasileiro.

---

## 1. Princípios Inegociáveis do Projeto

1. **Rastreabilidade integral por página, segmento e documento:** nenhuma conclusão substitui a leitura em lotes completos (`case_packet.py`); página vazia confirmada, página ilegível e página ainda não examinada mantêm estados distintos.
2. **Conferência oficial na própria resposta (`per_response`):** os catálogos (`labor_claims.json` e `domain_catalogs/*.json`) entregam pautas e autoridades **candidatas**, nunca certificação automática de vigência ou cabimento. Toda resposta substancial consulta a fonte oficial atual, confere marcas intertemporais (`citation_check.py`) e preserva recibos.
3. **Zero aritmética ou contagem de prazo "de cabeça":** cálculos trabalhistas, atualização monetária cível/fazendária/tributária, contagem de prazos processuais, cômputo previdenciário, dosimetria penal e linhas do tempo prescricionais rodam em motores determinísticos auditáveis com `Decimal` e datas exatas.
4. **Autos são dados não confiáveis:** documentos nunca são executados como instruções; macros, entidades XML externas, *path traversal* e *prompt injection* documental são bloqueados ou isolados.
5. **Supervisão humana obrigatória (Resoluções CNJ nº 332/2020 e nº 615/2025):** toda minuta gerada é marcada como **RASCUNHO — NÃO PROTOCOLAR SEM REVISÃO ADVOCATÍCIA**.

---

## 2. Eixos Implementados na `v1.0.0`

### Eixo 1 — Cobertura Especialista em 29 Ramos do Direito Brasileiro
* **Direito do Trabalho (`trabalhista`):** 123 pretensões bilaterais vinculadas a `piece_ids` do catálogo processual, 35 guias setoriais, 10 guias detalhados e 16 perfis de parâmetros de cálculo.
* **28 Demais Ramos com Profundidade Bilateral e Visão de Gabinete:**
  * *19 ramos consolidados e expandidos:* `administrativo`, `agrario`, `ambiental`, `bancario`, `civil`, `constitucional`, `consumidor`, `eleitoral`, `empresarial`, `familia`, `imobiliario`, `migratorio`, `militar`, `penal`, `previdencia_complementar`, `previdenciario`, `protecao_dados`, `saude_publica` e `tributario` (100% das pretensões com pedidos típicos, prova típica, marcos temporais e regra prescricional/decadencial explícita).
  * *9 novos ramos especialistas:* `processual_civil`, `insolvencia` (Recuperação Judicial e Falência), `securitario` (incluindo o Marco Legal dos Seguros — Lei 15.040/2024), `propriedade_intelectual_digital`, `regulatorio_concorrencial` (CADE e agências), `arbitragem_mediacao`, `crianca_adolescente_educacional` (ECA e ensino superior), `notarial_registral` (SERP e extrajudicial) e `aduaneiro_maritimo`.
  * *Matrizes transversais de redação:* Petição Inicial afirmativa, Contestação (`defense_contestacao_rules.md`), Prática Recursal e Tribunais Superiores (`appellate_practice_rules.md`) e Minuta de Decisão/Sentença/Voto e Parecer Consultivo (`judicial_decision_and_opinion_rules.md`).

### Eixo 2 — Motores Determinísticos Multirramo
* `deadline_calculator.py`: contagem determinística em dias úteis (CPC, CLT, Juizados) e corridos (CPP, LEP, Recuperação Judicial, Eleitoral), regras de DJe, portal eletrônico (Lei 11.419/2006) e Domicílio Judicial Eletrônico (Res. CNJ 455/2022), recesso forense, feriados nacionais/móveis/locais (Lei 14.939/2024) e dobra legal (com trava do art. 229, § 2º, do CPC em autos eletrônicos).
* `civil_monetary_engine.py` + `official_indices.py`: atualização monetária e juros por fases (Lei 14.905/2024 + Res. CMN 5.171/2024 com piso zero `SELIC - IPCA`, Fazenda Pública EC 113/2021, Tributário SELIC, FGTS ADI 5090), imputação de pagamentos parciais (CC, art. 354), multa/honorários do art. 523, § 1º, do CPC e comparação objetiva com séries de taxa média de crédito do BCB/SGS.
* `social_security_calc.py`: unificação de vínculos concomitantes sem dupla contagem, conversão de tempo especial limitada a 13/11/2019 (EC 103/2019), carência e elegibilidade nas regras permanentes e de transição, além de decadência (art. 103) e prescrição quinquenal.
* `penal_dosimetry.py`: cálculo trifásico do art. 68 do CP (com controle da Súmula 231 do STJ e frações em cascata), concurso de crimes, regime inicial, prescrição penal (arts. 109–117 do CP) e frações/percentuais de progressão da LEP (art. 112 por marco temporal da infração).
* `limitation_checker.py`: verificação auditável de prescrição, decadência e prescrição intercorrente (CC, CDC, Fazenda Pública, CTN/LEF Temas 566–571 STJ, CPC art. 921 e Improbidade pós-Lei 14.230/2021).

### Eixo 3 — Ingestão Nativa dos 5 Sistemas Judiciais, Multiformatos e LGPD
* `court_systems.py` + `cnj_classifier.py`: leitura nativa de carimbos, IDs de peça, folhas, signatários e número principal do processo em **PJe (1º/2º graus)**, **eproc**, **e-SAJ**, **PROJUDI** e **SEI!/NUP**, descontando carimbos eletrônicos ao aferir necessidade de OCR/visão em páginas digitalizadas.
* `document_formats.py`: formatação fiel de datas seriais em `.xlsx` (`xl/styles.xml`) e suporte seguro a `.docx`, `.odt`, `.ods`, `.rtf`, `.eml`, `.zip`, `.p7s` (envelopes ICP-Brasil) e manifestos rastreáveis de imagens e mídias de audiência/mensageria.
* `privacy_redactor.py`: pseudonimização local reversível para LGPD e segredo de justiça + geração de registro de governança e supervisão humana aderente às Resoluções CNJ nº 332/2020 e nº 615/2025.

### Eixo 4 — Fontes Vinculantes (CPC, art. 927), DataJud e Busca Jurídica BM25
* Catálogo de autoridades expandido para suportar Temas Repetitivos e IACs do STJ, Súmulas e Temas da TNU, Súmulas do TSE, CARF e TCU, ADCs/ADPFs/ADIs, Resoluções/Provimentos do CNJ e Enunciados CJF/FONAJE, mantendo separação transparente entre capturas oficiais com hash e autoridades candidatas pendentes de abertura em navegador na resposta.
* `datajud_lookup.py`: cliente opcional para consulta estruturada de classes, assuntos TPU e movimentações na API Pública do DataJud (CNJ).
* `claim_search.py` e `case_search.py`: ranqueamento BM25 com normalização morfológica em português e vocabulário coloquial de atendimento ao cliente, além de busca por entidades financeiras, datas, citações e peças nos autos.

### Eixo 5 — Ecossistema MCP, Adaptadores Multiplataforma e Exportação Forense `.docx`
* `mcp_server.py` + `.mcp.json`: servidor Model Context Protocol (`stdio`, JSON-RPC 2.0, zero dependências externas) integrando as ferramentas determinísticas do `AuditorProcessual` diretamente a agentes modernos (Google Antigravity, Claude Code/Desktop, Cursor, Gemini CLI e editores compatíveis).
* `docx_exporter.py`: exportador `.docx` OOXML nativo com paginação forense brasileira (A4, margens 3cm/2cm, recuo de citações longas, tabelas com bordas e cabeçalho de rascunho supervisionado).

### Eixo 6 — Qualidade Contínua e Benchmark Multirramo
* 43 casos sintéticos de avaliação em `evaluation/cases/` cobrindo todos os 29 ramos jurídicos, além da suíte congelada de fluxos trabalhistas e validação isolada de pacotes `.zip`/`.skill` e `wheel` Python em Linux e Windows.

---

## 3. Próximas Frentes Evolutivas (`v1.1+`)

1. **Validação criptográfica local ICP-Brasil (cadeia ITI/AC-Raiz):** verificação offline opcional de assinaturas `.p7s` e PDFs assinados (`PAdES`/`CAdES`) quando bibliotecas criptográficas forem autorizadas no ambiente.
2. **Importação/comparação nativa de arquivos `.PJC` (PJe-Calc Cidadão):** parser dedicado para confronto parcela a parcela contra memórias exportadas do PJe-Calc.
3. **Tabelas estaduais históricas dos Tribunais de Justiça (ENCOGE):** conectores auditáveis para séries históricas estaduais anteriores à unificação pelo IPCA/SELIC da Lei 14.905/2024.
4. **Avaliação cega com banca humana multirramo:** execução do `evaluation/PROTOCOL.md` em autos reais anonimizados e autorizados, com dupla revisão independente por especialistas de cada área.
