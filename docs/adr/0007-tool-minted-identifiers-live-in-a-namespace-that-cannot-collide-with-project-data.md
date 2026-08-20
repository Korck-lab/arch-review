# ADR-0007 — Tool-minted identifiers live in a namespace that cannot collide with project data

## Status

Accepted

## Context

A lint tool named its rules with the same letter-and-number shape as the project's filed record identifiers. Of the strings the two vocabularies shared, only a small minority actually corresponded. A namespace that is right often enough to reward guessing is worse than one that is always wrong: it produced several documented errors, each a label trusted instead of read. This is a design defect in the tool, not indiscipline in its users — a namespace that lets two different things share a label defeats the "read, never reconstruct" rule by construction.

## Decision

1. **Identifiers minted by tooling carry a prefix and shape that cannot be confused with identifiers that are project data.** Project-data identifiers do not move; only the tool namespace changes.
2. **Enforce structurally at the mint point.** The function that registers a rule or emits an observation raises on any name outside the namespace. A convention asking people to write the full name is not enough — that convention was already in force when the errors happened.
3. **Do not emit both old and new names for compatibility.** That puts the ambiguous token back into every artifact the rename was meant to clear. Publish an old-to-new mapping in the record for human migration; no tool ever prints an ambiguous string.
4. **Check the new namespace against every other identifier vocabulary the project already uses.** A namespace fix that creates a second collision is not a fix.
5. **Plan the rename as two sweeps.** A rename converts surviving bare references from *ambiguous* into *confidently wrong*, which is worse than the starting state. Sweep full-name references mechanically first, then bare tokens filtered by context. Never rewrite project data to fit the tool.

## Consequences

A bare identifier now has exactly one reading, and the guard survives a contributor who never reads this record. Names get longer and less skimmable, and artifacts written before the rename are stale against the mapping — the mapping is the migration aid, and it belongs in the record rather than in the tool's output.