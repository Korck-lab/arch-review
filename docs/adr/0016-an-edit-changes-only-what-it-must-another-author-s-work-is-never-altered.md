# ADR-0016 — An edit changes only what it must; another author's work is never altered

## Status

Accepted

## Context

Two ambiguities came to a head on one task. First, a presentational convention that had been *described* in internal notes was treated as binding, so edits were planned as annotations — old value left beside new — with the styling deferred to a second pass. The binding contract never required it, previous deliveries without it had been accepted, the machinery the second pass needed did not exist, the one attempt to build it wrote into the wrong part of the document, and until it ran the artifact carried two contradictory values side by side with nothing saying which was the correction.

Second, an edit destroyed another author's formatting without touching their text: the replaced range spanned a character they had marked, and the editor flattened the range to a single format. The text was correct; the record of their authorship was not — and no text-level instrument could have predicted it.

## Decision

1. **Plain replacement.** Unless the governing contract or format explicitly requires tracked markup, a correction replaces wrong with right and leaves nothing behind. The replacement is the final intended text, never old beside new.
2. **A plan that preserves the obsolete value is a planning bug, and it is mechanically detectable.** For every operation, diff the search text against the replacement text; if the edit script is only `equal` and `insert`, the old text survived. Refuse the plan as its own named class alongside not-found, empty-replace, and no-op. A legitimate expansion that genuinely keeps every old token may override the refusal with a recorded reason — but by exception, never by default. Without this test the rule is an aspiration nobody can run.
3. **Another author's work is never altered without explicit authority** — not their text, not their fields, not their formatting or metadata.
4. **Formatting counts as their work.** Before executing a plan, intersect every edit range against their marked runs in a format-carrying representation. Overlap means re-scope the edit, or accept the loss deliberately and record it. Never discover it afterwards.
5. **Verify with every instrument the change could damage.** Text damage is invisible to a formatting measurement and formatting damage is invisible to a content hash; run both after every pass.
6. **Verify a convention against the binding contract before building machinery for it.** A practice described in internal notes is not a requirement, and building for it can produce a worse artifact than not building at all.

## Consequences

The edit path stays inside one proven mechanism, and no self-contradicting intermediate state can exist. Cost: formatting-aware preflight is real implementation work, and a reader cannot see what changed without version history — acceptable when the contract asks for the corrected artifact rather than the difference, and a defect when it does not, so check which one the contract asks for.