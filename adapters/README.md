# Adaptadores de plataforma

O núcleo jurídico é único em `skills/legal-process-parser/`. Cada adaptador é
uma entrada curta para a plataforma correspondente; não misture instruções de
provedores no contexto de uma tarefa.

| Plataforma | Entrada | Forma de uso |
|---|---|---|
| Manus | `SKILL.md` na raiz | link GitHub, `.skill` ou `.zip` |
| Gemini CLI | `gemini-extension.json` + `GEMINI.md` | extensão GitHub ou pacote |
| Gemini Gem | `gemini/GEM_INSTRUCTIONS.md` | instruções e Knowledge selecionado |
| Grok | `grok/SYSTEM_INSTRUCTIONS.md` | instruções e arquivos anexados |
| ChatGPT/GPT | `chatgpt/INSTRUCTIONS.md` | Skill `.skill` ou link do repositório |
| Claude | `claude/CLAUDE_INSTRUCTIONS.md` | pacote com `SKILL.md` na raiz |

Todos os adaptadores ordenam: entrada → núcleo → tarefa → corpus do cliente.
Nas tarefas jurídicas, todos usam `legal_narrative.json`/`analise_juridica.md`
para a mesma narrativa afirmativa, com fonte por página e pesquisa normativa
oficial verificada.
Nenhum chama outra IA. O custo e o tempo dependem da análise do processo e das
ferramentas do provedor escolhido, não da existência dos demais adaptadores no
GitHub.
