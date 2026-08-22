"""Tests for taskset loading: the dataset contract at the load seam."""

from __future__ import annotations

from arch_review_v1.config import ArchReviewTasksetConfig
from arch_review_v1.taskset import ArchReviewTaskset


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
