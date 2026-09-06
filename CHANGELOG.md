# Changelog

## 0.11.0 — 2026-09-06

- Separação explícita entre aprovação técnica e mérito jurídico; nenhuma aprovação automática de conclusão final.
- Contrato validado em runtime, revisão por página vinculada ao conteúdo, suporte por fato e pesquisa por questão; tratamento de requisitos faltantes/controvertidos.
- Detecção conservadora de negação contraditória e voz distanciada na inicial; citações identificam arquivo/hash e documento.
- Revisões fornecidas dentro da saída preservadas antes da limpeza; memória textual/OCR/visual versionada e busca cumulativa paginada.
- Vínculo visual ao hash do arquivo e da renderização; sidecar vazio obrigatório rejeitado.
- ZIP cumulativo inclui versões e assets sem ZIPs recursivos; links históricos verificados.
- Fontes oficiais HTML/TXT/PDF textual com recibo e resposta bruta preservada.
- Núcleo seletivo reduzido, documentação de migração, recursos Python distribuídos e nove pacotes com licença e execução isolada.
- Regressões sintéticas para as falhas observadas; CI executa também os pacotes isolados.

## 0.10.0 — 2026-09-06

- Adicionada memória processual cumulativa (`case_memory.json`,
  `memoria_processual.md` e `passages.jsonl`) com versões, fingerprints,
  offsets integrais e atualização segura após novos uploads.
- PDF passou a usar extração/renderização por página com cache recuperável e
  diagnóstico de capacidades, sem declarar conclusão quando uma camada está
  pendente.
- Criado o contrato `legal_review.schema.json` e o validador provider-neutral
  `legal_review.py`, com fatos documentais/clientes, fontes oficiais capturadas,
  subsunção requisito por requisito, contrapontos, pedidos, cálculos e gate de
  conclusão.
- Petições iniciais receberam regra explícita de voz afirmativa; expressões de
  relatório documental são rejeitadas na revisão autoral.
- Incluídos protocolos de pesquisa oficial, memória, inicial e revisão, além de
  roteamento/adaptadores e documentação atualizados para ChatGPT, Claude,
  Gemini, Manus e Grok.
- Suíte ampliada para 56 testes, incluindo cobertura sem truncamento, bloqueio
  de revisão incompleta e contratos da nova etapa jurídica.

## 0.9.3 — 2026-08-26

- Substituída a voz de inventário documental por narrativa jurídica afirmativa,
  com fonte direta por peça, página, folha, `document_id` e `image_id` quando
  aplicável.
- Adicionados `legal_narrative.json`, `analise_juridica.md` e o protocolo
  `legal_narrative_rules.md` para fatos, alegações, provas, decisões, tese,
  subsunção e contrapontos.
- Ampliada a pesquisa normativa: Constituição, rito, legislação especial,
  regulamentos, normas locais e jurisprudência oficial permanecem pendentes
  até verificação de vigência, competência, hierarquia e direito intertemporal.
- Atualizados adaptadores de ChatGPT, Claude, Gemini, Grok e Manus, templates,
  roteador, schemas e validador; suíte ampliada para 53 testes.

## 0.9.2 — 2026-08-20

- Aplicados gates de qualidade para cobertura, proveniência, classificação, matriz de rastreabilidade e verificação legal.
- Adicionadas `quality_gate.json/.md` e `matriz_fato_prova_norma_pedido.json/.md` para impedir afirmações sem fonte e pedidos inventados.
- Suíte ampliada para 51 testes, incluindo ambiguidade de área e vínculos fato–prova–norma–pedido.

## 0.9.1 — 2026-08-20

- Documentação pública enxugada; decisões de evolução permanecem fora da skill distribuída.
- Reempacotamento multiplataforma e atualização das referências para a versão `v0.9.1`.
- Adicionados gates explícitos de qualidade e a matriz fato–prova–norma–pedido para reduzir afirmações sem proveniência.
- Mantida a suíte com 51 testes e os gates de precisão, proveniência, cobertura visual e conferência da base legal.

## 0.9.0 — 2026-08-20

- Migração de publicação para `github.com/lucianumm/AuditorProcessual`.
- Classificação automática e explicável de área jurídica (trabalhista, previdenciária, consumerista, civil, bancária, família/sucessões, penal, administrativa, tributária, empresarial, ambiental, constitucional e processual).
- Novo `legal_domain_profiles.json`, com fontes oficiais candidatas, perfil de redação, evidências por página e portas de verificação.
- Geração automática de `legal_basis.json` e `base_legal.md`; fundamentos permanecem provisórios até conferência de vigência, competência, direito intertemporal e jurisprudência.
- Suíte com 49 testes.

