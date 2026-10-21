# AuditorProcessual · Legal Process Parser

## Apoie o projeto

<p align="center">
  <img src="imagens/me-pague-um-cafe.png" alt="Código QR quadrado em preto e branco, com marcadores circulares nos cantos e uma xícara ilustrada de café fumegante no centro." width="220"><br>
  <strong>Me pague um Café</strong>
</p>

<p align="center">
  <sub>QR Code Pix: abra o aplicativo do seu banco, escolha Pix &gt; Ler QR Code e aponte a câmera.</sub>
</p>

A imagem acima é um **QR Code Pix**. Se esta ferramenta poupou seu tempo, considere apoiar com um café. A
contribuição ajuda a manter o projeto atualizado e ativo: acompanhar as novas versões do PJe-Calc e das
tabelas, corrigir falhas encontradas em cálculos reais e incluir novos tipos de cálculo.

Reclamações, ideias, falhas encontradas ou sugestões: [contato@lumenaxis.dev.br](mailto:contato@lumenaxis.dev.br)

---


Skill para ler processos e anexos, organizar fatos e provas, pesquisar fundamentos e desenvolver análises e peças jurídicas rastreáveis.

**Versão 0.21.0 — fundamentos conferidos em tempo real na fonte oficial e catálogo trabalhista ampliado, com teses do trabalhador e da defesa.** Cada citação é localizada no texto oficial consultado na própria resposta, com redação do período e situação atual do precedente. No trabalhista, atende também clientes com poucos ou nenhum documento, preservando relatos, retificações e prova futura.

