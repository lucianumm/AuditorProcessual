# Contestação, impugnação e peças defensivas: matriz bilateral

Guia aplicável a peças defensivas de conhecimento, cumprimento ou execução (`contestacao`, `embargos_monitorios`, `impugnacao_cumprimento`, `embargos_execucao_civil`, `embargos_execucao_fiscal`, `excecao_pre_executividade`, `contestacao_improbidade`, `resposta_acusacao` e `defesa_auto_infracao_*`). Redija na voz técnica da parte demandada, enfrentando analiticamente cada capítulo fático, probatório, jurídico e quantitativo da pretensão adversa.

## 1. Triagem processual e contagem determinística
1. **Rito, termo inicial e citação:** separe juntada do mandado/AR, confirmação no Domicílio Judicial Eletrônico (CPC, art. 246; Res. CNJ 455/2022), edital ou audiência (CPC, art. 335; CLT, art. 847). Audite o prazo em `deadline_calculator.py` (dias úteis no CPC/CLT/Juizados; corridos no CPP, LEP, Lei 11.101/2005 e ritos administrativos especiais) e confira a trava do art. 229, § 2º, do CPC em autos eletrônicos.
2. **Concentração e eventualidade (CPC, art. 336):** estruture camadas sucessivas (`preliminares -> prejudiciais -> mérito principal -> mérito subsidiário / parâmetros de liquidação`) para impedir preclusão consumativa.

## 2. Preliminares processuais e filtro de competência (CPC, art. 337)
Vincule cada preliminar pertinente a fato, documento e efeito exato (extinção sem mérito, remessa, suspensão ou saneamento):
- **Convenção de arbitragem (art. 337, X e §§ 5º–6º):** vedado o conhecimento de ofício; argua antes do mérito sob pena de renúncia tácita.
- **Incompetência e eleição de foro abusiva (CPC, art. 63, §§ 1º e 3º — Lei 14.879/2024):** confira pertinência do foro eleito com domicílio/residência das partes ou local da obrigação, impugnando ajuizamento em comarca aleatória.
- **Inépcia, ilegitimidade, falta de interesse, litispendência, coisa julgada ou conexão:** aponte o vício específico (pedido genérico fora do art. 324, ausência de correlação lógica ou identidade tríplice).
- **Valor da causa e gratuidade indevida (art. 337, III e XIII):** apresente cálculo do proveito econômico real e sinais objetivos de capacidade financeira nos próprios autos.

## 3. Prejudiciais de mérito (CPC, art. 487, II)
- **Prescrição, decadência e prescrição intercorrente:** separe `actio nata`, causas impeditivas/suspensivas (ex.: regulação de sinistro — Súmula 229 STJ; inquérito no CADE — Lei 14.470/2022) e interrupção única (CC, art. 202), conferindo em `limitation_checker.py`.
- **Quitação, transação, compensação ou novação recuperacional (Lei 11.101/2005, art. 59):** aponte recibos, extratos ou termos homologados por página e `document_id`.

## 4. Ônus da impugnação especificada (CPC, art. 341)
1. Mapeie **100% dos fatos constitutivos, documentos e pedidos acessórios** no `legal_review.json` (`assertion_reviews` e `issues`), evitando presunção de veracidade (ressalvado o art. 341, parágrafo único).
2. Distinga: **(a)** negativa fundada do fato; **(b)** admissão do fato bruto com qualificação jurídica diversa; **(c)** fato impeditivo, modificativo ou extintivo (CPC, art. 373, II), indicando prova documental acostada e prova instrutória a produzir.
3. Impugne inversão genérica do ônus da prova (CDC, art. 6º, VIII) ou distribuição dinâmica (CPC, art. 373, §§ 1º–2º) quando gerar prova diabólica ao réu.

## 5. Eventualidade quantitativa, reconvenção e pedidos
- **Redutores subsidiários:** impugne valores, termos iniciais de juros/correção (Lei 14.905/2024; Súmulas 54 e 362 STJ; EC 113/2021), cumulação de multas, culpa concorrente (CC, art. 945), *duty to mitigate the loss* e honorários.
- **Reconvenção (CPC, art. 343):** abra capítulo autônomo conexo com valor da causa próprio apenas quando autorizado pelo usuário.
- **Fechamento:** acolhimento das preliminares/prejudiciais, improcedência total com sucumbência, acolhimento eventual dos redutores, especificação motivada de provas e marcação **RASCUNHO — NÃO PROTOCOLAR**.
