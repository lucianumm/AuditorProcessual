# Adaptador Gemini

## Gemini CLI

Instale a extensão diretamente do repositório:

```text
gemini extensions install https://github.com/lucianumm/AuditorProcessual --ref v0.14.0 --consent
```

O `gemini-extension.json` carrega apenas `GEMINI.md`; a Skill em
`skills/legal-process-parser/` é ativada sob demanda. Reinicie o CLI depois da
instalação ou atualização.

## Gemini Gem

Use `GEM_INSTRUCTIONS.md` no campo de instruções do Gem. Em Knowledge, adicione
somente `skills/legal-process-parser/SKILL.md` e as referências da tarefa; não
adicione os adaptadores de outras plataformas nem o repositório completo.

Em análise, petição ou auditoria, carregue também
`skills/legal-process-parser/references/semantic_crosscheck_rules.md`.
