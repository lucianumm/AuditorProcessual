# Direito Penal, Processo Penal e Execução Penal

Catálogo: `domain_catalogs/penal.json`.

## 1. Regime e competência
- Legalidade estrita, irretroatividade da lei mais gravosa e retroatividade benéfica (CF, art. 5º, XXXIX e XL; CP, art. 2º), sistema acusatório (CPP, art. 3º-A; **ADIs 6298–6305 STF**). Competência pelo lugar da consumação (CPP, art. 70, ressalvado o estelionato por depósito/transferência/cheque no domicílio da vítima — art. 70, § 4º, c/ Lei 14.155/2021) e Justiça Federal nas hipóteses taxativas do art. 109, IV a XI, da CF.

## 2. Teses da defesa técnica
- **Nulidades, prova digital, busca e reconhecimento:** argua ilicitude de provas derivadas (CF, art. 5º, LVI; CPP, art. 157), quebra da **cadeia de custódia física ou digital** (CPP, arts. 158-A a 158-F — invalidade de meros *prints* de WhatsApp Web espelhados sem código *hash*/extração auditável — STJ), nulidade de busca pessoal ou ingresso domiciliar sem mandado e sem fundada suspeita objetiva prévia (CPP, arts. 240 e 244; Tema 280 STF) e **nulidade de reconhecimento fotográfico ou pessoal em desacordo com o rito cogente do art. 226 do CPP** (jurisprudência pacificada da 5ª e 6ª Turmas do STJ e STF).
- **Liberdade, ANPP, mérito, dosimetria e execução:** postule relaxamento ou substituição da preventiva por cautelares diversas diante de fundamentação abstrata ou falta de contemporaneidade (CPP, arts. 282, 312, § 2º, e 319; art. 316, p.u.), **retroatividade do ANPP** aos processos sem trânsito em julgado quando não recebida a denúncia ou desclassificada a imputação (CPP, art. 28-A; **Tema 1098 STF**), extinção da punibilidade por pagamento/suspensão pelo parcelamento e falta de lançamento definitivo nos crimes tributários materiais (**SV 24**; Lei 10.684/2003, art. 9º), tráfico privilegiado sem hediondez para primário de bons antecedentes (Lei 11.343/2006, art. 33, § 4º; Tema 712 STF), vedação de pena intermediária aquém do mínimo (**Súmula 231 STJ** como limite pró-acusação a ser debatido ou respeitado) e progressão de regime pela fração vigente na data do fato (LEP, art. 112).

## 3. Teses do Ministério Público / Acusação
- **Materialidade, autoria, cautelares e Júri:** demonstre justa causa, situação de flagrância em crimes permanentes (tráfico/posse de arma com elementos prévios concretos — Tema 280 STF), fonte independente ou descoberta inevitável (CPP, art. 157, §§ 1º e 2º), garantia da ordem pública por risco concreto de reiteração delitiva, vedação de ANPP em violência doméstica, reincidência ou habitualidade criminosa (art. 28-A, § 2º), soberania dos veredictos e **execução imediata da condenação pelo Tribunal do Júri** independentemente do *quantum* da pena (**Tema 1068 STF**) e exigência de exame criminológico favorável na progressão pós-**Lei 14.843/2024**.

## 4. Magistratura e gabinete (CPP, art. 387 e art. 315, § 2º)
- Evitar iniciativa probatória substitutiva da acusação (CPP, art. 212 e ADIs 6298–6305 STF), individualizar cada vetor do art. 59 do CP sem *bis in idem* com elementares ou qualificadoras (Súmula 241 STJ), aplicar detração para fixação do regime inicial (CPP, art. 387, § 2º) e não fixar regime mais gravoso apenas pela gravidade abstrata do delito (Súmulas 718 e 719 STF; Súmula 440 STJ).

## 5. Marcos intertemporais e motores
- **06/05/2010 (Lei 12.234/2010 — prescrição mínima 3 anos e fim da retroativa pré-denúncia)** · **23/01/2020 (Lei 13.964/2019 — Pacote Anticrime: ANPP, cadeia de custódia e percentuais art. 112 LEP)** · **11/04/2024 (Lei 14.843/2024 — saída temporária e exame criminológico)** · **10/10/2024 (Lei 14.994/2024 — feminicídio autônomo art. 121-A CP e progressão em 55%)**.
- Motores: `penal_dosimetry.py` (trifásico, prescrição e LEP), `deadline_calculator.py` (`rito="penal"`, dias corridos — CPP, art. 798) e `domain_catalog.py`.
