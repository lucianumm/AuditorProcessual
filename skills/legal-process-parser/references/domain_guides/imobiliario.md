# Direito Imobiliário, Locatício e Condominial

Catálogo: `domain_catalogs/imobiliario.json` (para procedimentos registrais puros, ver também `notarial_registral.json`).

## 1. Regime e competência
- Competência absoluta do foro da situação da coisa nas ações reais imobiliárias de propriedade, vizinhança, servidão, divisão, demarcação e nunciação (CPC, art. 47, § 1º) e geral nas locatícias (Lei 8.245/1991, art. 58, II). Incide o CDC nas incorporações e loteamentos perante adquirente destinatário final, observada a especialidade das Leis 4.591/1964, 6.766/1979, 9.514/1997 e 13.786/2018.

## 2. Teses do adquirente, locatário, locador ou condomínio
- **Incorporação, atraso de obra e distrato:** ultrapassada a tolerância de 180 dias corridos (Lei 4.591/1964, art. 43-A), exija resolução com restituição integral imediata (**Súmula 543 STJ**) ou manutenção do contrato com lucros cessantes presumidos (aluguel mensal) vedada cumulação com cláusula penal moratória (**Temas 970 e 971 STJ**, permitida inversão da multa contra a construtora se unilateral). Na desistência imotivada do comprador, limite a retenção a 25% (ou até 50% com patrimônio de afetação para contratos posteriores à **Lei 13.786/2018**, art. 67-A).
- **Propriedade, usucapião, adjudicação e locação/condomínio:** promova adjudicação compulsória judicial ou extrajudicial dispensado o registro prévio da promessa quitada (**Súmula 239 STJ**; art. 216-B da LRP c/ Lei 14.382/2022), usucapião constitucional/ordinária/extraordinária (CF, arts. 183 e 191; CC, arts. 1.238–1.242), despejo com liminar em 15 dias nas hipóteses taxativas (Lei 8.245/1991, art. 59, § 1º), renovatória empresarial no penúltimo semestre (art. 51, § 5º) e execução direta de cotas condominiais (CPC, art. 784, X), inclusive restrição convencional expressa a locações de curtíssima temporada por plataformas (STJ).

## 3. Teses da incorporadora, credor fiduciário ou réu
- **Validade da tolerância, comissão de corretagem e alienação fiduciária:** oponha a validade da cláusula de tolerância de 180 dias e da transferência da comissão de corretagem destacada no preço (prescrição trienal — **Tema 938 STJ**), a prevalência da **Lei 9.514/1997** sobre o CDC nos contratos com alienação fiduciária após registro/execução extrajudicial com intimação pessoal para purgação da mora (arts. 26–27 c/ **Lei 14.711/2023**), a precariedade/detenção que impede a usucapião e a decadência de 1 ano/prazo de garantia quinquenal de solidez e segurança (CC, art. 618; Súmula 194 STJ).
- **Locação e fiança:** sustente exoneração do fiador na prorrogação por prazo indeterminado mediante notificação com 120 dias (Lei 8.245/1991, art. 40, X) ou aditamento sem anuência (Súmula 214 STJ) e impenhorabilidade do bem de família do fiador em **locação comercial** (**Tema 1127 STF**, distinguindo da locação residencial — Tema 295 STF / Súmula 549 STJ).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Distinguir contrato com cláusula de alienação fiduciária registrado e inadimplido (submetido ao procedimento especial da Lei 9.514/1997) da simples promessa de compra e venda antes da entrega das chaves ou por culpa da construtora. Nas ações de despejo por falta de pagamento, franquear purgação da mora em 15 dias observados os limites do art. 62 da Lei 8.245/1991.

## 5. Marcos intertemporais e motores
- **28/12/2018 (Lei 13.786/2018 — Lei dos Distratos, irretroativa a contratos anteriores — Tema 1002/STJ)** · **08/03/2022 (Tema 1127 STF — bem de família do fiador comercial)** · **28/06/2022 (Lei 14.382/2022 — SERP e adjudicação extrajudicial)** · **30/10/2023 (Lei 14.711/2023 — garantias imobiliárias)**.
- Motores: `official_indices.py` (`189` IGP-M, `188` INPC, `433` IPCA, `226` TR), `civil_monetary_engine.py`, `limitation_checker.py`, `deadline_calculator.py` e `domain_catalog.py`.
