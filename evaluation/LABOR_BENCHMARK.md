# Avaliação trabalhista da análise à peça

Executar com casos autorizados e anonimizados, segundo PROTOCOL.md. Este guia
é um procedimento de avaliação, não resultado de revisão por advogado nem plano
pendente de implementação. Não distribuir autos privados no repositório.

Preparar conjuntos distintos: desenvolvimento para correções e teste reservado.
Incluir relato sem anexos, poucos documentos, documentação extensa, contratos
em curso, retificações, prova contrária tardia, ACT/CCT concorrentes, jornada com
mudança de regra, garantias, perícia e recursos. Dois revisores anotam os fatos,
fontes, pretensões pertinentes/afastadas, base normativa, contrapontos e pedidos
antes de ler o resultado do modelo; divergência recebe terceiro exame.

Executar o fluxo real do usuário: análise integral, pedido de uma tese, revisão
desse capítulo, segunda tese, novo documento e consolidação. Preservar a versão
do modelo, ferramentas observadas, arquivos, comandos do usuário e respostas.
O teste não fornece ao modelo as respostas esperadas. Medir por etapa, não só
pela petição consolidada. Não fazer chamadas pagas ou trocar provider implicitamente.

Contar separadamente: fatos omitidos/invertidos, datas aproximadas tornadas exatas,
fontes inexistentes, norma temporal inadequada, precedente sem aderência,
pretensão omitida ou indevida, pedido sem desenvolvimento, incompatibilidade
entre capítulos, preclusão não enfrentada e falso bloqueio por documento ausente.
Erro crítico não é compensado por boa redação. Registrar também os acertos que
dependem de dados presentes, relatos ou prova futura, sem porcentagem de êxito judicial.

Aplicar a rubrica e human_review.json do protocolo ao arquivo real da revisão,
vinculado por SHA-256. As versões de capítulos e de consolidações permitem
localizar o erro e a mudança. Medir tokens/tempo apenas por observação externa
efetiva; reler contexto necessário não equivale a carregar todo o repositório.

Para cálculos, usar saídas reais do PJe-Calc e os mesmos parâmetros, cenário,
versão, tabelas e arredondamento. Registrar referência por item, hash do arquivo
e responsável pela transcrição/conferência. Executar labor_calculations.py com
--reference e --reference-source; verificar resultados divergentes, abatimentos
e limites do título. A comparação numérica não valida por si a tese jurídica.

Publicar somente métricas agregadas com escopo, amostra, incerteza e verificações
executadas. Sem casos reais, laudos de avaliação ou saídas externas, manter
real_process_expert_review e real_pjecalc_comparison como not_run. As regressões
sintéticas do projeto são verificações de código e não substituem esta avaliação.
