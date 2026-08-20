# ADR-0023 — The approval ledger mints from every source, and re-entry is idempotent

## Status

Accepted

## Context

The approval ledger was the control surface for everything reaching the deliverable, but units were minted from one source only: the machine-derived candidate set. Hand-entered items arrived through a different path and were concatenated into a prompt as free-form text, so a hand item could never become a ledger unit, and the "refuse anything unapproved" flag could not see it dropped. One task was bitten exactly this way. The minting command also hard-refused when its outputs already existed, so there was no idempotent re-entry, every second run failed, and that pressure pushes people back onto the parallel manual path.

## Decision

1. **Every source normalizes into the same validated ledger envelope before approval.** Source-specific adapters may collect different raw evidence, but no source gets a lighter approval contract — a lighter schema for hand-entered items is exactly the hole that lets one escape the gate. An unvalidatable source is an unapprovable unit: an invalid item **refuses its whole declared batch** rather than skipping quietly.
2. **Keys are deterministic, derived canonically from source identity and content**, and prefixed to mark the source. The same item re-mints to the same key and never duplicates. Internal keys are barred from any text that reaches the deliverable.
3. **No backward migration: approved never becomes pending.** A materially redrafted unit is a *new* pending unit superseding the old, never a de-approved one. Detecting drift in the target artifact is the planning layer's job, not the ledger's.
4. **Superseded units are preserved, not deleted.** Deleting an approved unit would silently un-approve work already authorized and strand the record of what was authorized.
5. **The mint command is idempotently re-runnable.** The ledger *merges*: existing pending and approved units are preserved whole with their enrichment, new keys are appended, and units absent from the new set are marked superseded. Derived artifacts are regenerated; the ledger holds authoritative state. Re-runnability is a property of the one command, never a second command that can be forgotten.
6. **Prove it.** Re-running against a frozen ledger must produce zero new units and byte-identical entries.

## Consequences

Every publishable unit is visible to the approval gate, which was the whole point, and repeating an unchanged run is a no-op on ledger state. Cost: one invalid item blocks its batch, and superseded units accumulate — deliberate, but retention and presentation must preserve auditability without obscuring current units, and any future cleanup must preserve the approved set. Idempotent re-entry is guaranteed for the *same* derived set; merging a different one leaves orphaned keys that must be reconciled by hand.