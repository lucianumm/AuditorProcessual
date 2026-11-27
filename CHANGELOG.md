# Changelog

## 1.1.0 — 2026-11-27

- **Licença:** o projeto passa da MIT para a **PolyForm Noncommercial License 1.0.0** (`LICENSE`, texto oficial com as linhas `Required Notice`). Uso não comercial livre e, por permissão adicional do titular, também o uso interno na própria atividade profissional, inclusive remunerada, por profissional autônomo ou organização com até 5 pessoas; organizações maiores, venda, revenda, oferta como serviço a terceiros e inclusão em produtos, sistemas ou plataformas exigem licença comercial (`COMMERCIAL_LICENSE.md`). As versões até a 1.0.0 continuam sob a MIT.
- **Reanálise integral a cada pedido (CRIP, P0–P7).** Toda solicitação substantiva passa a reconstruir, a partir das fontes, os fatos, a prova, as normas e a coerência de tudo o que a resposta toca, com a análise-base como termo de comparação e não como verdade herdada. Nas plataformas de chat, `references/request_cycle_rules.md` (automático em analyze/petition/evidence/audit) e `request_cycle_details.md` (Ficha de Pedido, gatilhos de reabertura, orçamento de releitura e checklist) fecham cada resposta com o bloco "Reconferência deste pedido", em que a releitura sem execução local aparece como declarada pelo modelo, não atestada. Localmente, `scripts/request_cycle.py` (`begin`, `scope`, `reread`, `sweep`, `close`, `validate`) calcula o perímetro por fatos compartilhados, entrega as páginas por inteiro com recibo e orçamento declarado, varre o corpus em busca de prova contrária, compara os fatos reextraídos com a base, reconfere as citações do perímetro (inclusive de capítulos antigos) na consulta oficial da resposta, exige objeções adversariais resolvidas e a coerência global, deriva as Fichas de Pedido e grava o "Histórico de ciclos". O ciclo é ligado ao hash do conteúdo: `petition_workspace.py assemble` recusa consolidação sem ciclo encerrado e capítulo novo salvo sem ciclo, e marca os anteriores como `legacy_no_cycle`.
- **Coerência entre capítulos (`global_consistency.py`).** Bloqueia a consolidação quando salário, jornada, divisor ou adicional têm valores diferentes para o mesmo período, quando datas de admissão ou dispensa divergem, quando CPF, CNPJ ou número de processo não existem nas fontes, quando há pedido sem causa de pedir ou causa de pedir sem o pedido da análise, quando a mesma rubrica e competência entram em dois pedidos principais e, em contestação e recurso, quando alegação ou fundamento da decisão fica sem resposta. Designações alternadas das partes e remissões internas inexistentes geram alerta.
- **Prosa conferida além das quantidades.** `prose_dates.py` lê datas e períodos em português (sem confundir número de lei com data) e `prose_review.py` acusa data sem suporte nos fatos vinculados, data aproximada (mês/ano) tornada exata, período invertido ou além do apurado e frase com polaridade oposta à dos átomos do fato; sujeito da frase diferente do ator, parágrafo longo e citação extensa são alertas.
- **Consolidação estruturada (`piece_assembly.py`).** Numeração, "Dos pedidos" com principal, subsidiário e alternativo e a condição de apreciação, provas a produzir, valor da causa sempre `[CONFIRMAR]` (linhas executadas dos pedidos principais e estimativas registradas, com conferência do valor informado), documentos referidos por documento, página e folha, e matriz de rastreabilidade em anexo técnico. Na reclamação trabalhista, pedido sem indicação de valor bloqueia a consolidação no fluxo com ciclo. `docx_exporter.py` ganhou `--toc` e `--annex`.
- **Validade das conferências do catálogo.** `catalog_status.py` aplica TTL por tipo (15 dias para mérito pendente e ações de controle, 90 para precedentes, 60 para lei com alteração recente, 180 para norma estável, 365 para tratado) sobre `verified.on`; os briefs de pretensões trazem `freshness`, e conferência vencida ou nunca feita exige consulta nova no P3. `scripts/catalog_recheck.py` reconferiu no texto oficial (normas.leg.br, com recibo e assunto conferido no próprio artigo) as leis pendentes do catálogo de ramos: 487 das 528 foram localizadas e passaram a `localizado_no_texto_oficial`, e as autoridades pendentes nos demais ramos caíram de 625 (34%) para 138 (7,6%); as 41 restantes ficaram pendentes com o motivo registrado (captura recusada, assunto que não confere no artigo ou norma sem número identificável), e temas, ações de controle e súmulas de portais que bloqueiam robôs continuam pendentes até leitura pelo navegador. Um relatório mensal (`.github/workflows/catalog-freshness.yml`) lista vencidas e pendentes e a conferência manual dos portais que bloqueiam robôs.
- **Segurança.** `injection.py` (primeiro módulo extraído do `helpers.py`) amplia a detecção de instruções nos autos para comandos em PT/EN, mensagens dirigidas à IA, marcas de papel (`system:`, `[INST]`), caracteres bidirecionais e Unicode *tag*, texto espaçado e envio de dados para fora; os pacotes de leitura declaram o texto dos autos como dado e sinalizam trechos suspeitos. Corpus adversarial com ataques e frases jurídicas comuns que não podem disparar. `SECURITY.md` registra retenção, supervisão e uso de outro modelo só com autorização.
- **MCP com 28 ferramentas:** ciclo (`begin_request_cycle` … `close_request_cycle`), `check_global_consistency`, `petition_workspace`, `response_research`, `validate_legal_review` e `catalog_freshness`.
- **Qualidade e avaliação.** ruff (regras de correção) e cobertura com piso de 75% nos motores e validadores no CI; testes de propriedade com sementes fixas; `metrics.json` como fonte única das contagens, conferida pelo `verify_repository.py`; `evaluation/planted_errors.json` e `scripts/run_planted_errors.py` medem a detecção de erros plantados (20 de 20 previstos detectados; os 2 casos fora do alcance dos controles determinísticos não são detectados, como declarado). São casos sintéticos do próprio autor: medem regressão, não precisão em autos reais. 533 testes.
- **Documentação:** `docs/GUIA_USUARIO.md` (como pedir, modos, leitura do bloco de reconferência, glossário de estados e limites), `docs/PLANO_MELHORIA.md` (plano revisado com a situação de cada item), template de issue para erro em uso real sem dados de clientes, Dependabot. Adiados com motivo no ROADMAP: namespace do wheel, divisão completa do `helpers.py`, mypy, núcleo `SKILL.md` ≤ 8 KB, avaliação com casos reais e PJe-Calc, e o Eixo D (OCR × visão, tabelas, transcrição).

