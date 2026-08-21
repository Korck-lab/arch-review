"""Tests for taskset loading: the dataset contract at the load seam."""

from __future__ import annotations

from arch_review_v1.config import ArchReviewTasksetConfig
from arch_review_v1.taskset import ArchReviewTaskset


def test_load_builds_the_pilot_task():
    ts = ArchReviewTaskset(ArchReviewTasksetConfig())
    tasks = ts.load()
    assert len(tasks) == 1
    task = tasks[0]
    assert task.data.file_list == ["billing/charge.py", "billing/retry.py"]
    assert [d.id for d in task.data.seeded_defects] == ["d1", "d2"]
    assert [x.id for x in task.data.distractors] == ["x1"]
    assert task.data.difficulty == "medium"
    assert "checkout" in task.data.prompt
    assert "billing/charge.py" in task.data.diff
