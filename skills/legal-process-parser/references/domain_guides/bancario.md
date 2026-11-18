# Direito Bancário e Mercado de Crédito

Catálogo: `domain_catalogs/bancario.json`.

## 1. Regime e competência
- Incide o CDC às instituições financeiras (Súmula 297 STJ), afastado apenas em operações empresariais de grande porte para insumo produtivo sem vulnerabilidade fática/técnica. Competência da Justiça Estadual (ou Federal quando figurar a Caixa Econômica Federal — CF, art. 109, I).

## 2. Teses do mutuário, correntista ou investidor
- **Juros, capitalização e tarifas:** confronte a taxa pactuada com a **taxa média de mercado do BCB/SGS** para a mesma modalidade e época da contratação, demonstrando discrepância substancial (Temas 24–27 STJ; Súmula 530 STJ na ausência do contrato). Impugne capitalização diária sem informação clara da taxa diária efetiva (Tema 953 STJ), comissão de permanência cumulada com outros encargos (Súmula 472 STJ) e tarifas de cadastro/avaliação sem serviço efetivo ou seguro prestamista imposto por venda casada (**Tema 972 STJ**).
- **Fraudes digitais, Pix e consignados (RMC/RCC):** em transferências via Pix, engenharia social, central telefônica falsa ou abertura fraudulenta de conta, sustente a responsabilidade objetiva pelo risco da atividade e falha nos mecanismos de segurança/perfil transacional (**Súmula 479 STJ** — fortuito interno). Em cartões consignados (RMC/RCC) contratados sob aparência de empréstimo fixo ou descontos previdenciários sem contratação hígida, peça nulidade/conversão à taxa do consignado comum e repetição, observada a impenhorabilidade de até 40 SM poupados de boa-fé (CPC, art. 833, X — STJ).

## 3. Teses da instituição financeira
- **Pactuação expressa e culpa exclusiva:** demonstre a assinatura física ou biométrica auditável (geolocalização, selfie com prova de vida, IP, crédito efetivo na conta de titularidade do autor), taxa contratual próxima à média divulgada pelo BACEN (Súmula 382 STJ), pactuação expressa da capitalização mensal (Súmula 539 e 541 STJ) e culpa exclusiva da vítima ou de terceiro externo sem falha de segurança bancária.
- **Alienação fiduciária e garantias:** exija na revisional a quantificação incontroversa e o depósito das parcelas no tempo e modo contratados (CPC, art. 330, § 2º; Súmula 380 STJ) e defenda a consolidação da propriedade e busca e apreensão após constituição em mora (DL 911/1969 c/ **Lei 14.711/2023**, pagamento da integralidade da dívida pendente — Tema 722 STJ).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Rejeitar petição inicial revisional genérica que não discrimine as obrigações controvertidas nem indique o valor incontroverso (CPC, art. 330, §§ 2º e 3º). Ao aferir abusividade de juros, cotejar concretamente a série temporal do BCB da data e linha de crédito exatas, vedada limitação abstrata a 12% ao ano (Súmula 382 STJ). Nas fraudes eletrônicas, examinar se a movimentação destoava do perfil histórico do correntista.

## 5. Marcos intertemporais e motores
- **31/03/2000 (MP 1.963-17 / MP 2.170-36 — capitalização inferior à anual)** · **02/07/2021 (Lei 14.181/2021 — superendividamento)** · **30/10/2023 (Lei 14.711/2023 — execução extrajudicial DL 911/69)** · **30/08/2024 (Lei 14.905/2024 — inaplicabilidade da limitação geral do CC às instituições reguladas pelo CMN/BCB)**.
- Motores: `official_indices.py` (séries de taxas médias de crédito BCB `20714`, `25461`–`25471`, `22022`), `civil_monetary_engine.py` (`--compare-bank-rate`), `limitation_checker.py` e `domain_catalog.py`.
