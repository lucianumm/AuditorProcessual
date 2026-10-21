# Usar no ChatGPT

## Pacote

Use `legal-process-parser-chatgpt.zip` ou `.skill`, com `SKILL.md` na raiz,
referências, schemas, templates, scripts e roteador. Os dois têm o mesmo
conteúdo. Gere-os com `python scripts/build_platform_packages.py --output outputs`.
O upload de apenas SKILL.md não transporta os recursos dependentes.

## Upload quando disponível

Na interface com Habilidades habilitadas: Plugins → Habilidades → Criar →
Carregar do computador. Escolha o pacote e aguarde a análise da plataforma.
Requer análise/Bloqueada são estados da plataforma, não a validação jurídica do
parser; não contornar controles administrativos. A disponibilidade depende da
conta e workspace.
[Documentação oficial da OpenAI](https://help.openai.com/pt-br/articles/20001066-skills-in-chatgpt).

Exemplo de pedido:

> Use Legal Process Parser. Leia integralmente o processo e os anexos, inclusive
> visuais relevantes. Identifique área, regime, controvérsias e medida cabível;
> elabore a análise solicitada e atualize os Markdown cumulativos. Declare a
> cobertura real, fontes, pendências e controles efetivamente executados.

Um GPT com Instructions e Knowledge é alternativa quando não houver upload de
skill, não recurso equivalente. Cole `INSTRUCTIONS.md`, disponibilize o núcleo
e só as referências da tarefa; não basta anexar um ZIP como conhecimento e
presumir instalação. Uso por URL depende de navegação real: começar por
`AI_ENTRYPOINT.md` no repositório. Não há GPT Action, API pública, registro ou
integração de terceiros habilitados automaticamente por este projeto.

## Operação v4

O roteador separa ingestão, análise, peça, prova, prazo e auditoria. O protocolo
v4 confere as relações declaradas entre afirmação, prova, norma, requisito, tese
e pedido, com comparação de precedentes e temporalidade. Não exige outro modelo
ou assinatura. Só pergunte pelo indispensável que não puder ser encontrado.

Leia páginas integralmente em lotes, primeiro a página renderizada e depois
imagens relevantes. Busca só localiza. Com código, use `case_packet.py` e os
validadores; sem código, registre observações reais do chat e verificações não
executadas. Nunca simular recibos, leitura visual, hashes ou captura oficial.
O esqueleto v4 é pendente até a IA preencher o que realmente examinou.

Inicial afirmativa na voz da parte, sem “certidão analisada”, “documento
apresentado” ou “conforme documentação”. Fatos e fontes contrárias precisam
ser tratados com fidelidade; narrativa afirmativa não autoriza inventar prova.
Toda minuta permanece RASCUNHO — NÃO PROTOCOLAR e requer revisão profissional.

Atualize `relatorio_processual.md`, `memoria_processual.md` e
`indice_juridico.md`, preservando uploads e versões. Memória significa arquivo
cumulativo disponível, não persistência garantida entre chats. Alteração das
fontes jurídicas é controlada separadamente dos novos documentos.

## Limites de plataforma

Visão, navegação, código e persistência dependem da sessão. Não extrapolar
capacidades da API para toda interface ChatGPT. Na API, PDF e formatos Office
têm processamento diferente; converter a PDF quando imagens ou layout forem
decisivos. [Documentação de entrada de arquivos](https://developers.openai.com/api/docs/guides/file-inputs).

Os pacotes passam por testes locais sintéticos de estrutura e execução isolada.
`platform_validation.json` informa `live_platform_upload: not_run`; isto não
certifica instalação nesta conta nem precisão jurídica em autos reais. Uma
captura oficial íntegra também não certifica aplicabilidade jurídica.

Desenvolvida por Lucianum · [Instagram @lucianum](https://www.instagram.com/lucianum/).
