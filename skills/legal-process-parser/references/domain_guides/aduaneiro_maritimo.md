# Direito Aduaneiro, Marítimo e Portuário

Catálogo: `domain_catalogs/aduaneiro_maritimo.json`.

## Enquadramento e escopo
Rege controle aduaneiro, valoração AVA-GATT, classificação NCM/TEC, regimes especiais, RADAR/SISCOMEX, defesa comercial (*antidumping*) e perdimento (DL 37/1966, DL 1.455/1976 c/ Lei 14.651/2023 e Decreto 6.759/2009), além de transporte marítimo, *Bill of Lading* (BL), *demurrage*, Tribunal Marítimo (Lei 2.180/1954), afretamento e praticagem (Leis 9.432/1997, 9.537/1997 c/ Lei 14.813/2024 e 10.893/2004). Pretensões: `aduan_forfeiture_fraudulent_interposition`, `aduan_customs_retention_parametrization`, `aduan_customs_valuation_gatt`, `aduan_tariff_classification_ncm`, `aduan_special_customs_regimes`, `aduan_container_demurrage`, `aduan_cargo_damage_bl_subrogation`, `aduan_unlawful_cargo_bl_retention`, `aduan_maritime_tribunal_accidents`, `aduan_charter_pilotage_maritime_mortgage`, `aduan_siscomex_fee_afrmm`, `aduan_radar_siscomex_habilitation` e `aduan_antidumping_trade_remedies`.

## Polo ativo (importador, embarcador, seguradora ou armador)
- **Aduaneiro:** afaste perdimento no mero subfaturamento sem falsidade ideológica, cabendo só multa de 100% da diferença (DL 37/1966, art. 108, parágrafo único — STJ). Impugne quebra imotivada da ordem sequencial do AVA-GATT (Decreto 1.355/1994), reclassificação NCM retroativa (CTN, art. 146), retenção fora do prazo razoável ou coercitiva tributária mediante caução (Decreto 6.759/2009, art. 571; Súmula 323 STF) e excesso da Taxa SISCOMEX (Tema 1085 STF).
- **Marítimo:** pelo armador, cobre *demurrage* como indenização pré-fixada sem o teto do art. 412 do CC e com prescrição quinquenal quando prevista no BL/contrato (Tema 1035 STJ). Pela carga/seguradora sub-rogada (Súmula 188 STF), responsabilize objetivamente o transportador por avaria/falta (CC, arts. 749–750; DL 116/1967) e afaste retenção coercitiva de BL/carga (Res. ANTAQ 62/2021).

## Polo passivo (Aduana/União, transportador ou consignatário)
- **Defesa fazendária:** sustente perdimento (ou multa substitutiva de 100% — DL 1.455/1976, art. 23, § 3º) na interposição fraudulenta por ocultação do real adquirente ou falta de origem lícita dos recursos (Lei 10.637/2002, art. 59), revisão de canal verde no quinquênio (DL 37/1966, art. 54) e higidez de medidas *antidumping* (Decreto 8.058/2013).
- **Defesa marítima:** na *demurrage*, oponha prescrição ânua sem cláusula prévia ou no multimodal (Lei 9.611/1998, art. 22; Tema 1035 STJ) e suspensão do *free time* por culpa do armador/greve. Pelo transportador, argua decadência de 10 dias para avaria oculta (CC, art. 754, parágrafo único), prescrição ânua da descarga (DL 116/1967, art. 8º) e fortuna do mar.

## Magistratura e gabinete (CPC, art. 489, § 1º)
- Distinguir **Justiça Federal** (aduaneiro, navios/acidentes da navegação e Tribunal Marítimo — CF, art. 109, I, IX e X) de **Justiça Estadual** (cobranças privadas de frete e *demurrage*). Conferir presunção técnica relativa aos acórdãos do TM (Lei 2.180/1954, art. 18), sem suspensão automática da prescrição cível indenizatória.

## Marcos intertemporais
- **Tema 1035 STJ:** prescrição de 5 anos (cláusula unimodal) vs. 1 ano na *demurrage*.
- **Lei 14.301/2022 (BR do Mar):** afretamento na cabotagem e novas alíquotas do AFRMM.
- **Lei 14.651/2023 (24/08/2023):** duplo grau (20 + 20 dias no CEJUL) no perdimento (DL 1.455/1976, art. 27).
- **Lei 14.813/2024 (16/01/2024):** livre negociação e limites excepcionais de preço na praticagem (LESTA).

## Prova indispensável vs. prova futura
- **Indispensável no protocolo:** DI/DUIMP, *Invoice*, *Packing List*, BL com tradução juramentada (CPC, art. 192), auto de infração, protesto de avaria e *gate-in*/*gate-out*.
- **Prova futura/instrutória:** perícia merceológica (NCM), contábil de lastro financeiro (RADAR/interposição) e náutica/VDR (IAFN e TM).

## Integração com motores determinísticos
Use `domain_catalog.py --domain aduaneiro_maritimo`, valide peças (`defesa_auto_infracao_aduaneiro`, `defesa_tribunal_maritimo`, `recurso_voluntario_carf`, `mandado_seguranca`, `acao_anulatoria_debito_fiscal`) em `procedural_catalog.py`, audite decadência de 10 dias (CC, art. 754) e prescrições de 1 e 5 anos em `deadline_calculator.py` e `limitation_checker.py`, apure câmbio/SELIC em `civil_monetary_engine.py` e confira citações em `response_research.py`.
