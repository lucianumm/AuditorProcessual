# Changelog

## Não publicado

- Ingestão de autos do PJe: o número do processo vem do rodapé ("Número do processo: ...") ou, sem ele, do número CNJ mais frequente; os demais ficam em `manifest.cited_process_ids` (antes valia o primeiro número dos autos, às vezes um precedente citado na inicial).
- O rodapé de assinatura do PJe (1º grau "Documento assinado eletronicamente por ...", 2º grau "Assinado eletronicamente por: ..." e "ID. ... - Pág. N", link de validação, números do processo e do documento, "Fls.: N") é descontado antes de medir o texto da página e de decidir o OCR: página escaneada com só o rodapé vai para `needs_ocr_or_vision`. O texto preservado da página continua com o rodapé.
- Com o rodapé do PJe, as peças são separadas pelo id do documento (páginas consecutivas com o mesmo id) e cada uma é nomeada pela primeira peça citada no seu próprio início, sem herdar o rótulo da anterior; `court_page` vem de "Fls.: N" e `court_page_end` passa a considerar todas as páginas da peça. Páginas e peças ganham `pje_document_id`; o esquema da peça passa a aceitar `pdf_page_count`, que já era gravado.

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
