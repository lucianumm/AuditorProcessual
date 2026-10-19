# Controles sintéticos da v0.20.0

Comparação executada em 18/10/2026 contra a árvore do commit
36f388960ed94eff2bd94258affa8ec0c5f5c51d, com o conjunto de desenvolvimento
labor_upgrade_cases.json. São quatro regressões escolhidas pelas limitações
reproduzidas, sem amostra de generalização nem revisão jurídica profissional.

| Controle | Versão anterior | v0.20.0 |
|---|---|---|
| Usar `50 dias` como origem de percentual | Conferência numérica não distinguia a unidade | Rejeita a unidade incompatível |
| Percentual `cinquenta por cento` | Não reconhecia o valor | Reconhece e executa a transformação |
| Limite `no mínimo 50%` sem análise das condições | Aceitava a coincidência numérica | Exige tratamento do limite |
| Semana com mudança de regra e critério global fornecido | Critério global ainda não executável | Calcula 480 minutos no cenário, sem duplicar excessos diários |

Esses resultados se restringem à etapa de controle exercitada. Não demonstram
que uma conta errada seria aprovada pelo fluxo jurídico completo anterior nem
certificam a incidência das regras sintéticas. Não houve uso de autos reais,
chamada a modelo, anotação independente ou execução do PJe-Calc. Tokens não
foram medidos. Tempos registrados pelo comparador medem somente esse código.

Para reproduzir, materialize a árvore anterior em diretório separado e execute:

```text
python scripts/run_labor_regressions.py --baseline caminho/anterior --output comparacao.json
```

Para avaliar ganho profissional, aplicar PROTOCOL.md com casos autorizados,
anonimizados e rótulos independentes, além de resultados externos reais.
