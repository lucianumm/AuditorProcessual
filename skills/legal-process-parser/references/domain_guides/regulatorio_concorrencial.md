# Direito Regulatório, Infraestrutura e Concorrencial

Catálogo: `domain_catalogs/regulatorio_concorrencial.json`.

## Enquadramento e escopo
Rege defesa da concorrência no CADE e ações reparatórias antitruste (Leis 12.529/2011 e 14.470/2022), agências reguladoras (Lei 13.848/2019), concessões, PPPs e relicitações (Leis 8.987/1995, 11.079/2004 e 13.448/2017) e setores regulados: elétrico (ANEEL), telecomunicações (ANATEL), transportes e portos (ANTT/ANTAQ), petróleo e gás (ANP), saneamento (ANA/Lei 14.026/2020) e mineração (ANM). Pretensões: `reg_cartel_unilateral_conduct_cade`, `reg_merger_control_gun_jumping`, `reg_antitrust_damages_pass_on`, `reg_electric_sector_aneel_gd`, `reg_telecom_anatel_infrastructure`, `reg_transport_antt_antaq_freight`, `reg_oil_gas_biofuels_anp`, `reg_sanitation_universalization`, `reg_concession_rebalance_caducity`, `reg_agency_sanction_air`, `reg_ports_terminals_tariffs`, `reg_mining_cfem_anm` e `reg_relicitation_amicable_termination`.

## Polo ativo (regulado, concessionária, representante ou lesado antitruste)
- **Concessões e regulação:** vincule o reequilíbrio econômico-financeiro à **matriz contratual de riscos** e à álea extraordinária (Lei 8.987/1995, arts. 9º–10; Lei 11.079/2004, art. 5º, III), calculado por fluxo de caixa marginal ou TIR. Impugne normas editadas sem Análise de Impacto Regulatório (AIR) obrigatória (Lei 13.848/2019, art. 6º), cortes elétricos por débito pretérito/TOI unilateral (Tema 699 STJ) e taxas municipais em faixa de domínio (Tema 261 STF).
- **Reparação concorrencial:** postule ressarcimento em dobro e tutela da evidência fundada em acórdão do CADE, com prescrição suspensa durante a investigação administrativa (Lei 12.529/2011, arts. 46-A, 47 e 47-C — Lei 14.470/2022).

## Polo passivo (agência, poder concedente ou representado)
- **Deferência técnica e matriz de riscos:** oponha a discricionariedade técnica da agência reguladora dentro da moldura legal e a alocação contratual de riscos ordinários (demanda/financiamento) à concessionária.
- **Defesa antitruste e sancionadora:** argua prescrição punitiva quinquenal e intercorrente trienal (Lei 9.873/1999, art. 1º; Lei 12.529/2011, art. 46), base da multa restrita ao ramo de atividade afetado (art. 37, I), responsabilidade simples sem solidariedade para signatários de leniência/TCC (art. 47, §§ 2º–3º) e prova efetiva do repasse do sobrepreço (*pass-on defense* — art. 47-A).

## Magistratura e gabinete (CPC, art. 489, § 1º; LINDB, arts. 20–24)
- Controlar legalidade, competência normativa, rito de AIR e devido processo sancionador sem substituir escolhas técnicas regulatórias legítimas. Avaliar expressamente impactos sistêmicos e tarifários antes de suspender resoluções, leilões ou caducidade (LINDB, arts. 20–21; CPC, art. 489, § 1º, IV).

## Marcos intertemporais
- **Lei 13.848/2019:** governança das agências e obrigatoriedade de AIR e consulta pública.
- **Lei 14.026/2020 (ADI 6492 STF):** universalização do saneamento até 2033 e vedação de novos contratos de programa.
- **Lei 14.300/2022:** transição tarifária de micro/minigeração distribuída até 2045 para protocolos em 12 meses.
- **Lei 14.470/2022 (17/11/2022):** *double damages*, *pass-on defense* não presumido e suspensão prescricional antitruste.

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** contrato de concessão com matriz de riscos, processo administrativo SEI/CADE integral, relatório de AIR/nota técnica e notas fiscais/faturas históricas.
- **Prova futura/instrutória:** perícia econômico-financeira (fluxo de caixa marginal), econométrica (sobrepreço e repasse em cartel) e de engenharia setorial.

## Integração com os motores determinísticos
Use `domain_catalog.py --domain regulatorio_concorrencial`, selecione peças (`representacao_cade`, `notificacao_ato_concentracao_cade`, `requerimento_administrativo`, `mandado_seguranca`) em `procedural_catalog.py`, audite prescrição punitiva/intercorrente e decenal da CFEM (Lei 9.636/1998, art. 47) em `limitation_checker.py`, confira cálculos em `civil_monetary_engine.py` e valide normas em `response_research.py`.
