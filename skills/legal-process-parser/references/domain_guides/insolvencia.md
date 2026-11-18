# Direito da Insolvência, Recuperação Empresarial e Falência

Catálogo: `domain_catalogs/insolvencia.json`.

## Enquadramento e escopo
Rege recuperação judicial, recuperação extrajudicial, falência, insolvência transnacional e incidentes concursais sob a Lei 11.101/2005 (LREF), reformada pela Lei 14.112/2020. Pretensões: `insolv_judicial_recovery_filing`, `insolv_stay_period_extension`, `insolv_extraconcursal_fiduciary_essentiality`, `insolv_credit_verification_late_claim`, `insolv_cram_down_creditor_plan`, `insolv_rural_producer_recovery`, `insolv_tax_regularity_transaction`, `insolv_procedural_substantive_consolidation`, `insolv_bankruptcy_conversion_priority`, `insolv_revocatory_objective_inefficacy`, `insolv_fresh_start_discharge`, `insolv_cross_border_insolvency` e `insolv_extrajudicial_recovery`.

## Polo ativo (devedor, recuperanda, massa falida ou habilitante)
- **Processamento, *stay* e ativos essenciais:** comprove o biênio de atividade regular (art. 48, inclusive produtor rural por ECD/LCDPR sem depender de 2 anos de registro na Junta — Tema 1145 STJ) e a documentação do art. 51. Proteja bens de capital essenciais no *stay period* de 180 dias corridos (arts. 6º, § 4º, e 49, § 3º; Súmula 480 STJ).
- **Plano, fisco e massa falida:** demonstre requisitos do *cram down* (art. 58, § 1º) e transação fiscal (art. 57; Lei 13.988/2020). Pela massa, proponha ineficácia objetiva no termo legal (art. 129) ou ação revocatória por conluio em 3 anos da quebra (arts. 130 e 132). Pelo falido, requeira *fresh start* trienal (art. 158, V).

## Polo passivo (credor oponente, fiduciário ou réu em revocatória)
- **Extraconcursalidade e trava bancária:** sustente não sujeição de créditos pós-pedido pelo fato gerador (Tema 1051 STJ), alienação/cessão fiduciária de recebíveis, arrendamento mercantil, ACC e CPR física (art. 49, §§ 3º–4º; Lei 8.929/1994, art. 11), além da execução livre contra coobrigados/avalistas (Súmula 581 e Tema 885 STJ).
- **Objeção ao plano e consolidação:** impugne supressão de garantias sem anuência expressa do credor titular, consolidação substancial sem os requisitos cumulativos do art. 69-J e ausência de CND/CPEN (art. 57), ou apresente plano alternativo dos credores (art. 56, § 4º).

## Magistratura e gabinete (CPC, art. 489, § 1º)
- Determinar constatação prévia objetiva quando necessária (art. 51-A) sem invadir a análise negocial da AGC. Exercer controle estrito de legalidade sobre cláusulas ilegais do plano, fundamentar concretamente a essencialidade de cada ativo operacional (CPC, art. 489, § 1º, II e IV) e cooperar com o juízo fiscal na substituição de constrições vitais (art. 6º, § 7º-B).

## Marcos intertemporais
- **Lei 14.112/2020 (vigência em 23/01/2021):** contagem em **dias corridos** (art. 189, § 1º, I), *stay* prorrogável uma única vez, plano alternativo de credores, consolidação substancial (arts. 69-G a 69-L), insolvência transnacional (arts. 167-A a 167-Y) e *fresh start* de 3 anos (art. 158, V).
- **Lei 13.988/2020:** transação tributária federal para recuperandas.

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** demonstrações contábeis do art. 51, relação de credores, registro prévio da garantia fiduciária (CC, art. 1.361, § 1º), protesto especial falimentar (Súmula 361 STJ) e título/cálculo até a data do pedido ou quebra na habilitação (art. 9º, II).
- **Prova futura/instrutória:** constatação prévia (art. 51-A), perícia contábil em impugnação de crédito, vistoria de essencialidade e rastreamento patrimonial na revocatória.

## Integração com os motores determinísticos
Consulte `domain_catalog.py --domain insolvencia`, selecione peças concursais em `procedural_catalog.py`, conte prazos em **dias corridos** em `deadline_calculator.py`, verifique decadência revocatória (art. 132) e extinção trienal (art. 158) em `limitation_checker.py`, apure atualização até o pedido/quebra (arts. 9º, II, e 124) em `civil_monetary_engine.py` e valide citações em `response_research.py`.
