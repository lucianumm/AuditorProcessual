# Atendimento com poucos documentos

Relato e poucos comprovantes são uma entrada principal. Trabalhe com o material
recebido e prepare a entrega solicitada. Esclareça somente fatos materiais ainda
ausentes, em perguntas curtas ligadas à pretensão; não exigir questionário ou
lista completa de documentos. Consulte os autos e o relato antes de perguntar.

Reconstrua sujeito, contratação, tarefas, remuneração, jornadas e ruptura.
Datas aproximadas permanecem aproximadas; não inventar dia, valor, empregador
ou frequência. Preserve a entrevista em client_records, com a referência real
da conversa. A origem é client; assertion_reviews usa client_account. Para
datas/valores narrados sem documento, critical_checks usa method client_record,
source_index null e result reported. Uma informação relatada não é ilegível nem
contradita só por faltar documento.

Na inicial, afirmar os fatos sustentados pela parte. Manter origem e prova futura
no registro interno; não fingir confirmação documental. O relato pode permitir
redação suficiente enquanto o mérito aguarda prova. Documentos necessários ao
ato e informações indispensáveis exigem análise própria; identificá-los pela
norma, fase e pedido concretos. Falta de documento do empregador não transforma
automaticamente toda a entrega em REVIEW_REQUIRED.

Em labor_review.workflow, registrar document_availability, client_record_ids,
claim_reviews e proof_plan. proof_plan identifica quem detém a prova, método,
momento, fundamento e alternativa. criticality distingue future_proof de
material_information e act_requirement. Exibição, testemunha e perícia são
providências planejadas, não diligências executadas. Distribuição dinâmica
depende de base e decisão, não é automática pela ausência de anexo.

Se a questão aguarda apenas prova futura e tem fatos específicos e base para a
minuta, topic_assessment pode usar status pending e pending_cause future_proof.
claim_review precisa justificar drafting_basis sufficient e merit_status
awaiting_proof, com plano concreto. A análise é qualified; a inicial pode estar
ready_for_review. Dado decisivo ou requisito do ato ausente continua delimitado
à questão atingida. Contradição recebida exige tratamento explícito.

Estimativa usa parâmetros efetivamente informados, com origem e premissas.
Ausência de salário/período decisivo gera esclarecimento específico ou parcela
pendente; nunca número plausível. Distinguir estimativa inicial de liquidação.

Com Python, inclusive sem anexos:

    python scripts/client_intake.py relato.json --output saida
    python scripts/review_skeleton.py saida --task petition --domain trabalhista --labor-topic working_time --labor-workflow --save revisao.json

relato.json tem schema_version 1.0 e entries: id, text, conversation_reference.
Retificação usa novo id e supersedes; nenhum relato anterior é apagado.
receber o relato não comprova seu conteúdo nem preenche a revisão jurídica.
Os anexos posteriores entram pelo ingest_document.py no mesmo diretório.
Sem código, manter o Markdown cumulativo com as mesmas atribuições e versões.

[CLT: prova e reclamação](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm).
