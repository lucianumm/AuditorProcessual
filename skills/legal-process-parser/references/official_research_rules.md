# Pesquisa normativa oficial

A classificação de área (`trabalhista`, `previdenciário`, `civil` etc.) apenas
define a ordem de pesquisa. A análise deve considerar Constituição, normas
processuais, legislação especial, regulamentos, atos locais e precedentes
oficiais que possam alterar competência, requisitos, prazos, prova ou pedido.

Use páginas oficiais HTTPS (`.gov.br`, `.jus.br`, `.leg.br` ou `.mp.br`)
para a captura automática local. Registre o texto consultado e sua origem com:

```text
python scripts/research_sources.py saida --url https://www.planalto.gov.br/...
```

A IA interpreta a fonte capturada e preenche no `legal_review.json` sua vigência,
competência, hierarquia, regime temporal e aderência aos fatos. A URL oficial e
o hash da cópia local confirmam propriedades diferentes: nenhum dos dois prova,
sozinho, que a norma incide no caso.

Quando só houver navegação da IA, registre a URL final, data, referência real
da ferramenta, trecho observado e contexto suficiente para conferência. O
registro `browser_observation` de `scripts/source_records.py` declara o nível
`self_recorded_unverified`: o JSON não atesta criptograficamente que a página
foi visitada. Não atribua hashes ou bytes que a plataforma não expôs. Uma fonte
fornecida pelo usuário tem origem declarada; confirme edição e vigência em
fonte oficial antes de tratá-la como direito verificado. Fonte inacessível
registra tentativa, motivo e questões afetadas. Não crie recibo de navegação
para fingir consulta concluída.

Organize uma agenda por questão: requisitos e exceções, norma material,
procedimento e competência, tempo dos fatos, normas especiais/locais,
precedentes favoráveis e contrários. Registre a razão de aplicar ou afastar a
fonte pertinente. Encerrar a pesquisa exige dizer por que as fontes consultadas
são suficientes para aquela questão; “verificado” sozinho não basta.

Para precedente, acrescente tribunal, número, data, questão decidida, fundamento
pertinente, status vinculante, distinção possível e situação atual. Não crie
ementas, artigos, precedentes ou citações de memória. Se a consulta oficial
estiver indisponível, delimite as questões dependentes e preserve as conclusões
independentes.
