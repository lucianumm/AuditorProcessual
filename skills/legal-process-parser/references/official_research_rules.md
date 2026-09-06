# Pesquisa normativa oficial

A classificação de área (`trabalhista`, `previdenciário`, `civil` etc.) apenas
define a ordem de pesquisa. A análise deve considerar Constituição, normas
processuais, legislação especial, regulamentos, atos locais e precedentes
oficiais que possam alterar competência, requisitos, prazos, prova ou pedido.

Use apenas páginas oficiais HTTPS (`.gov.br`, `.jus.br`, `.leg.br` ou `.mp.br`)
para a captura automática. Registre o texto consultado e seu hash com:

```text
python scripts/research_sources.py saida --url https://www.planalto.gov.br/...
```

A IA interpreta a fonte capturada e preenche no `legal_review.json` sua vigência,
competência, hierarquia, regime temporal e aderência aos fatos. Uma fonte pode
ser tecnicamente oficial e ainda assim não incidir no caso; por isso a captura
não equivale a verificação jurídica.

Para precedente, acrescente tribunal, número, data, tese/holding, status
vinculante, distinção possível e situação atual. Não crie ementas, artigos,
precedentes ou citações de memória. Quando a consulta oficial não estiver
disponível, registre a lacuna e mantenha o gate bloqueado.
