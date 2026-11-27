# Ciclo de Reanálise Integral por Pedido (CRIP)

A cada solicitação substantiva (analisar, desenvolver tese, redigir ou revisar
capítulo, incorporar documento ou relato, consolidar), reconstrua a partir das
fontes os fatos, a prova, as normas e a coerência de tudo o que a resposta toca e
confira o impacto sobre o que já foi redigido. A análise-base é ponto de partida,
nunca verdade herdada; o hash mostra o que mudou, não dispensa a releitura.
Cada pretensão da peça recebe uma Ficha de Pedido (`request_cycle_details.md`).

Modos: `integral` (padrão: análise, capítulo, revisão com fato/norma/pedido novo,
consolidação) executa P0–P7; `focado` (pedido expresso ou ajuste só de redação)
executa P0–P4 e P6 no perímetro direto; `rápido` (esclarecimento sem peça)
executa P0 e P3.

1. **P0 Ancoragem** — tarefa, polo, peça; o que mudou desde o último ciclo;
   perímetro de questões, fatos, pedidos e capítulos. Fato compartilhado
   (salário, jornada, admissão, dispensa) puxa todos os capítulos que o usam.
2. **P1 Releitura** — páginas citadas pelos fatos do perímetro e material novo,
   por inteiro; depois as `relevant` do perímetro até 60 páginas/120 mil
   caracteres. Varredura de contraprova no corpus: pagamento, quitação,
   negação, datas concorrentes, nomes, termos opostos.
3. **P2 Reconferência factual** — sujeito, ação, objeto, polaridade, data,
   período e valor reextraídos da fonte relida; cada fato igual, divergente,
   novo ou contraditado em relação à base.
4. **P3 Citações** — pesquisa da resposta (`response_research_rules.md`) e
   reconferência das citações já presentes nos capítulos do perímetro;
   autoridade do catálogo com `freshness.state` diferente de `fresh` exige
   consulta oficial nova.
5. **P4 Requisitos** — requisito → fato → prova → norma da época → exceção →
   consequência → pedido; lacuna com tratamento explícito.
6. **P5 Adversarial** — reler a minuta como a parte contrária, só com texto e
   fontes: fato invertido, data/valor errado, prova contrária omitida, norma fora
   do tempo, precedente sem aderência, objeção mais forte. Contexto separado
   quando houver (subagente, nova conversa, revisor); outro modelo só com
   autorização expressa do usuário. Sem isso, declarar "mesmo modelo".
7. **P6 Coerência global** — contra todos os capítulos: parâmetros, datas,
   períodos, nomes, CPF/CNPJ, processo, teses incompatíveis, *bis in idem*,
   pedido sem causa de pedir, causa de pedir sem pedido, valor da causa; um
   termo único por parte.
8. **P7 Relatório** — o que mudou e por quê, estado de cada pedido, o que não
   foi verificado, capítulos reabertos; linha no "Histórico de ciclos" de
   `relatorio_processual.md`.

Lacuna num passe delimita só a conclusão dependente. Sem execução local, a
releitura é **declarada pelo modelo (não atestada)**; com Python,
`scripts/request_cycle.py` registra recibos e grava o ciclo. Nunca declarar
passe, página ou consulta que não ocorreu.

Bloco obrigatório ao fim de toda resposta substantiva (5 a 9 linhas):

```markdown
### Reconferência deste pedido (ciclo C-0007 · modo integral)
- Perímetro: questões I2, I5 · fatos F3, F7 · capítulos horas-extras, intervalo · pedidos P2, P3
- Releitura: 14 páginas (doc A p. 3–9; doc C p. 1–7) — declarada pelo modelo, não atestada · contraprova: 3 achados
- Fatos: 11 iguais · 1 divergente (F7: 06/2023 → 05/2023, doc C p. 4) · 0 novos
- Citações reconferidas: 6 (5 com captura, 1 pelo navegador, não atestada) · 0 alteradas
- Adversarial (mesmo modelo): 4 objeções · 4 resolvidas · 0 críticas pendentes
- Coerência: salário igual nos 3 capítulos · 1 período ajustado · Reabertos: intervalo
- Não executado: comparação com PJe-Calc · Estado: P2 sustentado · P3 condicionado
```
