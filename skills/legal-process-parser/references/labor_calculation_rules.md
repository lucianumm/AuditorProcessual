# Cálculo trabalhista e conciliação de pagamentos

Aplicar response_research_rules.md antes de cada resposta sobre a conta.
labor_parameter_profiles.json e labor_parameters.py --profile selecionam oito
pautas de fórmulas, nunca taxas presumidas. No contrato local por resposta,
parameter_review segue labor_parameters.schema.json: campo factual reconferido,
trecho numérico oficial recém-consultado ou derivação explícita executada;
transformação, unidade, relação, período e incidência justificada. Conferir
somente parcelas pedidas e suas dependências. Nenhum número citado basta
sem justificar seu sentido e sua aplicação ao caso.

Confirmar finalidade: estimativa inicial, conciliação ou liquidação. Identificar
relação, competências, evolução salarial, espécie/natureza das parcelas,
marcos, base, quantidade, divisor, percentual, projeção, reflexos, abatimentos
e encargos. Cada parâmetro aponta para fatos ou normas; cada regra tem incidência
e período explicados. Nenhum divisor, adicional ou reflexo é universal.

Reconstruir salário fixo e variável, comissões, gratificações, descontos e
diferenças. Equiparação, acúmulo/desvio, parcelas indenizatórias e salariais
exigem requisitos e fontes próprios. Conferir bases por parcela e competência,
fontes contrárias, afastamentos, prescrição e pagamento, evitando duplicidades.

Use labor_calculation.schema.json quando preparar os parâmetros para execução.
Valores são strings decimais com ponto. inputs têm unidade e fontes.
items têm relação, competência, rubrica, segmento, expressão, bindings,
normas, pedidos, resultado esperado e inclusão no total. Permitir somente
aritmética + - * / com nomes vinculados; taxas/divisores/quantidades são inputs.
Cada parcela retorna fonte e fórmula.

Valores monetários não se somam a horas. Divisor em horas divide base monetária,
quantidade em horas recompõe moeda; multiplicadores são fatores adimensionais.
Expressar percentuais como fator ou dividir parâmetro percentual por 100.
Registre arredondamento por parcela ou só ao final. Reflexos usam dependências
explícitas; subtotais não entram outra vez no total. Abatimentos são negativos,
com pagamento identificado; alocações parciais exigem fatos distintos conferidos.

Exemplo puramente aritmético, sem taxa legal presumida:
base 2200.00 / divisor 220 * quantidade 10 * fator 1.50 = 150.00.
Cada número precisa da sua fonte e justificativa no caso; o exemplo não fixa
divisor ou adicional trabalhista.

Com Python:

    python scripts/labor_calculations.py parametros.json --case-output saida --output saida

O resultado contém calculo_trabalhista.json e memoria_calculo_trabalhista.md.
Na revisão v4, calculation_set integra labor_review para conferir
fatos/normas/pedidos e a revisão do corpus. Liquidação exige título e análise
de seus comandos. Conferir principal, pagamentos, atualização e contribuições
conforme título, períodos e critérios oficiais, sem índices presumidos.

Para comparar com PJe-Calc, extraia/confronte o resultado real em
referencia.json: input_revision, source_file_sha256, tool,
tool_version, table_revision, reviewer e items com id/result.
Use --reference referencia.json; divergências retornam código 1.
Esse registro não atesta sozinho que o software externo foi executado.
Acrescente --reference-source arquivo_real para conferir seus bytes contra o
hash declarado. Sem o arquivo, a integridade externa fica como not_checked.
Atualizações preservam contas anteriores em calculation_history.
Não inventar arquivo PJC, versão, tabelas ou aprovação profissional.
[Manual oficial PJe-Calc](https://www.trt8.jus.br/sites/portal/files/roles/pje-calc/manual_de_instalacao_-_pje-calc_cidadao.pdf).

Sem código, manter fórmulas e memória demonstrativa, registrar conferências
numéricas não executadas e distinguir cálculo estimado de liquidação.
Parâmetro ausente delimita a parcela afetada e sua prova necessária.

Uma hipótese de cumulação por calculation_set: alternativas incompatíveis
devem ter cenários próprios, com inclusão no total explicitamente conferida.
