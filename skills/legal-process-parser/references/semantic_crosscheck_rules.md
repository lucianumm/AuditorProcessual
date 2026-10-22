# Conferência semântica e controle adversarial

Leia este guia em análise, petição e auditoria jurídica. Use o índice para
localizar páginas; ele não substitui leitura integral.

## Leitura sem cortes

Para a conferência página a página, obtenha uma página integral por chamada:

    python scripts/case_memory.py saida --offset 0 --limit 1 --full-pages

Avance o offset uma página por vez até next_offset ser null. Repita para todos
os documentos; não use filtro, busca, trecho de 500 caracteres ou resumo como
substituto da leitura. Buscas servem para localizar e confrontar informação.
Registre cada página somente depois de examinar o conteúdo completo que está
realmente acessível. Páginas extensas podem exigir partição por passagem com
intervalos e citações preservados.

Se uma página não puder ser recuperada, declare a página e a camada ausente.
Quando texto e imagem forem relevantes, compare os dois; OCR, imagem e busca
são camadas de evidência diferentes. Não infira que uma página foi lida só
porque consta em reviewed_pages ou page_reviews.

## Registro de fatos e conflitos

Decomponha fatos em proposições localizáveis e identifique para cada uma:

- quem praticou ou relata a ação;
- o evento, objeto, obrigação e pessoas envolvidos;
- quando ocorreu, período, valor e unidade quando existirem;
- se a fonte relata uma alegação, registra um documento, decide uma questão ou
  sustenta uma inferência;
- a fonte exata e outras fontes que confirmam, qualificam ou contradizem.

Compare separadamente atores, datas, sequência de eventos, valores, períodos,
pagamento integral ou parcial, identificadores, nomes e polaridade. Uma
paráfrase contrária pode contradizer a fonte mesmo quando não repete suas
palavras. Verifique também fatos desfavoráveis e requisitos que não foram
demonstrados; não tente tornar o conjunto coerente por escolha silenciosa de
uma fonte.

Para cada conflito material, registre as duas proposições e as referências,
explique se a divergência é real, resolvida por contexto ou permanece em
aberto, e diga qual questão, afirmação ou pedido ela afeta. Conclusões
independentes continuam disponíveis quando não dependem da informação
controvertida. Sem base para resolver, mantenha a divergência e delimite o
efeito.

## Teste de cada questão jurídica

Para cada elemento de fato e requisito:

1. Localize a fonte primária e a passagem completa. Verifique sujeito,
   destinatário, período, condição e ressalvas em torno do trecho citado.
2. Distinga a existência de uma menção probatória da força, pertinência,
   admissibilidade e autenticidade que ainda precisem ser examinadas.
3. Relacione o fato controvertido, o ônus e padrão de prova aplicáveis, os
   documentos que o sustentam e os que o enfraquecem.
4. Verifique texto legal e redação vigente à época relevante. Preserve texto
   riscado, acrescentado, revogado ou sujeito a vigência posterior como
   versões distintas; não os trate como regra simultânea.
5. Confronte a hipótese com cada requisito, exceção e consequência da norma.
   Confirme jurisdição, competência, rito e precedentes aplicáveis, contrários
   e favoráveis.
6. Leia uma versão adversarial da conclusão: qual fato, exceção, distinção,
   condição processual ou fundamento autônomo a invalidaria?
7. Ajuste a conclusão e o pedido à força restante das fontes. Identifique o
   elo não demonstrado e limite a pendência à questão que depende dele.

Não se declare uma checagem independente por repetir a mesma inferência. Se não
houver revisor distinto, registre que a conferência adversarial foi realizada
pelo mesmo modelo. Os controles automáticos verificam dados, formato e
ligações declaradas; não provam que uma paráfrase decorre da fonte nem que uma
interpretação jurídica está correta.

## Peça e estratégia

Identifique a medida específica a partir do ato, prazo, polo, órgão, rito e
resultado buscado. Teste pressupostos, interesse, competência, admissibilidade,
preclusão, preparo e forma apenas quando pertinentes à medida. Separe
recomendação de medida, pedido de minuta e autorização de protocolo.

Nas contestações, confronte os pedidos e fundamentos da inicial. Em réplicas,
trate as defesas e provas novas. Em recursos, confronte cada fundamento
autônomo da decisão, sem confundir nome genérico da família do recurso com sua
espécie e cabimento. Para outras peças, carregue o perfil específico do rito e
do ato processual. Não presuma que a classificação por palavras isoladas
escolheu a peça.

Para analogia ou aplicação de regra de outro regime, identifique a autorização
legal ou lacuna, a função normativa, semelhanças e diferenças, compatibilidade,
limites de legalidade estrita, precedente contrário e efeito exato. Uma tese
cuja premissa normativa foi rejeitada não pode permanecer como tese ativa
fundada naquela aplicação. Identifique propostas novas como interpretação
proposta, sem apresentá-las como direito assentado.

## Saída e medidas de qualidade

A narrativa da petição inicial é afirmativa e se dirige ao juízo na voz da
parte. A linguagem não transforma alegação em fato judicialmente provado:
preserve a natureza da proposição e a relação com a fonte na análise
estruturada e redija os limites factuais com precisão.

Mantenha a peça em prosa legível, com referências curtas a documento, evento,
página e folha. Guarde hashes, identificadores técnicos e justificativas
analíticas no índice ou relatório interno. Após cada revisão, confronte
afirmações, fundamentos, datas, valores e pedidos entre a análise e a minuta.

Uma validação técnica aprovada significa apenas que os controles executados
foram satisfeitos. Não a rotule como confirmação automática de mérito,
incidência normativa, autoria, autenticidade ou suficiência de prova.