## 1.0.0 — 2026-11-18

- **29 ramos especialistas e 606 pretensões bilaterais:** além das 123 pretensões trabalhistas (todas agora vinculadas a `piece_ids` do catálogo processual), o projeto passa a cobrir **28 demais ramos do Direito com 483 pretensões completas (966 teses do polo ativo e 864 do passivo), 1.817 autoridades candidatas e 51 marcos temporais**, sem nenhuma lista vazia em `typical_requests` ou `evidence` e sem nenhum placeholder `"limitation": "conferir"`. Os 19 ramos existentes foram aprofundados (mínimo de 13 e até 30 pretensões por ramo) e nove novos ramos especialistas foram adicionados: `processual_civil` (inclusive Lei 14.879/2024 sobre foro de eleição, Tema 1076 e Tema 1198 do STJ), `insolvencia` (Recuperação Judicial, Falência e Lei 14.112/2020), `securitario` (Novo Marco Legal dos Seguros — Lei 15.040/2024 e súmulas do STJ), `propriedade_intelectual_digital`, `regulatorio_concorrencial` (CADE, Lei 14.470/2022 e agências), `arbitragem_mediacao`, `crianca_adolescente_educacional` (ECA, educação inclusiva, FIES/PROUNI e Revalida), `notarial_registral` (LRP, SERP — Lei 14.382/2022 e Res. CNJ 571/2024) e `aduaneiro_maritimo` (perdimento, valoração, *demurrage* e Tribunal Marítimo).
- **Guias bilaterais e matrizes transversais de redação:** todos os 28 guias de ramo (`domain_guides/*.md`) incluem diagnóstico de regime/competência, polo ativo, defesa técnica, visão de gabinete/decisão (CPC, art. 489, § 1º) e motores aplicáveis; três novos guias condicionais cobrem contestação e impugnação (`defense_contestacao_rules.md`), prática recursal e tribunais superiores (`appellate_practice_rules.md`) e minuta de decisão/sentença/voto e parecer consultivo (`judicial_decision_and_opinion_rules.md`).
- **Seis novos motores determinísticos multirramo (`Decimal` e datas auditáveis):**
  - `deadline_calculator.py`: contagem em dias úteis (CPC, CLT, Juizados) e corridos (CPP, LEP, Recuperação Judicial, Eleitoral), intimação por DJe, portal eletrônico (Lei 11.419/2006) e Domicílio Judicial Eletrônico (Res. CNJ 455/2022 e 569/2024), recesso forense, feriados móveis e Dia Nacional de Zumbi e da Consciência Negra (Lei 14.759/2023), indisponibilidade e feriado local (Lei 14.939/2024) e trava contra prazo em dobro de litisconsortes em autos eletrônicos (CPC, art. 229, § 2º).
  - `civil_monetary_engine.py` e `official_indices.py`: 21 séries oficiais do BCB/SGS (incluindo INPC, IGP-M, TR, CDI, poupança e séries de taxa média de crédito para revisionais bancárias sob o Tema 27/STJ), cálculo da taxa legal da Lei 14.905/2024 e Res. CMN 5.171/2024 (`max(0, SELIC - IPCA)`), regimes encadeados da Fazenda Pública (EC 113/2021), Tributário e FGTS (ADI 5090), imputação de pagamentos parciais (CC, art. 354) e multa/honorários do art. 523, § 1º, do CPC.
  - `social_security_calc.py`: fusão de vínculos concomitantes sem dupla contagem, conversão de tempo especial limitada a 13/11/2019 (EC 103/2019, art. 25, § 2º), carência, regras permanentes e de transição (pontos, idade progressiva, pedágios de 50% e 100%) e decadência/prescrição (Lei 8.213/1991, art. 103; Súmula 85/STJ).
  - `penal_dosimetry.py`: dosimetria trifásica (CP, art. 68) com controle da Súmula 231 do STJ, frações em cascata, concurso de crimes, regime inicial, prescrição penal (arts. 109–117, incluindo fatos anteriores à Lei 12.234/2010 e o Tema 1192/STF) e progressão de regime na LEP (art. 112, incluindo os 55% do feminicídio da Lei 14.994/2024 e os alertas da Lei 14.843/2024).
  - `limitation_checker.py`: 15 perfis normativos de prescrição, decadência e prescrição intercorrente (CC, CDC, Fazenda Pública, CTN, LEF art. 40 — Temas 566–571/STJ, CPC art. 921 e Improbidade pós-Lei 14.230/2021).
  - `datajud_lookup.py`: conector opcional para a API Pública do DataJud (CNJ) com resolução automática do tribunal pelo número CNJ, leitura de classes, assuntos TPU e movimentações e preservação de recibo SHA-256.
