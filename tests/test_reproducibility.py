"""Tests for the verdict-file reproducibility keys (spec #9, runner layer).

The keys are pure functions: identical inputs byte-identical, any component
change flips the key.
"""

from __future__ import annotations

from arch_review_v1.reproducibility import (
    content_hash,
    gold_version,
    prompt_version,
    review_hash,
    verdict_key,
)
from arch_review_v1.schemas import Defect, Distractor


def _gold() -> dict:
    return {
        "id": "t001-payment-race",
        "difficulty": "medium",
        "source": {"kind": "synthetic"},
        "defects": [
            Defect(
                id="d1",
                category="concurrency",
                file="billing/charge.py",
                lines=[25, 27],
                summary="check-then-act race",
                rationale="hand-written",
            )
        ],
        "distractors": [
            Distractor(
                id="x1",
                file="billing/retry.py",
                lines=[13, 27],
                concern="duplicate charge on retry",
                why_ok="the gateway dedups identical-key replays",
            )
        ],
    }


def test_content_hash_is_deterministic_and_order_free():
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})
    assert content_hash({"a": 1}) != content_hash({"a": 2})


def test_gold_version_is_stable_and_sensitive():
    gold = _gold()
    v1 = gold_version(gold)
    assert gold_version(gold) == v1
    gold["defects"][0] = Defect(
        id="d1",
        category="concurrency",
        file="billing/charge.py",
        lines=[25, 27],
        summary="changed summary",
        rationale="hand-written",
    )
    assert gold_version(gold) != v1


def test_gold_version_includes_prompt_notes():
    gold = _gold()
    v1 = gold_version(gold)
    gold["prompt_notes"] = "PR says it improves checkout performance"
    assert gold_version(gold) != v1


def test_prompt_version_extracts_the_stem():
    assert prompt_version("claim_extractor.v1.md") == "claim_extractor.v1"
    assert prompt_version("matcher.v1.md") == "matcher.v1"


def test_review_hash_is_short_and_sensitive():
    assert len(review_hash("a review")) == 16
    assert review_hash("a review") != review_hash("a different review")


def test_verdict_key_all_components_matter():
    base = verdict_key("t001", "a review", "goldv1", "promptv1", "model-a")
    assert base == verdict_key("t001", "a review", "goldv1", "promptv1", "model-a")
    assert len(base) == 16
    assert base != verdict_key("t002", "a review", "goldv1", "promptv1", "model-a")
    assert base != verdict_key("t001", "other review", "goldv1", "promptv1", "model-a")
    assert base != verdict_key("t001", "a review", "goldv2", "promptv1", "model-a")
    assert base != verdict_key("t001", "a review", "goldv1", "promptv2", "model-a")
    assert base != verdict_key("t001", "a review", "goldv1", "promptv1", "model-b")
