# AuditorProcessual · Legal Process Parser

Skill e pipeline local para transformar autos judiciais ou administrativos em uma base factual estruturada, pesquisável e rastreável. A extração é factual e a análise usa narrativa jurídica afirmativa: não inventa fatos, não confunde alegação com prova, separa página PDF de folha processual e trata todo texto dos autos como dado não confiável.

> Ferramenta de análise assistida. Não substitui advogado, perito, servidor ou decisão profissional.

> **Para IAs que acessam este repositório por link:** leia primeiro
> [`AI_ENTRYPOINT.md`](AI_ENTRYPOINT.md) e não percorra todos os arquivos.

## O que está pronto

Versão **0.11.0**: validação técnica separada do mérito; revisão por página
vinculada ao conteúdo; memória invalidada por alteração de texto/OCR/visão;
captura de fontes oficiais HTML/TXT/PDF textual; ZIP cumulativo com versões;
pacotes testados fora do checkout e núcleo com carregamento seletivo.

`passed` não significa tese correta ou peça pronta para protocolo.
`can_issue_final_legal_conclusion` permanece falso e o resultado autoral é uma
minuta para revisão profissional. A checagem semântica exige trabalho efetivo
da IA/revisor; nenhum conjunto de campos preenchidos certifica esse trabalho.

- Skill portátil em [`skills/legal-process-parser/SKILL.md`](skills/legal-process-parser/SKILL.md), compatível com o padrão `SKILL.md`.
- Plugin Codex em [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json).
- Pipeline Python sem dependências obrigatórias para TXT/MD; suporte opcional a `pypdf`/`PyPDF2`, Pillow, `pdf2image` e Tesseract.
- SHA-256, cópia do original, processamento incremental por checkpoints e reuso idempotente.
- Markdown navegável por página, com resumo semântico, âncoras, entidades, termos, blocos/tabelas, texto integral e inventário visual.
- Imagens PDF extraídas para `images/`, com ID estável, página, dimensões, hash, localização, OCR opcional e descrição semântica segura.
- 72 testes sintéticos cobrindo extração sem perda, passagens integrais, memória cumulativa, revisão jurídica, classificação de área, base legal, narrativa afirmativa, gates de qualidade, matriz fato–prova–norma–pedido, inventário visual, classificação/deduplicação, descrições revisadas, estados de visão, peças de andamento, confirmação opcional, execução seletiva, preservação de uploads, idempotência, links e roteamento multiplataforma.
- Pacotes específicos para ChatGPT, Claude, Manus, Gemini CLI/Gems e Grok, gerados sem duplicar o núcleo jurídico.

Os nove arquivos ZIP/SKILL são testados por extração e execução local isolada.
Isso não certifica a interface de upload nem as capacidades de cada conta de
ChatGPT, Claude, Gemini, Manus ou Grok. Visão, navegação, execução e persistência
continuam dependentes da plataforma; as instruções não concedem essas ferramentas.
- Entrada universal para uso por link em [`AI_ENTRYPOINT.md`](AI_ENTRYPOINT.md), [`llms.txt`](llms.txt) e [`SKILL.md`](SKILL.md).
- Classificação automática da área jurídica, base legal com evidências por página e perfil de redação específico para o caso.

O procedimento específico de upload e instalação está em
[`CHATGPT_UPLOAD.md`](CHATGPT_UPLOAD.md). A skill trabalha de forma incremental:
inspeciona os materiais já enviados, executa somente a tarefa solicitada e
mantém o histórico em `relatorio_processual.md` e `versions/`.

## Uso por link do GitHub

Quando a IA receber apenas o endereço do repositório, comece por
[`AI_ENTRYPOINT.md`](AI_ENTRYPOINT.md) ou [`llms.txt`](llms.txt). Eles encaminham
para a plataforma e a tarefa corretas. Não é necessário carregar ou ler o
repositório inteiro: o núcleo em `skills/legal-process-parser/` é analisado por
blocos, enquanto adaptadores, testes e arquivos de outras plataformas ficam fora
do contexto padrão.

