# ADR-0021 — One parser owns format knowledge; a parser swap is proven behavior-neutral

## Status

Accepted

## Context

Format knowledge lived in six pattern dialects that already disagreed: one tool's pattern stricter than another's, five copies of the same header parse, three variants of one line format. The migration risk is attribution, not the calendar — a parser swap must be provably neutral at exactly the moment a conclusion depends on the difference between a rule change and a parser change.

## Decision

1. **One module is the parser.** It produces both a consumer-compatible structure and its own richer layer: a census of what it saw, a ledger of parser-internal diagnostics, and a detected dialect with a confidence level. Every consumer delegates; the legacy state machines are retired, not kept alongside.
2. **Each grammar release has an immutable identity** — a content hash is the usual implementation, and any reproducible version scheme is acceptable — and that identity is pinned in the gate.
3. **Pin every corpus document as a frozen export, by hash, before the migration.** A frozen artifact whose bytes move trips the gate instead of silently re-anchoring counts. Extending the pins is a *precondition* of the migration, not part of it, or the migration redefines its own baseline.
4. **The migration is falsifiable.** Compare records, structural invariants, and downstream observations before and after, against the pinned corpus. Require count identity where count is itself part of the contract; elsewhere require record-level semantic equivalence, since equal counts can conceal changed meaning and a correct parser may legitimately split or join records. Where output legitimately changes, document the delta as a parse *correction* with its cause named — never a silent re-anchor.
5. **Known residual defects become a pre-registered failing test set**, written *before* the migration, red against the old behavior and green against the new. Committing to the expected deltas in advance is what separates a proven migration from one rationalized afterwards.
6. **Structure failures and count failures are different.** A structural invariant failure that feeds downstream slicing pauses the run; a count mismatch is a finding, never a parse repair.
7. **Parser-internal diagnostics never enter the public findings namespace.** The boundary is a one-way translation at the parser-to-observation seam.
8. **Migrate consumers in a stated, gated order**, each against the same gate, and document any consumer deliberately *not* migrated, with the reason.

## Consequences

One dialect model and one census replace several disagreeing patterns, and the migration carries its own proof rather than an assurance. Cost: corpus maintenance is ongoing as new dialects appear, and a corrected pin carries an honesty obligation — a future refinement may move it again, and each move must be recorded as a documented correction rather than a refresh.