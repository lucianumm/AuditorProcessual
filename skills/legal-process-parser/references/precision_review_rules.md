# Protocolo de precisão v4

Execute a tarefa pedida, com todos os autos disponíveis quando a análise integral
estiver no escopo. Consulta pontual pode usar índice; não rotular busca como
leitura integral. Identifique área/subárea/regime, polo, órgão, rito, fase, ato,
objetivo e marcos. Pergunte só se um dado indispensável continuar irresolvido
depois de buscá-lo. Não rodar todos os fluxos por padrão.

## Leitura e continuidade

Leia cada página inteira e primeiro sua renderização, quando visualmente
relevante; depois imagens/crops pertinentes. Confira datas, valores, números e
nomes decisivos na imagem se há OCR/digitalização ou divergência. Documento
Office textual não preserva paginação física, imagens, estilos, datas de
planilha ou revisão autoral automaticamente: converter para PDF e revisar quando
tais elementos importarem. Ilegível é diferente de vazio confirmado.

Com execução local, `scripts/case_packet.py saida --offset 0 --max-chars 12000`
entrega intervalos sem truncar o texto. Avance `next_offset` até null mantendo
o orçamento e a revisão constantes; registre recibos por página/camada em
`reading_coverage`. O recibo prova disponibilização, não compreensão: escreva
`page_reviews` somente depois de examinar efetivamente o conteúdo. Sem código,
registre referências observadas nas ferramentas do chat, nunca recibos fictícios.
Capacidades em `execution_context` precisam ter evidência da sessão; o nome da
plataforma não comprova visão, navegação ou persistência.

## Afirmação, prova e narrativa

Cada fato tem `assertion_reviews`: sujeito, ação, objeto, polaridade, alcance,
datas, período, valor/moeda quando relevantes. Confronte os mesmos campos da
fonte exata em `evidence`, indexada a `fact.sources` a partir de zero. Relacione
apoio, contradição e contexto; cite trecho/região e atribua relato, alegação,
decisão ou inferência ao sujeito correto. “Não comprovou o pagamento” não
significa “não pagou”; pagamento parcial não é quitação; outra pessoa, período
ou bem não prova a afirmação. Dados críticos têm `critical_checks`. Não resolver
contradição omitindo a prova adversa. Para conflitos/inferências decisivos,
acionar `semantic_conflict`.

Inicial sempre afirmativa na voz da parte. Isso não permite fabricar confirmação:
preserve relato e limites probatórios no registro de revisão, usando narrativa
adequada ao que a parte sustenta. Proibir “certidão analisada”, “documento
apresentado” e “conforme documentação” na minuta; narrar fatos com referência
direta ao documento/página/folha. Defesa e recurso enfrentam os fundamentos
pertinentes, não reciclam uma inicial. Toda minuta: RASCUNHO — NÃO PROTOCOLAR.

## Normas, precedentes e teses

Pesquisar normas oficiais relevantes de forma ampla, mas focalizada nas questões:
Constituição, códigos gerais/processuais, lei especial, atos locais/coletivos e
regulamentos aplicáveis. `normative_map` registra contexto integral do dispositivo,
requisitos, exceções, consequências, marcos, redação histórica, transições e razão
de incidência. Norma excluída/incerta não sustenta tese consolidada. Captura íntegra
é prova da origem dos bytes, não da interpretação. Acionar `official_research`.

Todo precedente usado tem `precedent_comparisons`: fatos relevantes, fundamento
determinante textual, semelhanças/diferenças, âmbito vinculante, posição favorável
ou adversa, situação atual, suspensão, modulação, superação e limite de uso. Não
usar só ementa/número do tema quando o contexto é decisivo; registrar o que não
foi possível conferir. Teses novas/analógicas são propostas, não direito pacífico.
Acionar `integration` ao integrar regimes, com lacuna/remissão e compatibilidade.

`thesis_reviews` compara prova, base normativa e adequação processual, requisito
por requisito, com a objeção mais forte, resposta, risco residual e motivo da
seleção. Sem porcentagem fictícia de êxito. Principal/subsidiária/alternativa
precisam ser compatíveis entre si e ligadas à mesma questão, provas, aplicações
e pedidos. Escolha peça específica no catálogo (`measure`), ou `custom` com base
oficial e razão; não presumir cabimento por fase ou palavra-chave. Conferir
pressupostos, ato, competência, prazo/preparo e alternativas; não inventar prazo.

## Atualização e saída

Use `legal_review.json` v4 quando produzir revisão estruturada; acione
`local_contract` para consultar o schema ao preenchê-lo. `corpus_revision`
identifica documentos e relações explícitas; `research_revision` identifica
fontes consultadas independentemente de uploads. Mudança de texto oficial
consultado não prova mudança legislativa: comparar capturas e conferir incidência
histórica. Originais, relações e versões são preservados; nenhum upload substitui
a memória silenciosamente. Gere/atualize `relatorio_processual.md`,
`memoria_processual.md` e `indice_juridico.md` com vínculos por página e item.

Execute `legal_review.py saida --review legal_review.json` quando houver código.
Sem código, informe controles não executados. V1–v3 continuam aceitas como
legadas, sem fingir os controles v4. Validação local confere consistência dos
registros da IA; não certifica veracidade, compreensão ou correção jurídica.
Uma lacuna delimitada restringe a conclusão dependente, não interrompe a leitura
nem bloqueia partes independentes. Acione `recovery`; mantenha limitações visíveis
e peça revisão profissional antes de uso judicial.
