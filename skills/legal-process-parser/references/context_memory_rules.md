# Memória processual cumulativa

`case_memory.json` é o índice de longo prazo de um caso. Ele relaciona cada
documento ao SHA-256, páginas, passagens integrais, peças, eventos e versões.
`memoria_processual.md` é a visão legível para a IA e `relatorio_processual.md`
é o índice de entrega; `passages.jsonl` mantém offsets para localização exata.

Ao receber novo arquivo, preserve o original em `versions/`, compare o hash,
adicione o documento e atualize a revisão. Não exclua nem substitua a história.
Se a revisão jurídica anterior foi feita sobre outra `corpus_revision`, marque-a
como `stale` e exija reavaliação das páginas e normas afetadas. Nunca misture
processos apenas porque têm partes, temas ou nomes semelhantes; relações entre
processos precisam de justificativa expressa.

Consultas posteriores usam `python scripts/ingest_document.py saida --mode QUERY`
e retornam o trecho inteiro com documento, página, peça e ID. A memória é
privada por padrão: não envie autos sigilosos a provedores externos sem
autorização.