- **Ingestão nativa dos 5 sistemas eletrônicos brasileiros, multiformatos e LGPD:** `court_systems.py` e `cnj_classifier.py` leem carimbos, IDs de documento, folhas, signatários e número principal do processo em **PJe (1º/2º graus)**, **eproc**, **e-SAJ**, **PROJUDI** e **SEI!/NUP**, descontando carimbos eletrônicos antes de decidir OCR/visão em páginas digitalizadas e endurecendo `detect_injection`. `document_formats.py` formata datas seriais de `.xlsx` via `xl/styles.xml` e extrai com segurança `.odt`, `.ods`, `.rtf`, `.eml`, `.zip`, `.p7s` e manifestos de imagens e áudio/vídeo. `privacy_redactor.py` implementa pseudonimização local reversível (LGPD/segredo de justiça) e gera registro de supervisão humana conforme as Resoluções CNJ nº 332/2020 e nº 615/2025.
- **Servidor MCP nativo, exportador forense `.docx` e busca BM25:** `mcp_server.py` expõe 16 ferramentas determinísticas via JSON-RPC 2.0 (`stdio` por linha e `Content-Length`), acompanhado de `.mcp.json` e adaptador `adapters/antigravity/`. `docx_exporter.py` gera minutas `.docx` OOXML em padrão forense A4 (margens 3cm/2cm, recuo de citações longas, tabelas com bordas e cabeçalho de rascunho supervisionado). `claim_search.py` incorpora BM25/IDF, radicalização morfológica em português e 82 grupos de sinônimos técnicos e coloquiais; `case_search.py` adiciona busca insensível a acentos, extração de entidades (`money`, `date`, `cnj`, `cpf_cnpj`, `citation`), filtro por peça e janela de páginas adjacentes.
- **Autoridades, avaliação e empacotamento:** `domain_authorities.schema.json` e `official_source_registry.json` passam a contemplar Temas/IACs do STJ, TNU, TSE, CARF, TCU, atos do CNJ e enunciados CJF/FONAJE (novas entradas curadas marcadas honestamente como `pendente_conferencia_oficial` até leitura no portal na própria resposta). Suíte sintética ampliada para 43 casos de avaliação cobrindo todos os 29 ramos, 9 pacotes isolados por plataforma e 484 testes automatizados.

## 0.23.0 — 2026-11-10

- Trabalhista: 123 pretensões (31 novas), 344 teses do trabalhador e 287 de defesa, 660 autoridades candidatas. Novas pretensões: limbo previdenciário, intervalos especiais, gratificação de função, diárias e ajuda de custo, salário-família e creche, não concorrência, invenções, morte do empregado, força maior e fato do príncipe, crédito na recuperação e na falência, desconsideração, penhora e fraude à execução, rescisória, mandado de segurança, tutela provisória, perícia, prova testemunhal, dissídio coletivo, representante comercial, fase pré-contratual, indenização adicional, trabalho infantil, licenças parentais, CTPS, atraso de salários, arbitragem e CCP, stock options, aposentadoria e contrato, alteração lesiva, custos do trabalho e comissão de representantes. Quarenta pretensões existentes ganharam teses (por exemplo, justa causa, horas extras, turnos, PDV, prescrição e honorários). Dois guias novos: `labor_details/contract_incident_rules.md` e `labor_details/special_actions_rules.md`.
- Precedentes do TST lidos no portal: a lista oficial de jurisprudencia.tst.jus.br (463 súmulas e 709 OJs) abriu pelo navegador da IA em 10/11/2026. 175 súmulas e OJs do catálogo registram situação, datas de publicação e hash do enunciado lido. O portal mostra canceladas em 2025, além das já catalogadas, as Súmulas 219, 268, 294, 329, 423, 429, 439, 449 e 452 e as OJs 270, 383 e 418 da SBDI-1, e o item I da Súmula 372 sem eficácia desde 11/11/2017. Duas teses antigas que citavam as Súmulas 268 e 294 sem esse aviso foram corrigidas, e um teste passa a exigir o aviso em toda tese que cite precedente cancelado ou norma revogada.
- Demais ramos: 257 pretensões (153 novas), 521 teses do polo ativo e 406 do passivo, 1.193 autoridades e 27 marcos temporais (seis com a data de publicação conferida no normas.leg.br). Todo ramo tem ao menos cinco pretensões; os guias dos 19 ramos ganharam roteiro das pretensões novas. Súmulas do STJ: o SCON recusou a captura local (HTTP 403) e 89 foram lidas pelo navegador (a 603 aparece cancelada). Temas do STF: título, leading case e situação lidos na página do tema, com aviso de que a tese não aparece nela; os Temas 1199, 1234, 6 e outros deixaram de estar pendentes.
- `scripts/catalog_intake.py` (manutenção): só aceita um dispositivo novo se o artigo, no texto oficial capturado, contiver o assunto esperado; 885 dispositivos passaram. Na primeira passagem, 14 foram recusados pelo assunto (dois por número de artigo errado) e 3 por leitura truncada do portal; todos foram corrigidos ou recapturados antes de entrar.
- `claim_search.py`: busca pretensões candidatas pelos fatos nos dois catálogos, sem acentos e com filtro por ramo.
- Catálogo de peças com 108 entradas: AIME, RCED, exigir contas, consignação em pagamento, renovatória e revisional de aluguel, dúvida registral, defesa de auto de infração ambiental, recurso de refúgio, acordo de não persecução civil, impugnação de edital, incidente de desconsideração e dissídio coletivo; habeas corpus, mandado de segurança, requerimento e recurso administrativo e exceção de pré-executividade alcançam os ramos que faltavam.
- `legislation_lookup.py` repete a leitura quando o normas.leg.br trunca a resposta de metadados. Registro de portais atualizado com o comportamento observado em 10/11/2026 (TST, SCON do STJ e STF).
- 383 testes. Leituras de portal pelo navegador são observações com hash do texto lido, não capturas com recibo; testes e catálogos não certificam mérito nem substituem revisão profissional.

