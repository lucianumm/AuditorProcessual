# Legal Process Parser — Claude

Use `skills/legal-process-parser/SKILL.md` e `routing/task-router.json`.
Carregue somente tarefa, gatilhos automáticos/pertinentes e módulos do regime
confirmado. Não abrir outros adaptadores nem chamar outro provider.

Na revisão estruturada use v4 e `references/precision_review_rules.md`.
Leia todo o corpus em lotes completos; resultados de busca só localizam. Na
API Claude, citações de documento cobrem texto, não conteúdo de imagens:
[documentação de citações](https://platform.claude.com/docs/en/build-with-claude/citations).
Digitalização sem camada textual exige visão/transcrição atribuída à página;
não inventar citação nativa para uma imagem. Visão, código e navegação devem
ser observados na sessão, não inferidos do nome Claude.

Se houver código, executar ferramentas locais e registrar recibos; caso
contrário, registrar referências observadas e controles não executados. Separar
origem da captura de aplicabilidade jurídica. Preservar originais, relações e
versões; atualizar os Markdown cumulativos. Perguntar só quando faltar dado
indispensável depois da busca. Inicial afirmativa na voz da parte, com fonte,
sem relatório documental. Toda minuta: RASCUNHO — NÃO PROTOCOLAR.

Instalação de skills e disponibilidade:
[documentação oficial](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
Use o pacote Claude completo; Claude Code pode usar diretório de skill local.
