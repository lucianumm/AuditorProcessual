# Identificação da medida e da peça processual

Leia este guia em análise e redação de peça. Reconheça separadamente o documento
que está nos autos e a providência juridicamente cabível agora. O título, a
etiqueta do sistema e palavras isoladas são indícios; confirme a função, o
conteúdo e a posição temporal do ato no processo.

## Decisão de cabimento

Construa a decisão a partir do que consta nos autos e do objetivo do usuário:

1. Identifique processo, órgão, competência, rito, fase, polo representado e
   relações com processos conexos. Se a área for híbrida, preserve as áreas
   concorrentes e explique qual regra rege cada questão.
2. Identifique o ato que exige providência, sua data, forma de comunicação,
   destinatário, conteúdo decisório, fundamentos autônomos e efeito prático.
   Separe data de assinatura, publicação, disponibilização, ciência e início de
   prazo; use somente o marco confirmado pela regra aplicável.
3. Defina o resultado pretendido com base no pedido. Não converta análise em
   autorização para redigir ou protocolar peça não solicitada.
4. Compare medidas plausíveis pelo cabimento, legitimidade, interesse,
   competência, rito, prazo, preparo, requisito formal, preclusão e adequação do
   resultado. Examine requisitos somente quando forem pertinentes à medida.
5. Escolha a medida e o nome específico da peça. Registre também alternativas
   plausíveis afastadas e o motivo concreto. Se não houver ato ou medida
   imediata demonstrável, registre `no_immediate_action`; não invente urgência.
6. Vincule cada conclusão aos fatos, atos, normas e fontes usados. Declare
   dúvida decisiva com escopo e efeito; continue as questões independentes.

## Contrato em `legal_review.json` v3

Preencha `piece_assessment` em análise, auditoria jurídica e petição. Inclua:

- `status`: `selected`, `no_immediate_action`, `needs_material_information`
  ou `outside_scope`;
- fase, ato desencadeador, polo, objetivo e nome exato da medida recomendada;
- justificativa sucinta e alternativas afastadas;
- requisitos de cabimento e admissibilidade, cada qual com estado, razão e IDs
  de fatos/normas que o sustentam;
- prazo como data ou condição somente quando o marco, a regra, o calendário e
  a forma de contagem estiverem confirmados; caso contrário, registre o dado
  preciso que falta.

Na tarefa `petition`, alinhe `piece_assessment.selected_piece` e
`drafted_piece_type` ao campo técnico `piece_type`. A taxonomia técnica agrupa
famílias (como `recurso`); `selected_piece` preserva o nome processual exato
(como o tipo de recurso efetivamente cabível). Uma família não substitui o
exame do recurso específico.

Se o usuário pediu somente análise, recomende a providência sem produzir a
minuta. Pergunte apenas se a informação material não puder ser localizada nos
autos, índices ou contexto disponível.
