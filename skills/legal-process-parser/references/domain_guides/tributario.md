# Direito Tributário (Judicial, Administrativo/CARF e Reforma Tributária)

Catálogo: `domain_catalogs/tributario.json`.

## 1. Regime e competência
- Legalidade estrita, anterioridade anual e nonagesimal, irretroatividade e capacidade contributiva (CF, arts. 145, § 1º, e 150, I a III; CTN, arts. 97 e 105–106). Tributos federais tramitam na Justiça Federal (JEF até 60 SM salvo anulação de lançamento de trato continuado quando superar o teto) e estaduais/municipais nas Varas da Fazenda/Execuções Fiscais.

## 2. Teses do contribuinte ou responsável
- **Decadência, prescrição e execução fiscal (Lei 6.830/1980):** suscite via exceção de pré-executividade sem garantia do juízo matérias cognoscíveis de ofício sem dilação probatória (**Súmula 393 STJ**): decadência quinquenal contada do fato gerador no pagamento parcial/ausência de dolo (CTN, art. 150, § 4º; Súmula 555 STJ) ou do 1º dia do exercício seguinte no lançamento de ofício (art. 173, I), prescrição quinquenal da cobrança (art. 174), **prescrição intercorrente automática `1 + 5` anos** da ciência da primeira tentativa infrutífera de localização do devedor ou de bens (LEF, art. 40; **Temas 566–571 STJ**) e ilegitimidade no redirecionamento ao sócio retirante ou sem poderes de gerência na época da dissolução irregular (CTN, art. 135, III; **Súmula 430 e 435 STJ**; **Temas 962 e 981 STJ**).
- **Repetição de indébito, bases de cálculo, CARF e Reforma Tributária:** postule restituição/compensação dos últimos 5 anos (CTN, arts. 165–170-A; Súmula 213 STJ admite MS declaratório), exclusão do ICMS destacado da base do PIS/COFINS (**Tema 69 STF**), limitação da base do ITBI ao valor da transação declarada com presunção de boa-fé (**Tema 1113 STJ**), denúncia espontânea antes de procedimento fiscal (CTN, art. 138, inaplicável a tributo declarado e impago — Súmula 360 STJ), exclusão de multas e juros no empate pró-Fisco no CARF (**Lei 14.689/2023**, art. 25, § 9º-A, do Decreto 70.235/1972) e não cumulatividade plena no regime de transição **CBS/IBS/IS (EC 132/2023 e LC 214/2025)**.

## 3. Teses da Fazenda Pública (PGFN, PGE e PGM)
- **Constituição por declaração, interrupção e garantias:** oponha constituição definitiva do crédito pela entrega da DCTF/GIA dispensando lançamento suplementar (**Súmula 436 STJ**), retroação da interrupção prescricional à data da propositura da execução pelo despacho citatório (CTN, art. 174, p.u., I; **Tema 179 STJ**, salvo demora imputável ao Fisco — Súmula 106 STJ), exigência de garantia integral para conhecimento dos embargos à execução fiscal (LEF, art. 16, § 1º — Tema 526 STJ), comprovação da repercussão financeira nos tributos indiretos (CTN, art. 166), trava de 30% na compensação de prejuízos fiscais (**Tema 117 STF**), incidência do IRPJ/CSLL sobre a SELIC apenas nas hipóteses ressalvadas fora da repetição de indébito (**Tema 962 STF**) e vedação de compensação antes do trânsito em julgado (CTN, art. 170-A).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º; Res. CNJ 547/2024)
- Observar a extinção de execuções fiscais de pequeno valor sem movimentação útil conforme o **Tema 1184 do STF e a Resolução CNJ 547/2024** (protesto prévio e tentativa concisa de conciliação/localização patrimonial), e limitar índices locais de correção e mora tributária ao teto da taxa SELIC federal (**Tema 1062 STF**).

## 5. Marcos intertemporais e motores
- **09/06/2005 (LC 118/2005 — prescrição quinquenal da repetição)** · **15/03/2017 (Modulação Tema 69 STF)** · **20/09/2023 (Lei 14.689/2023 — CARF)** · **20/12/2023 e 16/01/2025 (EC 132/2023 e LC 214/2025 — Reforma Tributária do Consumo: transição 2026–2033)**.
- Motores: `limitation_checker.py` (`ctn_art150_p4`, `ctn_art173_i`, `ctn_art174`, `lef_art40_intercorrente_1mais5`), `civil_monetary_engine.py` (`tributario_selic`), `deadline_calculator.py` e `domain_catalog.py`.
