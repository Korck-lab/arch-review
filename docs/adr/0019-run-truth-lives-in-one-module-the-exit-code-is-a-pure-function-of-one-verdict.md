# ADR-0019 — Run truth lives in one module; the exit code is a pure function of one verdict

## Status

Accepted

## Context

Run state was smeared across four uncoordinated records: an in-process park list that was append-only and never healed; a phase log whose parks stayed permanent even after a later round self-healed; raw per-call logs where a retried timeout stayed poisoned with no override path; and process exit codes that some stages simply discarded. Every consumer re-derived "did this succeed?" differently, so the answers disagreed. The exit surface was itself ambiguous — one code meant several different things, and some hard failures exited zero because their return codes were dropped.

## Decision

1. **One module owns run truth.** Its `verdict()` answers one question — continue, needs a human, or failed — and both non-continue states carry a **list** of reasons, never a collapsed single one.
2. **The process exit code is a pure function of that verdict.** No stage returns a per-stage constant to the caller.
3. **Healing takes machine evidence only, within the same lineage.** A stale failure is healed when a later record of the same phase, input, and retry lineage is non-parked; that later record is the evidence. A success from a different input or branch never erases an earlier failure. This removes a false failure after a sanctioned retry without editing the layer that produced it.
4. **Every override is scoped and carries a recorded reason.** There is no blanket force flag.
5. **By-design pauses are surfaced in the summary and never block**, keyed by phase, so a reader reconstructing the run cannot mistake "never ran" for "failed".
6. **Derived truth is persisted separately from the event log**, and reconstruction is read-only: it must yield a correct verdict from an old run directory with none of the new artifacts present. Lock that with a test against a mirror of a real pre-change run.
7. **State the precedence.** When a stage's artifact is present, the artifact is authoritative and the return code is diagnostic. Return-code meanings are the fallback only for stages that wrote nothing. Without stated precedence, two truth sources reappear — which is the defect being fixed.

## Consequences

"Did this run succeed?" is answered in one place, in one read, and the silent-pass holes become genuine failures. Cost: the artifact shape becomes load-bearing — every reader must tolerate a missing new key, the outcome module must explicitly understand each artifact type, and a new stage's artifact must be folded by name rather than guessed at.