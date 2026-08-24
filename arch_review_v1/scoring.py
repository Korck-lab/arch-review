"""Deterministic scoring of one review. Pure functions; the test seam.

Scoring follows the locked formula (issue #3), as amended by ADR-0030:
- recall = (full + 0.5 x partial) / D, 1.0 when D == 0;
- precision = matched / (claims - duplicate), 1.0 on empty denominator. A claim
  against a planted distractor is correct-looking code called a bug, so it costs
  precision exactly like any other false alarm (ADR-0030 reverses the earlier
  "distractor exempt" rule). ``distractor_hits`` stays a reported metric;
- a claim matching an already-fully-credited defect is neutral: excluded from
  numerator and denominator, logged as ``duplicate``;
- F1 = 2PR/(P+R), 0 when P+R == 0;
- an empty review scores recall 0, precision 1.0, F1 0 naturally, flagged by
  ``claims = 0``;
- ``review_required`` counts verdicts the matcher marked unsure.
"""

from __future__ import annotations

from arch_review_v1.schemas import Claim, Defect, Verdict


class ReviewScore:
    """The per-task score and the metrics recorded on the trace."""

    def __init__(
        self,
        recall: float,
        precision: float,
        f1: float,
        distractor_hits: int,
        false_alarms: int,
        claim_count: int,
        duplicate: int,
        review_required: int,
        per_category: dict[str, float],
    ) -> None:
        self.recall = recall
        self.precision = precision
        self.f1 = f1
        self.distractor_hits = distractor_hits
        self.false_alarms = false_alarms
        self.claim_count = claim_count
        self.duplicate = duplicate
        self.review_required = review_required
        self.per_category = per_category

    @property
    def metrics(self) -> dict[str, float]:
        out = {
            "recall": self.recall,
            "precision": self.precision,
            "distractor_hits": float(self.distractor_hits),
            "false_alarms": float(self.false_alarms),
            "claim_count": float(self.claim_count),
            "duplicate": float(self.duplicate),
            "review_required": float(self.review_required),
        }
        for category, value in self.per_category.items():
            out[f"recall_{category}"] = value
        return out


def score_review(
    defects: list[Defect], claims: list[Claim], verdicts: list[Verdict]
) -> ReviewScore:
    """Score one review against gold."""
    claim_count = len(claims)
    review_required = sum(1 for v in verdicts if v.unsure)

    if claim_count == 0:
        return ReviewScore(
            recall=0.0,
            precision=1.0,
            f1=0.0,
            distractor_hits=0,
            false_alarms=0,
            claim_count=0,
            duplicate=0,
            review_required=review_required,
            per_category={},
        )

    distractor_hits = sum(1 for v in verdicts if v.kind == "distractor")
    false_alarms = sum(1 for v in verdicts if v.kind == "false_alarm")

    # In-order credit with the duplicate rule (locked formula, issue #3): a claim
    # whose credits are all already fully credited is neutral (excluded from
    # numerator and denominator). A defect fully credited anywhere is never
    # counted partial.
    full_credited: set[str] = set()
    partial_credited: set[str] = set()
    matched_claims = 0
    duplicate = 0
    for v in verdicts:
        if v.kind != "matched":
            continue
        credits = [d for d in (v.defect_id, v.second_defect_id) if d is not None]
        if all(c in full_credited for c in credits):
            duplicate += 1
            continue
        matched_claims += 1
        if v.status == "full":
            full_credited.update(credits)
        else:
            partial_credited.update(credits)
    partial_credited -= full_credited

    d = len(defects)
    recall = 1.0 if d == 0 else (len(full_credited) + 0.5 * len(partial_credited)) / d

    # ADR-0030: a distractor hit is a false alarm. It stays in the denominator,
    # so planting a distractor exerts real precision pressure. Only the neutral
    # duplicate leaves the denominator.
    scoreable = claim_count - duplicate
    precision = 1.0 if scoreable <= 0 else matched_claims / scoreable

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    per_category: dict[str, float] = {}
    for category in {defect.category for defect in defects}:
        cat_ids = {defect.id for defect in defects if defect.category == category}
        per_category[category] = (
            len(full_credited & cat_ids) + 0.5 * len(partial_credited & cat_ids)
        ) / len(cat_ids)

    return ReviewScore(
        recall=recall,
        precision=precision,
        f1=f1,
        distractor_hits=distractor_hits,
        false_alarms=false_alarms,
        claim_count=claim_count,
        duplicate=duplicate,
        review_required=review_required,
        per_category=per_category,
    )
