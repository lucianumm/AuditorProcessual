# Processo, recursos, instrução e execução trabalhista

Identificar órgão, rito, polo, fase, ato e resultado pretendido. Conferir
cabimento pela decisão e seus fundamentos, não pelo nome do arquivo.
Use os candidatos trabalhistas de procedural_catalog.json; ausência de
entrada específica exige pesquisa e seleção custom fundamentada.

Inicial: competência, legitimidade, rito, prescrição, fatos, pedidos e valores,
provas, tutelas pertinentes e requisitos próprios. Contestação: impugnação
específica, preliminares, teses impeditivas/modificativas/extintivas, documentos,
pagamentos e ônus. Manifestação sobre defesa/documentos: enfrentar conteúdo
e efeitos concretos. Conferir eventual reconvenção e limites do ato solicitado.
[CLT](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm).

Defesa por pedido: usar defense_theses das pretensões em labor_claims.json como
roteiro, conferindo cada uma na fonte da resposta. Ordem típica: incompetência
material (inclusive suspensões nacionais em Tema pendente), prescrição bienal e
quinquenal, inépcia ou pedido sem valor indicado, fato impeditivo/modificativo/
extintivo com prova (pagamento, compensação, dedução global, exceção legal,
norma coletiva válida), ônus de cada parte, limites de condenação, gratuidade,
honorários recíprocos e eventual litigância de má-fé. Réplica e recurso do
trabalhador enfrentam cada defesa efetivamente apresentada com a tese
correspondente de claimant_theses, sem repetir a inicial. Candidatos de peça
específicos: acao_cumprimento_trabalhista, inquerito_falta_grave,
consignacao_pagamento_trabalhista, tutela_urgencia_reintegracao_trabalhista,
embargos_terceiro_trabalhista e reclamacao_constitucional_trabalhista.

Audiência: fatos controvertidos, encargo de prova, documentos, depoimentos,
requerimentos e protestos fundamentados. Razões finais enfrentam prova
produzida e controvérsias, respeitando limites da fase. Quesitos/impugnação
pericial usam método, dados, omissões e conclusões, com fontes reais.

Recursos: decompor capítulos e fundamentos autônomos. Conferir legitimidade,
interesse, representação, tempestividade, custas/depósito e hipóteses de
isenção/redução/substituição pela norma e valores atuais do caso. Conferir
impugnação específica, efeito e providência pretendida.

Recurso de revista: observar rito e fase, hipóteses próprias, prequestionamento,
trechos pertinentes, demonstração analítica, divergência quando cabível,
transcendência e óbices. Examinar limites de nova prova ou reexame fático.
Nos agravos, identificar o órgão, cada fundamento denegatório e o regime
de precedentes: agravo interno e AIRR têm hipóteses próprias. Consultar a
versão vigente da IN 40/TST e atos modificadores. Embargos, adesivo,
rescisória e MS exigem seus pressupostos próprios.

Prazos: separar assinatura, disponibilização, publicação, ciência e início.
Conferir forma de comunicação, regra, calendário do órgão/território, feriados,
recesso, suspensões e indisponibilidade reconhecida. labor_time.py deadline
conta os parâmetros fornecidos; regra e feriados precisam de conferência.
Vincule marco e atos em procedure_reviews; vencimento não confirmado fica
pendente, permitindo continuar outras questões.

Liquidação/execução: ler título, acórdãos integradores, trânsito/efeitos,
comandos, critérios e pagamentos. Respeitar os limites do título na conta.
Impugnar itens e valores concretos, justificar fórmula/critério e observar
garantia, legitimidade, matéria cognoscível e preclusão quando exigidos.
Agravo de petição precisa dos requisitos próprios, inclusive delimitação
pertinente. IDPJ, exceção, penhora, bens e sócios exigem sua base e prova.
Separar dívida trabalhista, contribuições, honorários e encargos.

Subsidiariedade processual segue autorização, lacuna e compatibilidade;
conhecimento e execução têm bases próprias. A competência e a coisa julgada
limitam a integração. Uma tese forte precisa também do instrumento e momento
processual corretos.

Uma pergunta de audiência, quesito ou pedido de exibição deve identificar o
fato controvertido, requisito da pretensão, detentor/encargo, resposta que se
pretende esclarecer e efeito no pedido. Após defesa, depoimento, laudo ou
decisão, atualizar procedural_updates e reexaminar capítulos dependentes.
Recursos enfrentam cada fundamento autônomo com passagem e parágrafo de resposta.
Na execução, confrontar sentença e todas as decisões integradoras, delimitações
e pagamentos; a tese da fase cognitiva não amplia automaticamente o título.
