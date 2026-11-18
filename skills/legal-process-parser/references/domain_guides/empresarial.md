# Direito Empresarial e Societário

Catálogo: `domain_catalogs/empresarial.json` (para Recuperação Judicial e Falência aprofundadas, ver também `insolvencia.json`; para PI/Marcas, `propriedade_intelectual_digital.json`).

## 1. Regime e competência
- Rege sociedades limitadas e anônimas (CC, arts. 966–1.195; Lei 6.404/1976), títulos de crédito, contratos empresariais interempresariais paritários (CC, art. 421-A) e estabelecimento empresarial na Justiça Estadual (Varas Empresariais especializadas onde instaladas), ressalvada convenção arbitral (Lei 9.307/1996; Lei 6.404/1976, art. 109, § 3º).

## 2. Teses do sócio retirante, minoritário ou credor empresarial
- **Dissolução parcial, exclusão e haveres:** postule retirada imotivada em sociedade por prazo indeterminado mediante notificação com 60 dias (CC, art. 1.029), dissolução parcial por quebra da *affectio societatis* ou exclusão de sócio por falta grave (arts. 1.030 e 1.085) e **apuração de haveres por balanço especial de determinação** na omissão do contrato social, avaliando ativos tangíveis e intangíveis a preço de saída na data da resolução (CPC, arts. 604–606), com juros de mora após o prazo contratual/legal de pagamento (CC, art. 1.031, § 2º).
- **Responsabilidade de administradores, títulos e trespasse:** responsabilize administradores por violação da lei/estatuto ou conflito de interesses (Lei 6.404/1976, arts. 153–159; CC, art. 1.016), execute notas promissórias, cheques, cédulas de crédito e duplicatas escriturais (Lei 5.474/1968; Lei 13.775/2018) com autonomia e abstração perante endossatário de boa-fé, e responsabilize solidariamente alienante e adquirente no trespasse irregular ou por passivos contabilizados em até 1 ano (CC, art. 1.146).

## 3. Teses da sociedade, controlador ou demandado
- **Pactuação contratual dos haveres e *business judgment rule*:** imponha a **força vinculante do critério contratual de apuração e parcelamento de haveres** livremente pactuado (CPC, art. 606, *caput*, *a contrario sensu* — jurisprudência STJ), proteja decisões negociais informadas e desinteressadas dos administradores sob a *business judgment rule* (Lei 6.404/1976, art. 159, § 6º) e suscite prescrição trienal de anulação de assembleia ou pretensão contra administradores/sócios (Lei 6.404/1976, arts. 286–287; CC, art. 206, § 3º, VII).
- **Títulos causais, endosso-mandato e IDPJ:** oponha exceções pessoais à duplicata sem aceite e sem comprovante de entrega da mercadoria/serviço, ilegitimidade passiva do banco no mero endosso-mandato salvo excesso de poderes (**Súmula 476 STJ**) e exigência estrita de desvio de finalidade ou confusão patrimonial na desconsideração (CC, art. 50).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Fixar expressamente na decisão da primeira fase da dissolução parcial a **data da resolução da sociedade**, o critério de apuração de haveres e a nomeação de perito especializado em avaliação de empresas (CPC, arts. 604–607), determinando o depósito da parcela incontroversa (art. 604, § 1º).

## 5. Marcos intertemporais e motores
- **18/03/2016 (CPC/2015, arts. 599–609 — procedimento de dissolução parcial)** · **20/09/2019 (Lei 13.874/2019 — sociedade limitada unipessoal art. 1.052, § 1º, e art. 50 CC)** · **26/08/2021 e 21/09/2022 (Leis 14.195/2021 e 14.451/2022 — quóruns reduzidos na limitada, arts. 1.061 e 1.076 CC)**.
- Motores: `civil_monetary_engine.py`, `limitation_checker.py`, `deadline_calculator.py`, `domain_catalog.py` e `citation_check.py`.
