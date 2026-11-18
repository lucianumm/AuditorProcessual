# Direito Processual Civil

Catálogo: `domain_catalogs/processual_civil.json`.

## Enquadramento e escopo
Rege competência, negócios processuais, tutelas provisórias, produção antecipada de provas, nulidades, cumprimento de sentença, precedentes qualificados, ação rescisória e admissibilidade recursal cível sob o CPC/2015 (Lei 13.105/2015). Pretensões: `pciv_resp_re_admissibility`, `pciv_interlocutory_appeal_mitigated`, `pciv_irdr_iac_precedents`, `pciv_rescissory_action`, `pciv_provisional_relief_stabilization`, `pciv_attorney_fees_equitable`, `pciv_nullities_prejudice`, `pciv_forum_selection_competence`, `pciv_procedural_business_agreement`, `pciv_autonomous_early_evidence`, `pciv_predatory_abusive_litigation`, `pciv_provisional_final_enforcement` e `pciv_res_judicata_issue_preclusion`.

## Polo ativo, recorrente ou exequente
- **Tutelas e provas autônomas:** demonstre probabilidade do direito, perigo de dano e reversibilidade (CPC, art. 300, § 3º), ou tutela de evidência (art. 311). Na antecedente (arts. 303–304), explicite o pedido de estabilização e adite em 15 dias úteis. Na produção antecipada sem urgência (art. 381, II–III), delimite os fatos sem formular pedido condenatório.
- **Recursos e rescisória:** em agravo fora do rol literal do art. 1.015, comprove inutilidade do reexame na apelação (Tema 988 STJ). Em REsp/RE, abra preliminar de relevância federal (CF, art. 105, § 2º — EC 125/2022) ou repercussão geral (CPC, art. 1.035), prequestionamento ficto (art. 1.025) e revaloração jurídica de fatos incontroversos (afastando Súmulas 5 e 7 STJ). Na rescisória (art. 966), recolha o depósito de 5% (art. 968, II) dentro do biênio (art. 975).

## Polo passivo, recorrido ou executado
- **Foro aleatório e nulidades:** argua ineficácia de eleição de foro sem vínculo com domicílio das partes ou local da obrigação (CPC, art. 63, §§ 1º e 3º — Lei 14.879/2024), preclusão (art. 278) e ausência de prejuízo concreto (*pas de nullité sans grief* — art. 282, § 1º).
- **Contrarrazões, cumprimento e honorários:** suscite falta de dialeticidade (Súmula 182 STJ; Súmulas 283/284 STF), erro grosseiro na troca entre agravo interno (art. 1.030, § 2º) e agravo em REsp/RE (art. 1.042), e Súmula 343 STF (Tema 136) na rescisória. Exija caução no cumprimento provisório para levantamento (art. 520, IV), impugne excesso com planilha (art. 525, § 4º) e afaste equidade em honorários de valor elevado (art. 85, § 8º-A; Tema 1076 STJ).

## Magistratura e gabinete (CPC, art. 489, § 1º)
- Declinar de ofício antes da citação em foro aleatório abusivo (art. 63, § 3º). Diante de indícios concretos de litigância predatória, determinar diligências proporcionais sem barrar acesso legítimo à justiça (Tema 1198 STJ; Rec. CNJ 159/2024). Enfrentar todos os argumentos infirmadores (art. 489, § 1º, IV) e realizar *distinguishing* analítico de precedentes (arts. 927, 947 e 976).

## Marcos intertemporais
- **CPC/2015 (18/03/2016):** isolamento dos atos processuais (`tempus regit actum` — art. 14).
- **Lei 14.365/2022 (03/06/2022) e Tema 1076 STJ:** vedação de equidade fora do art. 85, § 8º-A.
- **EC 125/2022 (15/07/2022):** filtro constitucional de relevância no REsp.
- **Lei 14.879/2024 (05/06/2024):** novo regime de pertinência da cláusula de eleição de foro (art. 63, §§ 1º e 3º).

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** certidão de intimação/trânsito, procuração, guia de preparo e feriado local (art. 1.003, § 6º), contrato com cláusula de foro/NJP e memória aritmética (arts. 524 e 525).
- **Prova futura/instrutória:** perícia na produção antecipada (art. 381), exibição incidental (art. 396) e oitiva em incidente de falsidade ou litigância abusiva.

## Integração com os motores determinísticos
Use `domain_catalog.py --domain processual_civil`, valide peças em `procedural_catalog.py`, conte prazos úteis e feriados em `deadline_calculator.py`, confira decadência bienal da rescisória e prescrição intercorrente (art. 921) em `limitation_checker.py`, audite cálculos do art. 523 em `civil_monetary_engine.py` e valide citações em `response_research.py` e `citation_check.py`.
