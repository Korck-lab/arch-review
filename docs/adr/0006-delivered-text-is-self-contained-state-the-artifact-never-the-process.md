# ADR-0006 — Delivered text is self-contained: state the artifact, never the process

## Status

Accepted

## Context

When the deliverable is a document consumed by a reader outside the project, its explanatory fields are the only place decisions get justified — and two classes of content leak into them. Internal process: how a conclusion was produced or handled ("escalated to chat", "not reproducible in our runner", "same shape as the earlier case"), tooling vocabulary, session facts. Internal coordinates: references only the producing team can resolve — checklist item numbers, internal unit identifiers, working-file paths, line numbers into a file the reader does not hold, revision numbers.

Both fail the same way: the reader cannot resolve them. Accuracy is not the issue; resolvability is. A line reference can be factually correct and still opaque, because resolving it requires holding that exact file at that exact version.

## Decision

Every claim in delivered text must be verifiable by its intended audience from the delivered artifact and sources that audience can actually reach.

1. **State the artifact.** Name the thing and the exact missing or wrong content. Where something is absent, say what the artifact lacks, not what the process lacked.
2. **No unresolvable coordinates.** Replace each internal reference with the content it points at, or drop it. References to the artifact itself, or to public standards and evidence the audience holds, are fine; references whose referent exists only inside the producing team are not.
3. **No process narration.** How the conclusion was reached is not part of the conclusion.
4. **Factually true of the artifact as it stands.** A change that was not made is a requirement, not a claim — never describe intended work as done.
5. **Internal notation stays in internal artifacts.** This rule governs delivered text only. In working notes, plans, and registers, identifiers and references are *required*; stripping them there would destroy the traceability other decisions depend on.
6. **Operational metadata belongs in its designated fields**, not inside substantive explanation.

## Consequences

Text gets slightly longer, because the referent is longer than the coordinate. It reads as written by someone who examined the artifact, which is both true and the safest posture. Process-shaped prose is also a strong signal of machine drafting, so this rule and any authorship or register gate reinforce each other. The rule needs mechanical enforcement to hold under deadline; without a check at each boundary it degrades into a style preference.