O roteamento está em [`routing/task-router.json`](routing/task-router.json). O
processo do cliente pode ser analisado integralmente — páginas, imagens, peças,
contexto e linha do tempo — sem carregar instruções irrelevantes.

Após a extração, a skill identifica a área predominante com pontuação, evidências
por página e margem de ambiguidade. `legal_narrative.json` e
`analise_juridica.md` preservam um inventário de trechos por página para a
posterior redação autoral pela IA. O resultado encaminha fontes oficiais e um perfil adequado ao
caso, mas mantém o fundamento como provisório até a conferência da vigência
normativa, competência, hierarquia, direito intertemporal, legislação
especial/local e jurisprudência aplicável.

Para análise, auditoria ou petição, o modelo usa ainda `case_memory.json`,
`memoria_processual.md` e `passages.jsonl` e entrega uma revisão estruturada em
`legal_review.json`. As normas precisam ser capturadas em fonte oficial e a
revisão deve passar pelo validador para gerar uma minuta sujeita à revisão profissional. A extração
isolada permanece `review_required`; novos uploads atualizam a memória e tornam
revisões antigas `stale` sem apagar versões.

## Uso rápido

Requer Python 3.10 ou superior.

Para a revisão jurídica, instale `jsonschema`; para PDF, `pypdf`, e para
renderização/OCR, as dependências opcionais e Poppler/Tesseract. A ingestão
TXT/MD continua sem dependências externas. O parser não chama provedores de IA:
o modelo do usuário interpreta e preenche os contratos.

```powershell
cd AuditorProcessual\skills\legal-process-parser
python scripts/ingest_document.py C:\dados\processo.pdf --output C:\dados\saida --task audit --confirm-scope
python scripts/validate_extraction.py C:\dados\saida
python scripts/validate_links.py C:\dados\saida
```

Para ler o corpus sem despejá-lo inteiro no contexto:

```powershell
python scripts/case_memory.py C:\dados\saida --offset 0 --limit 20
python scripts/case_memory.py C:\dados\saida --query "pagamento" --limit 10
```

Na leitura integral, percorra todos os lotes; buscas não substituem essa etapa.
Nos novos envios, `update.changed_pages` indica o que mudou para reavaliar as
dependências jurídicas. A memória é o arquivo preservado, não uma garantia de
persistência entre sessões de qualquer plataforma.

### Migração da versão 0.10

Revisões antigas não são automaticamente aprovadas. Acrescente `page_reviews`,
`facts[].support` e `issues[].research`, conforme o contrato atualizado.
Revisões visuais precisam de `source_sha256` e `render_sha256` por página;
use os hashes do arquivo e da renderização gerados na primeira ingestão.
Recapture fontes antigas para preservar também a resposta bruta `.source`.
Nenhum processo ou plano de melhoria deve ser enviado ao repositório público.

Depois que a IA produzir a revisão conforme
[`schemas/legal_review.schema.json`](skills/legal-process-parser/schemas/legal_review.schema.json),
instale `jsonschema`, capture cada norma oficial e valide a entrega:

```powershell
python -m pip install jsonschema
python scripts/research_sources.py C:\dados\saida --url https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm
python scripts/legal_review.py C:\dados\saida --review C:\dados\legal_review.json
```

O validador não inventa fatos nem decide o mérito: ele bloqueia páginas não
revisadas, trechos sem fonte, normas não capturadas, cálculos divergentes,
referências de pedidos inválidas e algumas formulações de relatório. Compatibilidade jurídica e suporte semântico exigem avaliação real, não apenas validação automática. Em petições iniciais, consulte
[`initial_petition_rules.md`](skills/legal-process-parser/references/initial_petition_rules.md)
para manter a redação afirmativa da parte.

Antes de executar, a skill inspeciona os arquivos, o manifesto e o relatório
cumulativo. Ela pergunta apenas quando o pedido estiver ambíguo, houver conflito
ou faltar um dado indispensável; não repete perguntas que possam ser respondidas
pelos autos. A pipeline executa uma tarefa por vez: `ingest`, `analyze`,
`petition`, `deadlines`, `evidence` ou `audit`. `--confirm-scope` é opcional e
serve apenas para registrar uma confirmação explícita quando ela for útil.

