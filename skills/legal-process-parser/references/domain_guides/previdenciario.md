# Direito Previdenciário (RGPS, RPPS e Assistência Social — BPC)

Catálogo: `domain_catalogs/previdenciario.json`.

## 1. Regime e competência
- **Justiça Federal (CF, art. 109, I e § 3º):** julga benefícios comuns do RGPS e BPC/LOAS contra o INSS (JEF até o teto absoluto de 60 SM — Lei 10.259/2001, art. 3º; delegada estadual apenas se a comarca distar mais de 70 km de Vara Federal — EC 103/2019). **Justiça Estadual:** competência exclusiva para benefícios **acidentários** contra o INSS (CF, art. 109, I; Súmula 501 STF e Súmula 15 STJ). Exige-se prévio requerimento administrativo negado ou excedido o prazo de 45 dias (**Tema 350 STF**) e petição inicial específica nas ações por incapacidade (Lei 8.213/1991, art. 129-A).

## 2. Teses do segurado, dependente ou requerente do BPC
- **Aposentadorias, regras de transição e reafirmação da DER:** confronte o CNIS com CTPS (presunção relativa — Súmula 75 TNU), fichas financeiras e recolhimentos sob responsabilidade do tomador PJ desde 04/2003 (Lei 10.666/2003), simule direito adquirido até 13/11/2019 e todas as transições da EC 103/2019 (arts. 15–20 e 26) e requeira subsidiariamente a **reafirmação da DER** para computar tempo até a segunda instância (**Tema 995 STJ**).
- **Tempo especial, rural/híbrida, incapacidade, pensão e BPC:** no tempo especial, aplique o enquadramento profissional até 28/04/1995, limites históricos de ruído (80 dB até 05/03/1997; 90 dB até 18/11/2003; 85 dB a partir de 19/11/2003 — Tema 694 STJ), ineficácia absoluta do EPI para ruído (**Tema 555 STF**), vedação de média aritmética simples no ruído variável (**Tema 1083 STJ**), impugnação motivada do EPI (**Tema 1090 STJ**) e vigilante armado/desarmado (**Tema 1031 STJ**), convertendo em comum até 13/11/2019. Some tempo rural remoto ao urbano na **aposentadoria híbrida** (**Tema 1007 STJ**), prorrogue o período de graça por prova ampla do desemprego involuntário (art. 15; Súmula 27 TNU) e, no BPC, exclua benefícios de até 1 SM de outro idoso/PCD e gastos extraordinários de saúde (Lei 8.742/1993, art. 20, §§ 11-A e 14).

## 3. Teses do INSS ou ente gestor de RPPS
- **Preliminares, decadência e carência:** oponha falta de interesse de agir (Tema 350 STF), perda da qualidade de segurado, vedação de cômputo para carência de recolhimento em atraso anterior à primeira contribuição em dia do contribuinte individual (Lei 8.213/1991, art. 27, II), **decadência decenal** para revisão do ato concessório (art. 103, *caput*) e prescrição quinquenal das parcelas (Súmula 85 STJ).
- **Teses vinculantes restritivas:** invoque a cogência da regra de transição do art. 3º da Lei 9.876/1999 que afastou a **Revisão da Vida Toda** (**ADIs 2110 e 2111 STF**), a proibição de conversão de tempo especial pós-13/11/2019 (EC 103/2019, art. 25, § 2º), a restrição do adicional de 25% à incapacidade permanente (**Tema 1095 STF**), a exigência de 2 documentos recentes (24 meses) para união estável pós-Lei 13.846/2019 (art. 16, § 5º) e irrepetibilidade restrita à boa-fé em erro interpretativo (Temas 692 e 979 STJ).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Não aplicar decadência sobre indeferimento ou cessação (**ADI 6096 STF**; Súmula 81 TNU) nem sobre matéria não apreciada na concessão (**Tema 975 STJ**). Fixar expressamente DII, DID, DER, DIB e DCB, avaliando condições pessoais e sociais na incapacidade (Súmula 47 TNU) e observando a Súmula 111/Tema 1105 STJ nos honorários.

## 5. Marcos intertemporais e motores
- **29/11/1999 (Lei 9.876/1999 e ADIs 2110/2111 STF)** · **18/06/2019 (Lei 13.846/2019)** · **13/11/2019 (EC 103/2019 — Reforma da Previdência)** · **09/12/2021 (EC 113/2021 — SELIC única nos atrasados)**.
- Motores: `social_security_calc.py` (vínculos concomitantes, conversão até 13/11/2019, transições e decadência), `civil_monetary_engine.py` (`fazenda_ec113`), `deadline_calculator.py` e `domain_catalog.py`.
