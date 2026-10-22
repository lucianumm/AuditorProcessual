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
`memoria_processual.md`, `passages.jsonl`), produza `legal_review.json` v4 com
`piece_assessment`, `norm_applications` e `theses`, capture as normas oficiais e
valide com `scripts/legal_review.py`. Use os estados por questão para delimitar
pendências e entregar conclusões independentes. Em análise e petição, siga os
guias de seleção da peça e integração normativa do roteador; carregue a regra de
inicial somente quando essa peça estiver em questão. A narrativa inicial é
afirmativa, na voz da parte.

Fundamentos em tempo real: antes de citar artigo, súmula, OJ, Tema ou ação de
controle, abrir a fonte oficial na própria resposta e copiar o dispositivo com
sua marca de redação ("Redação dada…", "Revogado…", "Vide ADI…") ou a linha de
situação do precedente; comparar com as datas dos fatos
(`references/citation_verification_rules.md`). TST, STF, LexML e Mediador
bloqueiam robôs: usar o navegador da plataforma ou arquivo oficial enviado; se
nada funcionar, registrar o bloqueio e delimitar a conclusão. Trabalhista:
escolher pretensões em `references/labor_claims_index.md` e abrir só as
entradas escolhidas (teses dos dois polos e autoridades candidatas).

Siga `references/precision_review_rules.md` no núcleo, incluindo cobertura de
intervalos, afirmações atômicas, temporalidade e comparação factual de
precedentes. `case_packet.py` exporta lotes integrais; recibos não comprovam
compreensão. Confirmar recursos na sessão; instalação não concede ferramentas.
Use apenas os gatilhos e módulos pertinentes. Originais, relações e versões
permanecem preservados e `indice_juridico.md` localiza itens por página.
[Documentação oficial de importação](https://help.manus.im/en/articles/14753565-how-to-share-and-use-skills-in-manus).
