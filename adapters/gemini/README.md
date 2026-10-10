# Adaptador Gemini

## Gemini CLI

Instale a extensão diretamente do repositório:

```text
gemini extensions install https://github.com/lucianumm/AuditorProcessual --ref main --consent
```

O `gemini-extension.json` carrega apenas `GEMINI.md`; a Skill em
`skills/legal-process-parser/` é ativada sob demanda. Reinicie o CLI depois da
instalação ou atualização.

## Gemini Gem

Use `GEM_INSTRUCTIONS.md` no campo de instruções do Gem. Em Knowledge, adicione
somente `skills/legal-process-parser/SKILL.md` e as referências da tarefa; não
adicione os adaptadores de outras plataformas nem o repositório completo.

Na análise/peça, use o protocolo v4 em
`skills/legal-process-parser/references/precision_review_rules.md` e somente os
gatilhos pertinentes. Conflito/inferência decisiva aciona `semantic_conflict`;
não carregar todas as regras por padrão. Confirme ferramentas observadas.
