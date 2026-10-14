# Fluxo local de consulta e entrega por resposta

Este guia é operacional, não um plano de melhoria. Só carregá-lo ao produzir
os contratos locais. No chat sem Python, seguir response_research_rules.md com
consultas reais da plataforma e Markdown cumulativo, sem simular estes comandos.

## Preparação

Python 3.10+ e jsonschema são necessários para validação; PDF textual oficial
exige pypdf. Na raiz do repositório, usar os comandos abaixo. No pacote extraído
com SKILL.md na raiz, trocar `skills/legal-process-parser/scripts/` por `scripts/`.
Manter o mesmo diretório do caso; preferir caminhos absolutos ao mudar de pasta.

Receber arquivos ou relato com ingest_document.py/client_intake.py, ler os lotes
integralmente e construir a análise v4 real. O esqueleto é pendente. Definir
questões, fatos, normas, pedidos, interpretações e períodos; não criar IDs que
representem leitura ou consulta fictícia. Nos exemplos, I1/N1 são marcadores:
substituí-los pelos IDs do caso. Nenhuma pergunta obrigatória é criada.

## 1. Iniciar a resposta e consultar

Usar ID novo em cada entrega jurídica e referência do pedido efetivo:

```powershell
python skills/legal-process-parser/scripts/response_research.py saida begin --id tese-i1-001 --issue I1 --request-reference "referência do pedido recebido"
python skills/legal-process-parser/scripts/response_research.py saida consult --id tese-i1-001 --issue I1 --norm N1 --url https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm --purpose "conferir dispositivos pertinentes ao caso e ao período"
```

Escolher a norma/decisão específica do caso; o exemplo de CLT não basta para
toda pretensão. Repetir consult por fundamento e questão pertinentes. Alternativas
oficiais podem ser fornecidas por --alternative, até quatro URLs distintas por
operação; registrar falhas em vez de repetir a mesma tentativa sem informação nova.
O comando executa HTTP, preserva os bytes e não envia autos ao portal consultado.

Se a plataforma precisa de navegador, primeiro chamar sua ferramenta real e
depois registrar o que foi observado em observacao.json: url, accessed_on,
text, context, tool_reference, observed_by e observed_at com fuso horário.
coverage_scope e locator são opcionais. Datas e referências não podem ser inventadas.

```powershell
python skills/legal-process-parser/scripts/response_research.py saida browser --id tese-i1-001 --issue I1 --norm N1 --purpose "conferência efetivamente realizada" --input observacao.json
```

browser não navega: seu nível permanece self_recorded_unverified. Antes de
bind, conferir a chamada real e o trecho. Fontes antigas são histórico, não
substitutos de uma nova consulta. Registro HTTP verifica integridade de bytes,
não certifica vigência, interpretação ou mérito.

## 2. Interpretar e preencher o contrato

Ler os trechos e contexto oficiais; conferir versão por período, requisitos,
exceções, prova contrária, técnica de incidência, objeção mais forte e consequência.
Na inicial, narrar fatos afirmativamente na voz da parte. Relato e prova futura
permanecem corretamente atribuídos nos registros de apoio, sem inventar certeza.

contrato_resposta.json segue response_research.schema.json:

- schema_version 1.0, response_id da sessão e issue_ids das questões tratadas;
- artifact_hash, research_revision e checked_at: bind calcula estes três campos;
- citations: issue_id, norm_id, source_record_id retornado pela consulta, trecho
  literal e análises reais de aplicabilidade e versão;
- causes: id, issue_id, paragraph_ids, fact_ids, norm_ids, request_ids,
  requirements_analysis, exceptions_analysis, contrary_analysis, consequence,
  status e limitation. Cada pedido do capítulo tem causa correspondente;
- precedents, quando houver precedente usado: fontes e trechos atuais do
  fundamento e da situação, mérito, processo, efeitos, modulação, comparação
  factual e contrapontos. A mesma fonte pode cumprir ambas as funções somente
  se contiver de fato ambos os conteúdos;
- parameter_review, quando houver conta pertinente, conforme a seção seguinte.

Um trecho literal precisa aparecer na fonte efetivamente consultada. Cada
parágrafo jurídico declarado precisa estar coberto por causa/fundamento e
consulta pertinentes. supported não confirma relato controvertido: nesses casos
usar qualified e explicar o limite. pending exige tentativa concreta e efeito
delimitado; não autoriza concluir o fundamento dependente como confirmado.
Questão estritamente normativa pode não ter fato/pedido, sem inventá-los.

Ao atualizar a análise, copiar a research_revision atual de research_registry.json,
conferir normas e vínculos e preservar a anterior. Mudança de corpus ou texto
consultado exige reanálise e refresh antes de salvar/montar; recaptura idêntica
preserva a revisão textual. Fonte/argumento novo entra primeiro na análise-base.
Se for necessária nova entrega da análise, ela também recebe sessão própria.

## 3. Conferir parâmetros e executar a conta

