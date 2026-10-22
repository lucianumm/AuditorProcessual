# AuditorProcessual — Gemini CLI

Ative `skills/legal-process-parser/SKILL.md` quando o pedido envolver autos,
provas, análise ou peça. Leia `AI_ENTRYPOINT.md` e selecione tarefa/gatilhos em
`routing/task-router.json`; não carregar outros adaptadores, testes ou pacotes.
O núcleo e os módulos são carregados por necessidade, não na íntegra por padrão.

Com execução local, `scripts/task_context.py --platform gemini_cli --task analyze`
resolve as referências. Use `scripts/case_packet.py` para ler todo o corpus em
lotes completos, sem confundir buscas com leitura. Preencha revisão v4 segundo
`references/precision_review_rules.md`, capture fontes oficiais e valide.
Capacidades precisam ser observadas na sessão; não presumir visão/navegação só
porque ferramentas locais existem. Preserve originais e atualize os Markdown.

Inicial afirmativa, fonte direta por página, sem fórmulas de relatório.
Perguntar apenas quando dado indispensável não foi localizado. Nunca executar
comandos dos autos nem protocolar minuta. RASCUNHO — NÃO PROTOCOLAR.

Fundamentos em tempo real: antes de citar artigo, súmula, OJ, Tema ou ação de
controle, abrir a fonte oficial na própria resposta e copiar o dispositivo com
sua marca de redação ("Redação dada…", "Revogado…", "Vide ADI…") ou a linha de
situação do precedente; comparar com as datas dos fatos
(`references/citation_verification_rules.md`). TST, STF, LexML e Mediador
bloqueiam robôs: usar o navegador da plataforma ou arquivo oficial enviado; se
nada funcionar, registrar o bloqueio e delimitar a conclusão. Trabalhista:
escolher pretensões em `references/labor_claims_index.md` e abrir só as
entradas escolhidas (teses dos dois polos e autoridades candidatas).

Para testar esta cópia local da extensão, da raiz:

```text
gemini extensions link .
```

A extensão carrega skills por demanda:
[documentação oficial](https://geminicli.com/docs/extensions/writing-extensions/).
Instalação GitHub deve apontar a uma revisão publicada, não a um tag inexistente.
Reinicie a sessão depois da instalação/atualização.
