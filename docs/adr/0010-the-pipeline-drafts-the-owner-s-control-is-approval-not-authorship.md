# ADR-0010 — The pipeline drafts; the owner's control is approval, not authorship

## Status

Accepted

## Context

A pipeline built on the rule "the human writes the prose" stopped one step short of its own purpose. It produced a fully triaged, evidence-complete candidate set and then halted with nothing written, and the quality gate that scores authored text never ran, because no authored text existed. The prohibition was also narrower in origin than it had become in practice: it had been layered on top of a risk call the owner had already made and already owned. The opposite failure is just as real: publishing generated prose automatically removes the accountable human from the consequential decision.

## Decision

1. **Drafting is in-method.** Producing candidate text for the artifact's own fields is the pipeline's job, not a boundary it must not cross.
2. **"Draft" means pre-staging candidate.** A draft is never delivered text and never touches the live artifact. The chain is: pipeline drafts, quality gate runs, a private staging copy is produced, the owner reviews and approves, and only then the live write happens.
3. **Approval is the primary control, not bookkeeping.** Every publishable unit needs an explicit, recorded approval before any live write, and the live write is the last action. Approval includes the right to replace: the owner may rewrite any unit at any point without justification. Passing a mechanical gate never substitutes for approval.
4. **Drafting and gating are adopted as a pair.** Taking the first without the second is the reckless combination. A gate on machine-drafted output becomes the acceptance criterion rather than an advisory check, so it must be load-bearing from day one.
5. **Remediation is bounded by a declared policy.** By default: one fix, one recheck. A further pass means the underlying content is wrong — escalate rather than continue tuning. Fixing the writing usually means fixing a content violation, not a register one.
6. **Never edit a counterpart's fields**, flagged or not, without explicit authority.

## Consequences

The pipeline produces a complete deliverable instead of a candidate set, and the quality gate is finally exercised on the case it was built for. Risks: approval fatigue, answered by approving at a grouped, reviewable semantic level rather than unit by unit; and register uniformity across a whole set, which per-item scoring cannot see and only a human read catches.