Para tentar OCR somente nas páginas PDF sem texto nativo útil (requer Tesseract e Poppler):

```powershell
python scripts/ingest_document.py C:\dados\processo.pdf --output C:\dados\saida --task ingest --confirm-scope --ocr --ocr-language por+eng
```

Para anexar descrições semânticas revisadas por humano ou modelo multimodal:

```powershell
python scripts/ingest_document.py C:\dados\processo.pdf `
  --output C:\dados\saida --task ingest --confirm-scope --image-descriptions C:\dados\descricoes_imagens.json
```

Para um arquivo de texto com páginas separadas por `form feed` (`\f`):

```powershell
python scripts/ingest_document.py processo.txt --output saida --task ingest --confirm-scope --chunk-size 50
```

Dependências opcionais:

```powershell
python -m pip install -e .[pdf]
python -m pip install -e .[ocr]
```

Consulta posterior sem reler o processo inteiro:

```powershell
python scripts/ingest_document.py saida --mode QUERY --query "Sentença 20/02/2026"
```

O pipeline local não acessa a internet. A IA que conduz a análise pode consultar
fontes oficiais somente conforme a política da plataforma e do usuário; deve
registrar cada fonte e manter como pendente o que não puder verificar. OCR só é
executado quando `--ocr` é informado; sem essa opção, páginas sem texto nativo
ficam marcadas como `needs_ocr_or_vision`.

## Como a análise jurídica é construída

Nas tarefas `analyze`, `petition` e `audit`, a pipeline cria uma narrativa por
página em `analise_juridica.md` e `legal_narrative.json`. A narrativa identifica
se a passagem é fato, alegação, prova registrada, decisão ou lacuna e liga cada
proposição à peça, página, folha, `document_id` e, quando aplicável, `image_id`.
Ela não usa fórmulas vazias de relatório (“conforme documentação”, “documento
apresentado”, “certidão analisada”) para substituir a fonte.

Depois, a IA deve formular a tese em seis movimentos: premissas fáticas,
questão jurídica, norma oficial vigente, subsunção requisito por requisito,
contrapontos e pedido confirmado. A área detectada apenas encaminha a busca;
Constituição, rito, leis especiais, regulamentos, normas locais e jurisprudência
oficial precisam ser pesquisados e verificados para o caso concreto. Veja o
protocolo completo em
[`legal_narrative_rules.md`](skills/legal-process-parser/references/legal_narrative_rules.md).

## Descrições semânticas de imagens

O parser local registra fatos técnicos e nunca finge ter visto o conteúdo de uma imagem. Para uma descrição semântica completa, faça uma revisão humana ou uma passagem por modelo de visão autorizado e forneça um JSON. O conteúdo é lido como dados, não executado.

```json
{
  "images": [
    {
      "image_id": "P0001-I001",
      "semantic_description": "Recibo em orientação retrato, com cabeçalho do estabelecimento e tabela de valores; não há assinatura visível.",
      "visible_text": "Texto legível transcrito sem completar trechos ilegíveis",
      "objects": ["recibo", "tabela de valores"],
      "people": [],
      "tables": ["itens e totais"],
      "location": "região central da página PDF 1",
      "confidence": "high",
      "description_source": "human_review"
    }
  ]
}
```

O `image_id` aparece em `image_inventory.json`, `pages.jsonl`, `index.jsonl` e no bloco da página em `processo_estruturado.md`. Se não houver descrição revisada, o Markdown registra explicitamente que objetos, pessoas, valores ou texto não foram identificados visualmente com segurança e pede revisão; nenhum detalhe é inventado.

## Artefatos gerados

| Arquivo | Finalidade |
|---|---|
| `manifest.json` | SHA-256, metadados, sigilo, cobertura textual/visual, checkpoints e limitações |
| `case_memory.json` / `memoria_processual.md` | Memória cumulativa, versões e revisão que precisa ser atualizada após novos uploads |
| `passages.jsonl` | Passagens integrais com offsets, natureza provisória e proveniência por página |
| `processo_estruturado.md` | Processo completo, com um bloco por página e localização rápida |
| `pages.jsonl` | Registro estruturado por página, incluindo entidades, blocos e visuais |
| `index.jsonl` | Busca exata por texto, termos, resumo, entidades e imagens |
| `image_inventory.json` | Catálogo de imagens/escaneamentos, hashes, caminhos e descrições |
| `legal_basis.json` | Área identificada, evidências por página, fontes normativas candidatas e perfil de redação |
| `base_legal.md` | Fontes oficiais encaminhadas e portas de verificação antes de qualquer peça |
| `legal_narrative.json` / `analise_juridica.md` | Narrativa afirmativa por página, fatos/alegações/provas/decisões, questões jurídicas e sequência de subsunção |
| `legal_review_validation.json` | Resultado do contrato autoral, capturas oficiais, cobertura e bloqueios |
| `ficha_estrategica.json` / `fundamentacao_estrategica.md` | Objetivo, jurisdição, tese, contrapontos e aplicação requisito por requisito após validação |
| `research_sources/` | Recibos de fontes oficiais capturadas, com URL final, data, texto e hashes |
| `quality_gate.json` / `quality_gate.md` | Gates explícitos de cobertura, proveniência, classificação, matriz e verificação legal |
| `images/` | Cópias derivadas de imagens incorporadas ao PDF, sem alterar o original |
| `rendered_pages/` | Renderizações integrais das páginas PDF quando `pdf2image`/Poppler estão disponíveis |
| `indice_pecas.md` | Segmentos/peças com páginas inicial e final |
| `cronologia.md` | Datas identificadas e fontes internas |
| `matriz_controversias.md` | Indícios de pedidos, provas e impugnações |
| `relatorio_auditoria.md` | Nome histórico mantido por compatibilidade; conteúdo em narrativa jurídica com fontes e limitações |
| `relatorio_processual.md` | Índice cumulativo de todos os uploads preservados e links para versões |
| `andamento_processual.json` | Contrato estruturado de eventos, prazos, evidências, pendências e tarefas |
| `relatorio_andamento.md` | Estado atual, últimos eventos e próximas conferências |
| `pendencias_e_prazos.md` | Marcos encontrados sem cálculo automático de vencimento |
| `matriz_documental.md` | Peças, intervalos de páginas e status técnico |
| `matriz_fato_prova_norma_pedido.json/.md` | Ligação rastreável entre fatos, provas mencionadas, normas candidatas e pedidos |
| `mapa_provas.md` | Menções documentais com fonte e revisão pendente |
| `checklist_manifestacao.md` | Conferências necessárias antes de uma manifestação |
| `minuta_peca.md` | Esqueleto de peça de trabalho, sem protocolo automático |
| `relatorio_conformidade.md` | Portas de qualidade e limitações da extração |
| `checkpoints.jsonl` | Recuperação e diagnóstico de blocos |

| Arquivo | Finalidade |
|---|---|
| `processo_completo.md` | Alias portátil do Markdown estruturado para compartilhamento |
| `images/index.json` | Índice de imagens únicas, classes, hashes e ocorrências |
| `assets/pages/` | Renderizações de páginas copiadas para o pacote portátil |
| `paginas_problematicas.md` | Fila de páginas sem camada textual, visual ou técnica suficiente |
| `processo_completo.zip` | Pacote completo com originais derivados, Markdown, índices e assets |

As expressões genéricas de inventário (“conforme documentação”, “documento
apresentado”, “certidão analisada” e equivalentes) não são usadas como
fundamentação. Consulte [`skills/legal-process-parser/references/legal_narrative_rules.md`](skills/legal-process-parser/references/legal_narrative_rules.md) para a linguagem exigida e o protocolo de pesquisa normativa oficial.

### Como localizar qualquer item

1. Procure o cabeçalho `## [Página PDF N]` no Markdown.
2. Use a âncora `PDF p. N` e, se existir, `fl. M` para distinguir a paginação física dos autos.
3. Consulte `image_inventory.json` pelo `image_id` para chegar ao arquivo em `images/`.
4. Use `index.jsonl` para busca exata por número de processo, data, valor, e-mail, CPF/CNPJ, termo-chave ou ID de imagem.
5. Confirme sempre no PDF original; o hash comprova integridade do arquivo processado, não autenticidade jurídica.

