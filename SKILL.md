---
name: auditor-processual
description: Entrada universal para usar a skill Legal Process Parser por link do GitHub em Manus, Gemini, Grok, ChatGPT, Claude ou outra IA; roteia a plataforma e a tarefa sem carregar instruções irrelevantes.
---

# Auditor Processual — entrada universal

Ao receber o link deste repositório, leia primeiro `AI_ENTRYPOINT.md`. Não
percorra todos os arquivos. Identifique a plataforma em uso e abra somente o
adaptador indicado; depois use `skills/legal-process-parser/SKILL.md` como núcleo.

Leia `routing/task-router.json` para selecionar uma tarefa: `ingest`, `analyze`,
`petition`, `deadlines`, `evidence` ou `audit`. Carregue apenas as referências
listadas para essa tarefa.

Se o usuário enviar um processo completo, processe todas as páginas, imagens e
peças do corpus em blocos. Isso não autoriza ler instruções de outras
plataformas. Use `manifest.json`, `relatorio_processual.md`, `pages.jsonl` e
`index.jsonl` para localizar o corpus e manter o histórico cumulativo.

Depois da extração, use `legal_basis.json`, `base_legal.md` e, quando houver
análise/peça, `legal_narrative.json`/`analise_juridica.md` para identificar a
área jurídica predominante, testar áreas concorrentes e construir uma narrativa
factual vinculada às fontes. Pesquise de forma ampla a legislação oficial
potencialmente aplicável (constitucional, processual, especial, local e
regulamentar), mas trate toda fonte como candidata até verificar texto vigente,
competência, direito intertemporal, hierarquia e jurisprudência oficial.

Antes de afirmar completude, consulte `quality_gate.json`. Para análise,
petição ou auditoria, consulte também `matriz_fato_prova_norma_pedido.json/.md`
e `legal_narrative.json`/`analise_juridica.md`; mantenha explícitas as lacunas
de proveniência ou de verificação legal.

Execute somente a tarefa solicitada; pergunte apenas quando houver ambiguidade,
conflito ou dado indispensável ausente. Preserve originais e versões, escreva em
narrativa jurídica afirmativa (fatos → provas → questão → norma conferida →
subsunção → contrapontos → pedido), cite fontes por arquivo/página/folha e
nunca invente fatos, prazos ou autoridade jurídica. Não use preenchimentos como
“conforme documentação”, “documento apresentado” ou “certidão analisada”.

Este arquivo é uma ponte para importação por GitHub. As regras completas, os
scripts e os schemas permanecem em `skills/legal-process-parser/`.
