# Regras de análise jurídica

## Voz e proveniência

- Escreva em narrativa jurídica afirmativa, vinculando cada parágrafo a peça,
  PDF p., folha processual, `document_id` e trecho.
- Diga diretamente o conteúdo da fonte: `A ré deixou de pagar`, `O contrato
  registra`, `A prova contém` e `A decisão determinou`, conforme a natureza do
  registro.
- Não descreva a atividade de leitura como resultado jurídico. Evite
  “conforme documentação”, “documento apresentado”, “certidão analisada”,
  “foi analisado” e expressões equivalentes sem fonte direta.
- Separe `fato_documentado`, `alegacao`, `prova_registrada`, `decisao`,
  `inferência` e `lacuna`. Uma menção a uma prova não confirma autenticidade,
  admissibilidade, pertinência ou suficiência.

## Camadas que devem convergir

1. **Factual:** texto visível/OCR e descrição de imagem, com âncora por página.
2. **Processual:** peça, evento, decisão, pedido, cumprimento, prazo e fase.
3. **Probatória:** origem declarada, conteúdo, integridade aparente,
   impugnação, nexo e lacunas; não atestar autenticidade sem perícia.
4. **Jurídica:** questão, norma vigente, requisitos, subsunção, efeitos,
   exceções, nulidades, prescrição/decadência e jurisprudência pertinente.
5. **Estratégica:** riscos e alternativas proporcionais às fontes, sempre como
   sugestões revisáveis, nunca como ordem de protocolo.

## Construção da tese

Para cada controvérsia, produza nesta ordem:

1. premissas fáticas e alegações, sem resolver conflitos silenciosamente;
2. questão jurídica ligada ao pedido ou à consequência processual;
3. base constitucional, legal, regulamentar, local e jurisprudencial;
4. subsunção de cada requisito aos fatos e às provas com fonte;
5. melhor argumento adverso, impugnações e risco de prova;
6. conclusão calibrada e providência/pedido confirmado.

Se o corpus não sustentar um requisito, escreva `FONTE AUSENTE`, `CONFLITO A
CONFERIR` ou `DEFINIR PEDIDOS`. Não complete por plausibilidade.

## Pesquisa oficial ampla

A classificação automática apenas encaminha a pesquisa. Teste áreas concorrentes
e procure normas processuais, constitucionais, especiais, locais e
regulamentares que possam alterar o resultado. Priorize Planalto/Diário Oficial,
portal do tribunal ou órgão competente, STF, STJ, TST, TSE, STM, TRFs/TRTs/TJs,
CNJ e reguladores.

Para cada fonte externa, registre URL, título, dispositivo, jurisdição, data de
acesso, redação vigente, revogação/alteração e pertinência ao fato. Mantenha
`candidate_unverified` até conferir vigência, hierarquia, competência e direito
intertemporal. Jurisprudência citada no processo não é precedente validado;
confirme tribunal, órgão, processo, data, tese e distinções no repositório
oficial.

## Conflitos e conclusão

Quando duas peças trazem datas, valores, partes ou versões diferentes, mantenha
as duas fontes, descreva a divergência e explique como ela afeta a tese. Não
declare completude ou conclusão final quando `quality_gate` estiver em
`review_required`. A minuta deve ser marcada **RASCUNHO — NÃO PROTOCOLAR** e
revisada por profissional habilitado.
