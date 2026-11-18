# Direito Notarial e Registral

Catálogo: `domain_catalogs/notarial_registral.json`.

## Enquadramento e escopo
Rege serviços notariais e de registro delegados (CF, art. 236; Lei 8.935/1994), registros públicos imobiliários e civis (Lei 6.015/1973 — LRP), o SERP (Lei 14.382/2022), protesto de títulos e CDAs (Lei 9.492/1997), desjudicialização (Provimento CNJ 149/2023 e Resolução CNJ 571/2024) e emolumentos (Lei 10.169/2000). Pretensões: `not_registral_doubt_proceeding`, `not_area_rectification_administrative_judicial`, `not_extrajudicial_usucapiao`, `not_extrajudicial_compulsory_adjudication`, `not_real_estate_incorporation_patrimony`, `not_civil_registry_name_gender_change`, `not_protest_titles_cda_judicial`, `not_notary_registrar_civil_liability`, `not_extrajudicial_inventory_divorce_minors`, `not_notarial_deed_digital_evidence`, `not_administrative_block_cancellation_fraud`, `not_serp_electronic_extract` e `not_emoluments_tax_nature_exemptions`.

## Polo ativo (apresentante, requerente extrajudicial ou lesado)
- **Imobiliário e SERP:** contra exigência ilegal ou fracionada fora de nota única, suscite dúvida prorrogando a prenotação (LRP, arts. 198 e 203). Maneje usucapião extrajudicial (art. 216-A — silêncio vale concordância), adjudicação extrajudicial direta/inversa (art. 216-B) e ato único de emolumentos na incorporação até o habite-se (art. 237-A).
- **RCPN, escrituras com incapazes e atas:** requeira alteração imotivada de prenome, sobrenomes familiares e gênero no RCPN (arts. 56–57; ADI 4275 STF). Lavre inventário e partilha extrajudiciais mesmo com herdeiros incapazes, garantido quinhão ideal em cada bem e parecer favorável do MP (Resolução CNJ 571/2024). Documente provas digitais por ata notarial (CPC, art. 384).

## Polo passivo (oficial, tabelião, Estado ou impugnante)
- **Princípios registrais e via administrativa:** defenda continuidade, especialidade, disponibilidade e prioridade (*tempus regit actum*). Oponha vedação de usar o art. 213 para acréscimo de área sem título, descabimento de REsp direto contra acórdão administrativo de dúvida (art. 204) e incompetência correcional no art. 214 quando o vício atingir negócio subjacente (exigindo ação contenciosa — art. 250).
- **Protesto e responsabilidade civil:** sustente constitucionalidade do protesto de CDA (ADI 5135 STF), ônus do devedor de cancelar protesto regular após quitação tardia (Lei 9.492/1997, art. 26; Tema 725 STJ), ilegitimidade passiva do "cartório" e responsabilidade subjetiva do delegatário (prescrição trienal) vs. objetiva do Estado (Lei 8.935/1994, art. 22; Tema 777 STF).

## Magistratura e corregedoria permanente (CPC, art. 489, § 1º)
- Separar **função administrativo-correcional** (dúvida do art. 198 e nulidade formal de pleno direito do art. 214 da LRP, sem coisa julgada material) de **jurisdição contenciosa cível**. Na gratuidade de emolumentos (CPC, art. 98, § 1º, IX), exigir prática imediata do ato antes de eventual dúvida do oficial (§ 8º).

## Marcos intertemporais
- **Lei 13.286/2016 e Tema 777 STF:** responsabilidade subjetiva de notários/registradores (prescrição de 3 anos) e objetiva do Estado.
- **Lei 14.382/2022 (28/06/2022):** SERP, extrato eletrônico (art. 6º), prazos em dias/horas úteis (LRP, arts. 9º, 19 e 188), arts. 56–57 do RCPN e adjudicação extrajudicial (art. 216-B).
- **Provimento CNJ 149/2023 e Resolução CNJ 571/2024 (26/08/2024):** Código Nacional Extrajudicial e escrituras de inventário/divórcio com incapazes ou testamento autorizado.

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** inteiro teor da matrícula atualizada, título causal ou extrato SERP, nota devolutiva, planta/memorial com ART e ata notarial.
- **Prova futura/instrutória:** notificações pelo oficial, perícia de agrimensura em retificação contenciosa e perícia documentoscópica/digital.

## Integração com os motores determinísticos
Acione `domain_catalog.py --domain notarial_registral`, valide peças (`suscitacao_duvida_registral`, `pedido_retificacao_registro`, `ata_notarial`, `escritura_publica_extrajudicial`, `sustacao_protesto`) em `procedural_catalog.py`, confira prazos úteis da Lei 14.382/2022 em `deadline_calculator.py`, audite prescrição trienal (Lei 8.935/1994, art. 22) e tributária de emolumentos em `limitation_checker.py` e valide atos do CNJ em `response_research.py`.
