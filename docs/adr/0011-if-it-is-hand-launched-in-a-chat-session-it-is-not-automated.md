# ADR-0011 — If it is hand-launched in a chat session, it is not automated

## Status

Accepted

## Context

A phase was declared in-method but lived nowhere in the pipeline. The gap was closed by hand-launching agents in a chat session. That worked once and is not automation: unreproducible, unlogged, uncosted, and it left the quality gate to be run afterwards, standalone, against a file the pipeline had no record of.

## Decision

1. **The phase lives in the pipeline, with a run record.** Every model call is logged the way every other phase logs one, so the output is reconstructible from the record alone.
2. **Gates run inside the phase, on the phase's own output.** A gate beside the pipeline is a gate someone forgets, and a skipped gate is indistinguishable downstream from a passing one.
3. **Open human decisions are an input, not a blocker.** Declare each pending decision, its branches, and the units it blocks in a data file. Instruct the model to describe the branches neutrally and never resolve one, and mark the affected units *deterministically* from the declared list rather than trusting the model to remember. A complete output is one where every pending decision is enumerated and keyed — not one with no visible gaps.
4. **Derive artifact properties, never assume them.** A count or a layout that held for the first input is not a constant.
5. **One command chains the phases, and run health is checked between stages** rather than trusting a status line. Refuse to proceed past a parked stage unless the caller adjudicates that specific stage with a recorded reason. **There is no blanket force flag:** an override carrying no reason is indistinguishable, one session later, from a failure that never happened.
6. **Re-using a completed, compatible run is first-class**, not a shortcut — and re-deriving invalidates any adjudication built on the previous set.
7. **The chain stops before the live external write**, and a downstream stage never trusts an upstream stage's output without re-verifying what it depends on.

## Consequences

One command, one run record, and iteration becomes cheap. Cost: another module in the chain, and some duplicated runner code deliberately held apart so a change to one phase cannot silently alter another. The pipeline must keep clear boundaries between re-derivation, redrafting, approval, and execution.