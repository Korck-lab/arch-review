# Execution plan (estimate 1–2 business days)

## Phase 1 — Dataset (the bulk of the value; ~half a day+)
- [ ] Write 6 pilot tasks (1 per main category), with complete gold.yaml
- [ ] Validate format by running 1 model by hand (no verifiers yet)
- [ ] Complete 30 tasks (balance category × difficulty)

## Phase 2 — Environment (~2-3h with scaffold)
- [x] Scaffold and implement ReviewData/ReviewTask/Taskset (package `arch_review_v1`, 48 tests green)
- [x] Two judges with rubrics; one F1 reward with inline `record_metrics`
- [ ] `uv run eval` smoke test with 3 tasks (needs an inference API key)

## Phase 3 — Results (~2h + API cost)
- [ ] Full eval on 2–3 models (1 strong, 1 medium, 1 cheap)
- [ ] Final README in English: methodology, score table, per-category analysis

## Phase 4 — Publish
- [ ] Public repo on GitHub (account to confirm)
- [ ] `prime login` (Rafael) + `prime env push`

## Phase 5 — Apply
- [ ] Fill the typeform (docs/06), Rafael's review, submit with his ok

## Risks
- SWE-Swiss assigned to someone else during the build → plan Bs on the same credential
- Unstable judge on matching → fix rubric + few-shot examples in the judge prompt; measure agreement on 5 tasks by hand
- Spreadsheet dates indicate their slow review cycle — apply right after publishing, do not wait for infinite polish
