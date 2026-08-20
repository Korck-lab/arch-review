# ADR-0025 — Delegate context-heavy work to subagents; the main session keeps the decision

## Status

Accepted

## Context

Long sessions accumulate context faster than the work justifies. A large document export can be tens of thousands of tokens to pull into the window, a broad multi-file sweep is more, and a ruling that needs a deep, slow answer burns attention the main thread could spend on the next unit.

Compaction is the trailing fix — it shrinks a context that already grew, and discards detail on the way. Subagents are the leading one: only the subagent's report enters the main window, while the files it read, the sweeps it ran, and the long drafts it wrote stay in its own. Without a recorded rule, a session either bloats because everything is read inline, or under-delegates because a subagent is only reached for at the last moment.

## Decision

1. **Delegate when the work would pull a large or slow load into the main session.** The trigger is *what enters the main context*, not the size of the work: a multi-file read, a full-document export, a broad sweep, or a deep ruling belongs in a subagent window. The main session receives the conclusion and the load-bearing evidence for it — never raw dumps.
2. **Choose a worker suited to the task's required capability, risk, latency, and cost**, and fan out genuinely independent investigations in parallel rather than running them serially inline. Do not encode a fixed worker taxonomy or model tier here; capabilities change faster than this record does.
3. **A subagent's output is evidence to verify, not a verdict to accept.** Re-measure its load-bearing claims in the main session before they become findings, plans, or recorded decisions. A report of success is especially weak evidence that an external side effect actually landed — audit the target state directly.
4. **Delegation never bypasses a gate.** A subagent does not perform actions the project reserves for an explicit owner grant, and does not touch content owned by another party. It gathers, analyzes, and drafts.
5. **The main session owns the decision and the write.** A subagent proposes and returns; the main session adjudicates, approves, and records.

## Consequences

The main session stays lean across long runs, and deep questions get a full answer without occupying the main thread. Cost: an asynchronous round trip, and a subagent cannot see the main session's context — the prompt must carry the facts it needs, or the answer comes back weaker. Risks: trusting an unverified claim, guarded by item 3; and delegating a decision that should stay with the owner, guarded by item 5.