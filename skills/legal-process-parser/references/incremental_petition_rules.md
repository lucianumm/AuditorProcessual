# Análise integral e elaboração tese por tese

Use quando o usuário construir a peça por capítulos, continuar uma tese ou
consolidar a petição. Confirme o escopo pelo pedido; análise integral cria a
base e o mapa de candidatos, sem redigir todos os capítulos automaticamente.
Pedido de peça completa continua sendo atendido no escopo solicitado.

Cada resposta jurídica, capítulo e consolidação tem consulta oficial nova,
conforme response_research_rules.md. Preservar a pesquisa anterior como histórico,
sem reutilizar seu recibo como consulta atual. Na execução local, capítulo v2
inclui response_research ligado ao conteúdo exato; sem código, registrar chamada
observável e fontes no Markdown, sem simular o controle local.

## Base comum

Concluir a leitura integral do material recebido, com relatos atribuídos,
cronologia, sujeitos, regime, provas, contradições, questões e pesquisa pertinente.
Registrar hipóteses possíveis e afastadas com motivo. Datas aproximadas não
recebem dia escolhido pela IA; labor_events.py mantém mês, intervalo ou data
desconhecida com o trecho literal do relato. Limites de data não escolhem marco
legal: cálculo e prescrição precisam da hipótese e do fundamento concretos.

Manter relatorio_processual.md como localizador cumulativo e mapa_teses.md
como andamento da elaboração. Identificar o capítulo escolhido, recuperar fatos,
prova contrária, requisitos, norma temporalmente aplicável, pesquisa e pedidos.
Teses dependentes da mesma jornada, salário ou evento compartilham a mesma
informação na análise-base. Alteração de fato decisivo reabre seus dependentes.

## Capítulo escolhido

Desenvolver a tese solicitada e as dependências necessárias. Consultar os guias
da pretensão e setor pertinentes; não carregar todos os roteiros. Pesquisar
fundamentos favoráveis e contrários, comparar o inteiro teor e conferir situação
do precedente. Não exigir outra IA. Analogia/subsidiariedade segue o guia próprio
com lacuna/remissão, compatibilidade, limites e resposta ao contraponto.

Redigir narrativa jurídica na voz da parte. Na inicial, fatos afirmativos;
atribuição do relato e necessidade de prova permanecem nos registros de apoio.
O capítulo desenvolve requisitos, consequência e pedido correspondente.
Exibição, audiência ou perícia decorrem de controvérsia específica: relacionar
quem detém a prova, método, momento, base e alternativa. Falta de documento
não bloqueia automaticamente a redação; lacuna material limita a questão.

Conferir cada parágrafo: sujeito, conduta, polaridade, período, quantidade,
alcance e fonte. Justificar inferências e enfrentar prova contrária. Verificar
se o mesmo parâmetro aparece de maneira compatível nos capítulos já redigidos.
Uma revisão preenchida não comprova suporte semântico: a IA precisa ler e
interpretar o conteúdo. Não inventar percentual de êxito.

## Versões e manifestações do usuário

Estados: identificado no mapa, draft, reviewed, approved ou needs_review.
Salvar versão nova preserva as anteriores e reinicia o estado do capítulo.
approved exige manifestação real do usuário vinculada à versão e à dependência;
a IA não supõe aprovação por silêncio. reviewed registra a conferência efetiva,
sem fingir revisão por especialista. Isso registra o fluxo, não impõe perguntas
ou aprovação obrigatória para cada resposta de chat.

Novo upload ou fonte alterada sinaliza análise-base pendente. Reexaminar o
material novo, atualizar a análise e comparar dependências. Somente capítulos
com dependências alteradas recebem needs_review; versões e manifestações
anteriores permanecem preservadas. A peça consolidada anterior é identificada
como desatualizada. Fontes novas podem exigir reavaliação mesmo sem mudar fatos.

## Consolidação solicitada

Reunir os capítulos na ordem escolhida somente quando solicitado. Conferir
qualificações, competência, cronologia, valores, hipóteses subsidiárias,
duplicação de pedidos, fundamentos incompatíveis, pedidos sem desenvolvimento
e capítulos ausentes. Consolidação parcial identifica o escopo e pedidos ainda
não abrangidos. Rascunhos podem ser reunidos quando o usuário solicitar, sem
atribuir aprovação inexistente; revisão final permanece distinta da montagem.

## Execução local opcional

    python scripts/petition_workspace.py saida init --review analise.json
    python scripts/petition_workspace.py saida context --issue I1
    python scripts/petition_workspace.py saida save --chapter-file capitulo.json
    python scripts/petition_workspace.py saida review --chapter horas-extras --reference "referência da revisão efetiva"
    python scripts/petition_workspace.py saida approve --chapter horas-extras --reference "manifestação real do usuário"
    python scripts/petition_workspace.py saida refresh --review analise_atualizada.json
    python scripts/petition_workspace.py saida preview --chapter horas-extras --chapter fgts --save-preview consolidacao_preview.json
    python scripts/petition_workspace.py saida assemble --chapter horas-extras --chapter fgts --research-response saida/response_research/consolidacao-001/response.json

--allow-drafts na consolidação registra a reunião de rascunhos; não altera seus
estados. Antes de save, preencher e vincular a pesquisa do capítulo; entre
preview e assemble, iniciar consulta própria da consolidação, conferir os
fundamentos e usar bind com --artifact apontando ao preview. Se fonte/corpus
mudar, reanalisar e refresh antes de salvar/montar; gerar novo preview após
qualquer mudança do conteúdo. local_response_workflow.md mostra
os comandos completos. O schema petition_chapter.schema.json é carregado
somente ao preencher esse JSON. Sem código, manter os mesmos vínculos,
estados e versões em Markdown.
O arquivo cumulativo permite retomar mediante acesso ou fornecimento da última
versão; não prometer memória permanente de uma plataforma.

O contexto local é exportado em lotes --offset/--max-chars. Avançar até
next_offset null, usando --expected-revision na continuação. Cada parágrafo
factual declara assertions com campos reconferidos na análise-base. O validador
detecta divergências nos campos declarados e algumas inversões de negação;
não prova que todas as afirmações da prosa foram identificadas ou sustentadas.
