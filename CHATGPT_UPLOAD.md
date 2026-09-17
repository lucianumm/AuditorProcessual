# Upload no ChatGPT

## Arquivo recomendado

Use legal-process-parser-chatgpt.skill. Ele é um ZIP com SKILL.md na raiz,
referências, templates, schemas e scripts. Se a interface não aceitar .skill,
use legal-process-parser-chatgpt.zip, que possui o mesmo conteúdo.

## Passo a passo

1. Abra o ChatGPT e selecione Plugins.
2. Abra a aba Habilidades/Skills.
3. Selecione Criar e depois Carregar/Upload do computador.
4. Arraste o arquivo .skill ou .zip para a janela exibida.
5. Aguarde a verificação automática.
6. Revise as informações de segurança e instale somente se reconhecer a origem.
7. Teste com: “Use Legal Process Parser para analisar este processo e informe
   a cobertura real, as fontes e as pendências antes de redigir qualquer minuta.”

O ChatGPT pode marcar uma habilidade como “Precisa de revisão” ou “Bloqueada”.
Isso exige revisão do conteúdo e das políticas do workspace; não deve ser
contornado.

## Escopo do pacote

O pacote orienta o ChatGPT a:

- extrair e localizar páginas, peças e imagens;
- separar fatos, alegações, provas, decisões e inferências;
- criar análise processual, cronologia, matriz documental e mapa de provas;
- redigir narrativa jurídica afirmativa em `analise_juridica.md`, vinculando fatos,
  alegações, provas e decisões a página, folha, peça e `document_id`;
- criar minutas de petições e peças com campos ausentes explícitos;
- pesquisar legislação oficial ampla e estruturar a tese por norma, subsunção,
  contrapontos e pedido, mantendo fontes não verificadas como pendentes;
- bloquear invenção de fatos, cálculo de prazo sem premissas e protocolo automático.
- inspecionar os materiais e perguntar somente se o pedido não puder ser determinado com segurança;
- executar somente a tarefa e os artefatos autorizados pelo usuário.

Os scripts locais não são executados automaticamente pelo upload. Para usar a
pipeline Python, execute-a no ambiente autorizado ou forneça os artefatos de
saída ao ChatGPT conforme a política de dados aplicável.

Não escreva “conforme documentação”, “documento apresentado” ou “certidão
analisada” como substitutos de fatos e fontes. Consulte
`references/legal_narrative_rules.md` e `legal_narrative.json` antes de redigir.

## Uso por link do GitHub

Se o usuário fornecer somente o endereço do repositório, leia primeiro
`AI_ENTRYPOINT.md` e `routing/task-router.json`. Use o adaptador ChatGPT e o
núcleo `skills/legal-process-parser/`; não leia adaptadores de Manus, Gemini,
Grok ou Claude, testes, changelog e empacotamentos. O processo do usuário pode
ser analisado integralmente por páginas e imagens sem carregar o restante das
instruções.

## Compatibilidade

O formato segue o padrão aberto Agent Skills e pode ser instalado separadamente
em Codex e Claude, mantendo SKILL.md na raiz do pacote correspondente.

Referência oficial: https://help.openai.com/pt-br/articles/20001066-skills-in-chatgpt

## Visão semântica e entrega portátil

O pacote não obriga chamadas a outros modelos. O ChatGPT pode revisar a página inteira e produzir `vision_review.json` usando o contrato em `schemas/vision_review.schema.json`; depois o pipeline local consolida imagens por SHA-256, separa recursos técnicos e cria `images/index.json`, `assets/pages/`, `paginas_problematicas.md` e `processo_completo.zip`. Use `--require-semantic-vision` somente quando quiser bloquear uma entrega sem revisão multimodal real; no uso comum, `best_effort` registra a pendência para conferência.
