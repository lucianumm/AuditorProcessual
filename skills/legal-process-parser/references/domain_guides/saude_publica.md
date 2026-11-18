# Direito Sanitário e Saúde Pública (SUS)

Catálogo: `domain_catalogs/saude_publica.json` (para planos de saúde privados, ver `consumidor.json`).

## 1. Regime e competência
- Direito fundamental à saúde e dever solidário dos entes federativos (CF, arts. 23, II, e 196–200; Lei 8.080/1990), estruturado pela repartição administrativa de competências do SUS (**Tema 793 STF**) e pelos parâmetros vinculantes para medicamentos não incorporados fixados pelo STF no **Tema 1234 e nas Súmulas Vinculantes 60 e 61 (set/2024)**:
  - **Competência da Justiça Federal (SV 60):** demandas relativas a medicamentos registrados na ANVISA mas **não incorporados** ao SUS cujo custo anual unitário seja **igual ou superior a 210 salários mínimos** (ou sem registro/importação autorizada excepcionalmente contra a União — Tema 500 STF), vedada a inclusão isolada de Estados/Municípios sem a União.
  - **Competência da Justiça Estadual:** medicamentos já incorporados nas listas RENAME/REMUME de responsabilidade estadual/municipal e não incorporados com custo anual inferior a 210 SM (com ressarcimento interfederativo na forma da SV 60).

## 2. Teses do paciente, Ministério Público ou Defensoria
- **Medicamentos incorporados, oncológicos, UTI e home care:** exija entrega imediata de fármacos e insumos constantes dos protocolos clínicos do SUS (direito subjetivo líquido e certo), início do primeiro tratamento oncológico no prazo máximo de **60 dias** (Lei 12.732/2012, art. 2º), internação em leito de UTI na rede pública ou custeio suplementar na rede privada diante da indisponibilidade de vaga, *home care* multidisciplinar e Tratamento Fora de Domicílio (TFD).
- **Medicamento não incorporado (SV 61 e Tema 1234 STF):** demonstre cumulativamente, com apoio no NATJUS: (i) registro na ANVISA; (ii) negativa administrativa prévia; (iii) ilegalidade ou mora excessiva da CONITEC; (iv) imprescindibilidade clínica e inexistência de substituto terapêutico no SUS; (v) incapacidade financeira; e (vi) **evidência científica de alto nível** (ensaios clínicos randomizados, revisão sistemática ou meta-análise). Em erro médico na rede pública ou conveniada ao SUS, acione diretamente o ente público/hospital (CF, art. 37, § 6º; **Tema 940 STF** — ilegitimidade passiva do servidor médico).

## 3. Teses da União, Estados, Municípios e ANVISA
- **Reserva técnica-científica e sustentabilidade do SUS:** oponha ausência de registro sanitário na ANVISA (**Tema 500 STF** — vedação geral de medicamentos experimentais e *off-label* sem protocolo/evidência qualificada), disponibilidade de alternativa terapêutica eficaz nos PCDTs do SUS, ausência de evidência científica de alto nível exigida pela **SV 61**, fixação do pagamento pelo preço máximo de venda ao governo (PMVG/CMED com desconto CAP) e ilegitimidade ou direcionamento do cumprimento conforme a repartição financeira do **Tema 793 e SV 60**. Nas autuações sanitárias (Lei 6.437/1977 e Lei 9.782/1999), sustente o poder de polícia precautório da ANVISA e vigilâncias locais.

## 4. Magistratura e gabinete (CPC, art. 489, § 1º; SV 60 e 61)
- Consultar obrigatoriamente o **NATJUS / plataforma e-NatJus (CNJ)** antes de deferir tutela de urgência para tecnologia não incorporada (vedada concessão baseada apenas em receituário isolado — SV 61), observar o teto de 210 SM para declínio à Justiça Federal e vedar pagamento direto em dinheiro ao autor salvo impossibilidade comprovada de aquisição direta pelo ente público com prestação de contas.

## 5. Marcos intertemporais e motores
- **22/05/2013 (Lei 12.732/2012 — prazo de 60 dias na oncologia)** · **22/05/2019 (Temas 500 e 793 STF)** · **16/09/2024 e 19/09/2024 (Tema 1234 e Súmulas Vinculantes 60 e 61 do STF)**.
- Motores: `deadline_calculator.py`, `civil_monetary_engine.py` (`fazenda_ec113`), `limitation_checker.py` e `domain_catalog.py`.
