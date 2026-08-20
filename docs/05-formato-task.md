# Formato de uma task

```
tasks/
  t001-payment-race/
    diff.patch          # o diff a revisar (50–300 linhas, sintético ou OSS c/ licença citada)
    context.md          # descrição do sistema fingido (2-5 parágrafos) + o que o PR diz que faz
    gold.yaml           # gabarito
```

## gold.yaml
```yaml
id: t001-payment-race
difficulty: medium          # easy | medium | hard
source: synthetic           # ou URL + licença se derivado de OSS
defects:
  - id: d1
    category: concorrencia
    file: billing/charge.py
    lines: [42, 58]
    summary: "check-then-act entre saldo e débito sem lock; dupla cobrança sob corrida"
    rationale: >
      Escrito à mão: por que é bug, cenário concreto de falha, como um reviewer sênior o formularia.
distractors:
  - file: billing/retry.py
    why_ok: "retry tem idempotency-key; parece duplicação mas não é"
prompt_notes: "PR diz 'melhora performance do checkout'"
```

## Scoring
- **defect_recall**: judge compara cada issue do review do modelo com `defects[]` (match semântico: mesmo arquivo/tema/causa). recall = matched/total.
- **precision**: issues do modelo sem correspondência em `defects[]` nem explicáveis pelos `distractors` contam como falso alarme. precision = matched/claimed.
- Reward final sugerido: média harmônica (F1), + métricas por categoria para o README.
- Judge: rubrica fixa, temperatura 0, modelo barato-forte (definir na Fase 3); prompt do judge versionado no repo.
