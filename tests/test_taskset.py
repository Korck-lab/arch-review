"""Tests for taskset loading: the dataset contract at the load seam."""

from __future__ import annotations

import re

import yaml

from arch_review_v1.config import ArchReviewTasksetConfig
from arch_review_v1.taskgen import decompose
from arch_review_v1.taskset import ArchReviewTaskset, _TASK_DIR


def test_load_builds_the_six_pilots_and_their_easy_subtasks():
    ts = ArchReviewTaskset(ArchReviewTasksetConfig())
    tasks = ts.load()
    assert len(tasks) == 19
    assert [t.data.task_id for t in tasks] == [
        "t001-payment-race",
        "t001-payment-race-d1",
        "t001-payment-race-d2",
        "t001-payment-race-d3",
        "t002-shop-orders",
        "t003-reports-export",
        "t003-reports-export-d1",
        "t003-reports-export-d2",
        "t004-warehouse-sync",
        "t004-warehouse-sync-d1",
        "t004-warehouse-sync-d2",
        "t005-notify-queue",
        "t005-notify-queue-d1",
        "t005-notify-queue-d2",
        "t005-notify-queue-d3",
        "t006-customer-webhooks",
        "t006-customer-webhooks-d1",
        "t006-customer-webhooks-d2",
        "t006-customer-webhooks-d3",
    ]


def test_load_builds_the_pilot_task():
    ts = ArchReviewTaskset(ArchReviewTasksetConfig())
    task = ts.load()[0]
    assert task.data.file_list == ["billing/charge.py", "billing/retry.py"]
    assert [d.id for d in task.data.seeded_defects] == ["d1", "d2", "d3"]
    assert [x.id for x in task.data.distractors] == ["x1", "x2"]
    assert task.data.difficulty == "hard"
    assert "checkout" in task.data.prompt
    assert "billing/charge.py" in task.data.diff


def test_every_committed_subtask_is_reproducible_from_its_parent(tmp_path):
    """ADR-0029: the taskset ships exactly the deterministic decomposition.

    Every hard task must ship its decomposition: one committed sub-task per
    clean split. The splitter is deterministic, so re-running it into a fresh
    directory must reproduce the committed `-dN` directories byte for byte. A
    defect the splitter marks needs-hand-write must not appear as a committed
    sub-task. Any committed `-dN` directory that is not cleanly reproducible
    fails here.
    """
    for task_dir in sorted(_TASK_DIR.glob("t[0-9][0-9][0-9]-*")):
        if re.search(r"-d[0-9]+$", task_dir.name):
            continue  # a sub-task, not a parent; the parent drives the check
        produced = decompose(task_dir, tmp_path / task_dir.name)
        clean = {
            p.name
            for p in produced
            if yaml.safe_load((p / "_meta.yaml").read_text())["status"] == "clean"
        }
        committed_ids = {
            p.name for p in _TASK_DIR.glob(f"{task_dir.name}-d[0-9]*")
        }
        assert clean == committed_ids, (
            f"{task_dir.name}: splitter clean {sorted(clean)}, "
            f"committed {sorted(committed_ids)}"
        )
        for sub_path in sorted(produced):
            if sub_path.name not in committed_ids:
                continue
            gold = yaml.safe_load((sub_path / "gold.yaml").read_text())
            assert gold["difficulty"] == "easy"
            assert len(gold["defects"]) == 1
            for fname in ("diff.patch", "context.md", "gold.yaml", "_meta.yaml"):
                assert (sub_path / fname).read_text() == (
                    _TASK_DIR / sub_path.name / fname
                ).read_text(), f"{sub_path.name}/{fname} drifted from the splitter"
            gold = yaml.safe_load((sub_path / "gold.yaml").read_text())
            assert gold["difficulty"] == "easy"
            assert len(gold["defects"]) == 1
            for fname in ("diff.patch", "context.md", "gold.yaml", "_meta.yaml"):
                assert (sub_path / fname).read_text() == (
                    _TASK_DIR / sub_path.name / fname
                ).read_text(), f"{sub_path.name}/{fname} drifted from the splitter"
