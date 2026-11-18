# Direito Digital e Proteção de Dados Pessoais (LGPD)

Catálogo: `domain_catalogs/protecao_dados.json`.

## 1. Regime e competência
- Regido pela **LGPD (Lei 13.709/2018)**, direito fundamental autônomo (CF, art. 5º, LXXIX — EC 115/2022), em diálogo com o CDC (art. 45 da LGPD nas relações de consumo) e o Marco Civil da Internet (Lei 12.965/2014). Competência da Justiça Estadual ou Federal conforme os sujeitos, Trabalhista quando oriundo da relação de emprego (CF, art. 114, I e VI) e administrativa sancionadora da **ANPD** (art. 55-J).

## 2. Teses do titular dos dados, MP ou entidade legitimada
- **Bases legais, dados sensíveis e direitos do titular:** impugne tratamento desprovido de base legal idônea ou com desvio de finalidade/excesso ante o princípio da necessidade (arts. 6º, 7º e 11), consentimento genérico ou viciado (arts. 8º e 9º), compartilhamento não informado de dados de saúde, biométricos ou genéticos (art. 11, § 4º), negativa ou demora no atendimento de requisição de acesso, correção, eliminação, portabilidade ou **revisão de decisões automatizadas e *credit scoring*** (arts. 18 e 20; Súmula 550 STJ).
- **Incidentes de segurança e reparação:** demonstre falha técnica ou organizacional de segurança (arts. 44 e 46), omissão na comunicação tempestiva de incidente relevante à ANPD e aos titulares (art. 48 e Regulamento de Incidentes da ANPD — prazo padrão de 3 dias úteis), responsabilidade solidária entre controlador e operador quando este descumpre a lei ou instruções lícitas (art. 42, § 1º), inversão do ônus da prova (art. 42, § 2º) e dano moral individual ou coletivo em vazamento de dados sensíveis ou exposição concreta a fraudes.

## 3. Teses do controlador, operador ou encarregado
- **Hipóteses não dependentes de consentimento e excludentes (art. 43):** demonstre enquadramento legítimo em execução de contrato, obrigação legal/regulatória, exercício regular de direitos em processo, proteção do crédito ou legítimo interesse apoiado em LIA (*Legitimate Interest Assessment* — arts. 7º e 10), inaplicabilidade da LGPD para fins exclusivamente jornalísticos, artísticos, acadêmicos ou segurança pública (art. 4º) e excludentes do art. 43 (não realização do tratamento, inexistência de violação à legislação ou culpa exclusiva do titular/terceiro).
- **Ausência de dano *in re ipsa* em dados comuns e dosimetria ANPD:** sustente que o vazamento de dados cadastrais comuns (nome, CPF, telefone, endereço), sem comprovação de utilização fraudulenta ou abalo concreto, **não gera dano moral presumido** (jurisprudência da 2ª Seção/Turmas do STJ — AREsp 2.130.619), e invoque na esfera administrativa da ANPD a adoção prévia de boas práticas, governança, RIPD e pronta contenção para atenuação das sanções (art. 52, § 1º; Res. CD/ANPD 4/2023) e cláusulas-padrão na transferência internacional (**Res. CD/ANPD 19/2024**).

## 4. Magistratura e gabinete (CPC, art. 489, § 1º)
- Distinguir dado pessoal comum de **dado pessoal sensível** (art. 5º, II) ao aferir a configuração do dano extrapatrimonial, verificar a cadeia de agentes de tratamento (controlador vs. operador — art. 5º, VI e VII) e resguardar segredo industrial/comercial ao determinar explicação de critérios algorítmicos (art. 20, §§ 1º e 2º).

## 5. Marcos intertemporais e motores
- **18/09/2020 (Vigência material e processual da LGPD)** · **01/08/2021 (Vigência das sanções administrativas da ANPD — art. 65, I-A, Lei 14.010/2020)** · **10/02/2022 (EC 115/2022 — direito fundamental)** · **27/02/2023 (Res. CD/ANPD 4/2023 — dosimetria)** · **23/08/2024 (Res. CD/ANPD 19/2024 — transferência internacional)**.
- Motores: `privacy_redactor.py` (pseudonimização LGPD e trilha Res. CNJ 615/2025), `limitation_checker.py`, `deadline_calculator.py` e `domain_catalog.py`.
