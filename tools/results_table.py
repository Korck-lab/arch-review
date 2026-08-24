"""Build the README results tables from one or more eval run directories.

Reads every `traces.jsonl` under the given run dirs, groups rollouts by task id
and reviewer model, and prints two markdown tables: the curated scenarios and
the single-defect sub-tasks derived from them (ADR-0029). The two are reported
apart on purpose — a sub-task is a slice of its parent's diff, so one blended
mean would credit the same defect twice.

Usage:  python tools/results_table.py outputs/<run-dir> [<run-dir> ...]
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

_SUBTASK = re.compile(r"-d[0-9]+$")


def model_of(run_dir: Path) -> str:
    """Reviewer id from a run dir named `<env>--<provider>--<model>--<harness>--<hash>`."""
    parts = run_dir.name.split("--")
    return parts[2] if len(parts) >= 3 else run_dir.name


def rollouts(run_dir: Path):
    """Yield (model, task_id, f1, metrics) for every scored rollout."""
    for line in (run_dir / "traces.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        task_id = rec["task"]["data"]["task_id"]
        for trace in rec["traces"]:
            rewards = trace.get("rewards") or {}
            if "f1" not in rewards:
                continue
            model = (trace.get("agent") or {}).get("model") or model_of(run_dir)
            yield model, task_id, rewards["f1"]["score"], trace.get("metrics") or {}


def table(rows: dict[str, dict[str, list]], models: list[str]) -> str:
    head = "| Task | " + " | ".join(f"{m} F1" for m in models) + " |"
    rule = "|---|" + "---|" * len(models)
    out = [head, rule]
    for task_id in sorted(rows):
        cells = []
        for m in models:
            scores = rows[task_id].get(m)
            cells.append(f"{mean(scores):.2f}" if scores else "—")
        out.append(f"| {task_id} | " + " | ".join(cells) + " |")
    means = []
    for m in models:
        allscores = [s for t in rows for s in rows[t].get(m, [])]
        means.append(f"**{mean(allscores):.2f}**" if allscores else "—")
    out.append("| **Mean** | " + " | ".join(means) + " |")
    return "\n".join(out)


def detail(rows: dict[str, dict[str, list]], metrics: dict, model: str) -> str:
    out = [
        "| Task | F1 | Recall | Precision | Claims | False alarms |",
        "|---|---|---|---|---|---|",
    ]
    for task_id in sorted(rows):
        f1 = rows[task_id].get(model)
        ms = metrics[task_id].get(model)
        if not f1 or not ms:
            continue
        g = lambda k: mean([m.get(k, 0.0) for m in ms])
        out.append(
            f"| {task_id} | {mean(f1):.2f} | {g('recall'):.2f} | "
            f"{g('precision'):.2f} | {g('claim_count'):.1f} | {g('false_alarms'):.1f} |"
        )
    allf1 = [s for t in rows for s in rows[t].get(model, [])]
    allm = [m for t in metrics for m in metrics[t].get(model, [])]
    if allf1:
        g = lambda k: mean([m.get(k, 0.0) for m in allm])
        out.append(
            f"| **Mean** | **{mean(allf1):.2f}** | {g('recall'):.2f} | "
            f"{g('precision'):.2f} | {g('claim_count'):.1f} | {g('false_alarms'):.1f} |"
        )
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    parents: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    subs: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    pmet: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    smet: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    models: list[str] = []
    for d in argv:
        for model, task_id, f1, ms in rollouts(Path(d)):
            if model not in models:
                models.append(model)
            bucket, mbucket = (subs, smet) if _SUBTASK.search(task_id) else (parents, pmet)
            bucket[task_id][model].append(f1)
            mbucket[task_id][model].append(ms)

    print(f"MODELS: {models}\n")
    print("### Curated scenarios\n")
    print(table(parents, models))
    print("\n### Single-defect sub-tasks\n")
    print(table(subs, models))
    for m in models:
        print(f"\n### Detail — {m} (curated scenarios)\n")
        print(detail(parents, pmet, m))
        print(f"\n### Detail — {m} (sub-tasks)\n")
        print(detail(subs, smet, m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
