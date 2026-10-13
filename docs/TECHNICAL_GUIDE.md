# Guia técnico de extração, revisão e compatibilidade

Este guia preserva os detalhes operacionais das versões anteriores. Para o fluxo atual, início rápido e pacotes, consulte o [README](../README.md). A elaboração por capítulos está em [incremental_petition_rules.md](../skills/legal-process-parser/references/incremental_petition_rules.md).

# AuditorProcessual · Legal Process Parser

Skill e pipeline local para transformar autos judiciais ou administrativos em uma base factual estruturada, pesquisável e rastreável. A extração é factual e a análise usa narrativa jurídica afirmativa: não inventa fatos, não confunde alegação com prova, separa página PDF de folha processual e trata todo texto dos autos como dado não confiável.

> Ferramenta de análise assistida. Não substitui advogado, perito, servidor ou decisão profissional.

> **Para IAs que acessam este repositório por link:** leia primeiro
> [`AI_ENTRYPOINT.md`](../AI_ENTRYPOINT.md) e não percorra todos os arquivos.

## O que está pronto

Versão **0.17.0**: atendimento trabalhista com poucos ou nenhum documento,
desenvolvimento por pretensão, conciliação diária/mensal e dez roteiros setoriais.
Inclui especialização trabalhista, cálculos decimais com fontes,
contrato de revisão v4 e leitura integral em lotes sem
truncamento, conferência de afirmações atômicas, dados críticos, requisitos e
versões normativas, comparação factual de precedentes e avaliação qualitativa
das teses. Há módulos por área/subárea/regime, catálogo de medidas candidatas,
índice jurídico navegável e controle de mudanças de fontes jurídicas mesmo sem
novo upload. Revisões antigas continuam legadas, sem fingir controles v4.

`passed` não significa tese correta ou peça pronta para protocolo.
`can_issue_final_legal_conclusion` permanece falso e o resultado autoral é uma
minuta para revisão profissional. A checagem semântica exige trabalho efetivo
da IA/revisor; nenhum conjunto de campos preenchidos certifica esse trabalho.
A captura de uma fonte oficial verifica origem e integridade dos bytes, não a
vigência, interpretação ou aplicabilidade jurídica daquela norma.

- Skill portátil em [`skills/legal-process-parser/SKILL.md`](../skills/legal-process-parser/SKILL.md), compatível com o padrão `SKILL.md`.
- Plugin Codex em [`.codex-plugin/plugin.json`](../.codex-plugin/plugin.json).
- Pipeline Python sem dependências externas para texto, DOCX e XLSX; suporte opcional a `pypdf`/`PyPDF2`, Pillow, `pdf2image` e Tesseract. Office é extraído como segmentos lógicos: imagens, layout, estilos e valores de fórmulas exigem conferência adicional.
- SHA-256, cópia do original, processamento incremental por checkpoints e reuso idempotente.
- Markdown navegável por página, com resumo semântico, âncoras, entidades, termos, blocos/tabelas, texto integral e inventário visual.
- Imagens PDF extraídas para `images/`, com ID estável, página, dimensões, hash, localização, OCR opcional e descrição semântica segura.
- Testes sintéticos cobrem extração, memória cumulativa, revisão jurídica, classificação, narrativa afirmativa, gates, inventário visual, execução seletiva, integridade e roteamento multiplataforma.
- Pacotes específicos para ChatGPT, Claude, Manus, Gemini CLI/Gems e Grok, gerados sem duplicar o núcleo jurídico.

Os nove arquivos ZIP/SKILL são testados por extração e execução local isolada.
Isso não certifica a interface de upload nem as capacidades de cada conta de
ChatGPT, Claude, Gemini, Manus ou Grok. Visão, navegação, execução e persistência
continuam dependentes da plataforma; as instruções não concedem essas ferramentas.
- Entrada universal para uso por link em [`AI_ENTRYPOINT.md`](../AI_ENTRYPOINT.md), [`llms.txt`](../llms.txt) e [`SKILL.md`](../SKILL.md).
- Classificação automática da área jurídica, base legal com evidências por página e perfil de redação específico para o caso.

