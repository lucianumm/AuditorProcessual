# Direito Securitário

Catálogo: `domain_catalogs/securitario.json`.

## Enquadramento e escopo
Rege seguros de dano e de pessoas, regulação de sinistro, seguro auto, vida, habitacional, rural, garantia, D&O/E&O, prestamista, cosseguro, resseguro e sub-rogação sob o Código Civil (arts. 757–802), DL 73/1966, LC 126/2007 e o **Marco Legal dos Seguros (Lei 15.040/2024)**. Pretensões: `sec_claim_regulation_denial`, `sec_intentional_risk_aggravation_intoxication`, `sec_life_preexisting_disease_suicide`, `sec_auto_total_loss_third_party`, `sec_housing_insurance_sfh`, `sec_rural_agricultural_climate`, `sec_liability_do_eo`, `sec_surety_bond_judicial_contractual`, `sec_insurer_subrogation_regress`, `sec_prescription_intertemporal`, `sec_coinsurance_reinsurance`, `sec_credit_life_tying` e `sec_group_life_nonrenewal_cancellation`.

## Polo ativo (segurado, beneficiário, tomador ou sub-rogada)
- **Regulação e coberturas:** exija manifestação em 30 dias sob pena de decadência da recusa e vede inovação ulterior nos motivos da negativa nos contratos sob a Lei 15.040/2024 (arts. 86–87). Afaste recusa por doença preexistente sem exame prévio nem prova de má-fé (Súmula 609 STJ), negativa por embriaguez em seguro de vida (Súmula 620 STJ), cancelamento sem interpelação prévia de mora (Súmula 616 STJ) e venda casada de seguro prestamista (Tema 972 STJ).
- **Sub-rogação e garantia:** pela seguradora paga a indenização, demande o causador nos limites do desembolso (CC, art. 786; Súmula 188 STF; Lei 15.040/2024, art. 93). Substitua penhora por seguro garantia acrescido de 30% (CPC, art. 835, § 2º).

## Polo passivo (seguradora, resseguradora ou causador)
- **Delimitação, agravamento e prescrição:** oponha exclusão clara e destacada, agravamento intencional causal no seguro de dano (CC, art. 768; Lei 15.040/2024, art. 14), carência bienal objetiva para suicídio ressalvada a reserva matemática (Súmula 610 STJ) e prescrição ânua contada da ciência da recusa (CC, art. 206, § 1º, II; Súmulas 101 e 229 STJ; Lei 15.040/2024, art. 126).
- **Legitimidade e limites:** argua descabimento de ação proposta exclusiva pelo terceiro contra a seguradora no seguro facultativo (Súmula 529 STJ), ausência de solidariedade presumida no cosseguro (art. 34), autonomia do resseguro (LC 126/2007, art. 14) e dever pré-contratual exclusivo do estipulante no seguro coletivo (Tema 1112 STJ).

## Magistratura e gabinete (CPC, art. 489, § 1º)
- Separar seguros paritários de grandes riscos de contratos consumeristas de adesão. Distinguir delimitação objetiva do risco de perda da garantia por conduta dolosa, enfrentando os laudos de regulação e o nexo causal (art. 489, § 1º, IV, CPC). No seguro habitacional, manter competência estadual salvo comprometimento comprovado do FCVS em apólice pública (Súmula 327 STJ).

## Marcos intertemporais
- **Lei 15.040/2024 (publicada em 10/12/2024, vigência após 1 ano em 11/12/2025 — art. 134):** revoga os arts. 757–802 e 206, § 1º, II, do CC. Contratos anteriores seguem o CC/2002; contratos vigentes sob a nova lei submetem-se à decadência de 30 dias na regulação (art. 86), vedação de inovação na recusa (art. 87) e prescrição de 1 ano para o segurado e 3 anos para beneficiários/terceiros (art. 126).

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** apólice/certificado, condições gerais vigentes, questionário de risco/DPS, aviso de sinistro, carta de negativa integral e comprovantes de prêmio ou desembolso sub-rogatório.
- **Prova futura/instrutória:** exibição integral do dossiê de regulação, perícia médica/prontuários, perícia agronômica (ZARC) ou de engenharia/contábil.

## Integração com os motores determinísticos
Use `domain_catalog.py --domain securitario`, selecione peças em `procedural_catalog.py`, audite a suspensão administrativa da prescrição (Súmula 229 STJ) em `limitation_checker.py`, calcule correção desde a apólice/desembolso em `civil_monetary_engine.py` e confira a lei vigente na contratação em `legislation_lookup.py` e `citation_check.py`.
