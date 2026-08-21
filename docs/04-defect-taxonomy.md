# Seeded defect taxonomy (manual curation — the soul of the project)

Each task seeds 1–4 defects from distinct categories. Target: 30 tasks, balanced coverage, increasing difficulty. Each defect has a gold answer with a hand-written justification (this is the anti-"vibecoded").

## Categories (from Rafael's CTO/due-diligence repertoire)
1. **Concurrency**: race condition, deadlock, check-then-act, shared state without lock
2. **Data**: N+1 query, destructive migration without rollback, missing transaction, missing index on hot query
3. **Contracts**: public API compatibility break, semantic change without versioning, swallowed silent error
4. **Security**: hardcoded secret, SQL injection, path traversal, PII logging, missing authz on new endpoint
5. **Resilience**: retry without backoff/idempotency, missing timeout, fallback that masks a failure, cache without invalidation
6. **Architecture**: introduced circular dependency, broken layer (UI→DB direct), vendor-detail coupling, growing god object
7. **Operability**: metric/log removed from critical path, feature flag without kill switch, config in code

## Dataset anti-patterns (avoid)
- Defect detectable by a trivial linter (then it does not measure architectural judgment)
- Giant diff (keep 50–300 lines; the signal is density, not volume)
- Unintentional ambiguity: each seeded defect must be defensible as a real bug in human code review

## Distractors
- Each task includes correct code that LOOKS suspicious (to measure precision/false alarm) — document in the gold answer why it is ok.
