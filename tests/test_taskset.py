"""Tests for taskset loading: the dataset contract at the load seam."""

from __future__ import annotations

from arch_review_v1.config import ArchReviewTasksetConfig
from arch_review_v1.taskset import ArchReviewTaskset


def test_load_builds_the_six_pilot_tasks():
    ts = ArchReviewTaskset(ArchReviewTasksetConfig())
    tasks = ts.load()
    assert len(tasks) == 6
    assert [t.data.task_id for t in tasks] == [
        "t001-payment-race",
        "t002-shop-orders",
        "t003-reports-export",
        "t004-warehouse-sync",
        "t005-notify-queue",
        "t006-customer-webhooks",
    ]


def test_load_builds_the_pilot_task():
    ts = ArchReviewTaskset(ArchReviewTasksetConfig())
    task = ts.load()[0]
    assert task.data.file_list == ["billing/charge.py", "billing/retry.py"]
    assert [d.id for d in task.data.seeded_defects] == ["d1", "d2", "d3"]
    assert [x.id for x in task.data.distractors] == ["x1", "x2", "x3"]
    assert task.data.difficulty == "hard"
    assert "checkout" in task.data.prompt
    assert "billing/charge.py" in task.data.diff
