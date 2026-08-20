# ADR-0022 — Contract validators at the model-extraction seam, not prose in prompts

## Status

Accepted

## Context

A contract module structurally enforced the project's hard refusals on *script* output. On *model* output the same rules were prose in prompts — which is to say, unenforced. Two consequences were measured: a verdict returned in the wrong case shipped silently as unresolved, because nothing normalized the enum; and a return filter carrying two load-bearing rules was dead code, so deleting it would have dropped both with nothing failing.

This decision presumes a single model-call seam that all stages route through. Adopt that first; validators bolted onto individual call sites reproduce the problem they are meant to fix.

## Decision

1. **A dedicated module holds named per-stage contract validators**, invoked immediately after structured extraction at the single call seam. Each is a pure function from result to `(ok, reason)`: deterministic outcome, coded reason, never a crash on hostile input. **A validator failure parks; it never retries.**
2. **Model output gets no looser rule than script output.** The intuition that "the model quotes the source" inverts the real risk: a model invents an identifier-shaped token far more readily than a script does, and a wrong identifier looks exactly like a right one. This is the argument that answers the objection a reviewer will actually raise.
3. **Normalize before validating.** Case and whitespace on a closed enum are a normalization defect, not a retry case and not a validation failure.
4. **When retiring a filter, re-home its surviving rules as named validators with their own tests before deleting it.** Deleting without re-homing silently drops a rule; that is exactly how this contract eroded.
5. **Do not revive checks that are dead by design.** Record why, next to the code, so the next session does not "fix" it back.
6. **Fold every same-class check into the same module.** A range check living alone in one tool is how the pattern erodes from the other direction.

## Consequences

The hard refusals are enforced at the seam rather than requested in a prompt, contract violations stop at the model boundary with actionable reasons, and retiring the dead filter loses no rule. Cost: coverage is opt-in per stage, which is a deliberate and recorded asymmetry rather than an oversight, so new stages and new output fields must deliberately select or extend validators. A strict validator can park a whole unit on one bad field, and a loose one silently weakens the seam — pin every behavior, including "never crashes on hostile input", with tests.