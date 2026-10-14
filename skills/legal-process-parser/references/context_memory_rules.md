# Memória processual cumulativa

`case_memory.json` é o índice de longo prazo de um caso. Ele relaciona cada
documento ao SHA-256, páginas, passagens integrais, peças, eventos e versões.
`memoria_processual.md` é a visão legível para a IA e `relatorio_processual.md`
é o índice de entrega; `passages.jsonl` mantém offsets para localização exata.

Ao receber novo arquivo, preserve o original em `versions/`, compare o hash,
adicione o documento e atualize a revisão. Não exclua nem substitua a história.
Se a revisão jurídica anterior foi feita sobre outra `corpus_revision`, marque-a
como `stale` e reavalie as páginas, fatos, questões, pedidos e parágrafos
dependentes. Uma alteração normativa relevante também exige revisar as questões
que se apoiavam na versão anterior. Registre conflitos novos com o corpus
preservado. Nunca misture processos apenas porque têm partes, temas ou nomes
semelhantes; relações entre processos precisam de justificativa expressa.

Consultas posteriores usam `python scripts/ingest_document.py saida --mode QUERY`
ou `python scripts/case_memory.py saida --query TERMO` e devem devolver contexto,
documento, página, peça e ID. Paginação do resultado não equivale a leitura
integral inicial. O Markdown principal deve permitir encontrar documentos,
páginas, eventos, provas, questões, pedidos e versões. Sem acesso ao arquivo
anterior, solicite sua última versão; não presuma memória permanente da IA.
A memória é privada por padrão: não envie autos sigilosos a provedores externos
sem autorização.
