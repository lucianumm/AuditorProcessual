# Direito Eleitoral

Catálogo: `domain_catalogs/eleitoral.json`.

## 1. Regime e competência
- Competência especializada da Justiça Eleitoral (Juízes Eleitorais, TREs e TSE — CF, arts. 118–121; Código Eleitoral, Lei 4.737/1965), regida pelo princípio da celeridade, preclusão imediata por fases (registro, campanha, votação e diplomação — CE, art. 259) e prazos peremptórios contínuos no período eleitoral (LC 64/1990 e Lei 9.504/1997).

## 2. Teses do requerente, coligação ou Ministério Público Eleitoral
- **Registro, elegibilidade e cotas de gênero:** impugne registro em AIRC (prazo de 5 dias do edital — LC 64/1990, art. 3º) por ausência de condição de elegibilidade, desincompatibilização tempestiva ou incidência em inelegibilidade da Lei da Ficha Limpa (art. 1º, I, "d", "e", "g", "j", "l"). Em fraude à cota mínima de 30% de gênero (Lei 9.504/1997, art. 10, § 3º), aponte votação zerada/ínfima, ausência de atos de campanha e contas padronizadas (**Súmula 73 TSE** — cassação de todo o DRAP).
- **Ilícitos de campanha e abuso de poder (AIJE, AIME, RCED):** demonstre abuso de poder econômico, político ou uso indevido dos meios de comunicação com gravidade qualitativa/quantitativa (LC 64/1990, art. 22, XVI), captação ilícita de sufrágio (Lei 9.504/1997, art. 41-A — dispensa potencialidade, bastando anuência e dolo específico), condutas vedadas a agentes públicos (arts. 73–77), propaganda antecipada com pedido explícito ou "palavras mágicas" (art. 36-A) e uso de *deepfake* ou IA sem rotulagem (**Res. TSE 23.732/2024**, art. 9º-C).

## 3. Teses do candidato, partido ou representado
- **Decadência, litisconsórcio e elegibilidade superveniente:** suscite decadência estrita (AIJE e representações dos arts. 30-A, 41-A e 73 até a diplomação; AIME em 15 dias da diplomação — CF, art. 14, § 10; RCED em 3 dias — CE, art. 262), **extinção por ausência de citação de litisconsorte passivo necessário** (vice/suplentes na chapa majoritária — Súmula 38 TSE) e fato superveniente que afaste a inelegibilidade até a diplomação (Lei 9.504/1997, art. 11, § 10; Súmula 43 TSE).
- **Mérito defensivo e contas:** oponha ausência de gravidade (art. 22, XVI), liberdade de manifestação política pré-campanha sem pedido explícito de voto (art. 36-A), irrelevância percentual/valores módicos nas contas mediante aplicação dos princípios da proporcionalidade e razoabilidade (Lei 9.504/1997, art. 30, § 2º-A) e nulidade de gravação ambiental clandestina ilícita no processo eleitoral.

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Conferir formação completa do litisconsórcio passivo necessário antes da decadência, vedada inclusão ulterior após o termo final. Distinguir desaprovação de contas (que por si só não gera inelegibilidade — Súmula 41 TSE) da captação/gasto ilícito do art. 30-A. Nas eleições municipais, observar os limites de competência e os recursos eleitorais em 3 dias (CE, art. 258).

## 5. Marcos intertemporais e motores
- **04/06/2010 (LC 135/2010 — Ficha Limpa)** · **29/09/2015 (Lei 13.165/2015)** · **28/09/2021 (EC 111/2021 e Lei 14.211/2021 — federações e sobras eleitorais / ADIs STF)** · **27/02/2024 (Res. TSE 23.732/2024 — IA e desinformação eleitoral)**.
- Motores: `deadline_calculator.py` (`rito="eleitoral"` em dias contínuos no período eleitoral), `domain_catalog.py`, `legislation_lookup.py` e `citation_check.py`.
