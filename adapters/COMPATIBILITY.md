# Compatibilidade e limites observados

Documentação consultada em 2026-10-10. Condições de conta/interface mudam;
consultar a fonte oficial antes de instalar. A skill é provider-neutral e usa
somente o modelo do usuário. Ter adaptadores no repo não faz a IA carregar todos.

| Superfície | Distribuição deste projeto | Limite operacional |
|---|---|---|
| ChatGPT com Habilidades | ZIP/SKILL com SKILL.md na raiz | Recurso depende de elegibilidade/workspace; upload não garante ferramentas |
| GPT personalizado | Instructions + referências selecionadas em Knowledge | Não equivale a instalar skill nem executar Python automaticamente |
| Claude/Claude Code | ZIP próprio ou diretório local | Citações de texto não comprovam conteúdo de imagem; revisar scans |
| Gemini CLI | Extensão com skill no diretório skills/ | Skills por demanda; confirmar ferramentas e permissões na sessão |
| Gemini Gem | Instruções + Knowledge pertinente | Recurso de API não prova a mesma capacidade no Gem |
| Manus | Importação GitHub com SKILL.md raiz ou pacote | Confirmar as ferramentas realmente disponíveis e política de dados |
| Grok | Instruções e pacote de recursos | ID de arquivo em busca/Collections não substitui página/trecho do original |

As capacidades em `execution_context` começam `not_tested`. `available` exige
referência observada da sessão; `unavailable` registra a limitação. Nunca chamar
um segundo provider só para cumprir um checklist. Sem código, cumprir o método
com ferramentas reais e informar controles locais não executados. PDF visual,
Office textual, tabela/célula e citação nativa são camadas distintas.

Fontes primárias que orientaram os adaptadores:

- [OpenAI — Skills no ChatGPT](https://help.openai.com/pt-br/articles/20001066-skills-in-chatgpt) e [File inputs na API](https://developers.openai.com/api/docs/guides/file-inputs).
- [Anthropic — Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) e [Citations](https://platform.claude.com/docs/en/build-with-claude/citations).
- [Google — extensões/skills Gemini CLI](https://geminicli.com/docs/extensions/writing-extensions/) e [documentos na Gemini API](https://ai.google.dev/gemini-api/docs/document-processing).
- [Manus — importar e compartilhar skills](https://help.manus.im/en/articles/14753565-how-to-share-and-use-skills-in-manus).
- [xAI — Collections](https://docs.x.ai/developers/files/collections).

Validação separada por etapas: arquivo/pacote válido; execução local isolada;
importação na interface; uso com visão/busca reais; avaliação por especialista.
Este repositório testa automaticamente apenas as duas primeiras, com dados
sintéticos. Não anuncia homologação das empresas nem validação profissional real.
