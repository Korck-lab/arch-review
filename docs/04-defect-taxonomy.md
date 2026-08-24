# Seeded defect taxonomy (manual curation — the soul of the project)

Each task seeds 1–4 defects from distinct categories. Every defect carries a gold answer with a hand-written justification — this is the anti-"vibecoded".

v1 ships 6 curated scenarios covering all seven categories, plus 15 single-defect sub-tasks derived from them (ADR-0029). Breadth of coverage came first; task count is a later axis of growth.

## Categories (from Rafael's CTO/due-diligence repertoire)
1. **Concurrency**: race condition, deadlock, check-then-act, shared state without lock
2. **Data**: N+1 query, destructive migration without rollback, missing transaction, missing index on hot query
3. **Contracts**: public API compatibility break, semantic change without versioning, swallowed silent error
4. **Security**: hardcoded secret, SQL injection, path traversal, PII logging, missing authz on new endpoint
5. **Resilience**: retry without backoff/idempotency, missing timeout, fallback that masks a failure, cache without invalidation
6. **Architecture**: introduced circular dependency, broken layer (UI→DB direct), vendor-detail coupling, growing god object
7. **Operability**: metric/log removed from critical path, feature flag without kill switch, config in code

ADR-0028 later split the security family into four disjoint terms — `authorization`, `injection`, `traversal`, and `security` (the residue: secrets, crypto, SSRF, CSRF, TLS) — because one bucket hid variance across different review skills. The enforced vocabulary in `arch_review_v1/contract.py` therefore holds **ten terms** for these seven categories. The seven above are the curation axis; the ten are the scoring labels.

## Dataset anti-patterns (avoid)
- Defect detectable by a trivial linter (then it does not measure architectural judgment)
- Giant diff (keep 50–300 lines; the signal is density, not volume)
- Unintentional ambiguity: each seeded defect must be defensible as a real bug in human code review

## Distractors
- Each task includes correct code that LOOKS suspicious (to measure precision/false alarm) — document in the gold answer why it is ok.
- A claim against a distractor is scored as a false alarm and costs precision (ADR-0030). That is what makes the `why_ok` justification worth writing.