O procedimento específico de upload e instalação está em
[`CHATGPT_UPLOAD.md`](../CHATGPT_UPLOAD.md). A skill trabalha de forma incremental:
inspeciona os materiais já enviados, executa somente a tarefa solicitada e
mantém o histórico em `relatorio_processual.md` e `versions/`.

## Uso por link do GitHub

Quando a IA receber apenas o endereço do repositório, comece por
[`AI_ENTRYPOINT.md`](../AI_ENTRYPOINT.md) ou [`llms.txt`](../llms.txt). Eles encaminham
para a plataforma e a tarefa corretas. Não é necessário carregar ou ler o
repositório inteiro: o núcleo em `skills/legal-process-parser/` é analisado por
blocos, enquanto adaptadores, testes e arquivos de outras plataformas ficam fora
do contexto padrão.

O roteamento está em [`routing/task-router.json`](../routing/task-router.json). O
processo do cliente pode ser analisado integralmente — páginas, imagens, peças,
contexto e linha do tempo — sem carregar instruções irrelevantes.
O núcleo obrigatório ficou separado dos recursos condicionais. O schema
completo só é carregado ao preencher/validar JSON; regras de analogia, visão,
inicial e recuperação entram quando necessárias. `scripts/task_context.py`
mede caracteres das referências selecionadas; isso não estima tokens de um
modelo nem limita quantas páginas precisam ser examinadas.

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
python scripts/case_packet.py C:\dados\saida --offset 0 --max-chars 12000
python scripts/case_memory.py C:\dados\saida --query "pagamento" --limit 10
python scripts/case_memory.py C:\dados\saida --person "Ana" --date-from 2025-02-01 --limit 10
```

Na leitura integral, leia os intervalos completos de cada lote e avance o
`next_offset` até null, mantendo `max_chars` e `corpus_revision` constantes.
Páginas extensas são divididas sem perda de texto. Recibos locais registram
quais intervalos foram disponibilizados, não se a IA os compreendeu. A consulta
`case_memory.py --full-pages` continua disponível; sem essa opção, retorna
trechos de localização. Buscas não substituem leitura integral.
Nos novos envios, `update.changed_pages` indica o que mudou para reavaliar as
dependências jurídicas; `update.impacted_elements` aponta fatos, questões,
pedidos, aplicações normativas, teses e parágrafos vinculados. `next_offset` permite continuar a consulta
sem carregar `case_memory.json` inteiro. A memória é o arquivo preservado, não uma garantia de
persistência entre sessões de qualquer plataforma.

Em análise, petição e auditoria, use também
[`semantic_crosscheck_rules.md`](../skills/legal-process-parser/references/semantic_crosscheck_rules.md): confronte proposições, negações, atores, datas, valores, fontes contrárias e versões temporais. Trechos de busca e excertos de 500 caracteres servem para localização; não contam como leitura integral. O validador verifica estrutura e relações declaradas, mas não comprova que uma paráfrase decorre da fonte nem que a interpretação jurídica está correta.

### Migração da versão 0.10

Revisões antigas não são automaticamente aprovadas. Acrescente `page_reviews`,
`facts[].support` e `issues[].research`, conforme o contrato atualizado.
Revisões visuais precisam de `source_sha256` e `render_sha256` por página;
use os hashes do arquivo e da renderização gerados na primeira ingestão.
Recapture fontes antigas para preservar também a resposta bruta `.source`.
Nenhum processo ou plano de melhoria deve ser enviado ao repositório público.

### Migração da revisão jurídica v2 para v3

Revisões v1/v2 continuam legíveis, mas os novos controles de seleção de peça,
integração normativa e estratégia exigem `schema_version: "3.0"`. Preserve a
revisão anterior e acrescente `piece_assessment`, `norm_applications` e
`theses` antes de validar. Para cada questão, ligue uma técnica de aplicação
normativa e ao menos uma avaliação de tese aos IDs existentes. Em petição,
`drafted_piece_type` deve coincidir com `piece_type`; `selected_piece` registra
a espécie processual concreta. Na v3, deixe `unresolved` vazio e registre
pendências com escopo em `findings[]`. As definições canônicas dos três objetos
estão em `$defs` no schema principal.

O verificador confere a estrutura e as referências entre registros. Ele não
determina cabimento, compatibilidade analógica ou mérito; essas conclusões
precisam ser justificadas pela IA com fontes oficiais e análise do caso.

### Revisão v4 e migração das versões anteriores

Preserve a revisão anterior e preencha `schema_version: "4.0"`. O guia compacto
é [`precision_review_rules.md`](../skills/legal-process-parser/references/precision_review_rules.md).

| Registro | O que passa a ser conferido |
|---|---|
| `execution_context` | Capacidades observadas nesta sessão, sem presumir ferramentas pelo nome da IA |
| `reading_coverage` | Intervalos/camadas, com recibos locais ou referência real de ferramenta do chat |
| `assertion_reviews` | Sujeito, ação, objeto, polaridade, alcance, datas/períodos e valores, prova contrária e dados críticos |
| `normative_map` | Contexto, requisitos, exceções, consequências, versão temporal e regras de transição |
| `precedent_comparisons` | Fatos e fundamento determinante, semelhanças/diferenças, vinculação, suspensão, modulação e superação |
| `thesis_reviews` | Requisitos, prova, força normativa, adequação processual, objeção mais forte e risco residual |
| `research_revision` | Estado das fontes consultadas, independente dos documentos recebidos |

`strategy` explicita subárea e regime. `piece_assessment.catalog_id` identifica
a espécie concreta; `custom` exige razão e norma de cabimento. Os 23 candidatos
em [`procedural_catalog.json`](../skills/legal-process-parser/references/procedural_catalog.json)
são roteiros, não decisões automáticas. Os 14 módulos em
[`legal_specializations.json`](../skills/legal-process-parser/references/legal_specializations.json)
separam, por exemplo, RGPS, RPPS, BPC e vínculo estatutário/celetista. A IA deve
confirmar o enquadramento pelos autos e fontes oficiais, sem inferir o regime
apenas por palavras-chave.

Comandos adicionais, executados a partir do núcleo:

```powershell
python scripts/task_context.py --platform chatgpt --task petition --trigger initial --specialization trabalho_emprego
python scripts/procedural_catalog.py --domain trabalhista --phase sentenca --family recurso
python scripts/review_skeleton.py C:\dados\saida --platform chatgpt --save C:\dados\revisao_v4.json
```

O esqueleto é deliberadamente pendente: não preenche fatos, fontes ou páginas
como revisados. A IA deve ler, pesquisar, preencher e só então validar.
V1–v3 permanecem aceitas por compatibilidade com `legacy_controls_only`;
uma revisão antiga não recebe controles v4 automaticamente. A validação
v4 verifica a consistência das declarações da IA, não a verdade jurídica.

### Versões, fontes e localização jurídica

`indice_juridico.md/.json` liga páginas/segmentos, fatos, questões, normas,
aplicações, teses, pedidos e redação com âncoras verificadas. Para registrar
relação explícita entre dois arquivos preservados, sem apagar originais:

```powershell
python scripts/document_relations.py C:\dados\saida --older <sha256_anterior> --newer <sha256_novo> --relation corrects --reason "Retificação expressa do documento" --recorded-by "revisor"
```

Os tipos são `complements`, `corrects`, `supersedes`, `contradicts`,
`same_document_version` e `related_process`. Substituição circular é rejeitada;
relação nova muda a revisão do corpus e exige reavaliar o contexto.

Capturas HTTP e observações de navegador atualizam `research_registry.json`.
Alteração do texto consultado gera `legal_source_updates.json` e propaga impacto
sobre normas, questões, aplicações, teses, pedidos e parágrafos dependentes.
Análise/minuta anterior fica sinalizada e recuperável. Isso não prova que a lei
mudou: a IA compara o contexto/versões e eventual incidência histórica. Recaptura
com texto idêntico não muda a revisão de pesquisa. Revisão v4 com snapshot
desatualizado é rejeitada; a captura histórica pode ser mantida com tratamento
expresso da alteração.

A comparação é conservadora: mudanças de rodapé ou navegação também podem
disparar revisão quando estiverem no texto capturado. O aviso indica alteração
da fonte consultada, não revogação ou mudança de vigência automaticamente.

### Formatos locais e limites de extração

PDF requer biblioteca de extração; visão/OCR dependem de ferramentas e revisão
reais. DOCX conserva corpo, tabelas, controles de conteúdo, cabeçalhos/rodapés,
notas e comentários; revisões controladas ficam sinalizadas. XLSX conserva
todas as linhas/células extraídas, inclusive planilhas ocultas, fórmulas e valores
armazenados, sem executar fórmulas. DOCX/XLSX não têm paginação física de PDF:
as referências são segmentos lógicos. Recursos visuais incorporados deixam
conversão parcial e exigem conferência do original/renderização vinculada.
O extrator local de Office não transforma essa conferência em cobertura visual
completa automaticamente; registre a limitação e use o fluxo visual de PDF
para a cópia renderizada, preservando e relacionando o original.

Imagens soltas, DOC/XLS antigos, arquivos protegidos e outros formatos não
suportados devem ser preservados e convertidos ou lidos pela visão da plataforma.
Binário nunca é decodificado silenciosamente como texto. ZIP Office tem limites
de expansão e rejeita macros/entidades XML; não há execução de conteúdo dos autos.

Depois que a IA produzir a revisão conforme o protocolo v4 e
[`schemas/legal_review.schema.json`](../skills/legal-process-parser/schemas/legal_review.schema.json),
instale `jsonschema`, capture cada norma oficial e valide a entrega:

```powershell
python -m pip install jsonschema
python scripts/research_sources.py C:\dados\saida --url https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm
python scripts/legal_review.py C:\dados\saida --review C:\dados\legal_review.json
```

O validador não inventa fatos nem decide o mérito: ele bloqueia páginas não
revisadas, trechos sem fonte, normas não capturadas, cálculos divergentes,
referências de pedidos inválidas e algumas formulações de relatório. Compatibilidade jurídica e suporte semântico exigem avaliação real, não apenas validação automática. Em petições iniciais, consulte
[`initial_petition_rules.md`](../skills/legal-process-parser/references/initial_petition_rules.md)
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

O comando de ingestão não acessa a internet; `research_sources.py` acessa a URL
oficial indicada para produzir um recibo local. A IA que conduz a análise pode consultar
fontes oficiais somente conforme a política da plataforma e do usuário; deve
registrar cada fonte e manter como pendente o que não puder verificar. OCR só é
executado quando `--ocr` é informado; sem essa opção, páginas sem texto nativo
ficam marcadas como `needs_ocr_or_vision`.

## Especialização trabalhista — v0.16.0

A revisão trabalhista possui 11 temas selecionáveis: contrato/regime,
responsabilidade, jornada, remuneração, ruptura, garantias, coletivo, saúde,
assédio/discriminação, procedimento e execução. O núcleo carrega apenas os
guias pertinentes; leitura integral dos autos continua no escopo solicitado.

A IA reconstrói relações e períodos, reconcilia fontes por pessoa/competência,
confere cláusulas e vigência coletiva, registra ônus e confronta cada requisito.
Nexo, concausa, exposição e incapacidade têm avaliações próprias. Recursos e
execução têm candidatos e requisitos específicos; a pesquisa oficial confirma
cabimento, normas, precedentes, integração e versões aplicáveis.

Na revisão v4 trabalhista, labor_review integra o contrato principal, com
[schema próprio](../skills/legal-process-parser/schemas/labor_review.schema.json).
Consulta pontual usa scope.mode targeted; análise integral usa integral e
justifica temas afastados. Lacunas geram achados por questão, permitindo
entregas independentes. A finalização gera analise_trabalhista.md e acrescenta
relações, períodos, cláusulas e conferências ao índice jurídico cumulativo.
Novas fontes/documentos propagam impacto também nesses registros.

Roteamento e preparação, a partir da pasta da skill:

    python scripts/task_context.py --platform chatgpt --task analyze --domain trabalhista --labor-topic working_time
    python scripts/review_skeleton.py saida --domain trabalhista --labor-topic working_time --save revisao_trabalho.json
    python scripts/labor_analysis.py revisao_trabalho.json
    python scripts/legal_review.py saida --review revisao_trabalho.json

O esqueleto fica pendente até a leitura/pesquisa reais. A ferramenta não infere
enquadramento definitivo pelas palavras-chave e não preenche fatos jurídicos
automaticamente. Usuários de chats seguem os mesmos guias e entregam Markdown
com os vínculos, registrando ferramentas efetivamente disponíveis.

### Cálculos e calendário

O [motor decimal](../skills/legal-process-parser/scripts/labor_calculations.py)
executa fórmulas com parâmetros atribuídos, unidades, parcelas por competência,
reflexos dependentes e abatimentos identificados. Rejeita resultados divergentes,
unidades incompatíveis, duplicidades, ciclos e expressões executáveis.
Nenhuma taxa, base ou divisor legal é escolhido automaticamente.

    python scripts/labor_calculations.py parametros.json --case-output saida --output saida
    python scripts/labor_calculations.py parametros.json --reference referencia_pjecalc.json

São gerados calculo_trabalhista.json e memoria_calculo_trabalhista.md.
O [exemplo](../skills/legal-process-parser/templates/labor_calculation_example.json)
é inteiramente sintético e não fixa regra trabalhista. Substituir dados/fontes
pelo caso. A comparação externa exige resultado real transcrito e conferido,
hash do arquivo, versão e tabelas; não há geração fictícia de PJC nem atestado
de execução do PJe-Calc.

labor_time.py confere marcações com data/offset, inclusive passagem de dia, e
conta prazo com regra e calendário informados. Feriados, suspensões, marco e
modo de contagem precisam das fontes corretas. Duração física de jornada não
substitui o enquadramento de horas, intervalos ou adicionais.

Guia: [especialização](../skills/legal-process-parser/references/labor_core_rules.md),
[provas](../skills/legal-process-parser/references/labor_evidence_rules.md),
[coletivo](../skills/legal-process-parser/references/labor_collective_rules.md),
[cálculos](../skills/legal-process-parser/references/labor_calculation_rules.md),
[procedimento](../skills/legal-process-parser/references/labor_procedure_rules.md),
[saúde](../skills/legal-process-parser/references/labor_health_rules.md).
OIT/NORMLEX pode ser registrado como fonte oficial específica; vigência,
ratificação e ato brasileiro correspondente são conferências distintas.

## Atendimento trabalhista e desenvolvimento — v0.17.0

A skill parte do relato e do material disponível. A falta de cartões de ponto,
holerites ou documentos em poder da empresa é tratada por questão. O relato
específico pode permitir a redação da inicial enquanto a prova aguarda produção.
Dados materiais e documentos necessários ao ato são avaliados separadamente.
Perguntas são apenas sobre lacunas que realmente alteram a entrega.

O registro preserva quem informou o fato, quais documentos chegaram, o que está
controvertido, quem possui a prova e qual providência é pertinente. A inicial
continua afirmativa na voz da parte. Relato não vira confirmação documental,
diagnóstico ou diligência executada. Novas versões não apagam o relato anterior.

Com código local, criar relato.json com schema_version 1.0 e entries contendo
id, text e conversation_reference. Usar texto e referência efetivamente recebidos;
o arquivo templates/client_intake_example.json é inteiramente sintético.

    python scripts/client_intake.py relato.json --output saida
    python scripts/client_intake.py --output saida --read --max-chars 12000
    python scripts/case_memory.py saida --accounts --query "jornada" --limit 10
    python scripts/task_context.py --platform chatgpt --task petition --labor-intake --labor-claim overtime --labor-sector banking
    python scripts/review_skeleton.py saida --task petition --domain trabalhista --labor-topic working_time --labor-workflow --save revisao.json

O esqueleto permanece pendente: a IA precisa preencher a análise após ler o
relato, os anexos e as fontes oficiais. Avançar next_offset dos lotes de relato
até null; lote disponibilizado não comprova compreensão. Para novos anexos:

    python scripts/ingest_document.py novo.pdf --output saida --task ingest
    python scripts/legal_review.py saida --review revisao.json

Uma retificação usa novo id com supersedes apontando para o relato anterior.
O corpus, o índice e os vínculos dependentes são atualizados; entregas anteriores
permanecem recuperáveis e recebem indicação de desatualização quando necessário.
Sem Python/persistência, usar o mesmo procedimento em Markdown cumulativo e
registrar controles que não puderam ser executados.

Quinze pautas de pretensão aprofundam vínculo, jornada, remuneração, equiparação,
ruptura, garantias, responsabilidade, reparação, saúde, adicionais, coletivo,
recurso e execução. Dez roteiros cobrem bancos/atividade financeira, doméstico,
rural, motoristas, saúde, segurança, ensino, teletrabalho, plataformas e emprego
público. Selecionar pelo caso e carregar apenas os guias pertinentes; a seleção
não confirma regime, direito ou cabimento.

O workflow registra requisitos por pretensão, possibilidade de redigir e
suficiência da prova, contrapontos, providências, versões normativas, situação
dos precedentes, janelas de prescrição, comparação de cláusulas, fundamentos
recursais, alternativas estratégicas e perguntas de audiência/perícia.
As rotinas conferem os vínculos e os dados registrados; não certificam mérito.

Para conciliação, preparar labor_ledger.schema.json com regras e fontes do caso:

    python scripts/labor_ledger.py conciliacao.json
    python scripts/labor_time.py window janela.json

O motor de jornada confere intervalos com datas/offsets, sobreposição, excesso
diário e semanal adicional sem dupla contagem, unidade noturna fornecida e
semanas parciais. Folha é conciliada por vínculo, competência e rubrica;
confirmação bancária do mesmo pagamento não gera novo abatimento. Falta de
pagamento comparável retorna null, sem concluir inadimplência. A contagem da
janela não escolhe o regime prescricional. Parâmetros jurídicos precisam da fonte
e da justificativa; hipóteses especiais são segmentadas conforme o caso.

Entregas incluem relato_cliente.md, desenvolvimento_trabalhista.md e, havendo
ledger, conciliacao_trabalhista.json/MD. Em casos sem upload, intake_manifest.json
identifica explicitamente os relatos e zero páginas documentais; o ZIP contém
a memória e os arquivos disponíveis. Os controles permitem distinguir uma
inicial pronta para revisão de uma conclusão que ainda depende de prova.

[Guia de atendimento](../skills/legal-process-parser/references/labor_intake_rules.md) ·
[Desenvolvimento por pretensão](../skills/legal-process-parser/references/labor_development_rules.md).

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
[`legal_narrative_rules.md`](../skills/legal-process-parser/references/legal_narrative_rules.md).

Na revisão v3, `piece_assessment` registra a medida e seus pressupostos;
`norm_applications` distingue aplicação direta, remissão, integração e
interpretação sistemática por questão; `theses` liga cada estratégia aos fatos,
normas, objeções, respostas e pedidos. A analogia exige semelhanças,
diferenças, autorização ou lacuna, compatibilidade e limites específicos.
Consulte [`procedural_fit_and_piece_rules.md`](../skills/legal-process-parser/references/procedural_fit_and_piece_rules.md)
e [`norm_integration_rules.md`](../skills/legal-process-parser/references/norm_integration_rules.md).

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
| `case_index.sqlite3` | Índice local de consulta paginada com filtros; reconstruível a partir da memória |
| `recovery_findings.json` | Pendências técnicas por página e tentativas efetivamente observadas |
| `passages.jsonl` | Passagens integrais com offsets, natureza provisória e proveniência por página |
| `processo_estruturado.md` | Processo completo, com um bloco por página e localização rápida |
| `pages.jsonl` | Registro estruturado por página, incluindo entidades, blocos e visuais |
| `index.jsonl` | Busca exata por texto, termos, resumo, entidades e imagens |
| `image_inventory.json` | Catálogo de imagens/escaneamentos, hashes, caminhos e descrições |
| `legal_basis.json` | Área identificada, evidências por página, fontes normativas candidatas e perfil de redação |
| `base_legal.md` | Fontes oficiais encaminhadas e portas de verificação antes de qualquer peça |
| `legal_narrative.json` / `analise_juridica.md` | Narrativa afirmativa por página, fatos/alegações/provas/decisões, questões jurídicas e sequência de subsunção |
| `legal_review_validation.json` | Resultado do contrato autoral, capturas oficiais, cobertura e bloqueios |
| `legal_reviews/` | Revisões e recibos imutáveis por hash, inclusive tentativas não aprovadas |
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
fundamentação. Consulte [`skills/legal-process-parser/references/legal_narrative_rules.md`](../skills/legal-process-parser/references/legal_narrative_rules.md) para a linguagem exigida e o protocolo de pesquisa normativa oficial.

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

Quando Habilidades estiver habilitado na conta/workspace, carregue o pacote em
`Plugins → Habilidades → Criar → Carregar do computador`. A disponibilidade é
condicional, não universal. GPT com Instructions/Knowledge é uma alternativa,
não instalação equivalente nem execução automática dos scripts.
[Orientação oficial da OpenAI](https://help.openai.com/pt-br/articles/20001066-skills-in-chatgpt).
O repositório não oferece endpoint público, GPT Action ou cadastro universal.

Para a tela de upload mostrada no ChatGPT, use o arquivo
`legal-process-parser-chatgpt.skill` (ou o ZIP equivalente), que mantém
`SKILL.md` na raiz. Consulte [`CHATGPT_UPLOAD.md`](../CHATGPT_UPLOAD.md) para o
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
gemini extensions install https://github.com/lucianumm/AuditorProcessual --ref main --consent
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

### Pendências e entregas parciais

`legal_review.json` pode registrar `findings[]` com `scope`, `target_ids`,
`delivery_effect` e providência. O validador separa `technical_status`,
`analysis_status`, `draft_status` e o estado de cada questão em
`legal_review_validation.json`. Uma fonte faltante ligada a uma questão não
rebaixa automaticamente as demais. Uma lacuna decisiva, porém, não vira prova
por ser aceita: o trecho dependente é omitido da minuta parcial, que permanece
marcada **RASCUNHO — NÃO PROTOCOLAR**. `unresolved[]` antigo sem escopo continua
bloqueante até ser classificado e resolvido. Consulte
[`readiness_and_recovery_rules.md`](../skills/legal-process-parser/references/readiness_and_recovery_rules.md).

`recovery_findings.json` distingue página em branco confirmada, imagem sem
texto, conteúdo desconhecido e página ilegível. As tentativas registradas são
apenas as realmente executadas; OCR não equivale a descrição visual. Em novos
uploads, o índice SQLite e o grafo de dependências ajudam a reler somente as
passagens relevantes depois da leitura integral inicial.

### Avaliação reproduzível

Os casos em [`evaluation/cases/`](../evaluation/cases/) são sintéticos e têm
rótulos independentes. Após processar um caso em um diretório de saída e
produzir `legal_review.json`, execute da raiz do repositório:

```powershell
python scripts/evaluate_quality.py --case evaluation/cases/partial_independent/case.json --artifact-dir C:\dados\avaliacao
```

O avaliador mede omissões observáveis, rastreabilidade de citações,
contradições registradas e bloqueios indevidos. Tempo e tokens só entram quando
medidos externamente e informados; correspondência textual não atesta correção
ou persuasão jurídica. Para testar o código e os nove pacotes isolados:

```powershell
python -m unittest discover -s skills/legal-process-parser/tests -q
python scripts/verify_repository.py
python scripts/build_platform_packages.py --output outputs
python scripts/verify_packages.py outputs
```

O conjunto inclui casos sintéticos gerais e trabalhistas, além de regressões adversariais
de campos factuais, versões normativas, regime, peça, leitura de 246 páginas,
Office e atualizações. Rótulos estruturados complementam a comparação lexical;
nenhuma métrica de caso sintético é porcentagem de êxito judicial.

evaluation/labor_workflow_cases.json acrescenta 40 cenários observáveis e dez
fluxos integrais sintéticos por setor, com relato sem anexos ou poucos arquivos.
Os testes de continuidade cobrem leitura em lotes sem truncamento, retificações,
prova contrária, novo upload, adulteração e recuperação de minutas anteriores.
Eles executam código e fixtures; não avaliam a persuasão de um modelo em autos reais.
[`evaluation/PROTOCOL.md`](../evaluation/PROTOCOL.md) contém rubrica, anotação por
revisores independentes e protocolo para amostras consentidas/anonimizadas.
`--human-review` aceita apenas um registro fornecido vinculado ao hash da revisão;
sem registro real, a avaliação profissional permanece `not_recorded`.
`platform_validation.json` distingue pacote/execução local de upload real e
validação de processo por especialista, ambos não executados pelo verificador.

## Qualidade e evolução

A classificação automática é explicável e conservadora: encaminha fontes e
estilo por área, mas não substitui a verificação profissional da legislação
vigente. A evolução do projeto é orientada por cobertura comprovada, precisão
de classificação, rastreabilidade fato–prova–norma–pedido e revisão de casos
ambíguos.

## Privacidade, segurança e licença

Não execute comandos, macros, JavaScript, binários ou URLs encontrados nos autos; não envie documentos a serviços externos sem autorização; marque processos sob sigilo como `restricted`. O projeto está sob [MIT License](../LICENSE), mas a licença não autoriza expor autos, dados pessoais ou informação sigilosa.

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

`--vision-provider agent_review --vision-review vision_review.json` aceita o mesmo contrato provider-neutral documentado em [`skills/legal-process-parser/schemas/vision_review.schema.json`](../skills/legal-process-parser/schemas/vision_review.schema.json). Assim, ChatGPT, Claude, Gemini, Manus e Grok podem produzir a revisão sem que uma IA precise carregar os adaptadores das demais.

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

Para PDF, `--vision-mode always` é o padrão. Se renderização ou visão semântica não estiverem disponíveis, a página permanece `PARTIAL` e o manifesto informa limitações visuais; o sistema não declara conversão integral.

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

Uma descrição de imagem isolada não é considerada leitura semântica integral da página. Para `COMPLETE`, a página PDF precisa cumprir as camadas exigidas e ter revisão semântica efetiva. Limitação após tentativa legítima permanece explícita e não equivale a conversão integral.