## 0.8.0 — 2026-08-12

- Gate explícito de visão semântica (`required`, `best_effort`, `off`) com providers `sidecar` e `agent_review`; `--require-semantic-vision` falha cedo quando a revisão não existe.
- Inventário visual com classes `visual_asset`, `technical_artifact`, `qr_code`, `logo`, `document_scan`, `photo` e `unknown`, deduplicação por SHA-256, ocorrências por página e zoom de imagens pequenas relevantes.
- Entrega portátil com `processo_completo.md`, `images/index.json`, `paginas_problematicas.md`, `assets/pages/`, manifesto de codificação, ZIP completo e validador de links/assets.
- Contrato `vision_review.schema.json`, opção `--encoding utf-8-sig` e 46 testes sintéticos cobrindo o fluxo visual corrigido.

## 0.7.0 — 2026-08-11

- Entrada universal `AI_ENTRYPOINT.md`, `llms.txt` e roteador JSON para uso por link do GitHub sem leitura integral do repositório.
- Adaptadores mínimos para Manus, Gemini CLI/Gems, Grok, ChatGPT/GPT e Claude.
- Extensão Gemini CLI com `gemini-extension.json` e `GEMINI.md`; instruções prontas para Gems e Grok.
- Empacotamento específico por plataforma, mantendo um único núcleo jurídico e execução de uma tarefa por vez.
- Suíte ampliada para 41 testes com validação do roteamento e da separação de adaptadores.

## 0.6.0 — 2026-08-11

- Gate adaptativo: inspeciona os materiais primeiro e pergunta somente quando houver ambiguidade, conflito ou dado indispensável ausente.
- Execução seletiva por tarefa (`ingest`, `analyze`, `petition`, `deadlines`, `evidence` ou `audit`).
- `--confirm-scope` opcional, relatório cumulativo `relatorio_processual.md` e preservação de uploads anteriores em `versions/`.
- Perguntas determinísticas em scripts/scope_questions.py e regras em references/request_intake_rules.md.

## 0.5.0 — 2026-08-11

- Pacote compatível com upload de Skills no ChatGPT, com SKILL.md na raiz do arquivo .skill.
- Fluxo especializado para PETITION_DRAFT e PROCEDURAL_ANALYSIS.
- Regras e templates para petições, peças, análise processual, citações internas e revisão antes do protocolo.
- Suíte ampliada para 32 testes, incluindo os modos PETITION_DRAFT e PROCEDURAL_ANALYSIS.
- Execução seletiva por tarefa, sem geração automática de relatórios não solicitados.
- Suíte ampliada para 36 testes.

## 0.4.0 — 2026-08-11

- Aplicadas as peças de andamento processual: contrato JSON, relatório de andamento, prazos para revisão, matriz documental, mapa de provas, checklist, minuta de trabalho e conformidade.
- Adicionada proveniência por página, fila de tarefas e bloqueio explícito contra cálculo automático de prazos ou protocolo de minutas.

## 0.3.0 — 2026-08-10

- Correção arquitetural para separar renderização, inspeção técnica, OCR, visão semântica e consolidação.
- Conversão integral agora exige renderização e visão semântica aplicáveis; ausência de provider gera `PARTIAL`.
- Manifesto `1.1` com cobertura física, textual, de renderização e semântica independentes.
- Adicionados `--vision-mode`, `--render-dpi`, sidecar de descrições por página e testes de regressão contra falso `COMPLETE`.
- Melhorias visuais e de cobertura consolidadas na versão 0.4.0.

## 0.2.1 — 2026-08-10

- Créditos de autoria e links oficiais de Lucianum adicionados à documentação e aos metadados.

## 0.2.0 — 2026-08-10

- Markdown estruturado por página com resumo semântico, entidades, termos-chave e blocos/tabelas.
- Inventário de imagens PDF e scans, cópias derivadas, hash, dimensões, localização e OCR opcional.
- Campo `--image-descriptions` para descrições semânticas revisadas por humano ou modelo multimodal autorizado.
- `image_inventory.json`, schemas de página/visual e cobertura visual no manifesto e relatório.
- README, SKILL, template, protocolo visual e validador atualizados.
- Suíte ampliada para 22 testes.

## Créditos

Projeto desenvolvido e mantido por **Lucianum (lucianum7)** — [Instagram](https://www.instagram.com/lucianum/).
