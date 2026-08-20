# ADR-0008 — One observation contract between the deterministic layer and the model layer

## Status

Accepted

## Context

Several deterministic producers feed one model-driven consumer. This is the seam the system hinges on; getting it wrong reworks everything downstream. The convention that a tool reports facts and the model judges them had been enforced only by reading the code. Because the consumer is a language model, the failure mode is a producer quietly emitting something that reads like a verdict, or minting an identifier it has no authority to mint — which corrupts project data rather than merely being wrong. Validating only at assembly makes it worse, because the defect surfaces far from its cause.

## Decision

One module defines one observation shape and a `validate()` that **raises**.

1. **An observation is a structured fact plus a metadata-complete evidence block:** rule or observation type, stream, severity, confidence class, the fact, and enough source provenance — coordinates or a stable source key — to re-find and verify it.
2. **`validate()` refuses** any observation that carries a verdict, mints a project-data identifier the producer has no authority to assign, or comes from an unproven rule without being marked as such. Refusal happens at production, not at assembly.
3. **Confidence class is a required enum, never an optional annotation.** An unproven rule sitting unmarked among proven ones inherits their authority; that conflation is what makes a half-finished tool look finished.
4. **Streams stay separate and the consumer joins them.** Merging a suppression ledger into the same list as findings destroys the only false-negative guard there is.
5. **Every observation carries a stable key derived canonically from its identifying fields** — a content hash is the usual implementation, and a stable upstream record key is equally valid — so two runs are compared observation by observation rather than by count.
6. **Keep a self-test with one fixture per refusal *and* false-positive guards** proving legitimate input still passes. A contract that refuses valid input is unusable and fails mid-run; over-refusal, not under-refusal, is the failure mode that actually strands a run.

## Consequences

A producer can no longer drift into writing the judgment without raising, and evidence completeness is guaranteed at the point of production rather than hoped for downstream. Cost: producers must conform to a stricter schema and evolve it through coordinated migrations, and during one a converter or a second representation may coexist with the native shape. Retire the old shape rather than maintaining both.