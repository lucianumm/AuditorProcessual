# Protocolo de avaliação jurídica e de plataforma

Casos deste diretório são inteiramente sintéticos. Servem a regressões de código
e comparações observáveis, não a alegações de precisão jurídica em processos reais.
Não publicar autos nem rótulos que contenham dados de clientes. Versão 2 dos
casos pode comparar sujeito, polaridade, alcance, período, valor, fonte/trecho,
regime e peça específica além das métricas lexicais da versão 1.

## Aplicação por profissional

1. Separar conjuntos de desenvolvimento e teste, com casos consentidos e
   anonimizados, cobrindo áreas, ritos, regimes e material visual distintos.
2. Dois revisores jurídicos independentes anotam fatos decisivos, respectivas
   fontes/páginas, prova contrária, marcos, requisitos, autoridades e medida
   cabível antes de ler a resposta do modelo. Resolver divergências por terceiro
   revisor; preservar versões e justificativas dos rótulos.
3. Executar cada caso com instruções e modelo/versionamento registrados. Não usar
   outro provider sem autorização nem enviar conteúdo privado a serviços externos.
4. Medir extração, recuperação, raciocínio e redação separadamente. Contar omissões,
   citações inexistentes, fatos invertidos, norma temporalmente inadequada,
   precedente sem aderência, peça incabível, pedidos incongruentes e falsos bloqueios.
5. Aplicar a rubrica abaixo à revisão e à minuta completas. Erro crítico não pode
   ser diluído numa média. Reportar tamanho/amostragem do conjunto, distribuição
   por área, desacordo entre revisores e intervalos de incerteza; não anunciar
   “100% de acerto” com poucos casos sintéticos.

## Rubrica de 1 a 5

As oito dimensões são `factual_fidelity`, `complete_coverage`,
`legal_temporality`, `precedent_fit`, `procedural_fit`, `thesis_quality`,
`requests_consistency`, `writing_quality`.

1 = erro decisivo/omissão grave; 2 = vários erros materiais; 3 = resultado útil
com correções materiais; 4 = sólido, ajustes delimitados; 5 = conferido e adequado
no escopo avaliado. Se uma dimensão não se aplicar, justificar o critério adotado
nos comentários, sem simular verificação. “5” não garante resultado judicial.

Registro real opcional em `human_review.json`: `schema_version: "1.0"`,
`reviewer`, `reviewer_role`, `reviewed_on` ISO, `review_sha256` (SHA-256 dos bytes
de `legal_review.json`), `dimensions` com as oito notas, `critical_errors` (lista),
`comments`. Não distribuir registro preenchido fingindo avaliação profissional.
O avaliador aceita `--human-review` e confere o vínculo ao arquivo; não atesta
identidade, habilitação ou verdade das notas. Sem registro, `not_recorded`.

## Compatibilidade por plataforma

labor_workflow_cases.json contém 40 cenários de consistência observável e dez
fluxos integrais sintéticos. Testes executam atendimento sem documentos, redação
com prova futura, integridade de relatos, conciliação, marcos, capítulos e roteiros.
Fixtures não são respostas de modelo nem rótulos de mérito jurídico profissional.
A revisão independente e comparação com saída real do PJe-Calc permanecem
etapas de avaliação próprias, com materiais e registros reais.

O conjunto trabalhista inclui períodos contratuais, âmbito coletivo incorreto,
jornada noturna, cálculo e abatimento, categoria bancária, recurso de revista,
prova médica insuficiente e limites do título. Os rótulos e documentos são
sintéticos. labor_observable_accuracy compara seleção e estados registrados;
labor_calculation_total_correct compara o total de referência do cenário.
Essas métricas não medem desempenho jurídico de um modelo em autos reais.

Para avaliação trabalhista profissional, anotar também norma coletiva por
período/categoria, regime, rubrica, base, reflexos, pagamentos, ônus, pressupostos
recursais, nexo e limites do título. Conferir as contas com saída real do
PJe-Calc ou outra referência apropriada, preservando arquivo, versão, tabelas
e hash. Não reutilizar o conjunto de desenvolvimento como amostra de teste.

Etapas distintas: pacote bem formado; scripts executados isoladamente; importação
na interface; leitura de texto/visuais; busca oficial com fonte observável; minuta
revisada pelo especialista. `verify_packages.py` cobre apenas as duas primeiras
etapas com cenários sintéticos, sem login, chamadas pagas ou upload de autos.
Registre modelo, interface, data e ferramentas observadas ao testar as demais;
não inferir aprovação no ChatGPT/Claude/Gemini/Manus/Grok só porque o ZIP abriu.
