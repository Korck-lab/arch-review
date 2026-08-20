# ADR-0004 — Verifying a write to a live artifact you cannot fully observe

## Status

Accepted

## Context

Some writes go to an artifact the agent cannot read back completely: a rendered document, a hosted surface, a third-party system whose exports are lossy. The write happens through an interface built for humans, and every signal available for verifying it is partial.

Three incidents shape this decision. A scope-unbounded keystroke fired while focus had silently moved off the intended field and replaced an entire document with a single string; every state signal said the operation was fine, and the only symptom was a match counter reading that looked like a wedged search. A text-level export came back byte-identical twice after edits that had genuinely changed the document's structure, so a clean verification diff proved nothing about the defect class the recipient would actually see. And two delegated background agents reported edits as complete that had never landed.

## Decision

1. **Guard the mutation with a cheap precondition read that aborts, not logs.** Before every mutating call, read the interface's own count of what the operation will affect and compare it to the expected count. A mismatch aborts that operation. A guard whose result is only logged is not a guard.
2. **An ambiguous null reading means halt and escalate to a different instrument.** A zero-match on input known to be present is equally consistent with "the operation failed" and "the target is gone." Never retry through it; stop and look with an independent instrument.
3. **Never issue a scope-unbounded destructive operation without positive proof of scope.** Prove the operation is bounded by querying live state in the same step that issues it. Signals that can lie — a stale handle, a node still present in a torn-down view — are not proof.
4. **Verify by sole-difference proof, not by presence.** Re-read the artifact, revert only the intended change in memory, and hash. If the reverted hash equals the pre-write baseline hash, the intended change is provably the *only* change. Confirming that your edit is present cannot detect collateral damage; this can.
5. **A verification instrument blind to a defect class is not a passing check.** Verify in a representation that expresses every property the consumer can perceive. Where the cheap representation is lossy, add a structural check over a faithful one, and state which defect classes each instrument can and cannot see.
6. **Resolve any discrepancy with two independent reads.** When one representation synthesizes content the source does not contain, it can never settle a question about that content alone.
7. **A success report is not evidence that a side effect landed.** After any agent or process failure — and before treating a delegated write as done — audit the target state directly.
8. **Batch an edit set into one scripted pass that logs every guard reading.** Round trips are the expensive part; the guard log is the audit trail.

## Consequences

Every write is preceded by a bounded precondition check and followed by a proof that it was the only change, which is why silent corruption stops shipping. Cost: this is materially slower per edit than blind replacement, and maintaining a second faithful representation for the structural check is real work. Richer instruments such as rendered screenshots are a bonus and never a gate, so verification never blocks on their availability.