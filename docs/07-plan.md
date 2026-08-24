# Execution plan (estimate 1–2 business days)

## Phase 1 — Dataset (the bulk of the value; ~half a day+)
- [x] Write 6 pilot tasks (1 per main category), with complete gold.yaml
- [x] Validate format by running 1 model by hand (covered by the first 6/6 episode run)
- [x] 6 curated scenarios covering all 7 categories, decomposed into 15 single-defect sub-tasks (ADR-0029) — 21 tasks total.
      The original "30 tasks" target is dropped for v1: the risk section below ranks shipping over breadth, and coverage of every category is already met.

## Phase 2 — Environment (~2-3h with scaffold)
- [x] Scaffold and implement ReviewData/ReviewTask/Taskset (package `arch_review_v1`, 48 tests green)
- [x] Two judges with rubrics; one F1 reward with inline `record_metrics`
- [x] `uv run eval` smoke test with 3 tasks — runs via `tools/claude_proxy.py` + `claude -p` (no paid inference), 3/3 episodes scored, avg F1 0.50

## Phase 3 — Results (~2h + API cost)
- [x] Full eval on 2 models — `claude-opus-5` and `claude-haiku-4-5`, 21 tasks × 3 rollouts each, 126 episodes.
      A third model, `claude-fable-5`, was run and excluded: 49 of 63 rollouts died on proxy `502`. See the README.
- [x] Final README in English: methodology, score table, per-category analysis

## Phase 4 — Publish
- [x] Public repo on GitHub — https://github.com/Korck-lab/arch-review
- [x] `prime login` (Rafael) + `prime env push` — [korck/arch-review-v1](https://app.primeintellect.ai/dashboard/environments/korck/arch-review-v1), public, Hub integration test green

## Phase 5 — Apply
- [x] Typeform filled and submitted 24 Aug 2026 with Rafael's ok.
      The draft left the public repo (it held an e-mail address); the submitted copy is kept outside the repo.

## Risks
- SWE-Swiss assigned to someone else during the build → plan Bs on the same credential
- Unstable judge on matching → fix rubric + few-shot examples in the judge prompt; measure agreement on 5 tasks by hand
- Spreadsheet dates indicate their slow review cycle — apply right after publishing, do not wait for infinite polish