## 0.22.0 — 2026-11-02

- Legislação por via oficial alternativa: em 02/11/2026 o Planalto respondeu "Acesso Negado!" ao ambiente de execução. `legislation_lookup.py` resolve tipo, número e ano nos dados abertos do Senado, lê no normas.leg.br a data, a publicação no DOU, a ementa, a vigência informada (`legal_force`) e as revogações (`revoked_by`) e captura com recibo a compilação da Câmara. A leitura dos metadados é necessária: a Lei 7.102/1983 aparece como sem vigência (revogada pelo art. 70 da Lei 14.967/2024), embora o texto compilado não traga a marca.
- `citation_check.py`: reconhece as marcas da compilação da Câmara ("(Revogado pela Lei nº …, de 13/7/2017…)", "(… com redação dada pela…)", "(… acrescido pela…)", "(… transformado em § 1º pela…)") e corrige a leitura de artigos com separador de milhar ("Art. 1.694" era segmentado como art. 1, o que permitia conferir trecho no artigo errado do CC ou do CPC).
- Classificador de área: limite de palavra ("adi" não casa mais com "adicional", nem "reu" com "reunião"), remoção de qualificação e endereço antes da contagem, termos genéricos com peso reduzido e leitura do número único CNJ com conferência do dígito verificador (Justiça, tribunal e UF). Uma reclamação trabalhista de bancária deixou de ser classificada como Direito Administrativo.
- Catálogo trabalhista: 92 pretensões (novas: garantia do BEm e trabalho no exterior), 217 teses do trabalhador e 174 de defesa, 415 autoridades candidatas e 28 marcos temporais. As 162 autoridades legais anteriores foram reconferidas no normas.leg.br sem divergência; 94 dispositivos novos foram conferidos no texto oficial; 38 NRs vêm da lista oficial do MTE (NR-2 e NR-27 revogadas); as Súmulas Vinculantes 22, 23, 40 e 53 foram lidas na página do STF. Súmulas, OJs, Temas, ações de controle e convenções da OIT sem conferência no portal (o TST respondeu HTTP 202 vazio e o índice de temas do STF, 504) entram como `pendente_conferencia_oficial`, apenas como pontos de pesquisa. Nenhuma pretensão ficou com um único meio de prova; as sem precedente caíram de 44 para 29.
- 14 novos guias setoriais (ferroviários, marítimos, subsolo, telefonia, artistas/músicos/radialistas, condomínios, motociclistas, agentes comunitários de saúde, bombeiros civis, expatriados, entidades religiosas, salão-parceiro, avulsos e organismos internacionais), com dispositivos lidos no texto oficial; guia processual (sumaríssimo, revelia, preposto, prazos, recesso, intimações, ACP, protesto, CNDT, IRR, agravo de petição) e divisor por período no guia de cálculos.
- Demais ramos: `domain_catalog.py` e `references/domain_catalogs/` com 19 ramos (previdenciário, previdência complementar, consumidor, bancário, civil, família, penal, militar, administrativo, tributário, empresarial, ambiental, constitucional, eleitoral, saúde pública, proteção de dados, imobiliário, agrário e migratório), 104 pretensões, 166 teses do polo ativo e 118 do passivo, 319 autoridades (258 dispositivos conferidos no normas.leg.br, 40 súmulas do STJ capturadas no SCON com recibo e 12 súmulas vinculantes lidas no STF) e 19 marcos temporais com vigência conferida no texto (EC 103/2019, Pacote Anticrime, Lei 14.905/2024, EC 132/2023 e LC 214/2025, entre outros). A Súmula 545 do STJ consta com a redação revisada em 10/09/2025. Guias por ramo em `references/domain_guides/`.
- Peças: família como domínio próprio (alimentos, execução, divórcio, guarda, investigação de paternidade, inventário, medidas protetivas); contestação deixa de ser candidata no processo penal, que ganhou memoriais, apelação, RESE, embargos infringentes, agravo em execução, revisão criminal, pedido de liberdade, queixa-crime, ANPP e institutos da Lei 9.099/1995; peças tributárias, previdenciárias, administrativas, constitucionais, eleitorais, empresariais, cíveis e imobiliárias, com a base legal conferida (`basis`). 95 peças no catálogo.
- Perfis de classificação para eleitoral, militar, previdência complementar, saúde pública, proteção de dados, imobiliário, agrário e migratório; módulos de especialização para todos os ramos; roteador e `task_context.py --domain/--domain-claim` carregam só o guia e o índice do ramo.
- Registro de portais atualizado com a observação de 02/11/2026: normas.leg.br, dados abertos do Senado, SCON do STJ, Receita, INSS, Previdência, ANS, Anvisa, ANPD, CADE, MMA, TCU e atos do CNJ com captura local; TSE, STM, CARF, TRFs e TJs com navegador ou arquivo oficial. Padrões de host para TJs e TRFs.
- Sete casos sintéticos de avaliação fora do trabalhista. 371 testes; testes sintéticos e capturas não certificam mérito nem substituem revisão profissional.

## 0.21.0 — 2026-10-21

