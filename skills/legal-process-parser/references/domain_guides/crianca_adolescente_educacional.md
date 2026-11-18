# Direito da Criança, do Adolescente e Educacional

Catálogo: `domain_catalogs/crianca_adolescente_educacional.json`.

## Enquadramento e escopo
Rege proteção integral (CF, art. 227; ECA — Lei 8.069/1990), família substituta, poder familiar, acolhimento, ato infracional e SINASE (Lei 12.594/2012), além do direito educacional básico e superior: creche, inclusão escolar (Lei 13.146/2015), mensalidades (Lei 9.870/1999), FIES (Lei 10.260/2001), PROUNI e Cotas (Lei 12.711/2012 c/ Lei 14.723/2023), Revalida (Lei 13.959/2019) e prevenção ao *bullying* (Lei 14.811/2024). Pretensões: `eca_statutory_custody_substitute_family`, `eca_termination_suspension_parental_power`, `eca_adoption_national_international_sna`, `eca_institutional_foster_care_review`, `eca_infractional_act_sinase_measures`, `eca_daycare_preschool_vacancy`, `eca_inclusive_education_support_professional`, `eca_travel_artistic_sports_authorization`, `eca_fies_contracting_medical_abatement`, `eca_prouni_quotas_heteroidentification`, `eca_foreign_diploma_revalida`, `eca_bullying_cyberbullying_school_protection` e `eca_higher_education_documents_retention`.

## Polo ativo (MP, representante, estudante ou defesa socioeducativa)
- **Infância e socioeducativo:** fixe competência da Vara da Infância diante de risco (ECA, arts. 98 e 148, parágrafo único). Exija defesa técnica e oitiva mesmo em remissão cumulada com medida (Súmula 342 STJ) e afaste internação automática por ato análogo ao tráfico sem violência/reiteração (art. 122; Súmula 492 STJ).
- **Educação básica e superior:** exija vaga em creche/pré-escola (Tema 548 STF) e profissional de apoio escolar para TEA/PCD sem cobrança de taxa extra na rede privada (Lei 13.146/2015, art. 28, § 1º; ADI 5357 STF). Afaste retenção de histórico/diploma por inadimplência (Lei 9.870/1999, art. 6º) e postule abatimento de 1% no FIES para médicos da ESF e docentes públicos (Lei 10.260/2001, art. 6º-B).

## Polo passivo (genitores, instituição de ensino ou ente público)
- **Poder familiar e SNA:** sustente que carência material isolada não autoriza perda do poder familiar (ECA, art. 23), exija esgotamento da citação pessoal antes de edital (art. 158) e observância do SNA salvo art. 50, § 13.
- **Escolas e bancas:** distinga apoio escolar pedagógico/locomoção/higiene de terapias clínicas extraescolares, defenda não renovação de matrícula ao final do período letivo por inadimplência (Lei 9.870/1999, art. 5º), legalidade das bancas fenotípicas de heteroidentificação com contraditório (ADC 41 STF) e autonomia universitária no Revalida (Tema 1028 STJ).

## Magistratura e gabinete (CPC, art. 489, § 1º)
- Concretizar o melhor interesse com suporte em **laudos interprofissionais específicos**, vedadas fórmulas abstratas (CPC, art. 489, § 1º, II). Reavaliar acolhimentos a cada 3 meses com teto de 18 meses (ECA, art. 19, §§ 1º–2º), colher consentimento do maior de 12 anos (art. 28, § 2º) e preservar o sigilo legal (art. 143).

## Marcos intertemporais
- **Lei 13.812/2019:** vedação de viagem nacional de menor de 16 anos desacompanhado sem autorização (ECA, art. 83).
- **Lei 14.723/2023 (14/11/2023):** concorrência inicial na ampla concorrência antes das cotas, renda de 1 salário mínimo e quilombolas.
- **Lei 14.811/2024 (15/01/2024):** crimes de *bullying*/*cyberbullying* (CP, art. 146-A) e certidões em instituições (ECA, art. 59-A).

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** certidão de nascimento, laudo médico circunstanciado (TEA/PCD), contrato escolar, edital/vídeo da banca ou certidão CNES/docência no FIES.
- **Prova futura/instrutória:** estudo psicossocial interprofissional (ECA, arts. 151 e 161) e depoimento especial (Lei 13.431/2017).

## Integração com os motores determinísticos
Use `domain_catalog.py --domain crianca_adolescente_educacional`, selecione peças (`acao_destituicao_poder_familiar`, `pedido_adocao`, `defesa_ato_infracional`, `mandado_seguranca`, `habeas_corpus`) em `procedural_catalog.py`, conte prazos do ECA em **10 dias corridos** sem preparo (arts. 152, § 2º, e 198, II) em `deadline_calculator.py`, proteja dados de menores em `privacy_redactor.py` e valide citações em `response_research.py`.
