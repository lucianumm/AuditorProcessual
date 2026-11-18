# Minutas de decisão judicial, sentença, voto e parecer jurídico consultivo

Guia aplicável a minutas de apoio a gabinete (`decisão interlocutória`, `saneamento`, `sentença`, `voto/acórdão`) e `parecer_juridico` consultivo. Diferentemente das peças parciais, exige **imparcialidade estrita, exame simétrico dos dois polos e observância das Resoluções CNJ nº 332/2020 e nº 615/2025** (supervisão humana indelegável).

## 1. Estrutura lógica de sentença e voto (CPC, arts. 489 e 490)
1. **Relatório rastreável (art. 489, I):** sintetize partes, pedidos principais/subsidiários, fatos constitutivos, preliminares/mérito da defesa, réplica e instrução, referenciando documento, página PDF e folha em `case_memory.json`.
2. **Ordem cogente de apreciação:** **(a)** pressupostos processuais, competência (incluindo controle de foro aleatório — art. 63, § 3º) e condições da ação; **(b)** nulidades sob o filtro do prejuízo concreto (*pas de nullité sans grief* — art. 282, § 1º); **(c)** prejudiciais de mérito (prescrição/decadência auditadas em `limitation_checker.py`); **(d)** mérito principal e subsidiário; **(e)** reconvenção de forma autônoma.

## 2. Fundamentação analítica obrigatória (CPC, art. 489, § 1º)
Evite rigorosamente as seis hipóteses legais de nulidade por falta de fundamentação:
- **Subsunção concreta (incisos I a III):** proíba paráfrase isolada de lei, emprego de conceitos jurídicos indeterminados sem ligação fática concreta ou motivação padronizada genérica.
- **Enfrentamento integral dos argumentos infirmadores (inciso IV):** para acolher pedido ou defesa, enfrente expressamente **todos os argumentos fáticos, probatórios e jurídicos capazes, em tese, de infirmar a conclusão adotada**, conferindo cada `counterargument` em `legal_review.json`.
- **Precedentes, *distinguishing* e *overruling* (incisos V e VI; art. 927):** identifique os fundamentos determinantes (*ratio decidendi*) do precedente vinculante demonstrando ajuste aos fatos; para afastá-lo, explicite distinção fática material ou superação verificada no portal oficial.

## 3. Consequencialismo (LINDB, arts. 20–24) e dispositivo congruente
- Em direito público, regulatório, coletivo ou concursal, avalie as **consequências práticas da decisão** e eventuais regimes de transição/modulação (LINDB, arts. 20 e 21), vedada invalidação por valores abstratos sem exame das alternativas reais.
- **Congruência e liquidez (CPC, arts. 141, 492 e 497):** alinhe o dispositivo estritamente aos pedidos formulados, fixando extensão da obrigação, prazo, meio executivo, índices monetários/juros auditados em `civil_monetary_engine.py` (Lei 14.905/2024, EC 113/2021 ou SELIC), rateio de custas, honorários dentro das faixas objetivas do art. 85, §§ 2º, 3º e 8º-A (Tema 1076 STJ) e manutenção/revogação de tutela provisória (art. 1.012, § 1º, V).

## 4. Parecer jurídico consultivo (`parecer_juridico`)
1. **Estrutura:** *(I) Ementa; (II) Consulta e separação entre fatos documentados e declarados; (III) Quesitos; (IV) Análise bilateral por questão; (V) Riscos qualitativos, correntes divergentes e mitigação prática; (VI) Respostas objetivas aos quesitos*.
2. **Rigor opinativo:** confronte normas, marcos intertemporais e precedentes favoráveis e contrários localizados em `response_research.py`, classificando o grau de consolidação (*precedente vinculante*, *majoritário*, *controvertido* ou *tese inovadora*) sem inventar percentuais fictícios de êxito.
3. **Governança:** encerre com aviso expresso **MINUTA DE APOIO — SUJEITA À REVISÃO E VALIDAÇÃO HUMANA INTEGRAL**.
