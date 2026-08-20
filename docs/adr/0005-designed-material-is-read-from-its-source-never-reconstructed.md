# ADR-0005 — Designed material is read from its source, never reconstructed

## Status

Accepted

## Context

Some material in a project is *designed and versioned* rather than general knowledge: the rules of a method, the identifiers assigned to units of work, prescribed remedies, prescribed formats. It cannot be derived from a description, and its scope cannot be guessed from its name. A plausible reconstruction of designed material reads as authoritative and carries no error signal — that is what makes it expensive. Two reconstructions in one week produced a wrongly labeled unit of work, so the effort spent against it covered the wrong scope, and nearly minted duplicate units for damage the work itself had introduced.

## Decision

1. **Open the source before acting.** Load the method definition, spec, or rules file before answering a question, framing a unit of work, or making a change governed by it — including for a single narrow question. Memory of a previous session, a summary file, a handoff document, and a subagent's paraphrase are pointers, not sources.
2. **Do not state a rule as authoritative unless its source is loaded and version-identified.** Never invent a citation or a source location. Where a restatement is load-bearing, carry the reference with it.
3. **Identifiers are read, never inferred.** Locate the identifier in its register and quote its own text before acting on it. If a description arrives without one, search for the described content and recover the real identifier — do not assign one.
4. **A handoff is a lead, not a source.** Every load-bearing label in it — identifier, count, "verified", "already fixed" — is unverified until checked against the register and the current artifact.
5. **Damage from your own change completes the originating unit.** A defect introduced while executing a change is not a new unit of work: no new identifier, no new verdict. Repair it under the original identifier so counts stay honest. Where the project's vocabulary has no class for self-introduced damage, record it against the originating unit rather than forcing a wrong label — do not mint.

## Consequences

One extra read opens every task — cheap against one mislabeled unit. Identifiers stay traceable, so the register and the artifact cannot drift apart, and counts stay calibrated. The cost falls entirely on tasks where prior context did not already contain the authoritative material, which is exactly where the risk is.