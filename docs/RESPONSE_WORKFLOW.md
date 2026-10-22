# Pesquisa oficial por resposta — v0.21.0

Na v0.21.0, cada citação é conferida na fonte consultada: o dispositivo precisa
existir, o trecho precisa estar dentro dele e fora de redação riscada, e as marcas
"(Revogado…)", "(Redação dada…)", "(Incluído…)" e "(Vide ADI…)" são comparadas com
as datas dos fatos. Portais que recusam clientes automatizados (TST, STF, LexML,
Mediador, OIT) são registrados como bloqueio, nunca como consulta. Comandos
`response_research.py verify` e `unavailable`; regras em
[conferência de citações](../skills/legal-process-parser/references/citation_verification_rules.md).

Desde a v0.20.0, `labor_research.py --question QUESTAO --period-start YYYY-MM-DD
--period-end YYYY-MM-DD` direciona a agenda. `--discover saida --url URL_OFICIAL
--question QUESTAO` captura um índice e localiza candidatos; abrir o inteiro teor
e realizar a consulta da resposta continuam necessários. Parâmetros conferem
unidade, valores por extenso, limites e condições; `source_unit`,
`source_relation` e `conditions_analysis` delimitam o critério. A revisão de
parágrafos também aponta quantidades sem suporte e afirmações de certeza
incompatíveis com os registros, sem certificar toda a semântica da prosa.

O [guia operacional completo](../skills/legal-process-parser/references/local_response_workflow.md)
mostra `begin`, captura HTTP ou registro de navegador, interpretação, parâmetros,
vinculação, capítulo v2 e consolidação com consulta própria. O guia também está
nos pacotes de cada plataforma, sem depender de outro adaptador.

Por link ou chat sem execução local, seguir
[pesquisa por resposta](../skills/legal-process-parser/references/response_research_rules.md):
usar a ferramenta real, citar as passagens oficiais e preservar o Markdown.
Não declarar execução do validador, hashes ou persistência que não existam.

Fatos e relatos vêm do usuário, não da internet. A consulta verifica o direito
pertinente a esses fatos. Organização de arquivos e reprodução factual não
exigem buscas artificiais. Sem navegação ou fonte acessível, a conclusão
dependente fica delimitada; a leitura e questões independentes continuam.

Os contratos verificam registros e vínculos declarados, não a interpretação
jurídica nem toda frase que um modelo deixou de registrar. Toda minuta requer
revisão profissional antes de uso.
