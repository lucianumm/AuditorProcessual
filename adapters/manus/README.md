# Adaptador Manus

O repositório possui `SKILL.md` na raiz para importação direta por GitHub. O
Manus deve ler `AI_ENTRYPOINT.md`, abrir somente `skills/legal-process-parser/`
e ativar uma tarefa por solicitação.

## Instalação

No Manus, abra Skills → Add → Import from GitHub e use:

```text
https://github.com/lucianumm/AuditorProcessual
```

Também é possível usar o pacote `auditor-processual-manus.skill` ou `.zip` da
release. Em uma conversa, invoque a Skill pelo comando `/` e diga a entrega
desejada. O processo completo pode ser analisado; instruções de outras
plataformas não devem ser carregadas.

Antes de afirmar completude, consulte `quality_gate.json`. Para análise,
auditoria ou peça, use `legal_basis.json`, `legal_narrative.json`/
`analise_juridica.md` e `matriz_fato_prova_norma_pedido.json` para escrever
narrativa jurídica afirmativa, mantendo fatos, alegações, provas, decisões,
normas candidatas e pedidos rastreáveis. Não use “conforme documentação”,
“documento apresentado” ou “certidão analisada”. Pesquise normas oficiais
constitucionais, processuais, especiais, locais e regulamentares antes de
concluir a tese.

Na análise autoral, leia a memória cumulativa (`case_memory.json`,
`memoria_processual.md`, `passages.jsonl`), produza `legal_review.json`, capture
as normas oficiais e valide com `scripts/legal_review.py`. Sem validação,
mantenha `review_required`; a inicial é sempre afirmativa na voz da parte.
