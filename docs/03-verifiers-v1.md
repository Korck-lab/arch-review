# verifiers v1 — the contract (source: AGENTS.md + create-environments skill from the official repo)

Repo: https://github.com/PrimeIntellect-ai/verifiers (docs/ + skills/ are the sources; v0 `import verifiers as vf` is DEPRECATED — use `verifiers.v1`).

## Main rules
- ALWAYS start from the scaffold: `uv run init arch-review-v1` (options `-T` toolset, `-H` custom harness — probably unnecessary here).
- Run with `uv run`, never bare `python`.
- One package exports ONE `vf.Taskset` subclass via `__all__` (optional: `Env` for multi-agent, custom `Harness`). Do NOT create `load_environment()`/`load_taskset()`.
- Do not override `Taskset.__init__` (implement `load()`); do not override `Harness.__init__` (use `setup()`).
- Prefer ready-made harnesses over custom tools. Multi-run judge already exists: `--env.id agentic-judge`.
- Basic taskset = a few dozen lines: typed data/task/config classes, `load()`, decorated rewards.

## Minimal skeleton (adapted from the official example)
```python
import verifiers.v1 as vf

class ReviewData(vf.TaskData):
    seeded_defects: list[dict]   # [{id, category, file, lines, summary, rationale}]
    diff: str

class ReviewTask(vf.Task[ReviewData]):
    @vf.reward
    async def f1(self, trace: vf.Trace) -> float:
        ...  # extract claims (gold-blind) → match to gold → compute F1
             # recall, precision, distractor_hits, recall_<category> via trace.record_metrics

class ArchReviewTaskset(vf.Taskset[ReviewTask, vf.TasksetConfig]):
    def load(self) -> list[ReviewTask]:
        ...  # loads tasks/ from disk

__all__ = ["ArchReviewTaskset"]
```

> **Fixed (issues #8, #10):** `verifiers.v1` sums named rewards — `Trace.reward = sum(r.value for r in self.rewards.values())`. Two `@vf.reward` (recall + precision) would sum recall+precision, not F1. Hence a single `f1` reward. Recall, precision and per-category metrics are recorded inline via `trace.record_metrics` inside `f1` — `Task.score()` runs metrics before rewards, so `@vf.metric` hooks would force memoization.

## Before implementing, decide (checklist from the official skill)
- Dataset fields; tool need (here: none — single-turn review);
- control flow (single-turn; no simulated user);
- rewards (one F1 as single reward; recall, precision and per-category recorded inline via `record_metrics`);
- judge: yes — semantic matching between pointed-out issue and seeded defect (LLM judge with rubric).
