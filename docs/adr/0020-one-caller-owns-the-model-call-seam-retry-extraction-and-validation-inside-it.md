# ADR-0020 — One caller owns the model-call seam: retry, extraction, and validation inside it

## Status

Accepted

## Context

Three adapters sat at the model-call seam: a shared caller, a re-implementation inside the orchestrator, and an inline subprocess call in a third tool. Three independent implementations of one boundary is a seam in name only — it returned raw text, so every caller owned extraction, retry, and failure policy.

The consequences were measurable. Exactly one retry site existed in the whole toolchain, and it covered a format glitch; the timeout on the same call, at a self-measured rate of roughly one in ten, had no retry at all. One transient failure on a final aggregation call discarded every completed per-unit draft feeding it. And two copies of the response extractor had silently diverged — one tried objects first, the other arrays — so they agreed on every multi-element response and disagreed on a single-element one.

## Decision

1. **One caller is the single seam**, owning invocation, extraction, retry classification, validation dispatch, timeout, cost accounting, lineage, and call logging. Other entry points become thin delegations that preserve their own counters.
2. **Retry eligible transport and format failures only** — timeout, transport error, unextractable response — and only where the operation is safe to repeat. **Never retry to resample a semantic judgment.** Re-asking until the answer reads better is metric-gaming with extra steps.
3. **Attempt limits and backoff live in central configuration**, informed by provider behavior, deadlines, and rate limits — never hard-coded at call sites.
4. **A validation hook exists from the start, with a no-op default.** A validator failure parks immediately and never retries: a validator failure is about content, and content is not a retriable failure.
5. **Capability flags are parameters, not second methods.** A second method is how the multi-adapter shallowness this seam exists to delete grows back, and it is the most likely way this design decays.
6. **Test fakes replace the transport beneath the seam**, as a test-only subclass overriding the private runner. The production interface carries no hook whose only caller is a test.
7. **One extractor, respecting the response's requested top-level type.** Choosing one of two wrong orders preserves the bug rather than fixing it.
8. **A retried attempt's log is stamped with its successor**, so a health reader heals the first attempt instead of parking on it. Terminal failure still parks.

## Consequences

Previously unretried failures now retry, and extraction, cost, and logging collapse into one place that can be changed once. Risks: a run after this change is not bit-identical to one before it — a call that would have parked now succeeds, which is the point, but it means old runs are not comparable. The caller becomes critical infrastructure, and a loosely written validator silently weakens it, so pin validator, extraction, and compatibility behavior with tests.