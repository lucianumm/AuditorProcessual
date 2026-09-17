# Legal Process Parser — instruções para Claude

Leia `skills/legal-process-parser/SKILL.md` como núcleo e
`routing/task-router.json` como roteador. Para processos completos, examine
todo o corpus enviado — texto, imagens, peças, contexto, datas e linha do tempo
— em blocos e com citações por página.

Execute somente uma tarefa por solicitação. Antes de perguntar, procure os dados
no processo, no manifesto e em `relatorio_processual.md`. Pergunte apenas em
caso de ambiguidade, conflito ou lacuna indispensável. Preserve uploads e
versões, não invente conteúdo e marque toda minuta como **RASCUNHO — NÃO
PROTOCOLAR**.

Use `legal_basis.json`/`base_legal.md` e `legal_narrative.json`/
`analise_juridica.md` para encaminhar a área (trabalho, previdenciário,
consumidor etc.) e o padrão de redação. Escreva em narrativa jurídica
afirmativa, vinculando cada frase a peça, página, folha e `document_id`; evite
“conforme documentação”, “documento apresentado” e “certidão analisada”. Antes
de citar uma norma, confirme o texto vigente em fonte oficial, competência,
hierarquia e direito intertemporal, e preserve a proveniência por página.

Use `quality_gate.json` para decidir se a cobertura e a proveniência permitem
prosseguir. Em análise, auditoria ou peça, consulte a matriz
`matriz_fato_prova_norma_pedido.json/.md`; estados `review_required` devem ser
mantidos como pendências explícitas. Pesquise de forma ampla normas
constitucionais, processuais, especiais, locais, regulamentares e jurisprudência
oficial que possam incidir no caso.

Na etapa autoral, use a memória e as passagens integrais (`case_memory.json`,
`memoria_processual.md`, `passages.jsonl`) e preencha `legal_review.json`.
Capture cada norma em fonte oficial, valide o contrato com
`scripts/legal_review.py` e mantenha `review_required` quando houver qualquer
pendência. Petições iniciais devem ser afirmativas, na voz da parte, conforme
`references/initial_petition_rules.md`.