- Conferência de citações em fonte oficial (`citation_check.py`): localiza artigo e parágrafo no texto compilado, exige o trecho dentro do dispositivo e fora de redação riscada, lê "(Revogado…)", "(Vetado)", "(Redação dada…)", "(Incluído…)" e "(Vide ADI…)" e compara com as datas dos fatos; súmulas, OJs, Temas e ações de controle exigem identificador e linha de situação. Integrada a `response_research.py` (novos comandos `verify` e `unavailable`) e à revisão v4.
- Capturador corrigido: o User-Agent anterior era recusado pelo Planalto; respostas 202 vazias com desafio anti-robô (TST, CSJT), 403 (STF, OIT) e páginas de verificação (LexML) eram aceitas como consulta e agora são registradas como bloqueio. Captura de JSON oficial (BCB/SGS). A inspeção reextrai o texto dos bytes preservados; texto editado com hashes recalculados é recusado.
- Registro de portais oficiais por tipo de fonte e via de acesso observada (`official_source_registry.json`); `capabilities.py --probe-http` testa a captura local na execução.
- Validação por resposta: URL consultada igual à da norma, trecho com pelo menos três palavras, comparação tolerante a quebras de linha do HTML oficial, citação escrita na prosa exige norma conferida vinculada e `fontes.md` informa como cada citação foi conferida.
- Catálogo trabalhista v2: 90 pretensões (46 novas), 155 teses do trabalhador e 140 de defesa, 223 autoridades candidatas (162 dispositivos localizados no Planalto em 21/10/2026 e 61 precedentes com situação e confiança) e 13 marcos temporais, inclusive a EC 141/2026 (42h e 2 dias de repouso a partir de dois meses da publicação; 40h um ano depois) e a Res. 225/2025 do TST. Índice leve, mapa de teses por polo (`labor_catalog.py --markdown`) e agenda de pesquisa com as fontes específicas de cada tese.
- Guias setoriais reescritos e ampliados para 21 setores; seis novas peças processuais trabalhistas no catálogo de medidas; roteiro de defesa por pedido.
- Cálculo: unidade percentual própria (sem conversão silenciosa), `min`/`max`, oito novas pautas (atualização por fases, multa do FGTS, multas rescisórias, reflexo em DSR, intervalo suprimido, repouso em dobro, adicionais, projeção do aviso), total com o arredondamento das parcelas, trava contra abater o mesmo pagamento em mais de uma parcela e captura de séries oficiais com `official_indices.py`.
- Jornada e tempo: política `next_day` (CC, art. 132, § 3º), prorrogação de prazo para dia útil com calendário vinculado, relógio do local de trabalho no noturno, prorrogação do noturno, intervalos intra e interjornadas, trabalho em repouso em rubrica própria, minutos sem resíduo decimal, sufixo "Z" em qualquer Python suportado e prescrição contada para trás.
- Correções: leitor de números ("52 minutos e 30 segundos", "um terço", qualificadores depois do número, "até" sem falso positivo), comparação de valores derivados não exatos, banco de horas com saldo vencido ou sem crédito identificado em revisão, links de arquivos arquivados, propagação de revisão para provas, conferências internacionais, perguntas e estratégias, roteamento do atendimento e de sinônimos de domínio, dependência `jsonschema` declarada, saneamento de Markdown e versões dos documentos.
- 349 testes; pacotes por plataforma e wheel verificados com os módulos novos; regressões congeladas sem piora em relação à 0.20.0. Testes sintéticos e capturas do catálogo não certificam mérito nem substituem revisão profissional.

## 0.20.0 — 2026-10-18

- Linha do tempo atribuída, prova por requisito e comparação de fatos, campos atômicos, períodos, âmbitos e cláusulas com impacto em parágrafos, pedidos e contas; versões preservadas.
- Perguntas materiais com busca prévia e efeito delimitado à parcela; atualizações de defesa, depoimento, laudo, decisão e prova nova exigem fonte do ato recebido.
- Agenda de pesquisa por questão, âmbito e período; captura real de índices oficiais com localização de links candidatos. Inteiro teor, seleção e consulta nova da resposta continuam necessários.
- Quantidades por extenso, unidades, limites/condições e compatibilidade da transformação; origem e período também conferidos nas derivações de parâmetros.
- Critério semanal global executável em transições com base/início compatíveis, excesso diário preservado e cobertura parcial explícita; sem limite reiniciado por segmento.
- Revisão da prosa para quantidades sem suporte e afirmações de comprovação/incontrovérsia; capítulos passam a acompanhar também as dependências de cálculo.
- Comparação externa detalhada de parcelas/competências, bases, reflexos, abatimentos e arredondamento com arquivo/hash, versão e tabelas. Não simula execução do PJe-Calc.
- Guias aprofundados de vínculo/responsabilidade, jornada, remuneração, ruptura/garantias, saúde, instrução, recursos e execução; distinção expressa entre CLT 769 e 889.
- Comparador de versões por seis classes de erro e quatro regressões executáveis contra a versão anterior. Casos sintéticos de desenvolvimento não demonstram precisão profissional; materiais reais e rótulos independentes continuam necessários.
- Pacotes, wheel, comandos e documentação atualizados; QR de apoio preservado e apresentação do projeto corrigida no README.

## 0.19.0 — 2026-10-14

