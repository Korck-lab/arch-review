"""Paired bootstrap on the reviewer F1 gap, clustered by parent scenario.

The taskset holds 21 task directories but only 6 independently authored
scenarios: the 15 sub-tasks are slices of those same 6 diffs (ADR-0029), and
the 3 rollouts per task measure sampling noise, not new task evidence. Treating
21 or 126 as the sample size would understate the uncertainty by a wide margin.

So the resample unit is the parent scenario. Each bootstrap draw picks 6 parent
scenarios with replacement and recomputes the mean F1 gap over every rollout
belonging to them, keeping both reviewers on the same draw (paired). The two
populations are reported apart for the same reason `results_table.py` keeps
them apart.

F1 is recomputed from the stored metrics under the live formula (ADR-0030), so
this reads pre-ADR trace files correctly.

Usage:  python tools/significance.py <model-a> <model-b> outputs/<run-dir> ...
"""

from __future__ import annotations

import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent))  # import the sibling module

from results_table import _SUBTASK, rollouts  # noqa: E402

DRAWS = 10_000
SEED = 20260824  # pinned: the reported interval must be reproducible


def load(run_dirs: list[str]) -> dict[str, dict[tuple[str, str], list[float]]]:
    """(population -> (parent scenario, model) -> F1 of every rollout)."""
    data: dict[str, dict[tuple[str, str], list[float]]] = {
        "curated": defaultdict(list),
        "sub-tasks": defaultdict(list),
    }
    for d in run_dirs:
        for model, task_id, f1, _ in rollouts(Path(d)):
            population = "sub-tasks" if _SUBTASK.search(task_id) else "curated"
            data[population][(_SUBTASK.sub("", task_id), model)].append(f1)
    return data


def gap(cell: dict[tuple[str, str], list[float]], draw: list[str], a: str, b: str) -> float | None:
    """Mean F1 of `a` minus mean F1 of `b` over the drawn scenarios."""
    fa = [f for p in draw for f in cell.get((p, a), [])]
    fb = [f for p in draw for f in cell.get((p, b), [])]
    if not fa or not fb:
        return None
    return mean(fa) - mean(fb)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    model_a, model_b, run_dirs = argv[0], argv[1], argv[2:]
    rng = random.Random(SEED)
    data = load(run_dirs)

    print(f"{model_a} minus {model_b}; {DRAWS} draws, resampled by parent scenario, seed {SEED}\n")
    for population, cell in data.items():
        scenarios = sorted({p for p, _ in cell})
        observed = gap(cell, scenarios, model_a, model_b)
        if observed is None:
            print(f"{population}: no paired rollouts")
            continue
        draws = sorted(
            g
            for g in (
                gap(cell, [rng.choice(scenarios) for _ in scenarios], model_a, model_b)
                for _ in range(DRAWS)
            )
            if g is not None
        )
        lo = draws[int(0.025 * len(draws))]
        hi = draws[int(0.975 * len(draws))]
        favours_a = sum(1 for g in draws if g > 0) / len(draws)
        verdict = "separated" if lo > 0 or hi < 0 else "not separated at 95%"
        print(
            f"{population}: {len(scenarios)} scenarios, gap {observed:+.3f}, "
            f"95% CI [{lo:+.3f}, {hi:+.3f}], P({model_a} ahead) {favours_a:.2f} — {verdict}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
