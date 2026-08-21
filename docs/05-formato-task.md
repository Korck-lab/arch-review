# Task format

```
tasks/
  t001-payment-race/
    diff.patch          # the diff to review (50–300 lines, synthetic or OSS with cited license)
    context.md          # description of the fake system (2-5 paragraphs) + what the PR says it does
    gold.yaml           # gold answer
```

## gold.yaml
```yaml
id: t001-payment-race
difficulty: medium          # easy | medium | hard
source: synthetic           # or URL + license if derived from OSS
defects:
  - id: d1
    category: concurrency
    file: billing/charge.py
    lines: [42, 58]
    summary: "check-then-act between balance and debit without lock; double charge under race"
    rationale: >
      Hand-written: why it is a bug, concrete failure scenario, how a senior reviewer would phrase it.
distractors:
  - file: billing/retry.py
    why_ok: "retry has an idempotency-key; it looks like duplication but it is not"
prompt_notes: "PR says 'improves checkout performance'"
```

## Scoring
- **defect_recall**: judge compares each issue in the model's review with `defects[]` (semantic match: same file/theme/cause). recall = matched/total.
- **precision**: model issues with no match in `defects[]` and not explained by the `distractors` count as false alarms. precision = matched/claimed.
- Suggested final reward: harmonic mean (F1), plus per-category metrics for the README.
- Judge: fixed rubric, temperature 0, cheap-strong model (to define in Phase 3); judge prompt versioned in the repo.
