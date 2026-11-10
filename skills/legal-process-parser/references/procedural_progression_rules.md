# Regras para andamento processual e peças de trabalho

## Princípio de proveniência

Todo evento, prazo, documento, prova ou sugestão deve apontar para pdf_page,
court_page quando disponível, piece, document_id e uma âncora legível.
Quando a fonte não for suficiente, use needs_review, unknown ou not_assessed;
nunca complete o valor por plausibilidade.

## Peças geradas

O pipeline gera os seguintes artefatos derivados:

- andamento_processual.json: contrato estruturado de eventos, prazos, evidências,
  pendências e tarefas;
- relatorio_andamento.md: estado atual e fila de próximas conferências;
- pendencias_e_prazos.md: marcos encontrados sem calcular vencimento;
- matriz_documental.md: segmentos, páginas e status técnico;
- mapa_provas.md: menções documentais, sem conclusão de suficiência;
- checklist_manifestacao.md: itens a revisar antes de uma manifestação;
- minuta_peca.md: esqueleto de trabalho com fatos e pedidos em aberto;
- relatorio_conformidade.md: controles de cobertura e limitações.

## Limites jurídicos

Datas são apenas ocorrências textuais até que o profissional confirme seu
significado. O parser não aplica feriados, suspensões, intimações presumidas ou
regras de contagem sem parâmetros fornecidos. Uma menção a “prova” não confirma
autenticidade, admissibilidade, pertinência ou suficiência. Uma minuta nunca é
pronta para protocolo e não deve inserir fundamentos ou pedidos ausentes dos autos.

## Conferência de prazos

Antes de confirmar um vencimento, identifique e registre separadamente:

1. ato que abriu o prazo, destinatário e fonte que comprova a ciência;
2. forma de comunicação, data e eventual regra especial de início;
3. natureza do prazo e método de contagem, conforme o ramo e o rito;
4. calendário e expediente do órgão competente para o período;
5. suspensões, feriados, indisponibilidades e prorrogações oficialmente
   publicadas, se aplicáveis;
6. passos completos do cálculo, dispositivo vigente e resultado, com uma
   conferência independente da contagem.

Não use a data da decisão, do protocolo ou da publicação como termo inicial sem
confirmar a regra aplicável e o ato de comunicação. Uma data calculada só pode
ser registrada como confirmada quando o termo inicial, o calendário e as
suspensões pertinentes estiverem sustentados por fonte verificável. Caso
contrário, registre o próximo dado necessário e as questões que dependem dele.
Calendário nacional não substitui o expediente oficial do órgão competente.

Os arts. 219, 220, 224 e 231 do CPC são exemplos das regras de contagem e início
no procedimento civil comum; não se aplicam automaticamente a todo prazo,
ramo, rito, prazo material, audiência ou regime especial. Confirme texto
vigente, especialidade e exceções antes de usá-los.

## Revisão recomendada

1. resolver páginas PARTIAL e descrições visuais pendentes;
2. conferir número do processo, partes, peça, data e folha;
3. validar cada evento e distinguir data do documento de data do fato;
4. calcular prazos somente com marco, calendário e regra aplicável;
5. aprovar fatos, provas, pedidos e responsáveis;
6. só então adaptar a minuta para o formato exigido pelo órgão competente.
