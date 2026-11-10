# Pendências, recuperação e estado da entrega

Use este protocolo em análise, petição ou auditoria quando um controle indicar
`review_required` ou uma questão permanecer sem resposta segura. A pendência
precisa indicar causa e efeito, não apenas um código genérico.

## Unidade de decisão

Avalie separadamente cada questão jurídica e cada entrega solicitada. Relacione
fontes, fatos, requisitos, normas, contrapontos, pedidos e parágrafos. Registre
uma pendência com identificador, categoria, gravidade, escopo, itens afetados,
descrição, impacto, ação necessária, tentativas e resolução. Não use um único
estado global para concluir que todas as questões estão inconclusivas.

`analysis_status: concluded` admite conclusão favorável, desfavorável ou de
insuficiência fundamentada para determinada tese. `qualified` exige condição
e limite claros. `undetermined` identifica a informação decisiva ausente.
`draft_status` distingue peça pronta para revisão profissional, parcial e
bloqueada. `technical_status: passed` verifica apenas os controles técnicos;
`professional_review_status: reviewed` só pode constar se essa revisão ocorreu.

Uma pendência editorial não bloqueia conclusão jurídica. Citação inexistente
restringe a afirmação que depende dela; fonte normativa não consultada afeta
as questões que dependem daquela norma. Falha de integridade que compromete o
corpus impede declarar cobertura integral. Marcar `accepted_limitation` não
transforma uma lacuna decisiva em prova ou fundamento suficiente.

## Recuperação antes de perguntar

Procure o dado no índice, nas páginas completas, no contexto anterior e
posterior e nos uploads preservados. Para texto ilegível, examine a página
renderizada, OCR ou crop apenas se a ferramenta existir. Confronte texto,
imagem e versões sem escolher silenciosamente uma camada contraditória. Para
fonte jurídica ausente, consulte repositório oficial pertinente; registre
tentativa e limitação se indisponível. Não repita a mesma tentativa sobre a
mesma entrada sem informação nova.

Cada ação realizada deve informar pendência, ferramenta, entradas, resultado
observado e nova evidência. Se depender da visão ou pesquisa da IA hospedeira,
execute essa análise quando disponível; o script não deve marcar a ação como
realizada por mera intenção. Pergunte ao usuário somente sobre dado
indispensável que não foi encontrado depois dessas buscas.

## Saída útil

Entregue as questões sustentadas. Para as demais, apresente conclusão
condicionada ou explique precisamente por que não foi possível concluí-las.
Uma peça com lacuna em tese central deve dizer **MINUTA PARCIAL — RASCUNHO —
NÃO PROTOCOLAR** e destacar os trechos afetados. Não preencha uma lacuna com
afirmação plausível. A necessidade de revisão profissional aplica-se inclusive
às conclusões sustentadas, sem rebaixá-las automaticamente a `undetermined`.
