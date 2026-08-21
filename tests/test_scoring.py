"""Tests for the deterministic scorer (the test seam, spec #9)."""

from __future__ import annotations

import pytest

from arch_review_v1.schemas import Claim, Defect, Verdict
from arch_review_v1.scoring import score_review


def _defect(defect_id: str = "d1", category: str = "concurrency") -> Defect:
    return Defect(
        id=defect_id,
        category=category,
        file="billing/charge.py",
        lines=[25, 27],
        summary="a seeded defect",
        rationale="hand-written rationale",
    )


def _claim(claim_id: str = "c1") -> Claim:
    return Claim(id=claim_id, file="billing/charge.py", quote="an issue", summary="an issue")


def _verdict(
    claim_id: str,
    kind: str,
    defect_id: str | None = None,
    second: str | None = None,
    status: str = "full",
    distractor_file: str | None = None,
    unsure: bool = False,
) -> Verdict:
    return Verdict(
        claim_id=claim_id,
        kind=kind,
        defect_id=defect_id,
        second_defect_id=second,
        status=status,
        distractor_file=distractor_file,
        unsure=unsure,
    )


def test_all_full_match_scores_perfect():
    defects = [_defect("d1"), _defect("d2", category="operability")]
    claims = [_claim("c1"), _claim("c2")]
    verdicts = [_verdict("c1", "matched", "d1"), _verdict("c2", "matched", "d2")]
    score = score_review(defects, claims, verdicts)
    assert score.recall == pytest.approx(1.0)
    assert score.precision == pytest.approx(1.0)
    assert score.f1 == pytest.approx(1.0)


def test_partial_match_counts_half_in_recall():
    defects = [_defect("d1"), _defect("d2", category="operability")]
    claims = [_claim("c1"), _claim("c2")]
    verdicts = [_verdict("c1", "matched", "d1", status="partial"), _verdict("c2", "matched", "d2", status="partial")]
    score = score_review(defects, claims, verdicts)
    assert score.recall == pytest.approx(0.5)
    assert score.precision == pytest.approx(1.0)


def test_missing_defect_lowers_recall():
    defects = [_defect("d1"), _defect("d2", category="operability")]
    claims = [_claim("c1")]
    verdicts = [_verdict("c1", "matched", "d1")]
    score = score_review(defects, claims, verdicts)
    assert score.recall == pytest.approx(0.5)
    assert score.precision == pytest.approx(1.0)


def test_false_alarm_penalizes_precision():
    defects = [_defect("d1")]
    claims = [_claim("c1"), _claim("c2")]
    verdicts = [_verdict("c1", "matched", "d1"), _verdict("c2", "false_alarm")]
    score = score_review(defects, claims, verdicts)
    assert score.recall == pytest.approx(1.0)
    assert score.precision == pytest.approx(0.5)
    assert score.f1 == pytest.approx(2 * 0.5 * 1.0 / 1.5)
    assert score.false_alarms == 1


def test_distractor_claim_is_exempt_from_precision():
    defects = [_defect("d1")]
    claims = [_claim("c1"), _claim("c2")]
    verdicts = [
        _verdict("c1", "matched", "d1"),
        _verdict("c2", "distractor", distractor_file="billing/retry.py"),
    ]
    score = score_review(defects, claims, verdicts)
    assert score.recall == pytest.approx(1.0)
    assert score.precision == pytest.approx(1.0)  # distractor excluded from denominator
    assert score.distractor_hits == 1


def test_empty_review_scores_zero_precision_one_flagged_by_claims():
    defects = [_defect("d1")]
    score = score_review(defects, [], [])
    assert score.recall == 0.0
    assert score.precision == pytest.approx(1.0)
    assert score.f1 == 0.0
    assert score.claim_count == 0  # the empty-review flag


def test_all_distractors_give_empty_denominator_precision_one():
    defects = [_defect("d1")]
    claims = [_claim("c1")]
    verdicts = [_verdict("c1", "distractor", distractor_file="billing/retry.py")]
    score = score_review(defects, claims, verdicts)
    assert score.recall == 0.0
    assert score.precision == pytest.approx(1.0)
    assert score.f1 == 0.0


def test_duplicate_claim_is_neutral_in_numerator_and_denominator():
    defects = [_defect("d1")]
    claims = [_claim("c1"), _claim("c2"), _claim("c3")]
    verdicts = [
        _verdict("c1", "matched", "d1"),
        _verdict("c2", "matched", "d1"),  # duplicate: d1 already fully credited
        _verdict("c3", "false_alarm"),
    ]
    score = score_review(defects, claims, verdicts)
    assert score.recall == pytest.approx(1.0)
    assert score.precision == pytest.approx(0.5)  # 1 matched / (3 - 1 duplicate)
    assert score.duplicate == 1


def test_second_partial_credit_is_not_duplicate():
    defects = [_defect("d1")]
    claims = [_claim("c1"), _claim("c2")]
    verdicts = [
        _verdict("c1", "matched", "d1", status="partial"),
        _verdict("c2", "matched", "d1", status="partial"),
    ]
    score = score_review(defects, claims, verdicts)
    assert score.duplicate == 0  # d1 not fully credited, so neither claim is neutral
    assert score.recall == pytest.approx(0.5)  # best status: one partial


def test_claim_credits_two_defects():
    defects = [_defect("d1"), _defect("d2", category="operability")]
    claims = [_claim("c1")]
    verdicts = [_verdict("c1", "matched", "d1", second="d2")]
    score = score_review(defects, claims, verdicts)
    assert score.recall == pytest.approx(1.0)


def test_per_category_recall():
    defects = [
        _defect("d1", category="concurrency"),
        _defect("d2", category="operability"),
        _defect("d3", category="operability"),
    ]
    claims = [_claim("c1"), _claim("c2")]
    verdicts = [
        _verdict("c1", "matched", "d1"),
        _verdict("c2", "matched", "d2", status="partial"),
    ]
    score = score_review(defects, claims, verdicts)
    assert score.per_category["concurrency"] == pytest.approx(1.0)
    assert score.per_category["operability"] == pytest.approx(0.25)  # 0.5 / 2


def test_unsure_verdicts_count_review_required():
    defects = [_defect("d1")]
    claims = [_claim("c1")]
    verdicts = [_verdict("c1", "matched", "d1", unsure=True)]
    score = score_review(defects, claims, verdicts)
    assert score.review_required == 1


def test_metrics_names_present():
    defects = [_defect("d1", category="concurrency")]
    claims = [_claim("c1")]
    verdicts = [_verdict("c1", "matched", "d1")]
    metrics = score_review(defects, claims, verdicts).metrics
    for name in (
        "recall",
        "precision",
        "distractor_hits",
        "false_alarms",
        "claim_count",
        "duplicate",
        "review_required",
        "recall_concurrency",
    ):
        assert name in metrics
