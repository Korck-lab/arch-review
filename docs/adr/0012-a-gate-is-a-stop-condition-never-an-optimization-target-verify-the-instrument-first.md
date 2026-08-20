# ADR-0012 — A gate is a stop condition, never an optimization target; verify the instrument first

## Status

Accepted

## Context

Asked to make output "comfortably pass" a scoring gate, several rewrite experiments all failed, and a counterfactual explained why: substituting maximally good text into every field the project controlled did not move the document score, while a power control proved the measurement could detect deliberately degraded text. The same investigation exposed a defect in the instrument itself — one model was loaded in training mode, so dropout was active at inference. Byte-identical inputs scored far apart, and some identical windows crossed the gate in one pass and not another. Every earlier number from that instrument was an indication, not a measurement.

## Decision

1. **The gate gates; it is never optimized against.** No process may take "the number went down" as its acceptance criterion — not at generation time, not at rewrite time. Moving the optimization upstream into the generator's prompt is the same loop with a longer edge.
2. **Print the score; never act on it.** A loop whose stopping condition is the metric is the defect, even when its arithmetic turns out to have been sound.
3. **Check the property you actually want.** Replace a score-shaped check with a correctness-shaped one: does the replacement still say what the original said, completely and clearly? That is a standard you can hold an artifact to; a threshold on a score is a claim about the instrument.
4. **Bound any gate-triggered remediation.** One fix, one recheck, then escalate. Indefinite iteration against a threshold is the prohibited loop regardless of intent.
5. **Results predating an instrument fix are not reproducible and may not be cited as measurements.** Anything load-bearing is re-scored.
6. **Reproducibility is a checked property.** Configure inference deterministically where possible. Any conclusion resting on a score difference must include byte-identical replicates and report their spread. A difference smaller than the replicate spread is not a difference.
7. **A derived budget is a claim about the artifact and may be enforced; it is not an exemption.** A length or density budget derived from the project's own accepted output may gate, provided it has been shown to stand for the property it claims — and it is subject to this same rule: a stop condition, never a target. This record does not prohibit numeric gates; it prohibits optimizing against any proxy.

## Consequences

A question about output quality gets answered with a measurement instead of a rewrite. One real defect leaves the instrument, and the project's own prior numbers are honestly downgraded until re-scored. Cost: replicate runs and power controls are extra work, independent quality checks need their own design, and the honest answer is sometimes "the gate cannot be moved by anything we control", which is a finding rather than a failure.