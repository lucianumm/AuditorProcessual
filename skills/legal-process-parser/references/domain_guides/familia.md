# Direito de Família e das Sucessões

Catálogo: `domain_catalogs/familia.json`.

## 1. Regime e competência
- Competência das Varas de Família e Sucessões na Justiça Estadual, com segredo de justiça obrigatório (CPC, art. 189, II) e intervenção do Ministério Público sempre que houver interesse de incapaz (art. 178, II). Nas ações de guarda, alimentos e convivência, prevalece o foro do domicílio do guardião do incapaz (CPC, art. 53, I, "a") ou da mulher em situação de violência doméstica (art. 53, I, "d").

## 2. Teses do alimentando, cônjuge/companheiro ou herdeiro
- **Alimentos e execução:** demonstre o binômio necessidade-possibilidade e proporcionalidade (CC, art. 1.694, § 1º), indícios da paternidade nos alimentos gravídicos (Lei 11.804/2008, conversão automática com o nascimento — STJ), responsabilidade subsidiária e complementar dos avós (**Súmula 596 STJ**), isenção de Imposto de Renda sobre pensão alimentícia (**ADI 5422 STF**) e execute sob rito de prisão civil as 3 últimas prestações mais as vincendas (CPC, art. 528, § 7º; **Súmula 309 STJ**) ou expropriação com protesto e desconto em folha (arts. 528, § 1º, e 529).
- **Divórcio, união estável, guarda e sucessões:** postule decretação liminar/parcial do divórcio como direito potestativo incondicionado (EC 66/2010; CPC, art. 356), reconhecimento de união estável com equiparação sucessória ao casamento (**Tema 809 STF**), **afastamento da guarda compartilhada diante de probabilidade de risco de violência doméstica ou familiar** (**Lei 14.713/2023** — CC, art. 1.584, § 2º), partilha de quotas, aplicações e VGBL aberto de caráter de investimento, colação de adiantamento de legítima (CC, art. 2.002) e **inventário/partilha/divórcio extrajudicial em cartório mesmo com herdeiros incapazes ou testamento** (**Res. CNJ 571/2024**).

## 3. Teses do alimentante, requerido ou espólio
- **Exoneração, revisão e justificativa:** comprove alteração superveniente da capacidade financeira (CC, art. 1.699), maioridade civil sem estudo superior/técnico ou com autossustento mediante contraditório (**Súmula 358 STJ**), impossibilidade absoluta involuntária e temporária que elide a prisão civil (art. 528, § 2º) e irrepetibilidade dos alimentos, vedada compensação unilateral salvo pagamento direto excepcional de despesas *in natura* essenciais para evitar enriquecimento ilícito (STJ).
- **Regime de bens e sucessões:** oponha incomunicabilidade de bens sub-rogados anteriores ao casamento/união na comunhão parcial (CC, art. 1.659, I e II), separação obrigatória aos maiores de 70 anos salvo pacto antenupcial que a afaste (**Tema 1236 STF**; Súmula 377 STF exige esforço comum), distinção entre namoro qualificado e união estável (ausência de *affectio maritalis* atual) e prescrição bienal das prestações alimentares vencidas (CC, art. 206, § 2º, suspensa contra absolutamente incapazes — art. 198, I).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Aplicar o Protocolo para Julgamento com Perspectiva de Gênero (Res. CNJ 492/2023), realizar audiência de mediação ressalvada violência doméstica (CPC, art. 695; Lei 11.340/2006) e colheita de escuta especializada de crianças/adolescentes quando pertinente.

## 5. Marcos intertemporais e motores
- **10/05/2017 (Tema 809 STF — inconstitucionalidade do art. 1.790 CC)** · **08/06/2022 (ADI 5422 STF — IR sobre alimentos)** · **31/10/2023 (Lei 14.713/2023 — guarda e violência doméstica)** · **01/02/2024 (Tema 1236 STF — regime aos 70+)** · **26/08/2024 (Res. CNJ 571/2024 — inventário extrajudicial com incapazes)**.
- Motores: `civil_monetary_engine.py`, `limitation_checker.py`, `deadline_calculator.py`, `privacy_redactor.py` (segredo de justiça) e `domain_catalog.py`.