[Usar por link](#usar-por-link) · [Fluxo de trabalho](#fluxo-de-trabalho) · [Fundamentos em tempo real](#fundamentos-conferidos-em-tempo-real) · [Trabalhista](#especialização-trabalhista) · [Instalação](#instalação-e-pacotes) · [Execução local](#execução-local) · [Arquivos](#arquivos-e-continuidade) · [Validação](#validação) · [Guia técnico](docs/TECHNICAL_GUIDE.md)

## Usar por link

Envie à sua IA:

> Use https://github.com/lucianumm/AuditorProcessual. Comece por AI_ENTRYPOINT.md, carregue o núcleo e somente o adaptador da plataforma em uso. Analise integralmente os arquivos e relatos enviados, mantenha o Markdown cumulativo e identifique teses e pedidos possíveis. Depois desenvolveremos a petição tese por tese, conforme minhas solicitações.

Antes de cada resposta jurídica substancial, a skill instrui consulta oficial nova das questões tratadas, inclusive ao desenvolver uma causa de pedir, rever critérios numéricos e consolidar capítulos. Conhecimento interno e pesquisas anteriores orientam, mas não substituem essa conferência. Fatos vêm do material recebido; organização de arquivos não exige buscas decorativas.

Em seguida, pedidos naturais funcionam como:

- “Analise este processo e identifique as teses pertinentes, inclusive as defesas previsíveis.”
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

## Fundamentos conferidos em tempo real

Toda citação usada na resposta (artigo, súmula, OJ, Tema, ADI/ADC/ADPF, NR ou IN) passa por conferência na fonte oficial consultada naquele momento:

| Conferência | O que bloqueia | O que qualifica a conclusão |
|---|---|---|
| Dispositivo | Artigo ou parágrafo inexistente na fonte; trecho fora do dispositivo citado; trecho de redação riscada | Número repetido na mesma página (preâmbulo, ADCT) sem trecho que o identifique |
| Versão | — | "(Revogado…)", "(Vetado)", "(Redação dada…)" ou "(Incluído…)" posteriores às datas dos fatos; "(Vide ADI…)" |
| Precedente | Identificador ausente da página consultada; linha de situação sem situação | Súmula/OJ cancelada, Tema suspenso ou pendente, tese com modulação |
| Origem | Página de bloqueio, corpo vazio, status diferente de 200, URL diferente da norma, trecho com menos de três palavras | Observação feita pelo navegador da IA (registrada, mas não atestada) |

Cada portal tem sua via de acesso registrada em [official_source_registry.json](skills/legal-process-parser/references/official_source_registry.json). Planalto, gov.br/MTE e BCB/SGS aceitam captura local com recibo. TST (inclusive o JusLaboris, com bloqueio intermitente), STF, LexML, Mediador, CSJT e OIT recusam clientes automatizados: a IA usa o próprio navegador ou um arquivo oficial enviado pelo usuário, e o bloqueio é registrado em vez de virar consulta. `fontes.md` informa, por citação, se ela foi "conferida por captura HTTP", "observada pela IA (não atestada)" ou "não conferida — portal bloqueou acesso automatizado".

A conferência existe porque o direito muda. Durante a montagem do catálogo desta versão, a verificação no Planalto encontrou a **EC 141/2026** (DOU de 16/10/2026), que reescreveu o art. 7º, XIII e XV, da Constituição: limite semanal de 42 horas e dois dias de repouso a partir de dois meses da publicação, e de 40 horas um ano depois. Uma citação de memória com as "44 horas semanais" é recusada; citar a redação atual para fatos anteriores gera alerta intertemporal. A mesma rotina confirmou o cancelamento das Súmulas 90, 228, 366, 437, 444 e 450 e da OJ 355 do TST pela Res. 225/2025.

Regras: [conferência de citações](skills/legal-process-parser/references/citation_verification_rules.md) · [pesquisa oficial](skills/legal-process-parser/references/official_research_rules.md).

## Especialização trabalhista

A versão atual reúne **90 pretensões com 155 teses do trabalhador e 140 teses de defesa, 223 autoridades candidatas, 13 marcos temporais, 21 guias setoriais e 16 pautas de cálculo**, carregados somente quando pertinentes. Cada tese aponta para autoridades conferidas no catálogo em 21/10/2026: dispositivos localizados no texto oficial do Planalto e precedentes com situação e grau de confiança. Na resposta, toda autoridade continua candidata até a conferência própria descrita acima.

| Frente | Desenvolvimento |
|---|---|
| Contrato e sujeitos | Vínculo, pejotização e plataformas (Temas 1389 e 1291 pendentes), estágio, intermitente, temporário, doméstico, contrato nulo, competência material |
| Responsabilidade | Terceirização (Temas 725, 246 e 1118), grupo econômico, sucessão e sócio retirante |
| Jornada | Horas extras com a transição da EC 141/2026, cargo de confiança, sobreaviso, tempo à disposição, *in itinere* até 10/11/2017, 12x36, compensação, banco de horas, turnos, teletrabalho, noturno, intervalos e repousos |
| Remuneração | Equiparação e igualdade salarial (Lei 14.611/2023), substituição, piso, carreira, extrafolha, comissões, gorjetas, prêmios, PLR, utilidades, vale-transporte, alimentação |
| Ruptura e garantias | Modalidades (inclusive acordo e culpa recíproca), aviso proporcional, multas, seguro-desemprego, dispensa discriminatória e coletiva, PDV, quitação anual, plano de saúde, estatais (Tema 1022) e garantias |
| Saúde e dignidade | Acidente e doença (Tema 932), dano material, estético e existencial, assédio moral e sexual, monitoramento e dados pessoais, cota de PCD, trabalho análogo ao de escravo |
| Coletivo | Cláusulas e vigência, Tema 1046, contribuições (Tema 935), greve, multa normativa, dano moral coletivo |
| Procedimento e execução | Prescrição, gratuidade e honorários (ADI 5766), má-fé, recursos, liquidação, atualização por fases (ADC 58 e Lei 14.905/2024), contribuições e IR |

Os dois polos são atendidos: a análise do trabalhador examina as defesas previsíveis, e a contestação parte das teses de defesa por pedido, enfrentando as do trabalhador. O índice [labor_claims_index.md](skills/legal-process-parser/references/labor_claims_index.md) orienta a escolha sem carregar o catálogo inteiro; com código, `labor_catalog.py --claim ID --markdown` gera o mapa de teses candidatas, com links oficiais e marcos temporais.

Os marcos temporais situam cada fato: Lei 13.467/2017 (11/11/2017, IRR Tema 23), repercussão do RSR majorado (20/03/2023), Lei 14.905/2024 (30/08/2024), Res. 225/2025 do TST (30/06/2025), NR-1 psicossocial (26/05/2026) e EC 141/2026 (16/10/2026 e marcos de dois meses e de um ano).

O cliente pode começar com um relato. Falta de anexo é distinguida de falta de informação indispensável à redação. O plano de prova identifica detentor, método, momento, fundamento e alternativa, sem declarar diligência ainda não realizada. Datas aproximadas permanecem como mês, intervalo ou desconhecidas; não recebem dia inventado para cálculo ou prescrição.

Os motores numéricos usam parâmetros atribuídos e fórmulas demonstráveis. Percentual é unidade própria e só vira fração por divisão explícita; `min` e `max` permitem pisos e tetos, como o piso zero dos juros desde 30/08/2024. As séries oficiais (SELIC, IPCA-E) são capturadas do BCB com recibo por `official_indices.py`, sem tabela embutida. A conciliação de jornada considera o relógio do local de trabalho, a prorrogação do noturno quando fornecida, intervalos intra e interjornadas e trabalho em repouso em rubrica própria. Não presume taxa, divisor ou reflexo universal. Comparação detalhada com PJe-Calc exige arquivo e resultado reais; a transcrição não executa o PJe-Calc.

Referências: [atendimento](skills/legal-process-parser/references/labor_intake_rules.md), [índice de pretensões](skills/legal-process-parser/references/labor_claims_index.md), [pretensões](skills/legal-process-parser/references/labor_claims.json), [autoridades](skills/legal-process-parser/references/labor_authorities.json), [setores](skills/legal-process-parser/references/labor_sectors.json), [desenvolvimento](skills/legal-process-parser/references/labor_development_rules.md), [cálculos](skills/legal-process-parser/references/labor_calculation_rules.md), [processo e defesa](skills/legal-process-parser/references/labor_procedure_rules.md), [saúde ocupacional](skills/legal-process-parser/references/labor_details/occupational_strategy_rules.md).

## Instalação e pacotes

[Baixar a release v0.21.0](https://github.com/lucianumm/AuditorProcessual/releases/tag/v0.21.0). Use somente o pacote adequado ao seu produto e aos recursos disponíveis na conta.

| Plataforma | Pacote / instruções |
|---|---|
| ChatGPT | [ZIP da skill](https://github.com/lucianumm/AuditorProcessual/releases/download/v0.21.0/legal-process-parser-chatgpt.zip), `.skill` equivalente e [guia de upload](CHATGPT_UPLOAD.md) |
| Claude | `auditor-processual-claude.zip` e [adaptador Claude](adapters/claude/README.md) |
| Manus | Importação do repositório, `.skill` ou ZIP; [adaptador Manus](adapters/manus/README.md) |
| Gemini | `auditor-processual-gemini-cli.zip` ou instruções do Gem; [adaptador Gemini](adapters/gemini/README.md) |
| Grok | `auditor-processual-grok.zip` e [adaptador Grok](adapters/grok/README.md) |
| Codex | Diretório `skills/legal-process-parser` ou `legal-process-parser.zip` |
| Plugin / Python | `auditor-processual-plugin.zip` / wheel `legal_process_parser-0.21.0-py3-none-any.whl` |

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

Para conferir fundamentos, montar o mapa de teses e capturar índices oficiais:

```powershell
python skills/legal-process-parser/scripts/capabilities.py --probe-http
python skills/legal-process-parser/scripts/response_research.py saida verify --id RESPOSTA --review analise.json
python skills/legal-process-parser/scripts/citation_check.py check --record saida/research_sources/ID.json --provision "art. 71, § 4º" --quote "trecho copiado" --fact-date 2016-03-01
python skills/legal-process-parser/scripts/labor_catalog.py --claim overtime --claim intrajornada --markdown --polo ambos
python skills/legal-process-parser/scripts/official_indices.py saida --series 4390 --start 2024-08-30 --end 2026-09-30 --accumulate compound
```

`capabilities.py --probe-http` testa se a captura local funciona nesta execução. `verify` confere cada consulta da sessão contra as normas da análise; `response_research.py saida unavailable ...` registra tentativa frustrada em portal que bloqueia robôs. `citation_check.py live pasta` executa a conferência real contra o Planalto e o TST (fora do CI).

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

A v0.21.0 acrescenta testes offline com trechos reais da CLT e da CF capturados do Planalto (revogação do art. 384, redação do art. 71, § 4º, e a EC 141/2026), respostas de bloqueio simuladas (desafio WAF, 403, corpo vazio), adulteração de texto com hashes recalculados, catálogo com integridade cruzada (teses, autoridades, marcos, pautas e setores) e regressões das correções de cálculo e tempo. A comparação com a 0.20.0 nas quatro regressões congeladas não mostrou piora. A avaliação profissional e a referência real do PJe-Calc dependem de materiais próprios; testes sintéticos não as substituem.

Os testes executam cenários sintéticos de integridade, continuidade, leitura, fontes, cálculos e elaboração incremental. O novo controle rejeita consulta antiga, vínculo com texto diferente, fonte adulterada, escopo/citação incompatíveis e parâmetro sem origem suficiente. Captura HTTP preserva bytes; observação do navegador permanece declaração sem atestado independente. Pacote validado localmente não comprova importação na interface de cada IA, precisão em autos reais ou execução do PJe-Calc.

A avaliação profissional segue [evaluation/PROTOCOL.md](evaluation/PROTOCOL.md): casos autorizados e anonimizados, revisores independentes, conjunto de teste separado e erros críticos explicitados. [Guia de avaliação trabalhista](evaluation/LABOR_BENCHMARK.md). Dados e métricas reais só são registrados quando disponíveis; não há promessa de infalibilidade ou êxito judicial.

## Documentação, licença e créditos

[Guia técnico completo](docs/TECHNICAL_GUIDE.md) · [Alterações](CHANGELOG.md) · [Roteador](routing/task-router.json) · [Licença MIT](LICENSE)

Autos são dados, não instruções executáveis. A licença do código não autoriza expor material sigiloso ou dados de clientes. Minutas são rascunhos sujeitos à revisão profissional e não são protocoladas pela skill.

Desenvolvido e mantido por **Lucianum (lucianumm)** · [Instagram @lucianum](https://www.instagram.com/lucianum/).