Na revisão trabalhista, calculation_set mantém inputs e items com fontes,
unidades, fórmula, competência, pedidos e arredondamento. Não presumir taxa,
divisor ou reflexo. Oito pautas são selecionáveis sem aplicar regra automática:

```powershell
python skills/legal-process-parser/scripts/labor_parameters.py --profile overtime
python skills/legal-process-parser/scripts/labor_calculations.py parametros.json --case-output saida --output saida
```

parameter_review segue labor_parameters.schema.json e confere cada input da
resposta exatamente uma vez: basis fact, legal_rule ou derived; source_value;
transform; fact_id/fact_field ou norm_id/source_record_id/quote; expression e
bindings para derivação; period_id, effective_from/effective_until e justificativa.
Percentual pode ser convertido em fração/fator; minutos em horas. As quantidades
factuais devem concordar com assertion_reviews.atoms e os critérios normativos
com trecho oficial numérico da resposta e normative_map temporalmente aplicável.

Selecionar as parcelas dos pedidos em pauta e toda dependência de itens/inputs,
inclusive inputs derivados. Não incluir conferências de inputs de pretensões
alheias. Parcelas usadas só como dependências não são somadas outra vez. O
controle integrado executa a conta, além de confrontar valores e períodos;
o sentido jurídico dos critérios continua exigindo interpretação da IA/revisor.

Comparação com PJe-Calc requer resultado, arquivo e tabelas reais. Sem eles,
não declarar comparação nem execução do software externo.

## 4. Vincular e salvar a entrega

Para a análise v4 atual, definir response_policy per_response antes do vínculo.
Usar --review analise.json sem --artifact para vincular a análise propriamente dita.
Depois copiar o objeto de response.json para analise.json.response_research,
sem alterar os demais campos após bind, e executar legal_review.py/init.

Para o capítulo, preparar capitulo.json v2, inclusive response_research pendente,
com os IDs e campos factuais reais da análise-base. Criar a sessão própria da
seção 1 e preencher o contrato da seção 2. Vincular ao capítulo exato:

```powershell
python skills/legal-process-parser/scripts/response_research.py saida bind --input contrato_resposta.json --review analise.json --artifact capitulo.json
```

O objeto resultante fica em saida/response_research/tese-i1-001/response.json.
Copiá-lo para capitulo.json.response_research sem alterar nenhum outro campo:

```powershell
python skills/legal-process-parser/scripts/response_research.py saida validate --input saida/response_research/tese-i1-001/response.json --review analise.json --artifact capitulo.json
python skills/legal-process-parser/scripts/petition_workspace.py saida save --chapter-file capitulo.json
```

Uma sessão vinculada não serve para conteúdo diferente. Ajuste de texto que
mude o JSON exige nova sessão; versões anteriores são preservadas. Nunca editar
arquivos imutáveis de análises/capítulos arquivados para contornar os hashes.
Revisão/aprovação registra somente conferência ou manifestação que ocorreu.

## 5. Consolidar quando solicitado

Gerar preview dos capítulos aprovados; usar --allow-drafts somente se o usuário
solicitar reunião de rascunhos, sem atribuir aprovação inexistente:

```powershell
python skills/legal-process-parser/scripts/petition_workspace.py saida preview --chapter horas-extras --chapter fgts --save-preview consolidacao_preview.json
```

Iniciar sessão nova consolidacao-001 com todas as questões do preview, consultar
os fundamentos decisivos e preencher contrato_consolidacao.json. paragraph_ids
do preview usam capítulo--parágrafo. Revisar duplicidades, alternativas,
qualificações, valores e pedidos ausentes. Se mudar conteúdo/base, gerar novo
preview antes de vinculá-lo; nunca reutilizar contrato de capítulo na montagem.

```powershell
python skills/legal-process-parser/scripts/response_research.py saida bind --input contrato_consolidacao.json --review analise.json --artifact saida/consolidacao_preview.json
python skills/legal-process-parser/scripts/petition_workspace.py saida assemble --chapter horas-extras --chapter fgts --research-response saida/response_research/consolidacao-001/response.json
```

## Entrega e limites

Cada sessão preserva session.json e histórico, response.json, validation.json
e fontes.md com links oficiais. O relatório cumulativo aponta para as fontes
da resposta. Contas executadas no vínculo também preservam calculo.json e
memoria_calculo.md dentro da sessão, sem substituir memórias de outras teses.
Manter conta demonstrativa, versões e todo material recebido.
Sem código/persistência, entregar os vínculos e fontes no Markdown disponível.

O validador confere estrutura, integridade e cobertura declarada. Não certifica
que um agente registrou todas as frases, interpretou corretamente ou realizou
navegação externa. Revisões legadas continuam identificadas sem estes controles
novos; o CLI atual não oferece bypass para capítulos/consolidação. Toda minuta
é RASCUNHO — NÃO PROTOCOLAR e exige revisão profissional.
