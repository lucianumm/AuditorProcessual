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

Para análise e peças, seguir `references/precision_review_rules.md` no núcleo.
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

Pergunte apenas diante de ambiguidade material ou dado indispensável que não
pôde ser localizado. Lacuna delimitada não interrompe leitura nem impede
conclusões independentes. Qualidade técnica e origem da captura não certificam
interpretação ou mérito: toda minuta é RASCUNHO — NÃO PROTOCOLAR e depende de
revisão profissional. Instalação por ZIP/link não concede visão, navegação,
execução nem persistência; verifique capacidades na sessão.
