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
source: { kind: synthetic }  # kind: synthetic | oss; oss also needs url, license, attribution
defects:
  - id: d1
    category: concurrency
    file: billing/charge.py
    lines: [42, 58]
    summary: "check-then-act between balance and debit without lock; double charge under race"
    rationale: >
      Hand-written: why it is a bug, concrete failure scenario, how a senior reviewer would phrase it.
distractors:
  - id: x1
    file: billing/retry.py
    lines: [13, 27]
    concern: "duplicate charge on retry"
    why_ok: "retry has an idempotency-key; it looks like duplication but it is not"
prompt_notes: "PR says 'improves checkout performance'"
```

## Scoring
- **defect_recall**: judge compares each issue in the model's review with `defects[]` (semantic match: same file/theme/cause). recall = matched/total.
- **precision**: model issues with no match in `defects[]` and not explained by the `distractors` count as false alarms. precision = matched/claimed.
- Suggested final reward: harmonic mean (F1), plus per-category metrics for the README.
- Judge: fixed rubric, `claude-sonnet-5`, overridable via `env.taskset.task.judge.model`; judge prompt versioned in `prompts/judge/*.v1.md`.
- The judge asks for `temperature=0.0` (`config.py:21`) and sends it on the wire (`verifiers/v1/judge.py:178`). The dev shim `tools/claude_proxy.py` **discards** it, so a run through the shim is not temperature-pinned. See the README section "Reproducibility".
