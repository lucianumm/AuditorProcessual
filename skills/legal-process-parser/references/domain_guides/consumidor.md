# Direito do Consumidor e Saúde Suplementar

Catálogo: `domain_catalogs/consumidor.json`.

## 1. Regime e competência
- Aplica-se o CDC (Lei 8.078/1990) ao destinatário final fático e econômico ou equiparado com vulnerabilidade comprovada (teoria finalista mitigada — STJ). Foro do domicílio do consumidor (CDC, art. 101, I), admitido JEC até 40 SM quando dispensável perícia complexa.

## 2. Teses do consumidor
- **Fato e vício, cadastros, cobrança e comércio eletrônico:** postule responsabilidade objetiva solidária na cadeia de fornecimento (arts. 12, 14, 18 e 25, § 1º), inversão do ônus da prova por hipossuficiência ou verossimilhança (art. 6º, VIII), direito de arrependimento em 7 dias fora do estabelecimento (art. 49), cancelamento e dano moral *in re ipsa* por negativação indevida ou sem prévia notificação (art. 43, § 2º; Súmula 359 STJ) e repetição em dobro do indébito pago em contrariedade à boa-fé objetiva (art. 42, parágrafo único — Corte Especial STJ, EAREsp 676.608).
- **Planos de saúde e superendividamento:** exija cobertura de tratamento prescrito (quimioterapia oral, home care, terapias multidisciplinares para TEA/PCD) superando negativa baseada exclusivamente no rol da ANS (**Lei 14.454/2022**, art. 10, § 13, da Lei 9.656/1998; Súmula 302 STJ), nulidade de reajuste etário abusivo (**Tema 952 STJ**) ou rescisão unilateral de beneficiário em tratamento contínuo (**Tema 1082 STJ**), e repactuação global de dívidas preservando o mínimo existencial (**Lei 14.181/2021**, arts. 104-A a 104-C).

## 3. Teses do fornecedor ou operadora
- **Excludentes, decadência/prescrição e Súmula 385:** oponha inexistência de defeito e culpa exclusiva do consumidor ou de terceiro externo (arts. 12, § 3º, III, e 14, § 3º, II), decadência de 30/90 dias para vícios aparentes ou a partir da constatação do vício oculto (art. 26), prescrição quinquenal para fato do produto/serviço (art. 27), prazo de 30 dias para saneamento do vício (art. 18, § 1º) e exclusão de dano moral quando preexistente anotação legítima (**Súmula 385 STJ**).
- **Transporte aéreo e saúde suplementar:** aplique a limitação indenizatória material e a prescrição bienal das Convenções de Varsóvia/Montreal no transporte aéreo internacional (**Tema 210 STF**), a validade de reajustes coletivos justificados por sinistralidade atuarial (**Tema 1016 STJ**), a exclusão de medicamentos sem registro na ANVISA (**Tema 990 STJ**) e a coparticipação legítima transparente.

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Decidir sobre a inversão do ônus da prova na decisão de saneamento (CPC, art. 373, § 1º; Súmula/jurisprudência STJ — regra de instrução, evitando decisão-surpresa). Distinguir mero inadimplemento contratual de lesão a direitos da personalidade. Na repetição em dobro (art. 42, p.u.), verificar a modulação temporal fixada pela Corte Especial do STJ (30/03/2021 para relações não vinculadas a serviços públicos).

## 5. Marcos intertemporais e motores
- **30/03/2021 (Modulação STJ na repetição em dobro — EAREsp 676.608)** · **02/07/2021 (Lei 14.181/2021 — superendividamento e Dec. 11.150/2022)** · **22/09/2022 (Lei 14.454/2022 — critérios de superação do rol da ANS)**.
- Motores: `limitation_checker.py` (`art26_30dias`, `art26_90dias`, `art27_5anos`), `civil_monetary_engine.py`, `deadline_calculator.py` e `domain_catalog.py`.
