# Ciclo de reanálise — detalhes para peça, revisão e consolidação

Complementa `request_cycle_rules.md`; carregar ao redigir, revisar ou consolidar peça,
ou ao executar o ciclo localmente.

## Orçamento de releitura

Releia sempre, por inteiro, as páginas citadas pelos fatos do perímetro e o
material novo. As demais entram por prioridade (página com entidade do fato —
data, valor, nome — antes da página só da mesma peça) até 60 páginas ou 120 mil
caracteres por ciclo, salvo pedido do usuário. O que ficar de fora é listado em
"Não executado", nunca omitido.

## Gatilhos de reabertura

| Evento | Reabre |
|---|---|
| Upload ou nova versão de documento | P0–P7 nas questões cujos fatos citam o documento ou cujas entidades ele contém |
| Relato novo ou retificação | P1–P7 nos fatos do relato |
| Mudança de fonte oficial | P3–P7 nas questões que usam a norma ou o precedente |
| Manifestação do usuário (mudar tese, retirar pedido) | P0, P4, P6, P7 |
| Capítulo novo salvo | P6 sobre todos os capítulos salvos |
| Consolidação | P0–P7 com perímetro = peça inteira |

## Ficha de Pedido

Para cada pretensão da peça, reconstruída a cada ciclo:

1. identificação, texto, natureza (principal, subsidiário, alternativo) e condição;
2. causa de pedir: questões, teses e parágrafos onde está desenvolvida;
3. fatos constitutivos e prova (documento, página, folha) com o estado de cada um;
4. requisitos normativos, cada um ligado a fato e prova;
5. norma aplicável à época, citação conferida no ciclo e marca intertemporal;
6. precedentes: aderência, situação atual, modulação;
7. objeção mais forte e resposta;
8. compatibilidade com os demais pedidos (subsidiariedade, exclusão, *bis in idem*);
9. quantificação por motor determinístico, com parâmetros, origem e período;
10. reflexos e dependências;
11. prescrição e decadência do período pedido;
12. estado: sustentado, condicionado ou lacuna decisiva, com o motivo.

Ficha incompleta entra em "Dos Pedidos" com `DEFINIR`. No trabalhista, rito
ordinário e sumaríssimo exigem pedido certo, determinado e com indicação de
valor: conferir na própria resposta a redação vigente do art. 840, § 1º, e do
art. 852-B, I, da CLT; sem quantificação, o pedido é bloqueado, não estimado.

## Checklist antes de entregar

1. Reli inteiras as páginas de cada fato usado e fiz a varredura de contraprova?
2. Sujeito, data, período, valor e polaridade de cada frase batem com a fonte?
3. Cada citação foi conferida neste ciclo, com vigência à época e situação atual?
4. Cada requisito tem fato e prova, ou a lacuna está tratada?
5. A objeção mais forte foi enfrentada?
6. Parâmetros (salário, jornada, datas, períodos) idênticos aos dos outros capítulos?
7. Todo pedido tem causa de pedir e toda causa de pedir termina em pedido? Há *bis in idem*?
8. Pedidos subsidiários e alternativos têm condição e são compatíveis?
9. Valores vieram de motor determinístico com memória?
10. Registrei o que não foi verificado e os capítulos reabertos?

## Execução local

```text
python scripts/request_cycle.py saida begin --request "texto do pedido" --issue I1 --issue I3 [--depth integral|focado|rapido] [--statement "manifestação"]
python scripts/request_cycle.py saida scope --cycle C-0001 [--max-pages 60 --max-total-chars 120000]
python scripts/request_cycle.py saida reread --cycle C-0001 --offset 0 --max-chars 12000   # repetir até next_offset null
python scripts/request_cycle.py saida sweep --cycle C-0001
python scripts/request_cycle.py saida close --cycle C-0001 --atoms atomos.json --findings objecoes.json \
    --sweep-review varredura.json --response-id <id da pesquisa> --chapter-file capitulo.json   # ou --artifact preview.json
python scripts/petition_workspace.py saida save --chapter-file capitulo.json   # capítulo com "request_cycle": {"cycle_id": "C-0001"}
python scripts/petition_workspace.py saida assemble --chapter capitulo --research-response resposta.json --cycle C-0002
```

`atomos.json`: `[{"fact_id", "atoms": {...}, "source_page", "treatment"}]`, extraídos
da página relida; divergência ou fato novo exige `treatment`. `objecoes.json`:
`[{"id", "severity": "critical|material|minor", "reviewer":
"same_model_clean_context|separate_context|other_model_authorized", "objection",
"resolution"}]`. `varredura.json`: `[{"page_id", "assessment":
"irrelevant|context|supports|contrary", "treatment"}]` para cada página fora do
perímetro apontada pela varredura.

`close` executa a reconferência factual, a reconferência das citações na
consulta oficial desta resposta, a coerência global e o diferencial, gera
`request_cycles/<id>/ciclo.md` e acrescenta o "Histórico de ciclos". O ciclo
fica ligado ao hash do conteúdo: qualquer alteração posterior exige novo ciclo.
`assemble` recusa consolidação sem ciclo encerrado e capítulo salvo sem ciclo;
capítulos anteriores à v1.1 aparecem em `legacy_no_cycle`. Controles executados
não certificam mérito; a minuta continua RASCUNHO — NÃO PROTOCOLAR.