## Modos disponíveis

`INGEST`, `AUDIT_FULL`, `QUERY`, `COMPARE`, `EVIDENCE_ANALYSIS`, `DECISION_ANALYSIS`, `PLEADING_AUDIT`, `PETITION_DRAFT`, `PROCEDURAL_ANALYSIS`, `CALCULATION_SUPPORT` e `UPDATE`.

Os modos usam a mesma ingestão rastreável. O parser não presume a área do Direito e usa “Não identificado nos autos” quando não há evidência suficiente.

## Instalar como skill

### Qualquer IA por link

Envie o endereço do repositório e peça: “Leia `AI_ENTRYPOINT.md`, identifique a
plataforma, use somente o adaptador correspondente e analise o processo completo
conforme a tarefa solicitada.” A IA deve abrir somente os arquivos roteados.

### Codex

1. Clone este repositório ou baixe `skills/legal-process-parser`.
2. Copie a pasta para `%USERPROFILE%\.codex\skills\legal-process-parser` (ou use o instalador de skills apontando para `https://github.com/lucianumm/AuditorProcessual/tree/main/skills/legal-process-parser`).
3. Reinicie o Codex e peça: “Use Legal Process Parser para ingerir este processo e informe a cobertura real.”

### ChatGPT / GPTs

Carregue a pasta como Skill em `Plugins → Skills → Create → Upload` ou anexe-a a um GPT como conhecimento e copie as regras centrais para Instructions. Para chamar o pipeline por HTTP, publique uma API própria com autenticação, privacidade, limites e um schema OpenAPI; este repositório não oferece endpoint público.