- Consulta oficial nova por resposta jurídica substancial, capítulo e consolidação; captura HTTP executada ou observação de navegador explicitamente não atestada.
- Sessões versionadas, timestamps, corpus e pesquisa, hash do conteúdo, citações e causas/fundamentos ligados a fatos, requisitos/exceções, contrapontos e pedidos.
- Precedentes exigem conferência atual do fundamento e da situação, com mérito, processo, efeitos, modulação e comparação separados.
- Parâmetros numéricos com origem factual, trecho oficial ou derivação executada, transformação e período; seleção das parcelas pedidas e dependências sem calcular pretensões alheias.
- 44 roteiros trabalhistas, dez guias setoriais e oito pautas de fórmula sem taxas presumidas; novos guias de carreira/remuneração variável, modalidades contratuais e acordo extrajudicial.
- Novas revisões por resposta e capítulos v2, preview e pesquisa própria da consolidação; versões legadas preservadas e identificadas sem os controles novos.
- Testes adversariais de recência, adulteração, escopo, causa de pedir, precedentes e parâmetros; verificação dos novos recursos nos pacotes e wheel isolados.
- README e fluxo local atualizados. Controles não certificam mérito jurídico, navegação externa, revisão profissional real nem execução de PJe-Calc.

## 0.18.0 — 2026-10-12

- Análise integral como base comum, elaboração da tese escolhida, contexto seletivo, capítulos versionados e consolidação explícita.
- Estados de rascunho, revisão, aprovação atribuída ao usuário e reavaliação por dependência; preservação de versões e invalidação de consolidações anteriores.
- 30 roteiros de pretensão, guias granulares de remuneração, jornada, ruptura e garantias, e estratégia de prova em saúde ocupacional.
- Cronologia de relatos com datas exatas, meses aproximados, intervalos e marcos desconhecidos, vinculada aos trechos recebidos.
- Agenda seletiva de pesquisa oficial, recaptura real por fonte e distinção entre mérito, situação processual e efeito do precedente.
- Conciliação de créditos e compensações em banco de horas; semanas com mudança de regra não reiniciam automaticamente o limite semanal.
- README reorganizado por uso, fluxo, instalação, comandos, continuidade e validação; detalhes anteriores preservados no guia técnico.
- Avaliação de mérito real, importação nas interfaces e comparação executada com PJe-Calc continuam dependendo de materiais e registros reais.

## 0.17.0 — 2026-10-12

- Atendimento com poucos ou nenhum anexo: relatos atribuídos, retificações preservadas, busca e leitura em lotes.
- Possibilidade de redigir a inicial separada da suficiência da prova; prova futura com plano concreto não bloqueia automaticamente a minuta.
- Desenvolvimento por 15 pretensões e 10 roteiros setoriais selecionáveis, sem carregar os demais guias.
- Workflow vincula requisitos, prova, conciliação, versões por período, situação de autoridades, prescrição, coletivos, capítulos recursais e alternativas.
- Jornada e folha conciliadas com parâmetros e fontes: virada de dia, unidade noturna fornecida, cobertura semanal, excesso sem dupla contagem e pagamento identificado.
- Relatos integram revisão do corpus, índice e propagação de mudanças; integridade é conferida contra os arquivos persistidos.
- Históricos de relatos e entregas preservados; finalização sem documentos identifica zero páginas e inclui os arquivos disponíveis no ZIP.
- 40 cenários observáveis, 10 fluxos integrais sintéticos e regressões de continuidade, sem alegação de certificação jurídica ou execução real do PJe-Calc.

## 0.16.0 — 2026-10-12

- Especialização trabalhista por 11 temas, com guias condicionais e contrato vinculado à revisão v4.
- Relações e períodos, cláusulas coletivas por âmbito/vigência, provas e ônus por questão, saúde e pressupostos próprios.
- Motor Decimal com fórmulas explícitas, unidades, competências, reflexos, deduções, dependências e comparação externa vinculada.
- Conferência de jornada por data/offset e calendário explícito com feriados/suspensões, sem prazo legal presumido.
- Catálogo ampliado com recursos de revista/agravos, instrumentos de instrução, liquidação e execução.
- Fontes oficiais OIT/NORMLEX e conferências de ratificação; índices e propagação de alterações incluem os registros trabalhistas.
- Testes adversariais e verificações de distribuição incluem os novos recursos e cálculos sintéticos.

## 0.15.0 — 2026-10-10

- Corrigidos erro de sintaxe, schema de impacto em teses/aplicações e referência legível ao arquivo nas citações.
- Revisão v4 com afirmações atômicas, fontes contrárias, conferência de dados críticos, mapa normativo temporal, comparação factual de precedentes e confronto qualitativo das teses; versões anteriores continuam legadas.
- Leitura em lotes completos limitados por caracteres, recibos de exportação e verificação de intervalos sem lacunas; não declara compreensão automaticamente.
- Extração textual segura de DOCX/XLSX, tabelas, todas as linhas, planilhas ocultas e fórmulas não executadas; recursos visuais e revisões autorais têm limitações explícitas.
- Módulos por área/subárea/regime, catálogo de medidas candidatas e roteador com referências condicionais e orçamento mensurado.
- Relações cumulativas entre documentos, índice jurídico navegável e registro de alterações de fontes jurídicas independente dos uploads, com entregas antigas sinalizadas e preservadas.
- Oito casos sintéticos de avaliação, rubrica profissional opcional vinculada à revisão e testes adversariais adicionais.
- Empacotamento determinístico, recursos novos incluídos antes do staging, validação de schemas/versões/sintaxe e evidência local separada de upload real nas plataformas.

## 0.14.0 — 2026-09-27

- Adicionada conferência semântica adversarial para leitura página a página, decomposição de fatos, contradições, direito intertemporal, argumentos contrários e limites de automação.
- Memória incremental agora propaga alterações também para aplicações normativas e teses; trechos de busca são explicitamente tratados como localizadores, nunca prova de leitura integral.
- Revisão v3 rejeita tese ativa apoiada em técnica normativa recusada, analogia sem vínculo aplicado/limitado à questão e medida escolhida com requisito de admissibilidade não atendido; campos v3 exigem `schema_version: 3.0`.
- Citações na minuta exibem referência legível e mantêm hashes/IDs técnicos no índice; o lint ignora citações literais ao avaliar a voz do redator.
- Fontes oficiais capturadas distinguem integridade técnica de vigência e aplicabilidade; textos riscados/acrescentados em HTML são preservados como versões distintas.
- Revisão inválida ou bloqueada marca análises e minutas anteriores como não utilizáveis e mantém cópias recuperáveis; README e adaptadores atualizados.
- Incluídos casos de regressão para os problemas identificados na revisão anterior.

