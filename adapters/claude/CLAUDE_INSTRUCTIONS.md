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

Fundamentos em tempo real: antes de citar artigo, súmula, OJ, Tema ou ação de
controle, abrir a fonte oficial na própria resposta e copiar o dispositivo com
sua marca de redação ("Redação dada…", "Revogado…", "Vide ADI…") ou a linha de
situação do precedente; comparar com as datas dos fatos
(`references/citation_verification_rules.md`). TST, STF, LexML e Mediador
bloqueiam robôs: usar o navegador da plataforma ou arquivo oficial enviado; se
nada funcionar, registrar o bloqueio e delimitar a conclusão. Trabalhista:
escolher pretensões em `references/labor_claims_index.md` e abrir só as
entradas escolhidas (teses dos dois polos e autoridades candidatas).

Instalação de skills e disponibilidade:
[documentação oficial](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
Use o pacote Claude completo; Claude Code pode usar diretório de skill local.