Para a tela de upload mostrada no ChatGPT, use o arquivo
`legal-process-parser-chatgpt.skill` (ou o ZIP equivalente), que mantém
`SKILL.md` na raiz. Consulte [`CHATGPT_UPLOAD.md`](CHATGPT_UPLOAD.md) para o
passo a passo e a referência oficial da OpenAI.

### Claude

Use `auditor-processual-claude.zip`, que mantém `SKILL.md` na raiz, e faça
upload em `Customize → Skills` no Claude.ai. No Claude Code, copie o diretório
para `.claude/skills/legal-process-parser/`. Para a API Anthropic, envie o ZIP
pela Skills API com code execution habilitado e mantenha autos no ambiente
autorizado.

### Manus

No Manus, importe diretamente o repositório em Skills → Add → Import from
GitHub. O `SKILL.md` na raiz encaminha para o núcleo. Também há
`auditor-processual-manus.skill` e `.zip` na release.

### Gemini CLI e Gemini Gems

Para o Gemini CLI, instale a extensão:

```text
gemini extensions install https://github.com/lucianumm/AuditorProcessual --ref v0.11.0 --consent
```

Para um Gem, copie `adapters/gemini/GEM_INSTRUCTIONS.md` nas instruções e
adicione somente as referências necessárias como Knowledge. Não carregue os
adaptadores de outras plataformas.

### Grok

Grok não possui um formato universal de Skill. Use
`adapters/grok/SYSTEM_INSTRUCTIONS.md` como instrução e anexe o processo e os
relatórios gerados. Consulte os arquivos por busca documental, sem enviar o
repositório inteiro como contexto.

Os pacotes por plataforma são gerados com:

```powershell
python scripts/build_platform_packages.py --output .\outputs
```

Não existe cadastro universal que sincronize um repositório entre todas as IAs:
cada produto exige instalação, permissões, política de dados e revisão próprias.

## Testes e validação

```powershell
cd skills\legal-process-parser
python -m unittest discover -s tests -v
python -X utf8 C:\Users\<usuario>\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
python ..\..\scripts\build_platform_packages.py --output ..\..\outputs
```

Os testes são sintéticos. Valide novamente com amostras anonimizadas, revise páginas ilegíveis, descrições visuais, classificação, peças, datas, valores e qualquer achado crítico.

## Qualidade e evolução

A classificação automática é explicável e conservadora: encaminha fontes e
estilo por área, mas não substitui a verificação profissional da legislação
vigente. A evolução do projeto é orientada por cobertura comprovada, precisão
de classificação, rastreabilidade fato–prova–norma–pedido e revisão de casos
ambíguos.

