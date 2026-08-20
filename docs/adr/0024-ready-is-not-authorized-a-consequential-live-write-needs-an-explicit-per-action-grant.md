# ADR-0024 — Ready is not authorized: a consequential live write needs an explicit, per-action grant

## Status

Accepted

## Context

The pipeline already stops short of the live external write, and separate decisions govern *how* that write is performed once it starts. What was never recorded is the **permission** rule for the write itself.

A fully verified plan and an authorized action are not the same thing. "Verified" means every precondition was checked and the change is ready; without an explicit rule it is easy for a future session to read "ready" as "licensed" and execute it. The action in question is the highest-stakes one in the workflow — hard or impossible to unwind, with a third party's work exposed to it. Reversibility through version history does not remove the operational or social consequence, so it is the wrong boundary to draw the rule at.

## Decision

1. **No consequential live external write without a current, explicit grant from the responsible owner for that action.** "Consequential" is set by the project's authorization policy and covers any mutation with external effect — a document write, a sent message, a deployment, a ticket transition — not only the irreversible ones. A verified plan is a candidate, never a license.
2. **The grant is temporary and per-action.** It covers the named target and change set and does not extend forward: a later task, a later iteration, even a later action against the same target needs a fresh grant. A past grant is never standing authorization.
3. **When in doubt whether a grant covers a particular action, ask.** Never infer a wider grant from a narrower one.
4. **Only the covered mutation is gated.** Read-only analysis, drafting, linting, plan generation, staging, and private-copy review continue freely unless separately restricted — they are exactly what makes the gated action quick and safe once granted.
5. **Prospective only.** Actions already taken under an earlier arrangement stand.

## Consequences

The highest-stakes action is never automatic, and standing authorization cannot be drifted into by silence. The handoff is unambiguous: the pipeline produces a verified plan, the owner's go-ahead executes it, and nothing in between is actionable against the live target. Cost: a verified plan cannot execute while the owner is unavailable, and repeated changes require repeated grants — which is the point. Risk: the rule being read as blocking staged or private work; it does not, because only the covered live mutation is gated.