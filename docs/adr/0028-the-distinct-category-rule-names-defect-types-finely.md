# ADR-0028 — The distinct-category rule names defect types finely; authorization, injection, and traversal are separate from security

## Status

Accepted

## Context

The dataset contract requires every defect in a medium or hard task to carry a distinct category (`DIFFICULTY_RULES` in `arch_review_v1/contract.py`). The rule exists to force varied defect types: a task should exercise more than one review skill, and two defects of the same type are redundant.

`CATEGORIES` held seven terms, and `security` was one of them. The bucket is wide enough to hide real variance. Path traversal, injection, a missing ownership check, SSRF, and secret mishandling all landed in `security`, yet they are different review skills: one reviewer reads path construction, another reads authorization semantics, a third reads server-side request flow. A hard task can plausibly carry two of them on different mechanisms.

The pilot hit this twice (issue #11). Seeding a second security-family defect moved a task to hard, where the distinct rule rejected the pair:

- t003: d1 is a path traversal. A candidate second defect, a missing ownership link between `user` and `report_id`, is also `security`.
- t006: d2 is missing ownership middleware. A candidate SSRF on the caller-supplied webhook URL is also `security`.

The candidates themselves were later examined against the rollout data and judged not defensible — the reviewers flag cross-user path writes (traversal, already d1), not a read-side IDOR, and t006's recurring concern was the unvalidated body, seeded as a resilience defect with no category conflict. The structural problem remains: at the pilot's current scale the rule has already blocked twice, and Phase 1 targets 30 tasks. Same-family pairs on different mechanisms will recur.

Relaxing the rule — "at least two distinct categories" — would retune the gate, which ADR-0018 forbids. Keeping the coarse bucket leaves real pairs unseedable as the taskset scales.

## Decision

1. **Widen `CATEGORIES` by splitting `security` into disjoint sub-terms.** The distinct check itself is untouched: it still requires every defect in a task to carry a different term.
2. **Define the security-family terms so they do not overlap.** A defect gets exactly one.
   - `authorization` — missing or incorrect access control: ownership checks, middleware, ACLs, IDOR.
   - `injection` — untrusted input reaching an interpreter: SQL, shell, format strings, eval.
   - `traversal` — path escape via separators or leading dots.
   - `security` — the residue: secret handling, cryptography, SSRF, CSRF, TLS, rate and abuse.
3. **Reclassify existing seeds to the finer terms where they clearly belong.** t003's path-traversal defect becomes `traversal`; t006's missing-ownership-middleware defect becomes `authorization`. No other seed changes category.
4. **This is a gate fix, not a retune.** The rule's intent — varied defect types — is preserved and enforced over a vocabulary fine enough to express real variance. The failing bucket is the defect, and the category vocabulary is the re-anchored expectation (ADR-0018 item 2).

## Consequences

A hard task may now carry two security-family defects when they are different review skills, so the rule stops blocking legitimate pairs as the taskset scales. Per-category recall metrics gain `recall_authorization`, `recall_injection`, and `recall_traversal`; the scorer derives these names dynamically and needs no change. Cost: gold authors must pick the precise term, and the residual `security` bucket is defined by exclusion. Risk: a defect might straddle two sub-terms; the definitions above decide each case by its primary mechanism.
