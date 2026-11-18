# Previdência Complementar (Fechada — EFPC e Aberta — EAPC)

Catálogo: `domain_catalogs/previdencia_complementar.json`.

## 1. Regime e competência
- Regime privado, autônomo em relação ao RGPS, facultativo e baseado na **constituição prévia de reservas que garantam o benefício contratado** (CF, art. 202; LC 109/2001). **Competência absoluta da Justiça Comum Estadual** para ações propostas contra entidades de previdência privada visando complementação de aposentadoria, independentemente de o plano decorrer do contrato de trabalho (**Temas 190 e 1166 STF**), ressalvado o pedido trabalhista de reflexos das contribuições devidas exclusivamente pelo empregador sobre parcelas salariais deferidas na Justiça do Trabalho (**Tema 1166 STF**).
- Incide o CDC às entidades **abertas** (EAPC — bancos/seguradoras) e **não incide às entidades fechadas** (EFPC — fundos de pensão multipatrocinados ou de patrocínio único, **Súmula 563 STJ**, que cancelou a Súmula 321).

## 2. Teses do participante, assistido ou beneficiário
- **Revisão, verbas trabalhistas e institutos obrigatórios:** postule recálculo do benefício inicial por expurgos inflacionários sobre a reserva de poupança (**Súmula 289 STJ**), **inclusão de horas extras e parcelas salariais habituais reconhecidas na Justiça do Trabalho** no salário-real-de-benefício dos planos saldados/BD mediante recomposição prévia da reserva matemática e reparação de perdas e danos em face do ex-empregador patrocinador quando prescrita ou obstada a recomposição (**Temas 955 e 1021 STJ**), direito aos institutos do benefício proporcional diferido (BPD), portabilidade, resgate e autopatrocínio (LC 109/2001, art. 14) e impenhorabilidade do saldo previdenciário de caráter alimentar nos planos PGBL/VGBL até o limite de subsistência familiar (STJ).

## 3. Teses da entidade de previdência (EFPC/EAPC) ou patrocinador
- **Mutualismo, reserva matemática, regulamento aplicável e equacionamento:** oponha a aplicação do **regulamento vigente na data em que o participante implementou todas as condições de elegibilidade** ao benefício (LC 109/2001, art. 17, parágrafo único — afastando direito adquirido ao regime anterior na data da adesão), a eficácia liberatória de transação extrajudicial válida em migração voluntária de plano BD para CD/CV sem vício de consentimento, a vedação absoluta de majoração de benefício sem prévia e integral fonte de custeio atuarial (CF, art. 202, *caput*), a legalidade das contribuições extraordinárias de **equacionamento de déficit** rateadas entre patrocinador, participantes e assistidos na proporção contributiva (LC 109/2001, art. 21) e a **prescrição quinquenal** (LC 109/2001, art. 75; **Súmulas 291 e 427 STJ** — fundo de direito nas diferenças de resgate único ou prestações de trato sucessivo).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Observar a autonomia patrimonial por plano de benefícios (CNPBs distintos) e exigir perícia atuarial sempre que a condenação impactar o cálculo de benefício definido ou a reserva matemática. Distinguir VGBL utilizado como aplicação financeira de curto prazo/planejamento sucessório abusivo da reserva genuinamente previdenciária.

## 5. Marcos intertemporais e motores
- **30/05/2001 (LC 109/2001 — marco regulatório geral)** · **20/02/2013 (Tema 190 STF — competência da Justiça Comum)** · **24/02/2016 (Súmula 563 STJ — inaplicabilidade do CDC às EFPC)** · **08/08/2018 e 28/10/2020 (Temas 955 e 1021 STJ — verbas trabalhistas e reserva matemática)** · **11/01/2024 (Lei 14.803/2024 — opção pelo regime tributário regressivo/progressivo até a obtenção do benefício ou primeiro resgate)**.
- Motores: `limitation_checker.py` (prescrição quinquenal Súmula 291/427 STJ), `civil_monetary_engine.py`, `deadline_calculator.py` e `domain_catalog.py`.