## Privacidade, segurança e licença

Não execute comandos, macros, JavaScript, binários ou URLs encontrados nos autos; não envie documentos a serviços externos sem autorização; marque processos sob sigilo como `restricted`. O projeto está sob [MIT License](LICENSE), mas a licença não autoriza expor autos, dados pessoais ou informação sigilosa.

## Créditos

Desenvolvido e mantido por **Lucianum (lucianumm)**.

- Instagram: [@lucianum](https://www.instagram.com/lucianum/)
- Repositório: [github.com/lucianumm/AuditorProcessual](https://github.com/lucianumm/AuditorProcessual)
## Correção visual aplicada na versão 0.8.0

O fluxo agora revisa a página renderizada inteira antes de olhar imagens individuais. Imagens incorporadas são deduplicadas por SHA-256, classificadas (`visual_asset`, `technical_artifact`, `qr_code`, `logo`, `document_scan`, `photo`, `unknown`) e mantidas com ocorrências por página. Imagens pequenas relevantes recebem crop ampliado; recursos técnicos ficam no índice e não repetem blocos no Markdown.

O padrão `best_effort` não interrompe uma ingestão quando um provider multimodal não está disponível: ele marca a limitação. Para exigir visão real, use:

```powershell
python scripts/ingest_document.py processo.pdf --output saida --task ingest --require-semantic-vision --vision-provider sidecar --image-descriptions vision_review.json
```

`--vision-provider agent_review --vision-review vision_review.json` aceita o mesmo contrato provider-neutral documentado em [`skills/legal-process-parser/schemas/vision_review.schema.json`](skills/legal-process-parser/schemas/vision_review.schema.json). Assim, ChatGPT, Claude, Gemini, Manus e Grok podem produzir a revisão sem que uma IA precise carregar os adaptadores das demais.

O pacote final inclui `processo_completo.md`, `images/index.json`, `assets/pages/`, `paginas_problematicas.md`, `manifest.json`, `processo_completo.zip` e validação de links/assets:

```powershell
python scripts/validate_extraction.py saida
python scripts/validate_links.py saida
```

O manifesto registra `vision_policy`, `vision_provider`, `encoding.input` e `encoding.output`. `--encoding utf-8-sig` está disponível para compatibilidade com visualizadores antigos; o padrão é UTF-8.

O pipeline distingue explicitamente:

## Camadas de processamento e integridade

| Camada | Significado |
|---|---|
| Texto nativo | Texto extraído da camada textual do PDF/arquivo |
| Renderização | Imagem integral da página criada e validada por `pdf2image`/Poppler |
| Inspeção técnica | Verificação de existência, tamanho e caminho da renderização |
| OCR | Leitura complementar; nunca substitui visão semântica |
| Visão semântica | Descrição multimodal revisada, carregada pelo sidecar `pages` |
| Consolidação | União rastreável das camadas, sem apagar divergências |

Para PDF, `--vision-mode always` é o padrão. Se renderização ou visão semântica não estiverem disponíveis, a página permanece `PARTIAL` e o manifesto informa `CONVERSÃO FÍSICA COMPLETA COM LIMITAÇÕES VISUAIS`; o sistema não declara conversão integral.

```powershell
python scripts/ingest_document.py processo.pdf --output saida --task ingest --confirm-scope --vision-mode always --render-dpi 150
```

O JSON de descrições pode conter tanto imagens quanto páginas revisadas:

```json
{
  "pages": {
    "1": {
      "semantic_description": "Página com certidão digitalizada; campos legíveis descritos sem inferência jurídica.",
      "transcription": "Transcrição visual literal; lacunas marcadas como [ilegível].",
      "elements": ["certidão", "assinatura visível"],
      "outcome": "completed",
      "description_source": "vision_model",
      "confidence": "high"
    }
  },
  "images": []
}
```

Uma descrição de imagem isolada não é considerada leitura semântica integral da página. Para `COMPLETE`, a página PDF precisa ter renderização validada e descrição semântica de página, ou uma limitação explícita após tentativa legítima.
