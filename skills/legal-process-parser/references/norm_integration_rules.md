# Aplicação integrada de normas e analogia

Use este protocolo por questão jurídica para distinguir incidência direta,
remissão, aplicação subsidiária/supletiva, analogia e interpretação sistemática.
Consulte a redação oficial vigente no período dos fatos e a regra própria do
ramo, rito, órgão e etapa antes de escolher uma técnica de integração.

## Teste de incidência

Para cada questão, identifique a norma especial e as regras de competência,
hierarquia, âmbito material, territorial e temporal. Classifique cada norma
invocada como incidência direta, remissão expressa, complemento supletivo,
aplicação subsidiária, integração por analogia, interpretação sistemática ou
afastada. Mostre como a norma resolve os elementos da questão.

Não presuma uma lacuna só porque o resultado da regra específica é desfavorável.
Investigue se existe silêncio juridicamente relevante, disciplina parcial,
remissão, conflito ou vedação expressa. Distinga lacuna normativa de ausência
de prova e de mera divergência interpretativa.

## Teste reforçado de aplicação subsidiária, supletiva ou analógica

Antes de importar regra de outro código, legislação ou ramo, registre:

1. a questão concreta e o regime especial que a governa;
2. a norma de integração ou remissão que autoriza o uso, ou a lacuna juridicamente
   reconhecida que o exige;
3. o instituto de origem e sua função normativa;
4. as semelhanças juridicamente relevantes entre a hipótese regulada e o caso;
5. as diferenças, limites, exceções e consequências que tornam a analogia
   inadequada ou apenas parcial;
6. a compatibilidade com texto especial, finalidade, princípios e estrutura do
   processo/regime de destino;
7. precedentes vinculantes, persuasivos e contrários, com estado atual e
   distinções factuais;
8. o efeito específico sobre o requisito, tese, prazo, prova e pedido.

Em matéria sujeita a legalidade estrita, não crie obrigação, infração,
penalidade, tributo, competência ou restrição por analogia. Verifique ainda
limites explícitos de interpretação e integração próprios do ramo. Por exemplo,
o [CTN, art. 108, §§ 1º e 2º](https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm)
estabelece limites expressos ao resultado da analogia e da equidade, e o
art. 111 especifica hipóteses de interpretação literal. Não transplante a
solução de uma área para outra sem testar sua autorização e compatibilidade.

### Exemplos oficiais de técnicas diferentes

Use-os apenas para classificar o método; confirme sempre a redação vigente e o
regime do caso concreto:

- [LINDB, arts. 4º e 5º](https://www.planalto.gov.br/ccivil_03/decreto-lei/del4657compilado.htm):
  analogia diante de omissão e interpretação conforme fins sociais e bem comum.
- [CPC, art. 15](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm):
  aplicação supletiva e subsidiária em processos eleitorais, trabalhistas e
  administrativos na ausência de normas que os regulem.
- [CLT, art. 8º, § 1º](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm):
  direito comum como fonte subsidiária do direito do trabalho; analise o alcance
  material da remissão, sem confundi-lo com integração processual.
- [CLT, arts. 769 e 889](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm):
  integração processual em contextos delimitados por omissão e compatibilidade,
  e regras próprias para trâmites e incidentes da execução.

O rótulo “subsidiário” não basta para transportar artigo de um código: delimite
se a regra de destino alcança direito material, procedimento, execução ou
somente ponto específico. Separe a norma que autoriza a integração da regra
emprestada que pretende aplicar.

## Registro estruturado

Na revisão v3, use `norm_applications`, uma entrada por relação relevante entre
questão e norma. `method` identifica a técnica; `basis_for_use` explica a
autorização ou incidência; `gap_or_remission` descreve omissão, disciplina
parcial ou remissão; `similarities` e `differences` justificam a comparação;
`compatibility_analysis`, `limits_and_contrary_authorities`, `temporal_fit` e
`result` demonstram o alcance da conclusão. Para incidência direta, explique
por que a norma governa a questão e registre os demais campos como não
aplicáveis com justificativa concreta, sem simular uma lacuna.

Toda tese por analogia deve apontar para a entrada correspondente em
`norm_applications`. Identifique-a como proposta interpretativa, salvo se a
fonte oficial comprovar entendimento consolidado. Não invente suporte
jurisprudencial nem apresente inovação como precedente assentado.
