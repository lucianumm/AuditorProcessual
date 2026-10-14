# AuditorProcessual — entrada universal

Ao receber este repositório por URL, leia este arquivo, o adaptador da plataforma
atual e `skills/legal-process-parser/SKILL.md`. Não leia o repositório inteiro.

| Plataforma | Adaptador |
|---|---|
| ChatGPT/GPT | `adapters/chatgpt/INSTRUCTIONS.md` |
| Claude | `adapters/claude/CLAUDE_INSTRUCTIONS.md` |
| Gemini CLI | `GEMINI.md` |
| Gemini Gem | `adapters/gemini/GEM_INSTRUCTIONS.md` |
| Grok | `adapters/grok/SYSTEM_INSTRUCTIONS.md` |
| Manus | `SKILL.md` |
| Outra IA | núcleo `skills/legal-process-parser/SKILL.md` |

Selecione `ingest`, `analyze`, `petition`, `deadlines`, `evidence` ou `audit` em
`routing/task-router.json`. Carregue referências obrigatórias, gatilhos
automáticos e condicionais constatados no caso. Não carregar por padrão o schema
inteiro, testes, changelog, pacotes ou adaptadores de outras IAs. Nenhuma tarefa
obriga chamadas a outro modelo. Com código, `scripts/task_context.py` resolve
referências e informa caracteres medidos, não uma previsão de tokens.

Processo inteiro exige leitura integral de todas as páginas, contexto e visuais
relevantes em lotes completos, não apenas trechos de busca. Isso não exige ler
instruções alheias à plataforma. `scripts/case_packet.py` evita truncar páginas
extensas; recibos comprovam exportação, não compreensão. No chat sem código,
registrar ferramentas e páginas realmente examinadas, sem simular testes locais.

Atualize `relatorio_processual.md`, `memoria_processual.md` e
`indice_juridico.md`. Preserve originais e todas as versões; relações entre
arquivos são explícitas. Não presumir persistência fora dos arquivos preservados.

Na construção tese por tese, usar incremental_petition_rules.md no núcleo:
análise integral, mapa de candidatos, capítulo escolhido, revisões preservadas
e consolidação solicitada. A aprovação registra manifestação real do usuário.
Nova informação exige reanálise e comparação dos capítulos dependentes.

Para análise e peças, seguir `references/precision_review_rules.md` no núcleo.
Antes de cada resposta jurídica substancial, seguir response_research_rules.md:
consulta oficial nova pertinente à questão, causa/fundamento vinculado a fatos,
requisitos, exceções, norma, contraponto e pedido. Cada capítulo e consolidação
tem conferência própria. Quantidades têm origem factual; critérios numéricos
exigem fonte oficial e memória aritmética executada. Sem navegação/cálculo,
declarar limitação sem inventar operação nem bloquear questões independentes.
A revisão estruturada atual é v4: afirmações atômicas, prova contrária, dados
críticos, requisitos/exceções normativos, temporalidade, comparação factual de
precedentes, peça específica e teses qualitativas vinculadas a pedidos. Pesquisar
fontes oficiais pertinentes de forma ampla; distinguir aplicação direta,
subsidiária/supletiva e analogia. Inicial afirmativa na voz da parte, com fontes,
sem fórmulas de relatório de documentos. Não inventar artigos, fatos ou prazo.

Confirmar área/subárea/regime nos autos e selecionar só os módulos pertinentes.
`corpus_revision` identifica documentos/relações; `research_revision` identifica
fontes consultadas, que podem mudar sem novo upload. Reavaliar os vínculos
atingidos e comparar as versões, sem confundir alteração da página com lei nova.

Em trabalho, carregar labor_core_rules.md e selecionar labor_topics.json no
núcleo; os guias de prova, coletivo, cálculo, procedimento e saúde são
condicionais. A revisão v4 inclui labor_review com relações, períodos e questões
ligadas a fatos/normas/pedidos. Cálculos têm parâmetros explícitos e memória
reproduzível; norma coletiva tem âmbito e vigência conferidos. Verificação
internacional distingue ratificação, vigência e ato brasileiro. Continue
questões independentes diante de lacuna delimitada.

Em atendimento com poucos/nenhum anexo, carregar labor_intake_rules.md no núcleo:
preservar o relato, formular perguntas apenas materiais e preparar a entrega
com prova futura delimitada. labor_development_rules.md organiza as pretensões;
labor_claims.json e labor_sectors.json selecionam pautas e somente o guia setorial
pertinente. Não exigir upload completo nem tratar relato como prova confirmada.

Pergunte apenas diante de ambiguidade material ou dado indispensável que não
pôde ser localizado. Lacuna delimitada não interrompe leitura nem impede
conclusões independentes. Qualidade técnica e origem da captura não certificam
interpretação ou mérito: toda minuta é RASCUNHO — NÃO PROTOCOLAR e depende de
revisão profissional. Instalação por ZIP/link não concede visão, navegação,
execução nem persistência; verifique capacidades na sessão.