## 0.13.0 — 2026-09-27

- Identificação estruturada da medida/peça por fase, ato, polo, finalidade, pressupostos, prazo e alternativas, com distinção entre espécie concreta e família técnica.
- Contrato `legal_review.json` v3 acrescenta `piece_assessment`, `norm_applications` e `theses`; o validador confere referências entre questões, fatos, normas, medidas e teses.
- Protocolo dedicado distingue incidência direta, remissão, aplicação subsidiária/supletiva, analogia e interpretação sistemática, com lacuna/autorização, semelhanças, diferenças, compatibilidade, limites e efeitos.
- Teses classificadas por grau de consolidação e papel estratégico, com objeção adversa, resposta, limites probatórios e compatibilidade processual.
- Precedentes precisam ser conferidos em fonte oficial pelo fundamento determinante, alcance, situação atual e distinções factuais.
- Roteamento carrega regras de petição inicial apenas quando essa peça estiver em questão; adaptadores, instalação Gemini, README e migração atualizados.

## 0.12.0 — 2026-09-17

- Pendências estruturadas por página, fato, norma, questão, pedido ou parágrafo, com entrega parcial das questões independentes e limites explícitos na minuta.
- Diferenciação entre página em branco confirmada, imagem sem texto, conteúdo desconhecido e página ilegível; fila de recuperação registra somente ações realizadas e impede tentativas idênticas repetidas.
- Memória cumulativa com índice SQLite paginado e filtros, revisão de páginas alteradas e propagação declarada de impacto sobre fatos, questões, pedidos e parágrafos.
- Pesquisa oficial com captura HTTP íntegra, observação de navegador explicitamente não atestada ou fonte indisponível; nenhum modo declara verificação de mérito.
- Controles próprios para inicial, contestação, réplica, recurso e compatibilidade dos pedidos, mantendo proveniência e revisão profissional obrigatória.
- Casos sintéticos anotados e avaliador reproduzível para omissões, citações, contradições e bloqueios indevidos; CI multiplataforma e validação portátil.

## 0.11.0 — 2026-09-06

- Separação explícita entre aprovação técnica e mérito jurídico; nenhuma aprovação automática de conclusão final.
- Contrato validado em runtime, revisão por página vinculada ao conteúdo, suporte por fato e pesquisa por questão; tratamento de requisitos faltantes/controvertidos.
- Detecção conservadora de negação contraditória e voz distanciada na inicial; citações identificam arquivo/hash e documento.
- Revisões fornecidas dentro da saída preservadas antes da limpeza; memória textual/OCR/visual versionada e busca cumulativa paginada.
- Vínculo visual ao hash do arquivo e da renderização; sidecar vazio obrigatório rejeitado.
- ZIP cumulativo inclui versões e assets sem ZIPs recursivos; links históricos verificados.
- Fontes oficiais HTML/TXT/PDF textual com recibo e resposta bruta preservada.
- Núcleo seletivo reduzido, documentação de migração, recursos Python distribuídos e nove pacotes com licença e execução isolada.
- Regressões sintéticas para as falhas observadas; CI executa também os pacotes isolados.

## 0.10.0 — 2026-09-06

- Adicionada memória processual cumulativa (`case_memory.json`,
  `memoria_processual.md` e `passages.jsonl`) com versões, fingerprints,
  offsets integrais e atualização segura após novos uploads.
- PDF passou a usar extração/renderização por página com cache recuperável e
  diagnóstico de capacidades, sem declarar conclusão quando uma camada está
  pendente.
- Criado o contrato `legal_review.schema.json` e o validador provider-neutral
  `legal_review.py`, com fatos documentais/clientes, fontes oficiais capturadas,
  subsunção requisito por requisito, contrapontos, pedidos, cálculos e gate de
  conclusão.
- Petições iniciais receberam regra explícita de voz afirmativa; expressões de
  relatório documental são rejeitadas na revisão autoral.
- Incluídos protocolos de pesquisa oficial, memória, inicial e revisão, além de
  roteamento/adaptadores e documentação atualizados para ChatGPT, Claude,
  Gemini, Manus e Grok.
- Suíte ampliada para 56 testes, incluindo cobertura sem truncamento, bloqueio
  de revisão incompleta e contratos da nova etapa jurídica.

## 0.9.3 — 2026-08-26

- Substituída a voz de inventário documental por narrativa jurídica afirmativa,
  com fonte direta por peça, página, folha, `document_id` e `image_id` quando
  aplicável.
- Adicionados `legal_narrative.json`, `analise_juridica.md` e o protocolo
  `legal_narrative_rules.md` para fatos, alegações, provas, decisões, tese,
  subsunção e contrapontos.
- Ampliada a pesquisa normativa: Constituição, rito, legislação especial,
  regulamentos, normas locais e jurisprudência oficial permanecem pendentes
  até verificação de vigência, competência, hierarquia e direito intertemporal.
- Atualizados adaptadores de ChatGPT, Claude, Gemini, Grok e Manus, templates,
  roteador, schemas e validador; suíte ampliada para 53 testes.

## 0.9.2 — 2026-08-20

