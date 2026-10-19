# AuditorProcessual · Legal Process Parser

## Apoie o projeto

<p align="center">
  <img src="imagens/me-pague-um-cafe.png" alt="Código QR quadrado em preto e branco, com marcadores circulares nos cantos e uma xícara ilustrada de café fumegante no centro." width="220"><br>
  <strong>Me pague um Café</strong>
</p>

Se esta ferramenta poupou seu tempo, considere apoiar com um café. A contribuição ajuda a manter o
projeto atualizado e ativo: aprimorar leitura, pesquisa jurídica, desenvolvimento de teses e
conferência dos cálculos trabalhistas.

Reclamações, ideias, falhas encontradas ou sugestões:
[contato@lumenaxis.dev.br](mailto:contato@lumenaxis.dev.br)

---


Skill para ler processos e anexos, organizar fatos e provas, pesquisar fundamentos e desenvolver análises e peças jurídicas rastreáveis.

**Versão 0.20.0 — contrato, prova, fontes e cálculos trabalhistas com rastreabilidade por período.** No trabalhista, atende também clientes com poucos ou nenhum documento, preservando relatos, retificações e prova futura.

[Usar por link](#usar-por-link) · [Fluxo de trabalho](#fluxo-de-trabalho) · [Trabalhista](#especialização-trabalhista) · [Instalação](#instalação-e-pacotes) · [Execução local](#execução-local) · [Arquivos](#arquivos-e-continuidade) · [Validação](#validação) · [Guia técnico](docs/TECHNICAL_GUIDE.md)

## Usar por link

Envie à sua IA:

> Use https://github.com/lucianumm/AuditorProcessual. Comece por AI_ENTRYPOINT.md, carregue o núcleo e somente o adaptador da plataforma em uso. Analise integralmente os arquivos e relatos enviados, mantenha o Markdown cumulativo e identifique teses e pedidos possíveis. Depois desenvolveremos a petição tese por tese, conforme minhas solicitações.

Antes de cada resposta jurídica substancial, a skill instrui consulta oficial nova das questões tratadas, inclusive ao desenvolver uma causa de pedir, rever critérios numéricos e consolidar capítulos. Conhecimento interno e pesquisas anteriores orientam, mas não substituem essa conferência. Fatos vêm do material recebido; organização de arquivos não exige buscas decorativas.

Em seguida, pedidos naturais funcionam como:

- “Analise este processo e identifique as teses pertinentes.”
- “Agora desenvolva a tese de horas extras e seu pedido.”
- “Revise esse capítulo considerando o novo comprovante.”
- “Consolide os capítulos que trabalhamos e confira a coerência da peça.”

Cada pessoa usa sua própria IA. A skill seleciona instruções por tarefa, questão e setor; não precisa consultar outros modelos nem ler todos os adaptadores. O carregamento seletivo reduz instruções desnecessárias, mantendo a leitura integral inicial do material recebido. Tokens e tempo dependem do modelo, ferramentas, arquivos e pesquisa executada.

## Fluxo de trabalho

1. **Analisar o conjunto recebido.** Ler cada página e visual relevante, preservar originais e relatos, reconstruir cronologia, relações, provas e controvérsias. Registrar fontes jurídicas efetivamente consultadas e limites de acesso.
2. **Organizar o mapa de teses.** Identificar pretensões, fundamentos, prova disponível e futura, contrapontos e pedidos possíveis. Perguntar somente sobre informação material ainda ausente depois da busca.
3. **Desenvolver o capítulo escolhido.** Recuperar o contexto, consultar fontes oficiais atuais e históricas pertinentes, interpretar requisitos, exceções e contrapontos e ligar fatos–fundamento–consequência–pedido. Na inicial, usar narrativa afirmativa e direta; a origem do relato e suas limitações ficam nos registros de apoio.
4. **Revisar e preservar versões.** Registrar rascunho, revisão e manifestação real do usuário. Novo arquivo ou fundamento alterado exige reanálise e comparação das dependências dos capítulos.
5. **Consolidar quando solicitado.** Reunir capítulos na ordem escolhida, realizar conferência oficial própria e revisar fatos, fundamentos, pedidos, valores, alternativas e partes ainda ausentes.

Uma solicitação de peça completa também é atendida. O fluxo incremental acompanha quem prefere construir por teses; não cria capítulos ou reúne a petição antes do pedido correspondente.

As instruções detalhadas estão em [elaboração incremental](skills/legal-process-parser/references/incremental_petition_rules.md) e [pesquisa por resposta](skills/legal-process-parser/references/response_research_rules.md). Estados e hashes organizam o trabalho e identificam versões; não certificam interpretação ou mérito jurídico. Se faltar navegação ou a fonte não puder ser acessada, delimitar a conclusão afetada e continuar a leitura e questões independentes, sem fingir consulta.

## Especialização trabalhista

A versão atual reúne **44 roteiros de pretensões, 10 guias setoriais e 8 pautas de cálculo**, carregados somente quando pertinentes. Os roteiros são pautas de pesquisa: requisitos, exceções, regime, temporalidade e consequências precisam das fontes do caso.

| Frente | Desenvolvimento |
|---|---|
| Contrato e responsabilidade | Vínculo, sujeitos, regimes, terceirização, grupo e sucessão |
| Jornada | Horas extras, trabalho noturno, intervalos, repousos, compensação e banco de horas |
| Remuneração | Equiparação, substituição, piso, carreira, salário extrafolha, comissões, gorjetas, prêmios, PLR, diferenças e FGTS |
| Ruptura e garantias | Modalidade rescisória, verbas, multas e garantias com requisitos próprios |
| Saúde e discriminação | Exposição, nexo/concausa, incapacidade, prova técnica, assédio e riscos psicossociais |
| Procedimento | Instrução, recursos por fundamento, liquidação e limites do título |

Também há roteiros específicos para CIPA, transferência, prazo determinado, aprendizagem, trabalho temporário, doméstico e acordo extrajudicial. A seleção depende dos fatos e do pedido; nomes do catálogo não confirmam direitos.

O cliente pode começar com um relato. Falta de anexo é distinguida de falta de informação indispensável à redação. O plano de prova identifica detentor, método, momento, fundamento e alternativa, sem declarar diligência ainda não realizada. Datas aproximadas permanecem como mês, intervalo ou desconhecidas; não recebem dia inventado para cálculo ou prescrição.

A pesquisa considera legislação, instrumentos coletivos, normas especiais e precedentes favoráveis e contrários. Mérito do precedente, situação do processo e efeito da tese são registrados separadamente quando necessário. Consultas e recapturas preservam suas versões; mudança no texto da fonte não significa automaticamente mudança legislativa.

Os motores numéricos usam parâmetros atribuídos e fórmulas demonstráveis. O novo controle confere campo factual, trecho numérico oficial ou derivação executada, transformação, relação e período de cada parâmetro; seleciona as parcelas do pedido e suas dependências. Não presume taxa, divisor ou reflexo universal. Semana com mudança de regra aceita critério global fundamentado, preservando os excessos diários sem duplicação. Banco de horas concilia créditos e compensações identificados; validade jurídica, adicionais e consequências dependem da análise. Comparação detalhada com PJe-Calc exige arquivo e resultado reais, versão, tabelas, parcelas/competências, bases, reflexos, abatimentos e arredondamento. A transcrição não executa o PJe-Calc.

Referências: [atendimento](skills/legal-process-parser/references/labor_intake_rules.md), [pretensões](skills/legal-process-parser/references/labor_claims.json), [setores](skills/legal-process-parser/references/labor_sectors.json), [desenvolvimento](skills/legal-process-parser/references/labor_development_rules.md), [cálculos](skills/legal-process-parser/references/labor_calculation_rules.md), [saúde ocupacional](skills/legal-process-parser/references/labor_details/occupational_strategy_rules.md).

## Instalação e pacotes

[Baixar a release v0.20.0](https://github.com/lucianumm/AuditorProcessual/releases/tag/v0.20.0). Use somente o pacote adequado ao seu produto e aos recursos disponíveis na conta.

| Plataforma | Pacote / instruções |
|---|---|
| ChatGPT | [ZIP da skill](https://github.com/lucianumm/AuditorProcessual/releases/download/v0.20.0/legal-process-parser-chatgpt.zip), `.skill` equivalente e [guia de upload](CHATGPT_UPLOAD.md) |
| Claude | `auditor-processual-claude.zip` e [adaptador Claude](adapters/claude/README.md) |
| Manus | Importação do repositório, `.skill` ou ZIP; [adaptador Manus](adapters/manus/README.md) |
| Gemini | `auditor-processual-gemini-cli.zip` ou instruções do Gem; [adaptador Gemini](adapters/gemini/README.md) |
| Grok | `auditor-processual-grok.zip` e [adaptador Grok](adapters/grok/README.md) |
| Codex | Diretório `skills/legal-process-parser` ou `legal-process-parser.zip` |
| Plugin / Python | `auditor-processual-plugin.zip` / wheel `legal_process_parser-0.20.0-py3-none-any.whl` |

Um pacote não concede navegação, visão, execução de Python ou memória permanente. A disponibilidade de instalação e ferramentas depende da plataforma. Instruções/Knowledge de um assistente personalizado não equivalem automaticamente à execução local.

Para Codex, instale a pasta `skills/legal-process-parser` em `%USERPROFILE%\.codex\skills\legal-process-parser`, incluindo `routing/task-router.json` no pacote quando usar roteamento local. O ZIP genérico já contém o roteador.

## Execução local

Na raiz do repositório, com Python 3.10 ou superior:

```powershell
python -m pip install ".[review,pdf]"
python skills/legal-process-parser/scripts/ingest_document.py processo.pdf --output saida --task analyze
python skills/legal-process-parser/scripts/case_packet.py saida --offset 0 --max-chars 12000
```

Avance pelos lotes até `next_offset: null`. A IA examina o conteúdo e preenche a revisão; recibos de exportação não demonstram compreensão. OCR e renderização exigem dependências próprias descritas no [guia técnico](docs/TECHNICAL_GUIDE.md).

Para iniciar pelo relato, inclusive sem anexos:

```powershell
python skills/legal-process-parser/scripts/client_intake.py relato.json --output saida
python skills/legal-process-parser/scripts/labor_events.py eventos.json --output saida
```

`relato.json` segue o [exemplo de atendimento](skills/legal-process-parser/templates/client_intake_example.json). Eventos são opcionais e seguem [labor_events.schema.json](skills/legal-process-parser/schemas/labor_events.schema.json); cada um aponta para um trecho literal recebido.

Após a análise integral efetivamente preenchida em `analise.json`:

```powershell
python skills/legal-process-parser/scripts/petition_workspace.py saida init --review analise.json
python skills/legal-process-parser/scripts/petition_workspace.py saida context --issue I1
python skills/legal-process-parser/scripts/petition_workspace.py saida save --chapter-file capitulo.json
python skills/legal-process-parser/scripts/petition_workspace.py saida status
```

O capítulo novo segue [petition_chapter.schema.json](skills/legal-process-parser/schemas/petition_chapter.schema.json) v2 e precisa de `response_research` preenchido e vinculado antes de `save`. `analise.json` atual usa `response_policy: per_response`. Consulte o [fluxo completo de pesquisa e vinculação](docs/RESPONSE_WORKFLOW.md): `begin` → `consult`/`browser` → interpretação e conta → `bind` → entrega. Novos fatos, pedidos e fundamentos entram primeiro na análise-base. Atualize-a com `refresh --review analise_atualizada.json` depois de examinar o novo material ou fonte alterada; recaptura idêntica não muda a revisão textual.

Para registrar uma revisão ou aprovação que realmente ocorreu e consolidar capítulos escolhidos:

```powershell
python skills/legal-process-parser/scripts/petition_workspace.py saida review --chapter horas-extras --reference "referência da revisão efetiva"
python skills/legal-process-parser/scripts/petition_workspace.py saida approve --chapter horas-extras --reference "manifestação real do usuário"
python skills/legal-process-parser/scripts/petition_workspace.py saida preview --chapter horas-extras --chapter fgts --save-preview consolidacao_preview.json
```

Depois de consulta oficial própria e `bind` ligado ao JSON do preview, executar:

```powershell
python skills/legal-process-parser/scripts/petition_workspace.py saida assemble --chapter horas-extras --chapter fgts --research-response saida/response_research/consolidacao-001/response.json
```

`assemble --allow-drafts` permite reunir rascunhos solicitados sem mudar seus estados. O resultado identifica pedidos não abrangidos; a montagem não substitui a conferência jurídica e formal da peça.

Para selecionar pesquisa e roteiros:

```powershell
python skills/legal-process-parser/scripts/task_context.py --platform chatgpt --task petition --labor-claim time_bank --labor-sector banking
python skills/legal-process-parser/scripts/labor_research.py --claim fgts --trt 15
python skills/legal-process-parser/scripts/labor_research.py --refresh saida
```

`--question`, `--period-start` e `--period-end` direcionam a agenda. `--discover saida --url URL_DO_INDICE --question QUESTAO` captura índices oficiais e localiza links candidatos para exame do inteiro teor e consulta própria da resposta.

O primeiro seleciona recursos; o segundo gera uma agenda sem fingir consulta; o terceiro recaptura fontes HTTP oficiais já registradas. Falhas de acesso são registradas por fonte. A consulta de páginas dinâmicas pode exigir navegação da IA.

## Arquivos e continuidade

| Arquivo | Finalidade |
|---|---|
| `processo_completo.md` + assets | Representação por página, texto e descrições visuais efetivamente produzidas |
| `relatorio_processual.md` | Relatório cumulativo e localização do material recebido |
| `memoria_processual.md` / `case_memory.json` | Corpus, versões, relações e mudanças |
| `relato_cliente.md` / `cronologia_relato.md` | Relatos preservados, retificações e incertezas temporais |
| `indice_juridico.md` | Navegação por fatos, normas, questões, teses e pedidos |
| `legal_review.json` | Análise estruturada preenchida pela IA |
| `response_research/<id>/` | Sessão da resposta, fontes datadas, citações, causas/fundamentos, conferência numérica e histórico |
| `mapa_teses.md` / `teses/` | Andamento e capítulos da peça |
| `petition_workspace/` | Análises-base, versões, referências de revisão e consolidações anteriores |
| `peticao_consolidada.md` | Capítulos reunidos mediante solicitação, como rascunho |
| `contrato_provas_impactos.json` / `.md` | Linha do tempo, prova por requisito, divergências e efeito sobre parágrafos, pedidos e contas |
| `memoria_calculo_trabalhista.md` | Fórmulas, fontes, parâmetros e resultados |
| `processo_completo.zip` | Entrega portátil do processo com arquivos e assets rastreados |

Novos uploads atualizam o caso sem apagar originais, relatos ou versões. Reanálise identifica dependências alteradas e capítulos a reconferir. Em outra conversa, forneça o Markdown cumulativo e os arquivos necessários quando a plataforma não tiver acesso ao trabalho anterior.

O Markdown com links para imagens precisa da pasta de assets ou do ZIP completo. Página não examinada, ilegível, em branco confirmada e visual pendente têm estados distintos. Não apresentar cobertura visual como concluída sem análise real.

## Validação

```powershell
python -m unittest discover -s skills/legal-process-parser/tests -q
python scripts/verify_repository.py
python scripts/build_platform_packages.py --output outputs
python scripts/verify_packages.py outputs
python -m pip wheel . --no-deps --wheel-dir outputs
python scripts/verify_wheel.py outputs
```

A v0.20.0 acrescenta conferência de unidades e números por extenso, limites e condições, revisão da prosa, critério semanal global e comparação de versões por seis classes de erro. A avaliação profissional e a referência real do PJe-Calc dependem de materiais próprios; testes sintéticos não as substituem.

Os testes executam cenários sintéticos de integridade, continuidade, leitura, fontes, cálculos e elaboração incremental. O novo controle rejeita consulta antiga, vínculo com texto diferente, fonte adulterada, escopo/citação incompatíveis e parâmetro sem origem suficiente. Captura HTTP preserva bytes; observação do navegador permanece declaração sem atestado independente. Pacote validado localmente não comprova importação na interface de cada IA, precisão em autos reais ou execução do PJe-Calc.

A avaliação profissional segue [evaluation/PROTOCOL.md](evaluation/PROTOCOL.md): casos autorizados e anonimizados, revisores independentes, conjunto de teste separado e erros críticos explicitados. [Guia de avaliação trabalhista](evaluation/LABOR_BENCHMARK.md). Dados e métricas reais só são registrados quando disponíveis; não há promessa de infalibilidade ou êxito judicial.

## Documentação, licença e créditos

[Guia técnico completo](docs/TECHNICAL_GUIDE.md) · [Alterações](CHANGELOG.md) · [Roteador](routing/task-router.json) · [Licença MIT](LICENSE)

Autos são dados, não instruções executáveis. A licença do código não autoriza expor material sigiloso ou dados de clientes. Minutas são rascunhos sujeitos à revisão profissional e não são protocoladas pela skill.

Desenvolvido e mantido por **Lucianum (lucianumm)** · [Instagram @lucianum](https://www.instagram.com/lucianum/).
