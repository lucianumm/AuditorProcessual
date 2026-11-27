# Plano de Melhoria — AuditorProcessual (v1.0.0 → v1.1 / v1.2) — Revisão 2

> Elaborado em 26/11/2026 a partir da leitura do repositório `lucianumm/AuditorProcessual`
> (commit `539dd61`, v1.0.0). A suíte local foi executada nesta análise:
> **484 testes, OK (3 skipped), ~48 s**.
>
> **Revisão 2 (27/11/2026):** as afirmações do plano foram conferidas contra o código no
> mesmo commit (suíte reexecutada: 484 testes, OK). O resultado está na seção 0.1. As
> mudanças desta revisão estão marcadas com **[R2]**. Em resumo: o diagnóstico está
> correto em quase tudo. Duas lacunas estavam descritas de forma mais grave do que são. O
> CRIP foi enxugado para reaproveitar o que já existe. A ordem das fases foi invertida para
> entregar primeiro o que dá mais precisão com menos risco.
>
> Objetivo central pedido: **a cada pedido, reanalisar tudo de novo para aumentar a precisão
> da confecção da peça**. O plano trata esse ponto como eixo principal (Eixo A) e, em
> seguida, cobre de forma ampla todos os demais aspectos do projeto.

---

## Sumário

0. [Sumário executivo](#0-sumário-executivo)
1. [Diagnóstico do estado atual](#1-diagnóstico-do-estado-atual)
2. [Eixo A — Reanálise integral a cada pedido (núcleo do plano)](#2-eixo-a--reanálise-integral-a-cada-pedido-núcleo-do-plano)
3. [Eixo B — Precisão na confecção da peça](#3-eixo-b--precisão-na-confecção-da-peça)
4. [Eixo C — Pesquisa, fontes e atualidade dos catálogos](#4-eixo-c--pesquisa-fontes-e-atualidade-dos-catálogos)
5. [Eixo D — Leitura e ingestão dos autos](#5-eixo-d--leitura-e-ingestão-dos-autos)
6. [Eixo E — Avaliação, métricas e prova de precisão](#6-eixo-e--avaliação-métricas-e-prova-de-precisão)
7. [Eixo F — Arquitetura, código e empacotamento](#7-eixo-f--arquitetura-código-e-empacotamento)
8. [Eixo G — Instruções para as IAs (engenharia de prompt)](#8-eixo-g--instruções-para-as-ias-engenharia-de-prompt)
9. [Eixo H — Segurança, LGPD e governança](#9-eixo-h--segurança-lgpd-e-governança)
10. [Eixo I — Experiência do usuário e documentação](#10-eixo-i--experiência-do-usuário-e-documentação)
11. [Cronograma por fases](#11-cronograma-por-fases)
12. [Indicadores de sucesso (KPIs)](#12-indicadores-de-sucesso-kpis)
13. [Riscos e mitigação](#13-riscos-e-mitigação)
14. [Anexos](#14-anexos) (inclui o **[R2]** Anexo E — Decisões pendentes)

---

## 0. Sumário executivo

O AuditorProcessual já é maduro em **rastreabilidade** (hash, versões, page_reviews,
estados de leitura), **conferência de citações** (`citation_check.py`, vigência, marcas
de redação) e **pesquisa oficial por resposta** (`response_policy: per_response`).

A principal lacuna em relação ao objetivo pedido é esta: **hoje, a cada pedido, só a
pesquisa jurídica é refeita. Os fatos, a prova e a coerência da peça são herdados da
análise-base** e só são reabertos quando mudam o `corpus_revision` ou o
`research_revision`. Na prática:

- o capítulo recebe só o recorte de dependências das questões selecionadas
  (`petition_workspace.py → dependencies()`), não a visão do caso inteiro;
- a releitura das páginas-fonte não é exigida a cada novo capítulo ou revisão;
- a consolidação (`assemble`) bloqueia pedido repetido, capítulo desatualizado e teses
  marcadas como excludentes, mas **não confere a coerência material entre capítulos**
  (mesmo salário, mesma data, mesmo período, mesma parte, *bis in idem* de valores);
- a revisão da prosa (`prose_review.py`) é **lexical**: confere quantidades com unidade
  e duas palavras de exagero ("comprovado", "incontroverso"). Ela não confere datas de
  calendário, nomes, períodos, sujeitos nem a correspondência semântica entre o parágrafo
  e o fato.

**Proposta central:** instituir o **Ciclo de Reanálise Integral por Pedido (CRIP)**, com
8 passes obrigatórios (P0–P7). Ele vale para toda solicitação substantiva do usuário e
para cada *pedido* da peça (ficha por pedido). Será implementado em três camadas: regras
para chat sem código, orquestrador local `request_cycle.py` com schema próprio e
ferramentas MCP. `save` e `assemble` passam a exigir um ciclo válido.

Os demais eixos atacam o restante:

- reduzir as **625 autoridades “pendente_conferencia_oficial”** dos demais ramos
  (~34% de 1.817);
- fazer a **primeira avaliação com casos reais** (hoje `real_process_expert_review` é
  `not_run`);
- corrigir o **empacotamento**: o wheel instala pacotes de topo chamados `scripts`,
  `references`, `schemas`, `templates` e `routing`, com risco de colisão;
- dividir o `helpers.py` (2.500 linhas);
- expor o fluxo de petição no MCP;
- criar uma fonte única para as contagens repetidas em 6+ documentos.

### 0.1 [R2] Verificação do plano contra o código

| Afirmação do plano | Conferência | Resultado |
|---|---|---|
| 625/1.817 autoridades pendentes nos demais ramos; 17 no trabalhista | `domain_authorities.json`: 625 de 1.817; `labor_authorities.json`: 17 de 660 | Confirmado |
| MCP com 16 ferramentas, sem revisão, *workspace* e pesquisa | `mcp_server.py`: 16 ferramentas, nenhuma de `legal_review`, `petition_workspace` ou `response_research` | Confirmado |
| `INJECTION_PATTERNS` com 8 regex | `helpers.py:91` | Confirmado |
| `prose_review.py` lexical, 56 linhas | Confere só quantidades com unidade, "comprovado" e "incontroverso" | Confirmado |
| `helpers.py` com 2.500 linhas | 2.500 linhas | Confirmado |
| Wheel com pacotes de topo genéricos | `pyproject.toml`: `packages = ["scripts", "references", "schemas", "templates", "routing"]` | Confirmado |
| Sem ruff/mypy/coverage no CI | `.github/workflows/test.yml` não tem nenhum deles | Confirmado |
| `real_process_expert_review` = `not_run` | `evaluation/LABOR_BENCHMARK.md:40` | Confirmado |
| `assemble()` não confere a coerência material entre capítulos | Só bloqueia pedido repetido, capítulo desatualizado, falta de aprovação e tese `exclusive_with` no mesmo cenário | Confirmado. **É a lacuna de maior impacto.** |
| L1: "fatos e prova são herdados da base" | **Parcial.** `refresh()` recalcula o `dependency_hash` (fatos, `assertion_reviews`, normas, períodos, cálculos) e marca `needs_review` com `change_impact`. `current_base()` revalida a precisão da base contra a memória. O que falta é a **releitura sem mudança** e a conferência de um erro que já estava na base | Corrigido no texto (L1) |
| L2: "o capítulo só vê o recorte" | **Parcial.** É verdade para a redação e a validação da prosa. A invalidação, porém, já segue fatos compartilhados: se o salário muda na base, todos os capítulos que usam aquele fato voltam a `needs_review`. O que falta é comparar **a prosa de um capítulo com a de outro** | Corrigido no texto (L2) |
| L9: não há data da conferência no catálogo | **Impreciso.** Cada autoridade já tem `verified.on` (data), `verified.method` e `verified.confidence`. Falta só a TTL por tipo e o controle de vencimento | Corrigido em 4.2; o custo cai |
| Ficha de Pedido como estrutura nova | Já existe `schemas/fact_evidence_norm_request.schema.json` ("Matriz de rastreabilidade fato-prova-norma-pedido") | A ficha passa a estender esse schema (2.4) |
| Perímetro de impacto e diff como peças novas | Já existem `labor_case_state.impact()` e `compare_reviews()`, usadas pelo `refresh()` | O P0 e o P7 passam a reaproveitá-las (2.5.2) |

**[R2] Conclusão da verificação:** o plano é **conveniente e bem fundamentado**. Os ajustes
desta revisão evitam três problemas: (a) criar estruturas paralelas às que já existem;
(b) transformar o ciclo em autodeclaração sem prova no chat; (c) começar pela
refatoração mais arriscada (namespace) antes de entregar ganho de precisão.

---

## 1. Diagnóstico do estado atual

### 1.1 Pontos fortes (preservar)

| Área | Evidência no repositório |
|---|---|
| Rastreabilidade | `case_memory.json`, `page_reviews` com `content_revision`, SHA-256, `versions/`, estados distintos para página ilegível, em branco e não examinada |
| Conferência de citações | `citation_check.py`: dispositivo existente, trecho dentro do artigo e fora da redação riscada, marcas "(Revogado…)/(Redação dada…)/(Vide ADI…)" comparadas às datas dos fatos |
| Pesquisa por resposta | `response_research.py begin/consult/browser/bind/validate`; o vínculo é feito ao hash do conteúdo exato e recusa recibo antigo |
| Conferência factual | `precision_validation.py`: átomos (sujeito, ação, objeto, polaridade, alcance), relação suporta/contradiz/contexto, e a fonte visual exige região |
| Integridade do *workspace* | `petition_workspace.py`: hash de estado, capítulos versionados, `needs_review` por `dependency_hash`, consolidação anterior marcada "RECONFERIR" |
| Motores determinísticos | Prazos, atualização monetária/BCB, previdenciário, dosimetria e prescrição, todos com `Decimal` |
| Honestidade epistêmica | Distinção consistente entre "captura HTTP com recibo" e "observação do navegador (não atestada)"; "RASCUNHO — NÃO PROTOCOLAR" |
| Testes | 484 testes sintéticos, CI em Ubuntu (3.10/3.12) e Windows, verificação de pacotes e wheel |

### 1.2 Lacunas encontradas (com localização)

| # | Lacuna | Onde | Impacto na precisão |
|---|---|---|---|
| L1 | A reanálise por pedido se limita à pesquisa jurídica. Mudança na base já reabre os capítulos (`refresh()` + `dependency_hash`), mas **sem mudança** nada é relido, e um erro factual que já estava na base e passou na validação não é reconferido **[R2: texto corrigido]** | `response_research_rules.md`, `petition_workspace.py: save_chapter()/refresh()` | Erro factual da base se propaga para todos os capítulos |
| L2 | A redação e a validação da prosa usam só o recorte das questões selecionadas. A invalidação segue fatos compartilhados, mas a prosa de um capítulo nunca é comparada com a de outro **[R2: texto corrigido]** | `petition_workspace.py: dependencies()`, `validate_chapter()` | Conflito com fato ou parâmetro escrito em outro capítulo não aparece |
| L3 | A consolidação não confere coerência material entre capítulos | `petition_workspace.py: assemble()` | Salário, datas, períodos e valores divergentes entre capítulos; *bis in idem* |
| L4 | A revisão da prosa é lexical (quantidades e duas palavras) | `prose_review.py` (56 linhas) | Datas, nomes, períodos, sujeitos e polaridade complexa passam sem controle |
| L5 | A releitura integral das páginas-fonte não é exigida em revisão ou novo capítulo | `incremental_petition_rules.md` | A paráfrase deriva da fonte ao longo das versões |
| L6 | Não há passe adversarial com contexto limpo; o mesmo modelo revisa o próprio raciocínio | `semantic_crosscheck_rules.md` reconhece o limite | Viés de confirmação |
| L7 | A peça consolidada é concatenação de capítulos; não há seção "Dos Pedidos" gerada, valor da causa nem numeração | `assemble()` | Pedidos sem causa de pedir, causa de pedir sem pedido, valor da causa incoerente |
| L8 | 625 de 1.817 autoridades dos demais ramos e 17 trabalhistas seguem `pendente_conferencia_oficial` | `domain_authorities.json`, `labor_authorities.json` | Mais pesquisa ao vivo e mais risco de citação de memória |
| L9 | O catálogo já registra `verified.on`, mas não há TTL por tipo de fonte nem rotina periódica de reconferência **[R2: texto corrigido]** | catálogos | Súmula cancelada ou lei alterada só é percebida na resposta |
| L10 | Avaliação só com casos sintéticos; o protocolo real nunca foi executado | `evaluation/LABOR_BENCHMARK.md` (`not_run`) | A precisão em autos reais não é medida |
| L11 | O MCP expõe 16 ferramentas, mas não expõe revisão (`legal_review`), *workspace* de petição nem sessão de pesquisa | `mcp_server.py` | Agentes MCP não conseguem cumprir o fluxo com controles |
| L12 | O wheel instala pacotes de topo genéricos (`scripts`, `references`, `schemas`, `templates`, `routing`) | `pyproject.toml` | Colisão com outros pacotes; importações frágeis |
| L13 | `helpers.py` com 2.500 linhas e 86+ funções distribuídas entre módulos | `scripts/helpers.py` | Manutenção difícil, acoplamento, regressões |
| L14 | Sem linter, checagem de tipos ou cobertura no CI | ausência de configuração ruff/mypy/coverage | Defeitos silenciosos |
| L15 | Contagens (606, 483, 123…) repetidas em 6+ arquivos .md sem checagem | README, SKILL.md, AI_ENTRYPOINT, ROADMAP, CHANGELOG, RESPONSE_WORKFLOW | Documentação inconsistente a cada versão |
| L16 | Histórico Git consolidado (3 commits; a árvore anterior não está disponível) | `git log`, `CONTROL_RESULTS.md` | Impossível bisseccionar regressões |
| L17 | A detecção de *prompt injection* nos autos usa 8 regex | `helpers.py: INJECTION_PATTERNS` | Cobertura baixa para injeção indireta ou ofuscada |
| L18 | O núcleo `SKILL.md` tem 16 KB de regras densas, muitas em negativa e espalhadas | `skills/legal-process-parser/SKILL.md` | A IA pula etapas; a ordem de operações não fica explícita |
| L19 | Importação real em cada plataforma não foi testada | `evaluation/PROTOCOL.md` | O comportamento real pode divergir do pacote validado |

---

## 2. Eixo A — Reanálise integral a cada pedido (núcleo do plano)

### 2.1 Conceito

O termo **"pedido"** cobre dois sentidos, e ambos são atendidos:

1. **Pedido do usuário**: cada solicitação substantiva na conversa ("desenvolva horas
   extras", "revise com o novo comprovante", "consolide").
2. **Pedido da peça**: cada pretensão formulada ao juízo (principal, subsidiário,
   alternativo).

**Regra-mãe proposta:**

> A cada solicitação substantiva, a IA executa o Ciclo de Reanálise Integral por Pedido
> (CRIP). Ele reconstrói, a partir das fontes, os fatos, a prova, as normas e a coerência
> de tudo o que a resposta toca. Também confere o impacto sobre tudo o que já foi
> redigido. A análise-base serve de ponto de partida e comparação, nunca de verdade
> herdada.

### 2.2 Os 8 passes do CRIP

| Passe | Nome | O que faz | Saída obrigatória | Bloqueia entrega se… |
|---|---|---|---|---|
| **P0** | Ancoragem | Classifica o pedido (tarefa, escopo, polo, peça). Lista o que mudou desde o último ciclo: uploads, relatos, retificações, fontes, capítulos e manifestações do usuário. Define o **perímetro de impacto**: questões, fatos, pedidos e capítulos atingidos | `cycle.scope`, `cycle.delta_since_last` | escopo ambíguo e material (aí pergunta) |
| **P1** | Releitura integral dirigida | Relê **por inteiro** todas as páginas citadas pelos fatos do perímetro, todas as páginas `relevant` vinculadas às questões do perímetro e todo material novo. Depois faz uma **varredura de contraprova** em todo o corpus (negações, pagamentos, datas concorrentes, nomes de partes, termos antônimos) | `reread_pages[]` com `content_revision`; `counter_evidence_sweep[]` | página do perímetro não relida ou varredura não executada |
| **P2** | Reconferência factual atômica | Reextrai os átomos (sujeito, ação, objeto, polaridade, alcance, data, período, valor) **direto da fonte relida**, sem copiar da base. Compara com `assertion_reviews` da base e registra as divergências | `fact_diff[]` (igual / divergente / novo / contraditado) | divergência material não tratada |
| **P3** | Pesquisa oficial nova e reconferência de citações | Mantém o fluxo atual (`begin → consult/browser → verify → bind`). Acrescenta: **reconfere todas as citações presentes nos capítulos do perímetro**, não só as novas; confere a situação atual dos precedentes; checa a TTL do catálogo | `research_session`, `citation_recheck[]` | citação sem conferência atual ou precedente com situação desconhecida |
| **P4** | Reconstrução jurídica requisito a requisito | Para cada questão do perímetro: requisito → fato → prova → norma vigente à época → exceções → consequência → pedido. Ao final, gera ou atualiza a **Ficha de Pedido** (2.4) | `requirement_matrix[]`, `request_cards[]` | requisito sem fato ou fato sem prova sem tratamento explícito |
| **P5** | Passe adversarial cego | Um revisor com **contexto limpo** recebe só a minuta e as fontes, sem o raciocínio. Ele busca: fato invertido, data ou valor errado, prova contrária omitida, norma fora do tempo, precedente sem aderência, pedido sem fundamento e a objeção mais forte da parte contrária. As objeções são reconciliadas uma a uma | `adversarial_findings[]` com `resolution` | objeção crítica sem resolução |
| **P6** | Coerência global | Confere a minuta nova contra **todos os capítulos já redigidos**, sem limitar ao recorte: parâmetros (salário, jornada, datas, períodos, divisores), nomes e qualificações, teses incompatíveis, *bis in idem*, pedido sem causa de pedir, causa de pedir sem pedido e valor da causa | `global_consistency[]` | conflito entre capítulos não tratado |
| **P7** | Diferencial e relatório | Gera o diff em relação à versão anterior (o que mudou e por quê), os estados por item (sustentado / condicionado / lacuna decisiva), as verificações não executadas e os capítulos que passaram a `needs_review` | bloco **"Reconferência deste pedido"** na resposta + `cycle.json` | — |

**Princípios operacionais:**

- **O hash detecta a mudança, mas não dispensa a releitura.** No perímetro de impacto, a
  página é relida mesmo sem alteração. O hash só serve para mostrar o que é novo.
- **O perímetro é amplo por padrão.** Um fato compartilhado (salário, jornada, admissão,
  dispensa, evento danoso) puxa todas as questões e capítulos que o usam.
- **Passes independentes continuam.** Uma lacuna em P3 delimita só a conclusão
  dependente; os outros passes seguem.
- **Profundidade configurável pelo usuário**, com padrão "integral":
  - `integral` (padrão para petição, análise e consolidação): P0–P7 completos;
  - `focado` (o usuário pede expressamente): P0–P4 + P6 só no perímetro direto;
  - `rápido` (perguntas de esclarecimento sem redação): P0 + P3.
- **[R2] Orçamento de releitura.** Um fato compartilhado como o salário pode estar ligado a
  dezenas de holerites, e o perímetro explode. Regra: o P1 relê por inteiro as páginas
  **citadas** pelos fatos do perímetro e o material novo. As demais páginas `relevant`
  entram até um teto configurável (padrão sugerido: 60 páginas ou 120 mil caracteres por
  ciclo). Acima disso, a seleção é feita por prioridade: página citada > página com
  entidade do fato (data, valor, nome) > página da mesma peça. O que ficou de fora é
  **declarado** em `not_executed` e no bloco de reconferência, nunca omitido.
- **[R2] Honestidade no chat.** Sem código, a IA não consegue provar que releu. No chat,
  o bloco de reconferência usa a mesma distinção que o projeto já faz entre captura com
  recibo e observação do navegador: "releitura declarada pelo modelo (não atestada)". Só a
  execução local (recibo do `reread` + `page_reviews`) registra o que foi entregue à IA.
  Isso evita que o bloco vire um selo de qualidade sem lastro.
- **[R2] Ciclo curto em revisões pequenas.** Se o usuário pede só ajuste de redação
  ("troque a palavra X"), sem mudança de fato, norma ou pedido, o ciclo roda em modo
  `focado` automaticamente, com P6 obrigatório. Isso evita ciclo integral para correção de
  vírgula, e o usuário pode forçar `integral` quando quiser.

### 2.3 Gatilhos de reabertura (o que dispara o CRIP além do pedido)

| Evento | Reabre |
|---|---|
| Novo upload ou nova versão de documento | P0–P7 nas questões cujos fatos citam o documento ou cujo tema ele toca (busca por entidades: partes, datas, valores) |
| Relato novo ou retificação do cliente | P1–P7 nos fatos do relato |
| Mudança de fonte oficial (`research_revision`) | P3–P7 nas questões que usam a norma ou o precedente |
| Manifestação do usuário ("mude a tese", "retire o pedido X") | P0, P4, P6, P7 |
| Capítulo novo salvo | P6 em todos os capítulos já salvos (coerência retroativa) |
| Consolidação | P0–P7 sobre a peça inteira, com perímetro = tudo |

### 2.4 Ficha de Pedido (pedido da peça)

Cada pedido da peça ganha uma ficha reconstruída a cada ciclo, com 12 itens de conferência:

1. **Identificação**: ID, texto, natureza (principal, subsidiário ou alternativo) e condição de apreciação.
2. **Causa de pedir**: questões e teses que o sustentam; parágrafos onde estão desenvolvidas.
3. **Fatos constitutivos** e sua prova (fonte: documento, página e folha), com o estado de cada um.
4. **Requisitos normativos**, cada um ligado a fato e prova.
5. **Norma aplicável à época**, citação conferida no ciclo e marca intertemporal.
6. **Precedentes**: aderência, situação atual, modulação.
7. **Objeção mais forte** e resposta.
8. **Compatibilidade** com os demais pedidos (subsidiariedade, exclusão, *bis in idem*).
9. **Quantificação**: memória de cálculo do motor determinístico, parâmetros com origem e período.
10. **Reflexos e dependências** de outros pedidos.
11. **Prescrição e decadência** do período pedido (`limitation_checker.py`).
12. **Estado final**: sustentado / condicionado / lacuna decisiva, com o motivo.

Uma ficha incompleta impede que o pedido entre na seção "Dos Pedidos" sem o marcador
`DEFINIR` (ver Eixo B).

**[R2] Implementação da ficha:** não criar schema novo do zero. A ficha estende o
`schemas/fact_evidence_norm_request.schema.json` (já é a "Matriz de rastreabilidade
fato-prova-norma-pedido") e se liga a `review.requests`, `limitation_checker.py` e ao
`calculation_set`. Assim, a matriz visível do Eixo B (3.2) passa a ser só uma
renderização da ficha, sem dado duplicado.

**[R2] Trabalhista:** para o rito ordinário e o sumaríssimo, a ficha exige pedido certo,
determinado e com indicação de valor (CLT, art. 840, § 1º; art. 852-B, I). O item 9
(quantificação) é **bloqueante** nesses ritos, e não apenas um alerta. A redação dos
dispositivos deve ser conferida no P3 do próprio ciclo, como qualquer outra citação.

### 2.5 Implementação por camada

#### 2.5.1 Chat sem código (ChatGPT, Gemini Gem, Grok, Claude.ai)

- Nova referência `references/request_cycle_rules.md`, carregada **automaticamente** nas
  tarefas `analyze`, `petition`, `evidence` e `audit` (gatilho `request_cycle` no
  `routing/task-router.json`).
- **Bloco de saída obrigatório** ao fim de cada resposta substantiva (modelo no Anexo A):
  "Reconferência deste pedido" com páginas relidas, fatos com divergência, citações
  reconferidas, objeções adversariais, conflitos entre capítulos e capítulos reabertos.
- O Markdown cumulativo (`relatorio_processual.md`) ganha a seção "Histórico de ciclos"
  com uma linha por ciclo.
- Em plataformas com subagentes ou novas conversas, P5 roda em contexto separado. Sem
  isso, o bloco declara: "passe adversarial executado pelo mesmo modelo".

#### 2.5.2 Execução local (Python)

**[R2] Mudança de desenho:** o CRIP **não** cria um segundo mecanismo de recibo paralelo ao
`response_research`. Hoje `save` e `assemble` já exigem uma sessão de pesquisa ligada ao
`artifact_hash`. Duas sessões independentes (pesquisa + ciclo), cada uma com seu hash,
duplicariam validação, aumentariam o atrito e abririam espaço para uma ficar válida e a
outra não. O ciclo passa a ser um **bloco `cycle` dentro da sessão de resposta** (schema
`response_research` v2). `request_cycle.py` vira uma CLI fina sobre essa mesma sessão.

Novo script `scripts/request_cycle.py`, com 5 comandos manuais e o resto automático:

```text
python scripts/request_cycle.py saida begin   --request "texto do pedido" --issues I1 I3 [--depth integral]
python scripts/request_cycle.py saida scope    # perímetro via labor_case_state.impact() + entidades compartilhadas
python scripts/request_cycle.py saida reread   --offset 0 --max-chars 12000   # páginas do perímetro em lotes, com orçamento
python scripts/request_cycle.py saida sweep    # varredura de contraprova (case_search + entidades + antônimos)
python scripts/request_cycle.py saida close   --atoms atoms.json --findings objecoes.json
#   close executa automaticamente: factdiff, recheck de citações (com TTL),
#   global_consistency e diff (compare_reviews); grava o bloco cycle na sessão de resposta
```

- Schema: o esboço do Anexo B vira o bloco `cycle` do `response_research.schema.json` v2,
  e não um arquivo independente.
- `petition_workspace.py save/assemble` continua exigindo **uma** sessão de resposta válida.
  A diferença é que a sessão passa a precisar do bloco `cycle` fechado.
- **[R2] Migração:** *workspaces* existentes não quebram. Seguindo o padrão
  `legacy_not_per_response` que já existe, capítulos salvos antes da v1.1 recebem
  `cycle_policy: legacy_no_cycle` e entram na consolidação com aviso, até serem salvos de
  novo. Isso exige teste de migração.
- `reread` registra recibos por página **e** exige `page_reviews` atualizados para as
  páginas relidas. O recibo continua sem provar compreensão, mas fica documentado o que
  foi entregue à IA.
- `sweep` reaproveita `case_search.py` (entidades `money`, `date`, `cnj`, `cpf_cnpj`) e
  acrescenta listas de antônimos jurídicos (pago/não pago, quitado/em aberto,
  admitido/negado, presente/ausente).

#### 2.5.3 MCP

Novas ferramentas em `mcp_server.py`: `begin_request_cycle`, `get_cycle_scope`,
`read_cycle_batch`, `run_counter_evidence_sweep`, `diff_fact_atoms`,
`recheck_citations`, `check_global_consistency`, `close_request_cycle`. Também passam a
ser expostas as já existentes que faltam: `validate_legal_review`,
`petition_workspace_*`, `response_research_*`.

### 2.6 Controles determinísticos novos que sustentam o CRIP

| Controle | Descrição | Arquivo |
|---|---|---|
| `consistency.parameters` | Extrai da prosa de **todos** os capítulos: salários, datas, períodos, jornadas, percentuais e divisores, e acusa valores diferentes para o mesmo parâmetro e o mesmo período | novo `scripts/global_consistency.py` |
| `consistency.entities` | Nomes de partes, CNPJ/CPF, número do processo, órgão e vara iguais em todos os capítulos | idem |
| `consistency.bis_in_idem` | Mesmas horas, competências ou eventos usados como base em pedidos não cumuláveis | idem + `labor_ledger.py` |
| `consistency.request_coverage` | Todo pedido tem causa de pedir desenvolvida e todo desenvolvimento termina em pedido | idem |
| `prose.dates` | Datas de calendário na prosa precisam existir nos átomos dos fatos vinculados | ampliar `prose_review.py` |
| `prose.periods` | Períodos ("de mar/2021 a jun/2023") conferidos contra `contract_periods` e fatos | idem |
| `prose.actors` | Sujeito da frase compatível com `atoms.actor` (heurística por papel: reclamante, reclamada, perito, juízo) | idem |
| `prose.polarity_ext` | Negação e polaridade além da comparação token a token atual (`opposite_polarity`) | ampliar `review_integrity.py` |
| `citation.ttl` | Autoridade com conferência mais antiga que a TTL do tipo de fonte exige nova consulta no ciclo | `citation_check.py` + catálogos |
| **[R2]** `consistency.glossary` | Mesmo papel processual com nomes alternados ("Reclamada", "Empresa", "Ré") na peça consolidada gera alerta, não bloqueio | `global_consistency.py` |
| **[R2]** `consistency.cross_refs` | Remissão interna ("item 3.2", "capítulo de horas extras") aponta para seção que existe na consolidação | idem |

**[R2] Nível de cada controle:** os controles de parâmetros, entidades e cobertura de
pedido são **bloqueantes** na consolidação. Os de glossário, legibilidade e atores
(`prose.actors`, que é heurístico) são **alertas**, para não gerar falso bloqueio, que é
uma métrica do Eixo E.

### 2.7 Critérios de aceite do Eixo A

- [ ] `save` e `assemble` rejeitam conteúdo sem ciclo fechado ligado ao hash.
- [ ] Teste de cenário: alterar o salário no capítulo B (já salvo o A) dispara conflito
      em P6 e `needs_review` em A.
- [ ] Teste de cenário: inserir no corpus uma página tardia contraditória dispara a
      varredura de P1, a divergência de P2 e o estado `disputed`.
- [ ] Teste de cenário: citar uma súmula cancelada num capítulo antigo faz P3 acusar o
      problema ao desenvolver outro capítulo.
- [ ] O bloco "Reconferência deste pedido" aparece em 100% das respostas substantivas
      no conjunto de replays de conversa (Eixo E).
- [ ] O modo `integral` é o padrão, e o usuário consegue escolher `focado` ou `rápido`.
- [ ] **[R2]** Um *workspace* criado na v1.0 abre, faz `refresh` e consolida na v1.1 com
      aviso `legacy_no_cycle`, sem erro.
- [ ] **[R2]** Num corpus de teste com 200 holerites ligados ao fato "salário", o P1 respeita
      o orçamento e lista em `not_executed` as páginas não relidas.

---

## 3. Eixo B — Precisão na confecção da peça

### 3.1 Consolidação deixa de ser concatenação

`assemble()` passa a produzir uma peça estruturada:

1. **Cabeçalho e qualificação** como campos confirmáveis (`[CONFIRMAR]`).
2. **Fatos** (seção comum) gerados a partir dos fatos usados pelos capítulos, sem
   duplicação e em ordem cronológica.
3. **Fundamentos** por capítulo, na ordem escolhida.
4. **Dos Pedidos**, gerado a partir das Fichas de Pedido: numeração, principal,
   subsidiários com condição expressa, reflexos e remissão ao capítulo.
5. **Valor da causa**: soma das quantificações dos motores, com memória anexa, e
   divergência acusada quando o usuário informar outro valor. **[R2]** O valor é sempre
   proposto como `[CONFIRMAR]`, nunca preenchido como definitivo. As regras de valor da
   causa variam por rito e ramo (CPC, art. 292; CLT, art. 840, § 1º), e há pedidos sem
   conteúdo econômico imediato. Pedido sem quantificação entra com `DEFINIR`, sem ser
   somado em silêncio como zero.
6. **Provas e requerimentos** (exibição, perícia, testemunhas) derivados do plano de
   prova (detentor, método, momento).
7. **Rol de documentos** com remissão documento/página/folha.
8. Rodapé **RASCUNHO — NÃO PROTOCOLAR**.

### 3.2 Matriz de rastreabilidade visível

Anexo técnico gerado para a peça (fora da prosa dirigida ao juízo):

| Pedido | Capítulo/§ | Fatos | Prova (doc/pág/fl.) | Norma conferida (data) | Precedente | Estado |
|---|---|---|---|---|---|---|

### 3.3 Qualidade redacional

- **Guia de estilo por peça**: inicial, contestação, réplica, recurso, manifestação.
  Estrutura, tom, extensão e fórmulas proibidas. Ampliar a lista de proibições atual
  ("conforme documentação" etc.) com vícios típicos de IA: "é importante destacar",
  "vale ressaltar", "cumpre salientar", adjetivação excessiva, redundância.
- **Glossário do caso**: um termo único por entidade (ex.: "Reclamada" sempre, sem
  alternar com "Empresa", "Ré" ou "Empregadora"), aplicado pelo `consistency.entities`.
- **Remissões internas** ("conforme item 3.2") conferidas automaticamente na consolidação.
- **Legibilidade**: alertas de parágrafo longo demais, frase acima de N palavras e
  citação literal excessiva.
- **Exportador `.docx`**: sumário, numeração automática de pedidos, notas de rodapé para
  as referências documentais e anexo da matriz.

### 3.4 Peças reativas

- **Contestação**: matriz automática "alegação da inicial × resposta" que acusa pedido
  não impugnado (risco de presunção de veracidade).
- **Recurso**: inventário dos fundamentos autônomos da decisão e de cada impugnação
  correspondente, com acusação de fundamento não atacado.
- **Réplica**: matriz "defesa/documento novo × resposta".

### 3.5 Critérios de aceite

- [ ] A consolidação gera "Dos Pedidos" e o valor da causa sem intervenção manual.
- [ ] A peça consolidada de teste com salário divergente entre capítulos é bloqueada.
- [ ] Contestação de teste com pedido não impugnado gera alerta.

---

## 4. Eixo C — Pesquisa, fontes e atualidade dos catálogos

### 4.1 Reduzir as autoridades pendentes

- **Situação atual:** 625/1.817 (~34%) nos demais ramos; 17 no trabalhista.
- **Priorização:** ordenar por frequência de uso (quantas pretensões citam a autoridade)
  e por risco (precedente vinculante > súmula > enunciado).
- **Meta:** < 15% pendentes na v1.1 e < 5% na v1.2, mantendo a honestidade do estado:
  pendente continua pendente até a leitura real.
- **Ferramenta:** relatório `catalog_status.py --pending --by-usage`.

### 4.2 Validade da conferência (TTL)

**[R2]** Cada autoridade **já tem** `verified.on`, `verified.method` e `verified.confidence`.
Basta acrescentar uma tabela de `ttl_days` por `kind` (no próprio catálogo ou no
`official_source_registry.json`) e o cálculo de vencimento no `citation_check.py`, sem
alterar as 2.477 entradas. TTL sugerida por tipo:

| Tipo | TTL sugerida |
|---|---|
| Tema com mérito pendente, IRDR, ADI em curso | 15 dias |
| Súmula/OJ/Tema julgado | 90 dias |
| Lei ordinária com alteração recente (< 2 anos) | 60 dias |
| Código ou lei estável | 180 dias |

Vencida a TTL, o CRIP (P3) exige nova consulta antes do uso.

### 4.3 Rotina periódica de reconferência

- Job agendado no GitHub Actions (mensal) para fontes com captura HTTP (normas.leg.br,
  Senado, SCON, BCB/SGS). Ele gera um *diff* do catálogo e abre um PR com as mudanças
  detectadas (revogação, nova redação, cancelamento).
- Para portais que bloqueiam robôs (TST, STF, TSE): lista de conferência manual
  assistida, gerada pelo job, a ser feita pelo navegador.

### 4.4 Profundidade da pesquisa

- **Teses do STF**: a página do tema não traz a tese. Criar captura específica da tese
  firmada (ata, acórdão) e registrar a falta quando não for obtida.
- **Jurisprudência regional**: súmulas de TRT/TJ e IRDR locais por tribunal, conforme o
  órgão do caso.
- **Normas coletivas** (Mediador): fluxo assistido de captura do instrumento integral,
  com âmbito, categoria e vigência.
- **Monitor de alterações**: para normas citadas no caso ativo, avisar se houve nova
  redação desde a última conferência.

---

## 5. Eixo D — Leitura e ingestão dos autos

| Ação | Detalhe |
|---|---|
| Comparação de camadas | Para páginas digitalizadas: OCR × visão × texto nativo, com divergência acusada em dados críticos (datas, valores, nomes, números) |
| Métrica de qualidade de OCR | Taxa de caracteres suspeitos, confiança do Tesseract por página, com reprocessamento automático em resolução maior |
| Tabelas | Extração estruturada de holerites, cartões de ponto e extratos (colunas e linhas) para alimentar `labor_ledger.py` sem digitação |
| Manuscritos e carimbos | Estado próprio "manuscrito — transcrição atribuída", nunca tratado como texto certo |
| Áudio e vídeo de audiência | Hoje só há manifesto. Transcrição opcional local (com autorização), com marcação de tempo e atribuição de falante como "não atestada" |
| Prova contrária tardia | Teste específico: documento decisivo na última página ou no último anexo |
| Grandes volumes | Teste de desempenho com autos de 3.000+ páginas; retomada (`resumable_pdf.py`) coberta em CI |

---

## 6. Eixo E — Avaliação, métricas e prova de precisão

> Sem medição em autos reais, "mais precisão" não pode ser demonstrado. Este eixo é o
> que dá prova ao Eixo A.

### 6.1 Conjunto de referência (*golden set*)

- **30–50 casos reais** autorizados e anonimizados (`privacy_redactor.py`), distribuídos
  por ramo (com peso maior no trabalhista), tamanho (relato sem anexo até 2.000+ páginas)
  e tipo de peça.
- Rótulos por **dois revisores independentes** antes de ver a saída, com terceiro
  revisor nas divergências, conforme o `PROTOCOL.md` já existente.
- Separação rígida entre **desenvolvimento** e **teste reservado**.

### 6.2 Replays de conversa multipasso

Novo tipo de teste que reproduz a jornada real e mede **cada etapa**:

```text
análise integral → tese 1 → revisão da tese 1 → tese 2 → novo documento → retificação do relato → consolidação
```

Isso verifica o CRIP: a cada passo, os erros introduzidos de propósito (salário
divergente, súmula cancelada, página contraditória) precisam ser detectados.

**[R2] Evitar que o teste "decore" os erros:** se quem planta o erro é quem escreve o
detector, a meta de 95% mede só o que já se esperava. Por isso: (a) metade dos erros
plantados é definida por um revisor que não escreveu o controle, ou sorteada de uma
taxonomia antes da implementação; (b) um lote de replays fica reservado e só roda na
medição da versão; (c) relatar à parte a taxa nos erros **não previstos** pelos controles
determinísticos.

### 6.3 Taxonomia de erros e métricas

| Métrica | Definição | Meta v1.2 |
|---|---|---|
| Citação inexistente ou incorreta | por 100 citações | 0 críticas |
| Norma temporalmente inadequada | por 100 citações | < 1 |
| Fato invertido ou atribuído ao sujeito errado | por 100 fatos | < 0,5 |
| Data aproximada tornada exata | ocorrências | 0 |
| Prova contrária omitida | por caso | < 0,2 |
| Pedido sem causa de pedir / causa de pedir sem pedido | por peça | 0 |
| Conflito entre capítulos não detectado | por consolidação | 0 |
| Falso bloqueio (lacuna inexistente) | por caso | < 0,3 |
| Detecção de erro plantado pelo CRIP | % dos erros plantados no replay | ≥ 95% |
| Rubrica humana (8 dimensões, 1–5) | média por dimensão, sem diluir erro crítico | ≥ 4 |

### 6.4 Comparação de versões

- O `evaluate_labor_batch.py` passa a comparar **v1.0 × v1.1 (com CRIP)** no mesmo
  conjunto, para provar o ganho.
- Medir também **custo**: tokens e tempo observados por ciclo, para calibrar os modos
  `integral`, `focado` e `rápido`.
- Cálculos: comparação real com PJe-Calc (arquivo `.PJC` com hash), já prevista no
  ROADMAP.

---

## 7. Eixo F — Arquitetura, código e empacotamento

| # | Ação | Prioridade |
|---|---|---|
| F1 | **Namespace do pacote**: mover para `legal_process_parser/` (`legal_process_parser.scripts`, `.references`, `.schemas`…), eliminando os pacotes de topo `scripts`, `references`, `schemas`, `templates` e `routing` no site-packages. Manter *shims* de compatibilidade por uma versão. **[R2]** Atenção: os pacotes por plataforma (ChatGPT, Gemini etc.) e os comandos documentados usam caminhos `scripts/...`. A mudança deve valer só para o **wheel** instalado, mantendo a árvore do repositório e os pacotes de chat como estão | Alta → **[R2] Média, Fase 3** |
| F2 | **Dividir `helpers.py`** (2.500 linhas) em módulos coesos: `text_normalization`, `dates`, `injection`, `page_quality`, `markdown`, `io_atomic`. **[R2]** Fazer de forma incremental (um módulo por PR, com `helpers.py` reexportando), nunca num único diff | Alta → **[R2] Média, contínua** |
| F3 | Remover os imports duplos `try: from .x / except ImportError: from x`, padronizando a execução por `python -m` | Média |
| F4 | **Qualidade estática**: `ruff` (lint + format), `mypy` gradual (começando pelos motores determinísticos), `coverage` com piso inicial de 80% nos motores e validadores | Alta |
| F5 | **Testes baseados em propriedades** (`hypothesis`) para `deadline_calculator`, `civil_monetary_engine`, `labor_time` e `penal_dosimetry` (invariantes: monotonicidade, ausência de dupla contagem, arredondamento) | Média |
| F6 | **Arquivos dourados** (*golden files*) para as saídas Markdown e DOCX, com revisão de diff no PR | Média |
| F7 | **MCP completo**: expor revisão, *workspace* de petição, sessão de pesquisa e CRIP (ver 2.5.3), com testes de protocolo | Alta |
| F8 | **Fonte única de métricas**: `metrics.json` gerado dos catálogos; README, SKILL, AI_ENTRYPOINT etc. usam marcadores atualizados por script, e `verify_repository.py` falha se divergirem | Média |
| F9 | **Migrações de schema**: `migrate_review.py` v3→v4→v5, com testes, para quando o CRIP alterar `legal_review` | Média |
| F10 | **Higiene de Git**: commits granulares, tags assinadas por versão, *conventional commits*, branch de release; não reescrever o histórico publicado. **[R2]** O histórico já consolidado (L16) não tem como ser recuperado; a medida só vale daqui em diante | Média |
| F11 | Logs estruturados (JSON) dos scripts para depurar ciclos, sem conteúdo sigiloso | Baixa |

---

## 8. Eixo G — Instruções para as IAs (engenharia de prompt)

### 8.1 Reestruturar o núcleo `SKILL.md`

Hoje o arquivo tem ~16 KB de regras corretas, porém densas, em ordem de leitura e não de
execução, com muitas formulações negativas. Proposta:

1. **Topo: "Ciclo obrigatório"** em 10 linhas numeradas (P0–P7 + entrega), sempre lido.
2. **Tabela "quando carregar o quê"** (substitui parágrafos de roteamento).
3. **Regras em forma positiva e verificável**: "Releia a página X inteira antes de citar
   o fato" em vez de "Não use busca como leitura".
4. **Formato de saída padronizado** por tipo de resposta (análise, capítulo, revisão,
   consolidação), sempre com o bloco "Reconferência deste pedido".
5. Mover para as referências os detalhes técnicos (schemas, comandos), mantendo no núcleo
   só o necessário para agir.
6. Meta: núcleo ≤ 8 KB, sem perder nenhuma regra (a regra movida fica referenciada).

### 8.2 Autoverificação explícita

Antes de entregar, a IA responde internamente a um **checklist curto** (Anexo C) e
reporta só o resultado no bloco de reconferência. Isso reduz etapas puladas sem inflar a
resposta.

### 8.3 Adaptadores por plataforma

- Testar **importação real** em ChatGPT, Claude, Gemini, Grok e Manus com o mesmo caso
  sintético e registrar o comportamento observado (modelo, data, ferramentas), conforme
  o protocolo existente.
- Para cada plataforma, documentar como executar P5 (passe adversarial) em contexto
  separado: subagente, nova conversa ou Gem/GPT revisor.

---

## 9. Eixo H — Segurança, LGPD e governança

| Ação | Detalhe |
|---|---|
| Injeção nos autos | Ampliar `INJECTION_PATTERNS` (hoje 8 regex) com variações em PT/EN, texto oculto (fonte branca, tamanho zero no PDF), metadados e comentários de Office. Criar um **corpus adversarial de testes**. Delimitar o conteúdo dos autos com marcadores no contexto entregue à IA |
| Pseudonimização por padrão | `privacy_redactor.py` aplicado antes de qualquer chamada externa (DataJud, portais), com mapa reversível só local |
| Trilha de supervisão humana | Registro de quem revisou, quando e qual hash (CNJ 615/2025), ligado às aprovações do *workspace* |
| Retenção | Política documentada de apagamento dos diretórios `saida/` e opção de cifrar em repouso |
| Dependências | `pip-audit`/Dependabot no CI; travar versões nas releases |
| Revisão de segurança | Revisão periódica do exportador DOCX, do parser ZIP/EML/P7S (*path traversal*, *zip bomb*, XXE) com testes de regressão |

---

## 10. Eixo I — Experiência do usuário e documentação

- **README em camadas**: (1) o que é e um exemplo de uso em 5 linhas; (2) fluxo; (3)
  detalhes técnicos em `docs/`. Tirar do topo as listas extensas de números e mudanças
  de versão (vão para o CHANGELOG).
- **Guia do advogado** (`docs/GUIA_USUARIO.md`): como pedir, como revisar, como ler o
  bloco de reconferência, quando usar os modos `integral`, `focado` e `rápido`.
- **Exemplo completo anonimizado** de ponta a ponta (entrada → análise → capítulo →
  consolidação), com as saídas reais.
- **FAQ** de limites: o que a skill não faz (protocolar, certificar mérito, executar o
  PJe-Calc).
- **Glossário** de estados (`draft`, `reviewed`, `approved`, `needs_review`,
  `pendente_conferencia_oficial` …).
- Canal de feedback estruturado (template de issue sem dados de cliente) para registrar
  erro encontrado em uso real e alimentar o Eixo E.

---

## 11. Cronograma por fases

**[R2] Ordem refeita.** A versão anterior começava pela refatoração de namespace (F1), que
toca todos os imports, quebra compatibilidade e não melhora em nada a precisão da peça. A
nova ordem entrega primeiro os controles determinísticos que pegam erro real
(coerência entre capítulos, datas e períodos na prosa, TTL), que são baratos, testáveis e
não mudam o fluxo do usuário. O ciclo completo vem depois, apoiado neles.

| Fase | Duração | Entregas | Critério de saída |
|---|---|---|---|
| **Fase 0 — Ganhos rápidos de precisão** | 2 semanas | `global_consistency.py` (parâmetros, entidades, cobertura de pedido) chamado no `assemble`; `prose_review` com datas e períodos; TTL sobre `verified.on`; `ruff` no CI (só lint, sem reformatar tudo); corpus de testes de injeção | Teste "salário divergente entre capítulos" bloqueia a consolidação; súmula com TTL vencida exige nova consulta |
| **Fase 1 — CRIP no chat (sem código)** | 1–2 semanas | `request_cycle_rules.md`; bloco de reconferência com "releitura declarada (não atestada)"; Anexo C; gatilho no `task-router.json`; `SKILL.md` com o "Ciclo obrigatório" no topo | Replays manuais em 2 plataformas mostram o bloco em todas as respostas substantivas |
| **Fase 2 — CRIP local** | 3 semanas | Bloco `cycle` na sessão `response_research` v2; `request_cycle.py` (begin/scope/reread/sweep/close); orçamento de releitura; factdiff; recheck; migração `legacy_no_cycle`; Ficha de Pedido sobre `fact_evidence_norm_request` | Todos os testes de cenário 2.7 passando, incluindo migração e orçamento |
| **Fase 3 — Confecção da peça + MCP** | 3 semanas | Consolidação estruturada (Dos Pedidos, valor da causa `[CONFIRMAR]`, provas), matriz, guia de estilo, DOCX ampliado; MCP com petição, pesquisa e CRIP; F1 (namespace só no wheel) | Peça de teste completa sem intervenção manual na estrutura; self-test MCP cobre as novas ferramentas |
| **Fase 4 — Fontes e avaliação real** | contínua, em paralelo | Redução de pendentes por uso e risco; job mensal; *golden set* (começar com 10 casos, não 30); comparação v1.0 × v1.1 | Relatório de avaliação com métricas agregadas |
| **Fase 5 — Prompt, UX e qualidade de código** | 2 semanas | `SKILL.md` ≤ 8 KB; teste de importação nas plataformas; README em camadas; guia do advogado; `mypy` nos motores; cobertura; F2 incremental | Importação registrada em pelo menos 3 plataformas |

Versões sugeridas: **v1.1** ao fim da Fase 2 (CRIP + coerência), **v1.2** ao fim das Fases 3–5.

**[R2] Capacidade:** o cronograma original somava ~17 semanas de trabalho, com fases em
paralelo. Para um mantenedor só, isso é otimista. As Fases 0 e 1 entregam a maior parte
do ganho de precisão em ~4 semanas e já se sustentam sozinhas, se o resto for adiado.

---

## 12. Indicadores de sucesso (KPIs)

| Indicador | Hoje | Meta v1.1 | Meta v1.2 |
|---|---|---|---|
| Respostas substantivas com ciclo de reanálise registrado | não existe | 100% local / ≥ 90% chat | 100% / ≥ 95% |
| Erros plantados detectados nos replays | não medido | ≥ 90% | ≥ 95% |
| Autoridades pendentes (demais ramos) | ~34% (625) | < 15% | < 5% |
| Autoridades com TTL vencida no uso | não medido | medido | 0 sem nova consulta |
| Casos reais avaliados | 0 | 15 | 30–50 |
| Erros críticos por peça (avaliação humana) | não medido | medido | → 0 |
| Cobertura de testes nos motores/validadores | não medida | ≥ 80% | ≥ 90% |
| Tamanho do núcleo `SKILL.md` | ~16 KB | — | ≤ 8 KB |
| Plataformas com importação testada | 0 registradas | 2 | 5 |
| **[R2]** Custo médio por ciclo `integral` (tokens e minutos, local) | não medido | medido | teto definido a partir da medição |
| **[R2]** Falsos bloqueios por consolidação (controles novos) | não medido | medido | < 0,3 |

---

## 13. Riscos e mitigação

| Risco | Efeito | Mitigação |
|---|---|---|
| Custo em tokens e tempo do ciclo integral | Respostas lentas e caras em autos grandes | Perímetro calculado por dependência (não o corpus inteiro a cada pedido); modos `focado`/`rápido` por escolha do usuário; medição real de custo (6.4) |
| Burocracia excessiva na resposta | Usuário cansado de blocos de controle | Bloco de reconferência curto (5–8 linhas), com detalhes no arquivo de ciclo |
| Falsa sensação de certeza com o ciclo "verde" | Uso sem revisão profissional | Manter a linguagem atual: "controles executados ≠ certificação de mérito"; RASCUNHO sempre |
| Passe adversarial pelo mesmo modelo | Viés mantido | Contexto limpo, prompt de revisor distinto, declaração explícita; quando possível, outro modelo **só com autorização do usuário** |
| Quebra de compatibilidade (namespace, schema) | Usuários atuais afetados | *Shims* por uma versão; `migrate_review.py`; notas de migração |
| Portais bloqueando robôs | Pesquisa P3 incompleta | Fluxo de navegador e arquivo oficial já existente; registro do bloqueio; delimitação da conclusão |
| Dados reais na avaliação | Risco LGPD | Autorização, pseudonimização, nada no repositório, só métricas agregadas |
| **[R2]** Bloco de reconferência vira autodeclaração no chat | A IA afirma ter relido sem ter relido; falsa segurança | Rótulo "declarado, não atestado" no chat; só o recibo local conta como registro |
| **[R2]** Perímetro de releitura explode em autos grandes | Ciclo lento, contexto estourado, páginas cortadas sem aviso | Orçamento de releitura com prioridade e lista explícita em `not_executed` |
| **[R2]** Dois mecanismos de recibo (pesquisa e ciclo) | Validação duplicada, estados inconsistentes | Bloco `cycle` dentro da mesma sessão `response_research` |
| **[R2]** Metas medidas com erros plantados pelo próprio autor do controle | Precisão superestimada | Erros definidos por terceiro ou sorteados; lote reservado; taxa separada para erros não previstos |
| **[R2]** Novos controles heurísticos geram falso bloqueio | Usuário passa a ignorar os alertas | Só parâmetros, entidades e cobertura bloqueiam; o resto é alerta; métrica de falso bloqueio |

---

## 14. Anexos

### Anexo A — Modelo do bloco "Reconferência deste pedido"

```markdown
### Reconferência deste pedido (ciclo C-0007 · modo integral)
- Perímetro: questões I2, I5 · fatos F3, F7, F12 · capítulos horas-extras, intervalo · pedidos P2, P3
- Releitura integral: 14 páginas (doc A p. 3–9; doc C p. 1–7) · varredura de contraprova: 3 achados
- Fatos: 11 iguais à base · 1 divergente (F7: fim do período 06/2023 → 05/2023, doc C p. 4) · 0 novos
- Citações reconferidas hoje: 6 (5 por captura HTTP, 1 observada pelo navegador, não atestada) · 0 com alteração
- Passe adversarial (mesmo modelo, contexto limpo): 4 objeções · 4 resolvidas · 0 pendentes críticas
- Coerência global: salário-base igual nos 3 capítulos · 1 ajuste de período aplicado ao capítulo intervalo
- Capítulos reabertos (needs_review): intervalo
- Não executado: comparação com PJe-Calc (sem arquivo .PJC)
- Estado: P2 sustentado · P3 condicionado (controle de jornada a exibir pela reclamada)
```

### Anexo B — Esboço do bloco `cycle` (**[R2]** dentro de `response_research.schema.json` v2)

```json
{
  "schema_version": "1.0",
  "cycle_id": "C-0007",
  "request_reference": "texto ou hash do pedido do usuário",
  "depth": "integral | focado | rapido",
  "started_at": "ISO-8601",
  "corpus_revision": "…",
  "research_revision": "…",
  "previous_cycle_id": "C-0006",
  "scope": {
    "issue_ids": [], "fact_ids": [], "request_ids": [], "chapter_ids": [], "page_ids": []
  },
  "delta_since_last": [{"kind": "upload|client_record|source|chapter|user_statement", "ref": "…"}],
  "reread_pages": [{"page_id": "sha:page", "content_revision": "…", "receipt": "…"}],
  "counter_evidence_sweep": [{"query": "…", "hits": [{"page_id": "…", "excerpt": "…", "relevance": "…"}]}],
  "fact_diff": [{"fact_id": "F7", "status": "same|divergent|new|contradicted", "fields": ["period_end"], "source": "…", "treatment": "…"}],
  "citation_recheck": [{"norm_id": "N3", "mode": "http|browser|unavailable", "checked_on": "…", "result": "unchanged|changed|cancelled|unavailable"}],
  "requirement_matrix": [{"issue_id": "I2", "requirement": "…", "fact_ids": [], "evidence": [], "norm_id": "…", "assessment": "met|disputed|missing", "treatment": "…"}],
  "request_cards": [{"request_id": "P2", "status": "supported|conditioned|decisive_gap", "checks": {"…": "…"}}],
  "adversarial_findings": [{"id": "A1", "severity": "critical|material|minor", "objection": "…", "resolution": "…", "reviewer": "same_model_clean_context|other"}],
  "global_consistency": [{"kind": "parameter|entity|bis_in_idem|coverage", "detail": "…", "chapters": [], "resolution": "…"}],
  "reopened_chapters": [],
  "not_executed": [],
  "content_hash": "hash do artefato entregue",
  "closed_at": "ISO-8601",
  "status": "closed|partial"
}
```

### Anexo C — Checklist de autoverificação (curto, antes de cada entrega)

1. Reli **inteiras** as páginas de cada fato que usei? Fiz a varredura de contraprova?
2. Sujeito, data, período, valor e polaridade de cada frase batem com a fonte relida?
3. Cada citação foi conferida **neste** ciclo, com vigência à época dos fatos e situação
   atual do precedente?
4. Cada requisito tem fato e prova, ou um tratamento explícito da lacuna?
5. A objeção mais forte da parte contrária foi enfrentada?
6. Os parâmetros (salário, jornada, datas, períodos) são idênticos aos dos outros capítulos?
7. Todo pedido tem causa de pedir, e toda causa de pedir termina em pedido? Há *bis in idem*?
8. Pedidos subsidiários e alternativos têm condição e são compatíveis?
9. Valores vieram de motor determinístico com memória?
10. Registrei o que **não** foi verificado e quais capítulos foram reabertos?

### Anexo D — Mapa das alterações por arquivo

| Arquivo | Alteração |
|---|---|
| `routing/task-router.json` | Gatilho automático `request_cycle` em analyze/petition/evidence/audit |
| `skills/legal-process-parser/SKILL.md` | Ciclo obrigatório no topo; reestruturação (Eixo G) |
| `references/request_cycle_rules.md` | **Novo**: regras do CRIP para chat e local |
| `references/incremental_petition_rules.md` | Exigir ciclo em capítulo, revisão e consolidação; coerência retroativa |
| `references/pleading_generation_rules.md` | Estrutura da consolidação; Fichas de Pedido; guia de estilo |
| `scripts/request_cycle.py` | **Novo**: CLI fina do CRIP sobre a sessão de resposta |
| `scripts/response_research.py` | **[R2]** Bloco `cycle` na sessão; validação conjunta pesquisa + ciclo |
| `scripts/labor_case_state.py` | **[R2]** `impact()`/`compare_reviews()` reaproveitadas no P0 e no P7 |
| `schemas/fact_evidence_norm_request.schema.json` | **[R2]** Estendido para a Ficha de Pedido |
| `scripts/global_consistency.py` | **Novo**: coerência entre capítulos |
| `scripts/prose_review.py` | Datas, períodos, atores, polaridade ampliada |
| `scripts/review_integrity.py` | Polaridade além da comparação token a token |
| `scripts/petition_workspace.py` | `save`/`assemble` exigem ciclo; consolidação estruturada |
| `scripts/citation_check.py` | TTL e reconferência em lote |
| `scripts/mcp_server.py` | Ferramentas do CRIP e do fluxo de petição |
| `scripts/helpers.py` | Divisão em módulos |
| `schemas/response_research.schema.json` | **[R2]** v2 com o bloco `cycle` (no lugar de um `request_cycle.schema.json` separado) |
| `pyproject.toml` | Namespace `legal_process_parser`; ruff/mypy/coverage |
| `.github/workflows/` | Lint, tipos, cobertura, pip-audit, job mensal de reconferência |
| `evaluation/` | Replays de conversa, *golden set* real (fora do repositório), comparação v1.0 × v1.1 |

---

### Anexo E — [R2] Decisões pendentes do titular

| # | Decisão | Opções | Recomendação |
|---|---|---|---|
| D1 | Escopo da adoção | (a) tudo; (b) Fases 0–2 agora, resto depois; (c) só Fase 0 | (b) |
| D2 | Profundidade padrão | `integral` sempre; `integral` só em petição e consolidação | `integral` em petição, análise e consolidação; `focado` automático em ajuste de redação |
| D3 | Rigor do bloqueio | `save` bloqueia sem ciclo; só `assemble` bloqueia | Só `assemble` bloqueia na v1.1; `save` passa a bloquear na v1.2 |
| D4 | Passe adversarial com outro modelo | Nunca; só com autorização do usuário por caso | Só com autorização, nunca por padrão (sigilo dos autos) |
| D5 | Casos reais para avaliação | Disponibilizar 10 casos anonimizados; adiar | Começar com 10, se houver autorização dos clientes |
| D6 | Namespace do wheel (F1) | Agora; Fase 3; não fazer | Fase 3, só no wheel |

*Este plano propõe melhorias de engenharia e de método. Ele não altera a natureza do
produto: as minutas continuam como **RASCUNHO — NÃO PROTOCOLAR** e dependem de revisão
profissional.*

---

### Anexo F — Situação da implementação na v1.1.0 (27/11/2026)

| Item do plano | Situação | Onde |
|---|---|---|
| L3/P6 Coerência material entre capítulos | **Feito** — bloqueia o `assemble` | `scripts/global_consistency.py` |
| L4 Prosa: datas, períodos, polaridade, sujeito | **Feito** — sujeito e legibilidade como alerta | `prose_dates.py`, `prose_review.py`, `review_integrity.py` |
| L1/L2/L5 CRIP P0–P7 no chat | **Feito** | `references/request_cycle_rules.md`, `request_cycle_details.md`, `SKILL.md`, adaptadores |
| CRIP local, ligado ao hash, migração `legacy_no_cycle` | **Feito** | `scripts/request_cycle.py`, `petition_workspace.py` |
| Orçamento de releitura e honestidade no chat | **Feito** | idem |
| Ficha de Pedido | **Feito** (derivada; suficiência jurídica continua autoral) | `request_cards()` |
| L7 Consolidação estruturada, valor da causa `[CONFIRMAR]`, matriz | **Feito** | `scripts/piece_assembly.py` |
| Peças reativas (contestação, recurso, réplica) | **Feito** | `reactive_findings()` |
| DOCX com sumário e anexo | **Feito** | `docx_exporter.py --toc --annex` |
| L9 TTL do catálogo | **Feito** | `catalog_status.py`, briefs com `freshness` |
| L8 Reduzir pendentes | **Feito para leis** (conferência no texto oficial com assunto no artigo); temas/ADI/súmulas de portais que bloqueiam robôs seguem pendentes | `scripts/catalog_recheck.py` |
| Rotina mensal de reconferência | **Feito** (relatório e artefato; sem PR automático) | `.github/workflows/catalog-freshness.yml` |
| L11 MCP completo | **Feito** — 28 ferramentas | `mcp_server.py` |
| L17 Injeção ampliada e corpus adversarial | **Feito** | `injection.py`, `tests/test_precision_v11.py` |
| L14 ruff, cobertura | **Feito** (ruff com regras de correção; cobertura ≥ 75% nos motores e validadores) | `pyproject.toml`, CI |
| F5 Testes de propriedade | **Feito** com sementes fixas (sem dependência nova) | `tests/test_properties_v11.py` |
| L15/F8 Fonte única de métricas | **Feito** | `scripts/metrics.py`, `metrics.json` |
| Erros plantados / replays | **Feito** (sintético, do próprio autor) | `evaluation/planted_errors.json`, `scripts/run_planted_errors.py` |
| Guia do advogado, glossário, FAQ, template de erro | **Feito** | `docs/GUIA_USUARIO.md`, `.github/ISSUE_TEMPLATE/` |
| Segurança: retenção, supervisão, Dependabot | **Feito** | `SECURITY.md`, `.github/dependabot.yml` |
| L12/F1 Namespace do wheel | **Adiado** — quebra `from scripts...`; sem ganho de precisão | ROADMAP |
| L13/F2 Dividir `helpers.py` | **Iniciado** (`injection.py`); restante incremental | ROADMAP |
| mypy | **Adiado** — começa pelos motores na próxima versão | ROADMAP |
| L18 `SKILL.md` ≤ 8 KB | **Adiado** — depende de teste de importação real por plataforma | ROADMAP |
| L10/L19 Casos reais, PJe-Calc, importação por plataforma | **Depende de material e contas do titular** | `evaluation/PROTOCOL.md` |
| Eixo D (OCR × visão, tabelas, transcrição) | **Adiado** — exige dependências opcionais e material real | ROADMAP |
