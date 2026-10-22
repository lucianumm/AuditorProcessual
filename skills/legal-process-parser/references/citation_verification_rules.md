# Conferência de citações em fonte oficial

Toda citação (artigo, súmula, OJ, PN, Tema, ADI/ADC/ADPF, NR, IN) é conferida na
consulta nova da própria resposta: o dispositivo existe na fonte, o trecho
pertence a ele e as marcas de versão ou situação ficam registradas. A incidência
no caso continua sendo análise autoral.

## Rota por tipo de fonte

`references/official_source_registry.json` indica o portal e a via de acesso.

- **Legislação (Planalto):** captura local (`response_research.py consult`).
  O texto compilado traz "(Revogado pela…)", "(Redação dada pela…)",
  "(Incluído pela…)", "(Vide ADI…)" e "(Vigência)".
- **TST (inclusive JusLaboris), STF, STJ, TRTs, LexML, Mediador, OIT:** recusam clientes automatizados
  (desafio anti-robô, 403). Consultar pelo navegador da IA e registrar com
  `browser`; ou usar arquivo oficial enviado pelo usuário. Se nem isso for
  possível, registrar a tentativa com `response_research.py unavailable` e
  delimitar a questão.
- **Índices econômicos (BCB/SGS):** captura JSON com recibo por série e período.

Página de bloqueio, corpo vazio ou resposta diferente de 200 nunca vira fonte:
o capturador recusa e a sessão registra `blocked_by_portal`.

## O que copiar da fonte

- **Artigo:** o dispositivo completo (caput, § ou inciso citado) com a marca de
  redação que o acompanha. Citar `provision` estruturado: "CLT, art. 71, § 4º".
- **Súmula/OJ/PN:** número, texto e a linha de situação (resolução, redação,
  cancelamento, DEJT). A Res. 225/2025 do TST cancelou súmulas e OJs superadas
  pela Lei 13.467/2017; conferir sempre a situação atual.
- **Tema/ação de controle:** tese, data do julgamento, situação (mérito pendente,
  tese firmada, embargos, trânsito, suspensão nacional) e modulação.
- O trecho tem ao menos três palavras e sai do dispositivo citado; quebras de
  linha do HTML não importam.

## Verificação local

```text
python scripts/response_research.py saida verify --id RESPOSTA --review legal_review.json
python scripts/citation_check.py check --record saida/research_sources/ID.json --provision "art. 71, § 4º" --quote "..." --fact-date 2016-03-01
```

Achados bloqueantes impedem a vinculação da resposta:
`provision_not_found`, `paragraph_not_found`, `quote_outside_provision`,
`quote_in_struck_text`, `precedent_not_found`, `quote_too_short`, URL da
consulta diferente da URL da norma.

Achados que qualificam a conclusão e exigem análise expressa:
`provision_revoked`, `provision_vetoed`, `wording_changed_after_facts`,
`provision_added_after_facts`, `wording_date_to_confirm`,
`constitutional_challenge_noted`, `precedent_cancelled_or_revoked`,
`precedent_suspended`, `tema_status_not_observed`, `provision_not_isolated`.

`provision_unstructured` indica dispositivo sem número reconhecível: a conferência
estrutural não foi executada e isso deve constar da limitação.

## Direito intertemporal

Marcas de versão são comparadas com as datas dos fatos (`normative_map.relevant_dates`
e átomos dos fatos). Fatos anteriores a 11/11/2017 seguem a redação anterior à
Lei 13.467/2017 (IRR Tema 23 do TST: aplicação imediata aos contratos em curso
para fatos a partir dessa data). Atualização monetária e juros mudam em
30/08/2024 (Lei 14.905/2024). Datas catalogadas orientam o alerta; a vigência
exata é confirmada na fonte.

## Na redação

- Parágrafo de fundamentos, impugnação ou pedidos que cite norma precisa vincular
  em `norm_ids` a norma conferida correspondente; citações soltas são recusadas.
- `fontes.md` informa por citação: "conferida por captura HTTP", "observada pela
  IA (não atestada)" ou "não conferida — portal bloqueou acesso automatizado".
- Nunca completar número, redação, data ou situação de memória.