- Aplicados gates de qualidade para cobertura, proveniência, classificação, matriz de rastreabilidade e verificação legal.
- Adicionadas `quality_gate.json/.md` e `matriz_fato_prova_norma_pedido.json/.md` para impedir afirmações sem fonte e pedidos inventados.
- Suíte ampliada para 51 testes, incluindo ambiguidade de área e vínculos fato–prova–norma–pedido.

## 0.9.1 — 2026-08-20

- Documentação pública enxugada; decisões de evolução permanecem fora da skill distribuída.
- Reempacotamento multiplataforma e atualização das referências para a versão `v0.9.1`.
- Adicionados gates explícitos de qualidade e a matriz fato–prova–norma–pedido para reduzir afirmações sem proveniência.
- Mantida a suíte com 51 testes e os gates de precisão, proveniência, cobertura visual e conferência da base legal.

## 0.9.0 — 2026-08-20

- Migração de publicação para `github.com/lucianumm/AuditorProcessual`.
- Classificação automática e explicável de área jurídica (trabalhista, previdenciária, consumerista, civil, bancária, família/sucessões, penal, administrativa, tributária, empresarial, ambiental, constitucional e processual).
- Novo `legal_domain_profiles.json`, com fontes oficiais candidatas, perfil de redação, evidências por página e portas de verificação.
- Geração automática de `legal_basis.json` e `base_legal.md`; fundamentos permanecem provisórios até conferência de vigência, competência, direito intertemporal e jurisprudência.
- Suíte com 49 testes.

## 0.8.0 — 2026-08-12

- Gate explícito de visão semântica (`required`, `best_effort`, `off`) com providers `sidecar` e `agent_review`; `--require-semantic-vision` falha cedo quando a revisão não existe.
- Inventário visual com classes `visual_asset`, `technical_artifact`, `qr_code`, `logo`, `document_scan`, `photo` e `unknown`, deduplicação por SHA-256, ocorrências por página e zoom de imagens pequenas relevantes.
- Entrega portátil com `processo_completo.md`, `images/index.json`, `paginas_problematicas.md`, `assets/pages/`, manifesto de codificação, ZIP completo e validador de links/assets.
- Contrato `vision_review.schema.json`, opção `--encoding utf-8-sig` e 46 testes sintéticos cobrindo o fluxo visual corrigido.

## 0.7.0 — 2026-08-11

- Entrada universal `AI_ENTRYPOINT.md`, `llms.txt` e roteador JSON para uso por link do GitHub sem leitura integral do repositório.
- Adaptadores mínimos para Manus, Gemini CLI/Gems, Grok, ChatGPT/GPT e Claude.
- Extensão Gemini CLI com `gemini-extension.json` e `GEMINI.md`; instruções prontas para Gems e Grok.
- Empacotamento específico por plataforma, mantendo um único núcleo jurídico e execução de uma tarefa por vez.
- Suíte ampliada para 41 testes com validação do roteamento e da separação de adaptadores.

## 0.6.0 — 2026-08-11

- Gate adaptativo: inspeciona os materiais primeiro e pergunta somente quando houver ambiguidade, conflito ou dado indispensável ausente.
- Execução seletiva por tarefa (`ingest`, `analyze`, `petition`, `deadlines`, `evidence` ou `audit`).
- `--confirm-scope` opcional, relatório cumulativo `relatorio_processual.md` e preservação de uploads anteriores em `versions/`.
- Perguntas determinísticas em scripts/scope_questions.py e regras em references/request_intake_rules.md.

## 0.5.0 — 2026-08-11

- Pacote compatível com upload de Skills no ChatGPT, com SKILL.md na raiz do arquivo .skill.
- Fluxo especializado para PETITION_DRAFT e PROCEDURAL_ANALYSIS.
- Regras e templates para petições, peças, análise processual, citações internas e revisão antes do protocolo.
- Suíte ampliada para 32 testes, incluindo os modos PETITION_DRAFT e PROCEDURAL_ANALYSIS.
- Execução seletiva por tarefa, sem geração automática de relatórios não solicitados.
- Suíte ampliada para 36 testes.

## 0.4.0 — 2026-08-11

- Aplicadas as peças de andamento processual: contrato JSON, relatório de andamento, prazos para revisão, matriz documental, mapa de provas, checklist, minuta de trabalho e conformidade.
- Adicionada proveniência por página, fila de tarefas e bloqueio explícito contra cálculo automático de prazos ou protocolo de minutas.

## 0.3.0 — 2026-08-10

- Correção arquitetural para separar renderização, inspeção técnica, OCR, visão semântica e consolidação.
- Conversão integral agora exige renderização e visão semântica aplicáveis; ausência de provider gera `PARTIAL`.
- Manifesto `1.1` com cobertura física, textual, de renderização e semântica independentes.
- Adicionados `--vision-mode`, `--render-dpi`, sidecar de descrições por página e testes de regressão contra falso `COMPLETE`.
- Melhorias visuais e de cobertura consolidadas na versão 0.4.0.

## 0.2.1 — 2026-08-10

- Créditos de autoria e links oficiais de Lucianum adicionados à documentação e aos metadados.

## 0.2.0 — 2026-08-10

- Markdown estruturado por página com resumo semântico, entidades, termos-chave e blocos/tabelas.
- Inventário de imagens PDF e scans, cópias derivadas, hash, dimensões, localização e OCR opcional.
- Campo `--image-descriptions` para descrições semânticas revisadas por humano ou modelo multimodal autorizado.
- `image_inventory.json`, schemas de página/visual e cobertura visual no manifesto e relatório.
- README, SKILL, template, protocolo visual e validador atualizados.
- Suíte ampliada para 22 testes.

## Créditos

Projeto desenvolvido e mantido por **Lucianum (lucianumm)** — [Instagram](https://www.instagram.com/lucianum/).
