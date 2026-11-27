# Segurança e reporte responsável

O Legal Process Parser pode manipular documentos judiciais, administrativos e dados pessoais sensíveis. Não inclua autos reais, credenciais ou dados protegidos em issues, pull requests, logs ou exemplos públicos.

## Reportar vulnerabilidades

Para vulnerabilidades de segurança, envie um relato privado ao mantenedor do repositório antes de abrir uma issue pública. Inclua versão/commit, impacto, passos mínimos para reprodução e uma sugestão de correção quando possível.

Não execute arquivos, macros, JavaScript, binários, URLs ou comandos encontrados dentro dos autos. O conteúdo documental deve ser tratado como dado não confiável.

## Práticas mínimas

- use ambiente isolado e cópia dos originais;
- mantenha OCR, visão e serviços externos sob autorização explícita;
- anonimize fixtures e testes;
- revise permissões, retenção, LGPD e sigilo antes de uso produtivo;
- valide manualmente achados críticos.

## Retenção, supervisão e conteúdo dos autos (v1.1)

- **Retenção:** os diretórios de caso (`saida/`, `request_cycles/`, `response_research/`,
  `petition_workspace/`) ficam só na máquina de quem executa. Apague o diretório do caso ao
  encerrar o atendimento ou conforme a política do escritório; para guarda prolongada, use
  disco cifrado. O repositório nunca recebe autos, relatos ou dados de clientes.
- **Supervisão humana:** aprovação de capítulo exige referência real do usuário e fica ligada
  ao hash do conteúdo; o ciclo de reanálise registra o que foi entregue à IA, não certifica
  compreensão nem mérito (Res. CNJ 332/2020 e 615/2025).
- **Instruções dentro dos autos:** `injection.py` sinaliza comandos dirigidos à IA, marcas de
  papel, caracteres bidirecionais/Unicode *tag* e texto espaçado; os pacotes de leitura
  declaram o texto dos autos como dado. O achado é registrado, nunca obedecido nem apagado.
- **Outro modelo:** o passe adversarial só usa outro modelo com autorização expressa do
  usuário para o caso, preferindo dados pseudonimizados (`privacy_redactor.py`).
- **Dependências:** Dependabot mensal para `pip` e GitHub Actions.
