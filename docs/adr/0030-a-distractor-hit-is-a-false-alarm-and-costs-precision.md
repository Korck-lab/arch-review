# ADR-0030 — A distractor hit is a false alarm and costs precision

## Status

Accepted. Reverses the "distractor exempt" clause locked in issue #3.

## Context

A distractor is correct code planted in the diff because it looks suspicious. `docs/04-defect-taxonomy.md` states its purpose in one line: it exists "to measure precision/false alarm". A reviewer that calls it a bug has misread working code, which is exactly the failure the precision term is meant to price.

The scoring formula locked in issue #3 did the opposite. It read "distractor exempt" and removed distractor verdicts from the precision denominator, alongside the neutral duplicate. `scoring.py` implemented that faithfully: `scoreable = claim_count - distractor_hits - duplicate`.

The exemption makes the distractor free. A reviewer can flag every planted distractor and lose nothing, so the hardest calls in the dataset apply no reward pressure at all. The curation cost of writing a defensible `why_ok` for each distractor bought no measurement. This is the root cause, not a tuning knob (ADR-0027): the mechanism the taxonomy describes was not connected to the score.

The counter-argument for exemption is that a distractor is the most defensible mistake a careful reviewer can make, so charging for it punishes caution. That argument does not survive the definition. A review that names working code as a defect sends an engineer to fix nothing. The cost of that is the whole reason precision is in the reward.

## Decision

1. **A distractor verdict counts in the precision denominator.** `precision = matched / (claims - duplicate)`. Only the duplicate — a second claim on an already-credited defect — stays neutral.
2. **`distractor_hits` remains a reported metric.** The count is still recorded on the trace and still separable from `false_alarms` in analysis. Only its effect on the score changes.
3. **A review made entirely of distractor claims scores precision 0, not 1.** The empty-denominator guard now fires only on an empty review, where recall is 0 and F1 is 0 regardless.
4. **Traces written before this ADR are rescored, never reused as-is.** `tools/results_table.py` recomputes F1 and precision from the stored metrics under the live formula. `matched` is recoverable from the old precision and its own denominator, so the rescore is exact arithmetic and needs no new judge call.

## Consequences

Published numbers move. Rescoring the 126-episode slate drops curated opus F1 from 0.828 to 0.758 and haiku from 0.848 to 0.833; sub-task opus goes 0.556 to 0.526 and haiku 0.492 to 0.476. The curated tier moves most, because that is where the distractors live — sub-tasks ship without them by ADR-0029.

The change also separates the two reviewers on a new axis. Opus hit 0.667 distractors per curated rollout against haiku's 0.111, which the old formula discarded entirely.

Cost: every trace file predating this ADR carries a stale `precision` metric and a stale `f1` reward. The rescore in `results_table.py` is the only correct reader of those files. A future run written under the live formula passes through it unchanged, since the recompute is the identity when no distractor was hit.
