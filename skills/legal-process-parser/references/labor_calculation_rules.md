# Cálculo trabalhista e conciliação de pagamentos

Aplicar response_research_rules.md antes de cada resposta sobre a conta.
labor_parameter_profiles.json e labor_parameters.py --profile selecionam
dezesseis pautas de fórmulas, nunca taxas presumidas. No contrato local por resposta,
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

## Unidades, limites e fases

- Percentual é unidade própria: só vira fração por divisão explícita por 100 na
  expressão (`base * pct / 100`) ou por input informado como fator; o motor
  recusa percentual usado como multiplicador.
- `min(...)` e `max(...)` estão disponíveis para pisos e tetos (ex.: juros
  `max(0, selic - ipca)` a partir de 30/08/2024; teto de dias de aviso).
- Atualização por fases (pauta monetary_update): pré-judicial, judicial até
  29/08/2024 e a partir de 30/08/2024, cada fase como parcela própria, com séries
  oficiais capturadas por `official_indices.py --series CODIGO --start --end`
  (BCB/SGS, com recibo). Acumulação composta ou simples conforme título e fonte.
- Pagamento informado como input com `role: payment` não pode ser abatido em
  mais de uma parcela; `payment_fact_ids` vale para qualquer tipo de parcela.
- Divisores, limites semanais e repousos ligados a 44 horas mudam com a EC
  141/2026 (42h e 2 dias de repouso a partir de dois meses da publicação; 40h um
  ano depois): decompor competências e conferir a contagem dos prazos.

## Jornada

`labor_ledger.py` aceita, além das regras diárias e semanais fornecidas:
`workplace_utc_offset` (janela noturna e data do turno pelo relógio do local),
`night_window.extension: after_full_window` (horas após a janela quando ela foi
integralmente trabalhada no mesmo intervalo, critério a conferir),
`intrajornada` (limiar e pausa mínima fornecidos) e `interjornada_min_minutes`.
Dia `rest_day_worked` registra trabalho em repouso ou feriado em rubrica própria,
fora do limite semanal. Minutos ficam com quatro casas decimais. Tolerância de
registro e compensação dependem de horário contratual e continuam conferidas
pelo autor da análise.

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

## Conferência semântica dos parâmetros e referência detalhada

labor_parameters confere quantidade por extenso, unidade e relação numérica;
50 dias não sustenta 50%. Delimitar o trecho do critério, source_unit,
source_relation (exact/minimum/maximum/greater_than/less_than) e
conditions_analysis para limites, condições e exceções. Formas não reconhecidas
permanecem pendentes; não substituí-las por coincidência de algarismos. A escolha
da condição e a incidência continuam análise jurídica, não conclusão do extrator.

Na referência externa schema_version 2.0, compare_reference exige o arquivo
original fornecido com --reference-source, hash, ferramenta/versão, tabelas e
responsável. Cada item registra external_locator e os mesmos relationship_id,
competence, claim_type, kind, segment, expression, bindings, include_in_total e
rounding_mode; total registra a soma externa; inputs traz
id/value/unit/external_locator; rounding identifica a política da referência.
Conferir bases, reflexos, abatimentos e arredondamento, não só total. Trata-se
de transcrição atribuída do resultado externo, sem fingir importação de .pjc
ou execução real do PJe-Calc. Sem arquivos reais, declarar a comparação pendente.
