# Desenvolvimento por pretensão e período

Use labor_review.workflow quando desenvolver pretensões, atendimento inicial,
conciliação, instrução ou recursos. Para escolher pautas sem carregar todo o
catálogo, executar labor_catalog.py --claim overtime --sector banking ou consultar
somente as entradas pertinentes de labor_claims.json/labor_sectors.json.
As entradas são roteiros de pesquisa; leis e requisitos precisam da fonte do caso.

## Contrato, documentos e pretensões

Reconciliar sujeitos e relações antes de comparar CTPS, holerite, ponto, extrato,
TRCT e informações do cliente. Cada observação mantém fonte, página/linha/região,
competência, rubrica e sujeito. Nas reconciliations, concordância exige mesmo
sujeito/objeto/período e campo reconferido. Documento de outra competência,
registro ausente, ilegível e pagamento parcial têm efeitos distintos.

claim_reviews liga pretensão, issue, topic_assessment, períodos e fontes.
Conferir todas as pautas da pretensão escolhida: requisitos, exceções, prova
contrária, ônus, consequência e resposta à objeção mais forte. Registrar
verified, alleged, disputed, awaiting_proof, missing_material ou not_applicable.
verified exige suporte documental conferido e base normativa; não certificar
requisito com relato isolado. Justificar exclusão e não fabricar direito candidato.
drafting_basis e merit_status têm funções diferentes, conforme labor_intake_rules.

## Versões, coletivos e situação atual

temporal_checks relaciona questão, período e normative_map. Se uma lei/cláusula
mudar durante o contrato, decompor o período e explicar transição/efeitos.
Contrato em curso usa reviewed_until como limite da análise, sem inventar ruptura.
Conferir redação integral oficial, requisitos, exceções e fontes contrárias.

authority_checks registra consulta datada, fonte da situação, âmbito, uso e
temporalidade do precedente. Distinguir afetação/suspensão de tese de mérito;
conferir inteiro teor, decisão de suspensão, modulação, revisão e cancelamento.
Uma notícia aponta para a pesquisa. Status técnico não atesta a visita nem a
correção da distinção. Fontes inacessíveis limitam somente conclusões dependentes.

collective_comparisons compara cláusulas literais de ACT/CCT/aditivos por sujeitos
e períodos, preservando ambas. A diferença textual produzida não decide validade,
precedência, disponibilidade ou ultratividade. Explicar seleção, conflito e
efeito sobre cada pedido e conta.

## Prescrição e calendário

prescription_reviews avalia cada pretensão: bienal, quinquenal, total, parcial,
intercorrente, exceção ou regra específica quando pertinente. Conferir os marcos
e projeções em fontes, interrupção/suspensão e efeitos da regra vigente.
window recebe anchor_date, unit, quantity, direction, leap_policy, adjustments
e expected_date. labor_time.py window conta parâmetros fornecidos, sem escolher
regra nem reconhecer prescrição. Cada ajuste tem fatos, normas e fundamento.
Não confundir janela de prescrição com prazo processual contado em dias úteis.

## Jornada, folha e cálculo

labor_ledger.schema.json organiza rules, days e payroll. Preparar os registros
após conferir todos os dias e documentos disponíveis. Rule tem relação, vigência,
limites diários/semanais, início de semana, base física/jurídica, janela noturna
e eventual unidade reduzida. Cada parâmetro precisa da fonte vigente do caso.
Um modelo de preenchimento não estabelece divisor, jornada ou percentual legal.

Days usa data, intervalos efetivamente trabalhados com offsets, origem, fontes e
estado worked/rest/leave/unknown. Separar intervalos de descanso; não subtrair
duas vezes nem inferir dias vazios como folgas. Regras concorrentes, sobreposição
e virada de dia precisam ser resolvidas. O motor calcula excesso diário e
semanal adicional sem somar novamente o mesmo excesso. Semana parcial continua
identificada, inclusive quando faltar o mês vizinho. Hora reduzida usa apenas
janela/unidade fornecidas; prorrogação, compensação e demais hipóteses especiais
precisam de segmentação e fundamentação próprias.

Payroll separa salary_parameter, due, payment e payment_confirmation por
relação/competência/rubrica. Confirmação bancária do mesmo pagamento não vira
outro abatimento. Ausência de valor comparável retorna null, não dívida ou
inadimplência presumida. Valores de relato produzem estimativa identificada.

    python scripts/labor_ledger.py conciliacao.json

Usar as quantidades apuradas em labor_calculations.py com fórmulas, bases,
reflexos e encargos atribuídos. Alternativas incompatíveis usam cenários próprios.
Comparação profissional com PJe-Calc exige saída real, versão, tabelas e bytes;
comparação com fixture sintética não comprova execução do software.

## Estratégia, peça e instrução

strategy_options compara teses registradas e explicita incompatibilidades por
cenário. Cada tese principal/subsidiária/alternativa liga fatos, normas, técnica
de integração e pedidos. Analogia precisa de lacuna/remissão, semelhanças,
diferenças, compatibilidade e contraponto, seguindo norm_integration_rules.md.
Não apresentar tese inovadora como entendimento pacífico ou atribuir chance fictícia.

appeal_chapters mantém trecho real da decisão, fundamentos autônomos,
instrumento e efeito pretendido. Cada fundamento challenged aponta para
parágrafos da questão. Conferir rito/fase, admissibilidade, prequestionamento,
transcendência, preparo e prazo; observar a IN 40/TST vigente ao distinguir
agravo interno e AIRR por fundamento. O agente deve ler a decisão inteira
para detectar fundamentos omitidos; a lista preenchida não prova essa leitura.

instruction_questions liga pergunta/quesito ao plano de prova, controvérsia e
questão. Saúde ocupacional mantém exposição, diagnóstico, nexo/concausa,
incapacidade e consequência separados. Não sugerir respostas a testemunhas;
perguntas buscam esclarecer fatos efetivamente controvertidos. Resposta recebida
vira fato atribuível e reabre tese/pedido correspondente.

Antes de entregar a peça, conferir qualificações, datas/valores decisivos,
desenvolvimento dos pedidos, pedidos subsidiários, duplicidades e coerência entre
capítulos. A inicial usa voz afirmativa; defesa/recurso enfrenta argumentos
pertinentes. Preserve texto literal em citações e a origem do relato no registro.
desenvolvimento_trabalhista.md e o índice tornam o trabalho localizável.
