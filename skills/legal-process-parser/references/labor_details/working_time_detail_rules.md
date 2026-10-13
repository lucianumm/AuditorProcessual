# Jornada por turno, dia, semana e regime

Carregar para night_work, time_bank, intrajornada, interjornada ou rest_days.
Preservar marcações originais e conferir a jornada narrada, efetiva e registrada.
Ponto uniforme, marcação ausente e erro de OCR são achados distintos. Em relato,
registrar frequência, variações e intervalo real sem fabricar todos os dias.

Aplicar uma regra conferida por relação e período. Separar duração física,
hora jurídica, tolerância, horas compensadas e parcela remunerável. A tolerância
precisa do conjunto de marcações e da hipótese normativa; não arredondar todas
as entradas por conveniência. Escalas e categorias especiais exigem seu regime.

Trabalho noturno: janela, unidade, prorrogação e cumulação são critérios separados.
O motor labor_ledger conta somente janela/unidade fornecidas. Intervalo entre
jornadas compara saída de um turno e entrada do seguinte, preservando o dia;
intervalo intrajornada depende da duração, período normativo, cláusula e
consequência específica. Conferir pedidos sobrepostos e natureza da parcela.

Banco de horas: conferir instrumento e requisitos, vigência, créditos, débitos,
acesso ao saldo, datas de compensação e ruptura. time_bank.py concilia movimentos
atribuídos e vencimentos fornecidos; não decide validade nem converte todo saldo
em horas extras. Alocação de uma compensação exige crédito identificável e não
pode consumir o mesmo crédito duas vezes.

Em mudança de regra no meio da semana, o cálculo semanal fica delimitado até
definir um critério global fundamentado; não reiniciar o limite a cada trecho.
Repousos, domingos e feriados exigem calendário territorial, escala, compensação
real e fonte própria. Dias ausentes continuam desconhecidos.

Comparar contas reais com o mesmo cenário, versão, tabelas e arredondamento
do PJe-Calc. Divergência numérica exige conferir parâmetros antes de atribuir
erro jurídico ao software. [Manual oficial](https://www.trt8.jus.br/sites/portal/files/roles/pje-calc/manual_de_instalacao_-_pje-calc_cidadao.pdf).
