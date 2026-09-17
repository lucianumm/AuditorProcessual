# AuditorProcessual — entrada universal para IAs

Este arquivo é o primeiro ponto de leitura quando o repositório for fornecido
por URL. Não leia o repositório inteiro. Identifique a plataforma e a tarefa e
abra somente os caminhos indicados.

## Roteamento por plataforma

| Plataforma | Primeiro arquivo | Próximo passo |
|---|---|---|
| Manus | `SKILL.md` | usar o núcleo em `skills/legal-process-parser/` |
| Gemini CLI | `GEMINI.md` e `gemini-extension.json` | ativar `skills/legal-process-parser/SKILL.md` |
| Gemini Gem | `adapters/gemini/GEM_INSTRUCTIONS.md` | adicionar somente referências necessárias como Knowledge |
| Grok | `adapters/grok/SYSTEM_INSTRUCTIONS.md` | anexar o processo e consultar os arquivos por busca documental |
| ChatGPT/GPT | `skills/legal-process-parser/SKILL.md` | usar o pacote `.skill` ou o núcleo do repositório |
| Claude | `adapters/claude/CLAUDE_INSTRUCTIONS.md` | usar o pacote com `SKILL.md` na raiz |

## Roteamento por tarefa

Depois de escolher a plataforma, leia `routing/task-router.json` e carregue
somente a referência da tarefa solicitada:

- `ingest`: extração integral, preservação e localização;
- `analyze`: contexto, cronologia, controvérsias, provas e riscos;
- `petition`: checklist e minuta da peça solicitada;
- `deadlines`: marcos e pendências para conferência;
- `evidence`: mapa de provas e fontes;
- `audit`: pacote completo, quando solicitado.

## Regra de corpus

Quando o usuário enviar um processo inteiro, analise todas as páginas e imagens
do corpus, mas não carregue instruções de outras plataformas. Use o manifesto,
`relatorio_processual.md`, `pages.jsonl` e `index.jsonl` para localizar o material
em blocos. Gere ou atualize os relatórios Markdown sem apagar versões anteriores.

Depois de representar todo o corpus, consulte `legal_basis.json`,
`base_legal.md` e, para análise/peça, `legal_narrative.json`/`analise_juridica.md`:
eles encaminham a área jurídica, as evidências por página, as fontes oficiais
candidatas e o padrão de redação. Escreva fatos e provas em narrativa afirmativa
com âncora direta; não descreva o ato de “analisar documentos”. Pesquise de
forma ampla normas constitucionais, processuais, especiais, locais e
regulamentares potencialmente aplicáveis. Só cite uma norma como fundamento
depois de verificar vigência, competência, hierarquia, direito intertemporal e
jurisprudência em fonte oficial.

Consulte também `quality_gate.json`/`quality_gate.md`. Em `analyze`, `petition`
ou `audit`, use `matriz_fato_prova_norma_pedido.json/.md` para vincular cada
afirmação a fonte, prova mencionada, norma candidata e pedido. `review_required`
é um bloqueio de certeza, não uma aprovação implícita. As regras detalhadas de
linguagem estão em `references/legal_narrative_rules.md`.

Para análise, auditoria ou peça efetivamente conclusiva, use também
`case_memory.json`, `memoria_processual.md` e `passages.jsonl`. A IA deve
produzir `legal_review.json` conforme `schemas/legal_review.schema.json`,
capturar fontes oficiais com `scripts/research_sources.py` e executar
`scripts/legal_review.py saida --review legal_review.json`. O contrato exige
revisão de todas as páginas, fatos com origem e citação literal, norma oficial
com vigência/competência, subsunção requisito por requisito, contrapontos e
pedidos compatíveis. Sem validação, preserve `review_required` e não apresente
conclusão jurídica final. Em petição inicial, siga
`references/initial_petition_rules.md`: redação afirmativa da parte e nenhuma
fórmula de relatório documental.

Não leia por padrão `adapters/` de outra plataforma, `tests/`, `build/`,
`CHANGELOG.md`, `LICENSE` ou arquivos de empacotamento. Abra-os apenas se o
usuário pedir manutenção do repositório.

## Contrato de saída

Para PDFs com imagens, a IA revisa primeiro a página inteira e depois os visuais relevantes. O núcleo usa `best_effort` por padrão; somente use `--require-semantic-vision`/`vision_policy: required` quando houver provider e `vision_review.json` real. Imagens são deduplicadas por SHA-256 e entregues em `images/index.json`, com assets de página em `assets/pages/` e ZIP portátil. Cada plataforma pode preencher o mesmo contrato sem ler os adaptadores das demais.

Execute uma tarefa por solicitação. Cite arquivo, página PDF, folha processual,
document_id e trecho quando disponíveis. Separe fato, alegação, prova, decisão e
inferência. Pergunte somente se houver ambiguidade, conflito ou dado indispensável
ausente. Nunca invente dados, calcule prazo sem premissas ou trate minuta como
protocolável.

Se houver novo upload, não substitua a memória: atualize as versões e o Markdown
cumulativo. Uma revisão cujo `corpus_revision` não corresponda ao corpus atual é
`stale` e precisa ser refeita. Não carregue arquivos de outras plataformas; o
mesmo contrato JSON é suficiente para qualquer modelo que esteja usando a skill.

O núcleo normativo está em `skills/legal-process-parser/SKILL.md`; este arquivo
apenas direciona a leitura para evitar desperdício de contexto. A saída
principal de análise deve ser uma narrativa jurídica afirmativa, com tese
organizada por fatos, prova, norma conferida, subsunção, contrapontos e pedido.
