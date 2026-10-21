# Especialização trabalhista

Use quando a questão for de trabalho. Selecione temas em labor_topics.json
e leia só os guias pertinentes. A primeira análise integral continua cobrindo
todas as páginas, imagens relevantes e contextos dos uploads. Busca localiza.

Toda resposta jurídica substancial segue response_research_rules.md: consulta
oficial nova na questão e período, conferência de requisitos/exceções, tese
contrária e consequências. Capítulo escolhido e consolidação têm conferência
própria. Fonte preservada e cálculo correto não certificam incidência jurídica.

Atendimento com poucos ou nenhum anexo é fluxo principal: ler labor_intake_rules.md.
Desenvolver pretensões com labor_development_rules.md. Escolher pretensões pelo
índice labor_claims_index.md e abrir só as entradas escolhidas de labor_claims.json:
cada uma traz teses do trabalhador e da defesa, autoridades candidatas
(labor_authorities.json), marcos temporais, pedidos, prova e pautas de cálculo.
Autoridade do catálogo é candidata até a conferência da resposta atual
(citation_verification_rules.md). Selecionar labor_sectors.json pelos fatos e
carregar só o guia setorial pertinente. No JSON, workflow distingue informação
recebida, possibilidade de redigir, prova futura e lacuna material. Esses
registros não exigem consulta a outra IA nem leitura de todos os roteiros.

## Marcos temporais obrigatórios

Antes de qualquer tese, situar os fatos em relação aos marcos de
labor_authorities.json (temporal_markers), entre eles:
- 11/11/2017: Lei 13.467/2017; aplicação imediata aos contratos em curso para
  fatos a partir dessa data (IRR Tema 23 do TST);
- 30/06/2025: Res. 225/2025 do TST cancelou súmulas e OJs superadas (90, 228,
  366, 437, 444, 450, OJ 355; partes das Súmulas 6 e 331), com efeitos ligados
  aos fatos anteriores conforme o caso;
- 30/08/2024: atualização e juros pela Lei 14.905/2024 (ADC 58 e SDI-1);
- 16/10/2026: EC 141/2026 (art. 7º, XIII e XV da CF): 42 horas semanais e 2 dias
  de repouso dois meses após a publicação, 40 horas um ano depois; cláusulas
  coletivas incompatíveis perdem efeito; exclusão de hipersuficientes do controle
  de jornada. Divisores, limites e reflexos baseados em 44 horas exigem
  decomposição por período e conferência da contagem dos prazos.

## Relação, sujeitos e períodos

Identifique polo representado, empregadores, tomadores, estabelecimentos,
categoria, território, atividades efetivas e forma de contratação. Atribua
chaves estáveis a cada relação e sujeito para impedir cruzamento de pessoas,
empresas ou competências. Nome comercial e CNPJ podem exigir reconciliação.

Confirme a distinção entre regime jurídico, modalidade e categoria: CLT,
doméstico, rural, temporário, aprendizagem, estágio, trabalho autônomo,
contratação por pessoa jurídica e emprego público. Teletrabalho, intermitência,
prazo determinado e categorias especiais exigem seus requisitos próprios.
Servidor estatutário exige análise da legislação e competência correspondentes.
Empregado de banco exige examinar o objeto do pedido antes de escolher entre
emprego e produto bancário. Registro de PJ não resolve sozinho vínculo/fraude.

Reconstrua admissão, funções, evolução remuneratória, jornadas, afastamentos,
mudanças e ruptura em contract_periods. Decomponha períodos quando o regime,
lei, cláusula ou base de cálculo mudar. Confira redação por período efetivo,
reconferindo marcos nas afirmações atômicas e na fonte original. Término não
delimitado e contrato em curso exigem tratamento contextual, sem inventar data.

