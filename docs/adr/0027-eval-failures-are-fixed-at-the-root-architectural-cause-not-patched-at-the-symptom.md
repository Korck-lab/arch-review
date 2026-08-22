# ADR-0027 — An eval failure is fixed at its root architectural cause, never patched at the symptom

## Status

Accepted

## Context

The eval is the instrument; its score is the signal. A failed episode, a crashed run, or a score that does not reflect the intended signal is a defect in exactly one of five layers: the gold data, the scoring formula, the judge contracts, the harness runtime, or the model seam. The pilot loop produced all three kinds of failure.

t001's distractor claimed the retry helper forwarded the idempotency key; the diff dropped it, so every rollout that flagged the gap was penalized. The symptom was a low precision. The cause was false gold. Fixing the diff corrected the layer the defect lived in.

Run 5's model calls all exited before producing a review: the CLI's internal session-title generation hard-failed on a gateway model alias. Capping concurrency would not have fixed it. Disabling title generation and pinning the model id fixed the seam.

The distinct-category rule blocked seeding two same-category defects that were real and reviewer-confirmed. Relaxing the rule to admit them would have been retuning a gate, which ADR-0018 forbids. The rule stayed; the defect went to an issue for a human decision.

A symptom patch is tempting because it is local and fast. It leaves the cause in place, so the next task or the next run re-fires it in a new form.

## Decision

1. **Diagnose to the layer before changing anything.** Name the failing mechanism and map it to exactly one layer: gold data, scoring, judge contract, harness runtime, or model seam. A fix that changes a different layer than the one that failed is not a fix; it is a workaround wearing a fix's clothes.
2. **Fix the cause for all instances, not the one in front of you.** The fix removes the mechanism, so no future episode can hit it. If the fix is specific to one task or one run, it is a symptom patch and does not satisfy this ADR.
3. **A gate that blocks a legitimate fix is escalated, never relaxed.** Relax the gate only through its own process — a decision or an ADR — and record the escalation visibly, as an issue or an explicit hold, before any temporary workaround is adopted. ADR-0018 binds.
4. **Constraint workarounds are allowed if flagged.** A fix for an external constraint — missing funds, a closed credential, a human-gated publish — may be temporary and may change layers, but it must be labeled as such and recorded, so it is not mistaken for the root fix.
5. **Re-measure after the fix and record before and after.** A root fix changes the numbers; a symptom patch rarely does. The recorded delta is the evidence that the fix landed at the right layer.

## Consequences

Failures cost more up front — a diagnosis and a layer-appropriate fix — but stop recurring. The eval stays trustworthy: a score is the signal, and a score improved by patching gold or relaxing a gate is noise. Cost: root fixes sometimes need a human decision, as in the distinct-category case, and until it lands the workaround stays visible and the failure stays on the books. Risk: misdiagnosing the layer, which a before-and-after re-measure (item 5) catches.
