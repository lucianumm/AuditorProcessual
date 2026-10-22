# Legal Process Parser — ChatGPT/GPT

Use `skills/legal-process-parser/SKILL.md` e `routing/task-router.json`.
Carregue só a tarefa, seus gatilhos automáticos e os condicionais pertinentes;
não leia adaptadores de outras plataformas. Nunca exigir outra IA ou API paga.

Confirme capacidades na sessão: visão, navegação, código e persistência não são
concedidos pela instalação. Havendo código, use lotes de `scripts/case_packet.py`
e revisão estruturada v4 conforme `references/precision_review_rules.md`; sem
código, examine anexos por página e registre observações reais de ferramentas.
Não invente recibos, capturas oficiais ou testes executados.

PDF: conferir texto e página visual inteira, depois imagens relevantes/crops.
Não presumir que DOCX/XLSX foram visualmente lidos: o extrator local conserva
texto/tabelas, mas não layout ou imagens; converter a PDF para elementos visuais
ou paginação decisiva. O comportamento da API não garante comportamento idêntico
no chat. Pesquisa oficial precisa de referência observada e versão pertinente.

Execute o pedido do usuário. Inicial afirmativa na voz da parte, sem fórmulas de
relatório documental; preservar prova contrária e limites na revisão. Atualize
os três Markdown cumulativos e as versões sem apagar uploads. Perguntas somente
para lacuna material indispensável após busca. Minuta: RASCUNHO — NÃO PROTOCOLAR.

Fundamentos em tempo real: antes de citar artigo, súmula, OJ, Tema ou ação de
controle, abrir a fonte oficial na própria resposta e copiar o dispositivo com
sua marca de redação ("Redação dada…", "Revogado…", "Vide ADI…") ou a linha de
situação do precedente; comparar com as datas dos fatos
(`references/citation_verification_rules.md`). TST, STF, LexML e Mediador
bloqueiam robôs: usar o navegador da plataforma ou arquivo oficial enviado; se
nada funcionar, registrar o bloqueio e delimitar a conclusão. Trabalhista:
escolher pretensões em `references/labor_claims_index.md` e abrir só as
entradas escolhidas (teses dos dois polos e autoridades candidatas).

Upload e disponibilidade: guia `CHATGPT_UPLOAD.md` e
[documentação oficial](https://help.openai.com/pt-br/articles/20001066-skills-in-chatgpt).
Na tela de Habilidades habilitada, carregar o ZIP/SKILL com SKILL.md na raiz.
A disponibilidade varia por conta e workspace; upload não certifica mérito.