Confira prescrição por pretensão e marcos efetivos, inclusive projeções,
interrupções, suspensões e exceções pertinentes. Pagamento parcial, verbas de
outra competência e quitação com alcance limitado têm efeitos distintos.
Em ruptura, examinar espécie, requisitos, condutas, prova adversa, verbas e
consequências. Garantias exigem fato gerador, período, requisitos e providência.

Grupo, sucessão, terceirização e sócios exigem fundamentos e prova próprios.
Identifique participação no processo e limites da fase. Para tomador público,
confira os precedentes e o encargo probatório específicos antes da tese.

## Questões e tese

Em análise integral, avaliar ou excluir com motivo os temas do catálogo. Em
consulta pontual, selecionar só os temas do pedido e dependências necessárias.
Cada topic_assessment liga questão, períodos, fatos, normas e pedidos; cobre
os checks do tema, ônus, pesquisa, objeção mais forte, resposta e motivo da
seleção. Um direito possível é candidato até confirmar seus requisitos.

Pesquisar Constituição, CLT, leis especiais, fontes coletivas, SST, atos locais,
precedentes e normas de integração pertinentes. Registrar fontes contrárias,
versões históricas e limites. Verificar ratificação, vigência, âmbito e ato
interno ao usar convenção internacional; consultar NORMLEX quando útil e
o ato brasileiro correspondente. O registro
international_checks relaciona instrumento, situação, marcos e atos brasileiros;
instrumento sem vigência confirmada não sustenta aplicação direta consolidada.
Analogia e subsidiariedade seguem
norm_integration_rules.md, com autorização, lacuna e compatibilidade próprias
do direito material, conhecimento ou execução trabalhista.

Antes de usar jurisprudência, conferir STF, TST e TRT competente pelo inteiro
teor e situação do tema: tese firmada, afetação, revisão, cancelamento,
suspensão, alcance e modulação. Notícia/ementa aponta a pesquisa; preserve o
fundamento efetivamente observado. O status de tema sobre pejotização,
terceirização ou negociação coletiva deve ser verificado na data da análise.

Na inicial, narrar fatos afirmativamente na voz da parte, com referências
diretas, atendendo initial_petition_rules.md. Preservar origem do relato e
necessidade probatória no registro; enfrentar documentos adversos e tratar
conflitos fielmente. Defesa e recurso atendem seus fundamentos. Conferir tese
sem pedido, pedido sem requisito, cumulações, reflexos, valores e alternativas.

## Registro e continuidade

Na revisão v4 trabalhista, preencher labor_review conforme
schemas/labor_review.schema.json ao produzir o JSON. Papéis:
relationships, contract_periods, collective_instruments,
topic_assessments, evidence_checks, health_assessments,
procedure_reviews e calculation_scope. O esquema não marca compreensão.

scope.mode integral exige seleção ou afastamento de todos os temas;
targeted limita a questão solicitada. Informações ausentes, divergências ou
fonte inacessível produzem achados por questão, com providência e efeito.
Continuar a leitura e conclusões independentes, preservando os limites da prova.

Com código, labor_analysis.py revisao.json confere o módulo. A finalização
jurídica gera analise_trabalhista.md, índice e, havendo cálculo, memória
demonstrativa. Novos uploads e fontes alteradas reabrem vínculos atingidos,
preservando originais, versões e relatórios anteriores. Sem código, entregar
os mesmos vínculos em Markdown e registrar os controles não executados.

Fontes de partida, verificadas em cada caso:
[CF](https://www.planalto.gov.br/ccivil_03/constituicao/constituicaocompilado.htm),
[CLT](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm),
[EC 141/2026](https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc141.htm),
[TST](https://www.tst.jus.br/indice-tematico-precedentes-trabalhistas-stf-tst),
[Res. 225/2025 TST](https://juslaboris.tst.jus.br/handle/20.500.12178/251919),
[STF](https://portal.stf.jus.br/jurisprudencia/),
[MTE](https://www.gov.br/trabalho-e-emprego/pt-br),
[NORMLEX](https://normlex.ilo.org/).
