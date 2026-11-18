# Direito Administrativo e Controle Externo

Catálogo: `domain_catalogs/administrativo.json`.

## 1. Regime e competência
- **Competência (CF, art. 109, I, e Varas da Fazenda):** União, autarquias e empresas públicas federais atraem a Justiça Federal (JEF até 60 SM salvo anulação de ato administrativo de efeitos amplos, demissão ou improbidade — Lei 10.259/2001, art. 3º, § 1º, III); Estados e Municípios tramitam nas Varas da Fazenda/JEFP (Lei 12.153/2009, teto de 60 SM). Em mandado de segurança, a competência define-se pela categoria e sede funcional da autoridade coatora, observada a decadência de 120 dias (Lei 12.016/2009, art. 23).

## 2. Teses do administrado, servidor ou contratado
- **Atos, concursos, PAD e servidores:** exija motivação explícita e análise das consequências práticas da invalidação (LINDB, arts. 20–24), direito subjetivo à nomeação dentro das vagas ou por preterição arbitrária (Tema 784 STF), nulidade de PAD por comissão não estável, cerceamento de defesa ou excesso desproporcional na pena de demissão (Lei 8.112/1990, arts. 128 e 149; Súmula 650 STJ) e reajuste dos pisos nacionais do magistério e da enfermagem (ADI 7222 STF).
- **Licitações, contratos, desapropriação e responsabilidade estatal:** pleiteie reequilíbrio econômico-financeiro por fato do príncipe, álea extraordinária ou evento alocado ao ente na matriz de riscos (Lei 14.133/2021, arts. 22, 103 e 124, II, "d"), indenização objetiva por conduta de agentes públicos ou custódia (CF, art. 37, § 6º; Tema 592 STF) e justa indenização contemporânea à avaliação na desapropriação (DL 3.365/1941), admitida mediação/arbitragem (Lei 13.867/2019).

## 3. Teses da Administração Pública e controle
- **Presunção de legitimidade, mérito administrativo e prescrição:** oponha a impossibilidade de substituição do mérito administrativo pelo Judiciário salvo ilegalidade ou desproporcionalidade manifesta, a vedação de equiparação remuneratória por súmula (SV 37), a limitação à correção de erro grosseiro em bancas de concurso (Tema 485 STF) e a prescrição quinquenal contra a Fazenda (Decreto 20.910/1932, art. 1º; Súmula 85 STJ).
- **Improbidade e Tribunais de Contas:** na defesa em improbidade, exija prova de **dolo específico** (vedada modalidade culposa) e aplique retroativamente a prescrição de 8 anos e a intercorrente de 4 anos aos processos sem trânsito em julgado até 26/10/2021 (Lei 8.429/1992 c/ Lei 14.230/2021; **Tema 1199 STF**). Perante o TCU e na execução de seus acórdãos, oponha a prescrição quinquenal e intercorrente trienal (Lei 9.873/1999; **Tema 899 STF**; Res. TCU 344/2022).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Indicar as consequências práticas e o regime de transição ou modulação ao invalidar contrato, edital ou ato administrativo (LINDB, arts. 20–21). Na responsabilidade por omissão estatal, distinguir omissão específica com dever individualizado de proteção de omissão genérica dependente de falha do serviço (*faute du service*). Na improbidade, individualizar a conduta dolosa por réu (art. 17-C da Lei 8.429/1992).

## 5. Marcos intertemporais e motores
- **26/04/2018 (Lei 13.655/2018 — LINDB)** · **01/04/2021 e 30/12/2023 (Lei 14.133/2021 e revogação definitiva da Lei 8.666/1993)** · **26/10/2021 (Lei 14.230/2021 — Improbidade / Tema 1199 STF)** · **09/12/2021 (EC 113/2021 — SELIC única na Fazenda)**.
- Motores: `deadline_calculator.py` (prazo em dobro — CPC, art. 183), `limitation_checker.py` (Dec. 20.910/32 e art. 23 LIA), `civil_monetary_engine.py` (`fazenda_ec113`), `domain_catalog.py`, `legislation_lookup.py` e `citation_check.py`.
