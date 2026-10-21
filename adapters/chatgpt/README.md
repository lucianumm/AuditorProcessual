# Adaptador ChatGPT/GPT

Use o pacote `legal-process-parser-chatgpt.skill` da release ou carregue o
diretório `skills/legal-process-parser/` como Skill. Em uma conversa iniciada
por link, leia `AI_ENTRYPOINT.md` e abra somente o núcleo e a tarefa solicitada.

Quando o usuário anexar um processo inteiro, analise o corpus integral e gere o
Markdown solicitado; não leia adaptadores de outras plataformas. Scripts locais
somente serão executados em um ambiente que ofereça essa ferramenta. Para
análise, peça ou auditoria, use `analise_juridica.md` como narrativa afirmativa
com fontes e confira a legislação oficial antes da tese.
