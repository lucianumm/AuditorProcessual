# Guia do advogado — como pedir, revisar e ler a reconferência

O AuditorProcessual prepara análises e minutas rastreáveis. Ele não protocola, não
certifica mérito e não substitui a revisão profissional: toda minuta sai como
**RASCUNHO — NÃO PROTOCOLAR**.

## 1. Como pedir

- **Análise integral:** envie os autos (ou o relato do cliente) e diga o objetivo:
  "analise os autos para contestação", "veja se cabe recurso".
- **Peça por capítulos:** depois da análise, peça um tema por vez:
  "desenvolva o capítulo de horas extras". Revise, aprove e só então peça a
  consolidação: "consolide os capítulos aprovados".
- **Documento novo ou retificação:** envie o arquivo ou diga o que mudou
  ("o cliente corrigiu a data de admissão para 02/06/2026"). A IA reabre o que
  depende disso.
- **Mudança de estratégia:** "retire o pedido de dano moral", "torne o pedido de
  equiparação subsidiário".

## 2. Os modos do ciclo de reanálise

A cada pedido substantivo a IA executa o ciclo de reanálise (P0–P7): relê as
páginas dos fatos atingidos, procura prova contrária, reconfere fatos e
citações na fonte oficial, examina a minuta como a parte contrária e compara
com todos os capítulos já escritos.

| Modo | Quando usar | O que muda |
|---|---|---|
| `integral` (padrão) | análise, capítulo, revisão com fato/norma/pedido novo, consolidação | todos os passes |
| `focado` | ajuste só de redação ou pedido expresso ("modo focado") | sem passe adversarial; perímetro direto |
| `rápido` | pergunta de esclarecimento, sem peça | só ancoragem e pesquisa |

Para escolher: "responda em modo focado" ou "faça a reanálise integral".

## 3. Como ler o bloco "Reconferência deste pedido"

Toda resposta substantiva termina com um bloco curto:

- **Perímetro:** questões, fatos, capítulos e pedidos que a resposta tocou.
- **Releitura:** quantas páginas foram relidas por inteiro. No chat, a releitura
  é *declarada pelo modelo, não atestada*; com execução local há recibo.
- **Fatos:** quantos ficaram iguais à análise-base, divergentes ou novos. Fato
  divergente sempre traz o motivo e a página.
- **Citações reconferidas:** quantas foram abertas na fonte oficial nesta
  resposta e por qual via (captura com recibo ou navegador, não atestada).
- **Passe adversarial:** objeções da parte contrária e como foram resolvidas.
- **Coerência global:** se salário, datas, períodos e partes batem entre capítulos.
- **Reabertos / Não executado:** o que precisa de nova revisão e o que não foi
  verificado. Leia esta linha com atenção: é aqui que aparecem os limites.
- **Pedidos:** sustentado, condicionado (depende de prova) ou lacuna decisiva.

## 4. O que a consolidação faz sozinha

- numera os capítulos e gera "Dos pedidos" com principal, subsidiário e
  alternativo (com a condição de apreciação);
- calcula o valor da causa a partir das memórias de cálculo e das estimativas
  registradas, sempre como `[CONFIRMAR]`, e avisa se o valor informado diverge;
- lista as provas a produzir e os documentos citados (documento, página, folha);
- gera a matriz de rastreabilidade (pedido × parágrafo × fato × prova × norma)
  como anexo técnico, fora do texto dirigido ao juízo;
- **bloqueia** a consolidação quando há salário, jornada, divisor ou adicional com
  valores diferentes entre capítulos, data de admissão/dispensa divergente,
  CPF/CNPJ/número de processo sem fonte, pedido sem causa de pedir, causa de
  pedir sem pedido, a mesma rubrica e competência em dois pedidos principais, ou,
  na contestação e no recurso, alegação ou fundamento sem resposta;
- na reclamação trabalhista, bloqueia pedido sem indicação de valor.

Termos alternados ("Reclamada", "Ré", "Empresa") e remissões internas
inexistentes geram alerta, não bloqueio.

## 5. Glossário de estados

| Estado | Significado |
|---|---|
| `draft` | capítulo salvo, ainda não revisado |
| `reviewed` / `approved` | revisão ou aprovação registrada com referência real do usuário |
| `needs_review` | algo de que o capítulo depende mudou; revisar antes de consolidar |
| `legacy_no_cycle` | capítulo salvo antes da v1.1, sem ciclo de reanálise |
| `pendente_conferencia_oficial` | autoridade do catálogo ainda não lida no portal oficial |
| `localizado_no_texto_oficial` | dispositivo localizado no texto oficial capturado (não certifica vigência na data dos fatos) |
| `fresh` / `expired` / `never_verified` | validade da conferência do catálogo; vencida ou nunca conferida exige nova consulta |
| `sustentado` / `condicionado` / `lacuna decisiva` | estado do pedido na Ficha de Pedido |

## 6. Limites (FAQ)

- **Protocola a peça?** Não.
- **Garante que a tese vence?** Não. Os controles conferem dados, fontes e
  coerência; a interpretação jurídica é de quem assina.
- **Executa o PJe-Calc?** Não. Compara com arquivo `.PJC` quando fornecido.
- **A releitura no chat é garantida?** Não. Sem execução local ela é declarada,
  e o bloco diz isso.
- **Usa outra IA?** Só com sua autorização expressa, caso a caso, para o passe
  adversarial.
- **Posso usar no escritório?** Sim: a permissão adicional do titular libera o
  uso interno na sua própria atividade profissional, inclusive nos casos de
  clientes. Vender, oferecer como serviço a terceiros ou incluir em produtos e
  sistemas exige licença comercial ([COMMERCIAL_LICENSE.md](../COMMERCIAL_LICENSE.md)).

