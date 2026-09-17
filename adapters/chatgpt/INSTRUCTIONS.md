# Legal Process Parser — instruções para ChatGPT/GPT

Use `skills/legal-process-parser/SKILL.md` como núcleo. Primeiro leia os
arquivos enviados, `manifest.json` e `relatorio_processual.md`; depois selecione
uma tarefa pelo pedido. Não pergunte o que já estiver identificável nos autos.

Analise o processo inteiro quando solicitado, incluindo páginas, imagens,
peças, contexto e linha do tempo, mas carregue somente as referências da tarefa.
Preserve versões, cite fontes internas, não invente fatos e marque minutas como
rascunho não protocolável.

Após a extração completa, use `legal_basis.json`, `base_legal.md` e
`legal_narrative.json`/`analise_juridica.md` para seguir o perfil da área
identificada. Escreva em narrativa jurídica afirmativa: diga o que a parte
sustenta, o que a prova registra e o que a decisão determinou, sempre com
peça/PDF p./folha/document_id. Não use “conforme documentação”, “documento
apresentado” ou “certidão analisada” como preenchimento. Trate as fontes
normativas como candidatas até conferir o texto oficial vigente, competência,
hierarquia e direito intertemporal; vincule cada fundamento a fatos, provas e
páginas do processo.

Leia `quality_gate.json` antes de afirmar cobertura ou certeza. Para análise,
auditoria ou petição, use a matriz fato–prova–norma–pedido e mantenha como
pendente qualquer linha sem fonte ou norma conferida. Pesquise também normas
constitucionais, processuais, especiais, locais, regulamentares e jurisprudência
oficial potencialmente pertinentes antes de concluir a tese.

Para uma análise ou peça final, leia `case_memory.json`, `memoria_processual.md`
e `passages.jsonl`, produza `legal_review.json` conforme o schema e capture as
fontes oficiais antes de executar `scripts/legal_review.py`. Sem validação,
mantenha `review_required`; em petição inicial, use sempre a voz afirmativa da
parte e siga `references/initial_petition_rules.md`.
