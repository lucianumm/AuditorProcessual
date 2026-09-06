# Narrativa jurídica afirmativa e fundamentação verificável

## Finalidade

Depois de representar todo o corpus, escreva como uma análise jurídica
profissional: apresente os fatos relevantes, identifique a fonte que os contém,
aplique a norma vigente ao conjunto probatório e desenvolva a tese solicitada.
O texto deve dizer o que ocorreu, o que cada parte sustenta, o que a prova
registra e o que a decisão determinou. Não descreva o ato mecânico de ler ou
auditar arquivos.

O estilo profissional não autoriza a IA a se declarar advogada, substituir a
decisão judicial, atestar autenticidade pericial ou protocolar uma peça. Toda
minuta permanece rascunho e precisa de revisão por profissional habilitado.

## Linguagem obrigatória

Cada parágrafo factual deve conter uma âncora que permita voltar ao corpus:

`[Peça | PDF p. N | fl. M | document_id: ID]`

Use `fl. M` somente quando a folha dos autos estiver identificada. Quando a
fonte for uma imagem, acrescente `image_id` e descreva apenas o que é visível ou
transcrito. Quando o texto não permitir afirmação segura, escreva a limitação
de modo direto: `A PDF p. N permanece ilegível; não é possível afirmar o seu
conteúdo sem OCR ou revisão visual.`

Classifique a proposição no próprio texto ou em metadado: `fato_documentado`,
`alegacao`, `prova_registrada`, `decisao`, `inferência` ou `lacuna`. A categoria
não substitui a análise de suficiência, autenticidade, pertinência ou valor
probante.

## Formulações proibidas como preenchimento

Não use, como introdução genérica ou conclusão sem fonte, expressões como
“conforme documentação”, “conforme documentos”, “documento apresentado”,
“certidão analisada”, “foi analisado”, “a documentação demonstra” ou “consta dos
autos” sem indicar peça, página, folha e document_id. Também não diga que um
arquivo “comprova” um fato quando a fonte apenas o menciona.

O problema não é a palavra documento em si. Ela pode ser usada quando o texto
identifica a peça e o seu conteúdo: `O contrato de 12/03/2024 registra a jornada
descrita na cláusula 4 (Contrato | PDF p. 18 | document_id: abc123).`

## Padrões de redação

Prefira construções afirmativas, sempre com a qualificação correta:

- `A petição inicial sustenta que ... (Petição Inicial | PDF p. 3 | document_id: ID).`
- `O contrato registra ... (Contrato | PDF p. 12 | fl. 8 | document_id: ID).`
- `O laudo descreve ...; a conclusão técnica nele contida é ... (Laudo/Perícia | PDF p. 27 | document_id: ID).`
- `A sentença determinou ... (Sentença | PDF p. 47 | document_id: ID).`
- `O extrato contém os lançamentos ... (Documento Financeiro | PDF p. 9 | document_id: ID).`
- `Não foi localizado, nas páginas representadas, o comprovante referido na decisão (Decisão | PDF p. 22 | document_id: ID).`

Não transforme alegação em fato: use `a parte sustenta`, `a defesa afirma` ou
`a decisão registra a alegação`. Não transforme uma menção em prova suficiente:
use `a peça menciona`, `o registro contém` ou `a prova localizada apresenta`,
seguido da análise de pertinência e suficiência.

## Estrutura da análise e da tese

Para cada questão relevante, siga esta sequência:

1. **Premissas fáticas:** fatos, alegações, provas e decisões, cada qual com
   fonte direta e sem apagar conflitos entre páginas.
2. **Questão jurídica:** formule a pergunta que precisa ser respondida e
   identifique o pedido ou consequência processual a que ela se conecta.
3. **Regra aplicável:** indique Constituição, lei, decreto, regulamento, ato
   normativo e precedente potencialmente pertinentes; só chame de aplicável ou
   cite artigo depois de conferir a fonte oficial vigente.
4. **Subsunção:** compare cada requisito da regra com fatos e provas citados,
   apontando o que está preenchido, o que falta e o que permanece controvertido.
5. **Contrapontos:** apresente a melhor versão dos argumentos adversos,
   impugnações, nulidades, prescrição/decadência e riscos de prova quando
   houver suporte no corpus.
6. **Conclusão e providência:** formule a tese de maneira proporcional ao grau
   de prova e indique pedidos somente quando confirmados pelo usuário ou pelos
   autos. Lacunas viram pedidos de esclarecimento ou campos `DEFINIR`, nunca
   conteúdo inventado.

## Pesquisa normativa ampla

1. Use a classificação apenas para encaminhar a pesquisa. Releia o corpus e
   teste áreas concorrentes, normas processuais, constitucionais, especiais,
   locais e regulamentares que possam alterar a solução.
2. Priorize o texto oficial: Planalto/Diário Oficial, portal do tribunal ou
   órgão competente, STF, STJ, TST, TSE, STM, TRFs/TRTs/TJs, CNJ e reguladores.
   Registre URL, título, dispositivo, jurisdição, data de acesso, redação
   vigente e eventual revogação. Não complete artigo ou precedente pela memória.
3. Separe `candidate_unverified` de `verified`. Uma fonte só pode sustentar a
   tese depois de conferidos vigência, competência, hierarquia, direito
   intertemporal, legislação especial/local e aderência aos fatos.
4. Pesquise jurisprudência em repositório oficial quando ela for necessária;
   registre tribunal, órgão julgador, processo, data, tese efetivamente adotada
   e distinções. Citação encontrada no processo não é precedente validado.
5. Se não houver acesso à fonte externa, declare a limitação e mantenha a
   norma como pendente. A análise pode organizar a questão e a tese possível,
   mas não deve apresentar fundamento não verificado como direito vigente.

Ao verificar uma fonte, atualize o registro em `legal_basis.json` ou em uma
seção equivalente da análise com `verification_status: verified`, URL, data de
acesso, dispositivo conferido e observação de vigência. Preserve a entrada
candidata anterior e o histórico da pesquisa; uma nova versão dos autos não
autoriza apagar a fundamentação ou as fontes de versões anteriores.

## Revisão de qualidade

Antes de entregar, verifique: todas as páginas e imagens relevantes estão
representadas; cada parágrafo factual tem fonte; conflitos estão explícitos;
cada norma tem estado de verificação; a tese percorre fatos–provas–normas–
subsunção–contrapontos–pedido; e nenhuma conclusão excede o `quality_gate`.
