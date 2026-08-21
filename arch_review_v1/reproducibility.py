"""Verdict-file reproducibility keys (spec #9, runner layer).

Every verdict is keyed by a hash of task id, review, gold version, judge prompt
version, and judge model, so identical re-runs produce byte-identical keys. The
functions are pure; the runner derives each component and names its verdict
files with ``verdict_key``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

KEY_LENGTH = 16
"""Hex characters kept from the digest; enough to collision-separate a 30-task
eval with near-zero risk."""


def content_hash(value) -> str:
    """Canonical sha256 of a JSON value (order-free, whitespace-free)."""
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _dump(value):
    """Serialize a pydantic model in a JSON value; pass others through."""
    return value.model_dump(mode="json") if isinstance(value, BaseModel) else value


def gold_version(gold: dict) -> str:
    """Hash of the gold content that defines a task's answer.

    Only the gold fields participate — id, difficulty, source, defects,
    distractors — so a doc or prompt edit does not bump the version.
    """
    view = {
        "id": gold["id"],
        "difficulty": gold["difficulty"],
        "source": gold["source"],
        "defects": [_dump(d) for d in gold["defects"]],
        "distractors": [_dump(x) for x in gold["distractors"]],
    }
    return content_hash(view)


def prompt_version(prompt_path: str) -> str:
    """The versioned stem of a judge prompt path (``matcher.v1.md`` → ``matcher.v1``)."""
    return Path(prompt_path).stem


def review_hash(review: str) -> str:
    """Short hash of the review text."""
    return content_hash({"review": review})[:KEY_LENGTH]


def verdict_key(
    task_id: str,
    review: str,
    gold_ver: str,
    judge_prompt_version: str,
    judge_model: str,
) -> str:
    """Stable key for one verdict file: any component change flips it."""
    payload = {
        "task_id": task_id,
        "review": review,
        "gold_version": gold_ver,
        "judge_prompt_version": judge_prompt_version,
        "judge_model": judge_model,
    }
    return content_hash(payload)[:KEY_LENGTH]
