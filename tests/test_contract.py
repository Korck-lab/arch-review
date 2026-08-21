"""Tests for the contract validators (the test seam, spec #9)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from arch_review_v1.contract import (
    ContractError,
    validate_extraction,
    validate_gold,
    validate_matching,
)
from arch_review_v1.schemas import (
    Claim,
    ClaimExtraction,
    Defect,
    Distractor,
    MatchResult,
    Verdict,
)

_TASK_DIR = Path("t001-payment-race")


def _good_gold() -> dict:
    return {
        "id": "t001-payment-race",
        "difficulty": "medium",
        "source": {"kind": "synthetic"},
        "defects": [
            {
                "id": "d1",
                "category": "concurrency",
                "file": "billing/charge.py",
                "lines": [25, 27],
                "summary": "check-then-act race",
                "rationale": "hand-written: two concurrent checkouts both debit",
            },
            {
                "id": "d2",
                "category": "operability",
                "file": "billing/charge.py",
                "lines": [38, 39],
                "summary": "success metric removed",
                "rationale": "hand-written: on-call signal goes blind",
            },
        ],
        "distractors": [
            {
                "id": "x1",
                "file": "billing/retry.py",
                "lines": [13, 27],
                "concern": "duplicate charge on retry",
                "why_ok": "the gateway dedups identical-key replays",
            }
        ],
        "prompt_notes": "improves checkout performance",
    }


def _defect(defect_id: str = "d1") -> Defect:
    return Defect(
        id=defect_id,
        category="concurrency",
        file="billing/charge.py",
        lines=[25, 27],
        summary="a seeded defect",
        rationale="hand-written rationale",
    )


def _distractor() -> Distractor:
    return Distractor(
        id="x1",
        file="billing/retry.py",
        lines=[13, 27],
        concern="duplicate charge on retry",
        why_ok="the gateway dedups identical-key replays",
    )


def _claim(claim_id: str = "c1") -> Claim:
    return Claim(id=claim_id, file="billing/charge.py", quote="an issue", summary="an issue")


# --- validate_gold ---------------------------------------------------------


def test_valid_gold_passes():
    result = validate_gold(_good_gold(), _TASK_DIR)
    assert result["id"] == "t001-payment-race"
    assert len(result["defects"]) == 2
    assert len(result["distractors"]) == 1


def test_id_must_match_directory():
    gold = _good_gold()
    gold["id"] = "t999-other"
    with pytest.raises(ContractError, match="directory name"):
        validate_gold(gold, _TASK_DIR)


def test_unknown_difficulty_rejected():
    gold = _good_gold()
    gold["difficulty"] = "extreme"
    with pytest.raises(ContractError, match="difficulty"):
        validate_gold(gold, _TASK_DIR)


def test_defect_count_outside_difficulty_range_rejected():
    gold = _good_gold()
    gold["difficulty"] = "easy"  # easy allows exactly 1 defect
    with pytest.raises(ContractError, match="requires 1-1 defects"):
        validate_gold(gold, _TASK_DIR)


def test_medium_requires_two_distinct_categories():
    gold = _good_gold()
    gold["defects"][1]["category"] = "concurrency"  # now both concurrency
    with pytest.raises(ContractError, match="distinct defect categories"):
        validate_gold(gold, _TASK_DIR)


def test_medium_requires_at_least_one_distractor():
    gold = _good_gold()
    gold["distractors"] = []
    with pytest.raises(ContractError, match="requires 1-unbounded distractors"):
        validate_gold(gold, _TASK_DIR)


def test_sequential_defect_ids_required():
    gold = _good_gold()
    gold["defects"][0]["id"] = "d2"
    gold["defects"][1]["id"] = "d3"
    with pytest.raises(ContractError, match="sequential"):
        validate_gold(gold, _TASK_DIR)


def test_unknown_category_rejected():
    gold = _good_gold()
    gold["defects"][0]["category"] = "performance"
    with pytest.raises(ContractError, match="category"):
        validate_gold(gold, _TASK_DIR)


def test_malformed_lines_rejected():
    gold = _good_gold()
    gold["defects"][0]["lines"] = [42]
    with pytest.raises(ContractError, match="lines"):
        validate_gold(gold, _TASK_DIR)


def test_reversed_lines_rejected():
    gold = _good_gold()
    gold["defects"][0]["lines"] = [58, 42]
    with pytest.raises(ContractError, match="1 <= start <= end"):
        validate_gold(gold, _TASK_DIR)


def test_synthetic_source_rejects_extra_fields():
    gold = _good_gold()
    gold["source"] = {"kind": "synthetic", "url": "https://example.com"}
    with pytest.raises(ContractError, match="extra fields"):
        validate_gold(gold, _TASK_DIR)


def test_oss_source_requires_attribution():
    gold = _good_gold()
    gold["source"] = {"kind": "oss", "url": "https://github.com/o/r/tree/v1.0", "license": "MIT"}
    with pytest.raises(ContractError, match="attribution"):
        validate_gold(gold, _TASK_DIR)


def test_copyleft_license_rejected():
    gold = _good_gold()
    gold["source"] = {
        "kind": "oss",
        "url": "https://github.com/o/r/tree/v1.0",
        "license": "GPL-3.0",
        "attribution": "Copyright (c) 2021 The Authors",
    }
    with pytest.raises(ContractError, match="license"):
        validate_gold(gold, _TASK_DIR)


def test_distractor_without_concern_rejected():
    gold = _good_gold()
    del gold["distractors"][0]["concern"]
    with pytest.raises(ContractError, match="concern"):
        validate_gold(gold, _TASK_DIR)


def test_unknown_top_level_key_rejected():
    gold = _good_gold()
    gold["extra"] = True
    with pytest.raises(ContractError, match="unknown gold.yaml keys"):
        validate_gold(gold, _TASK_DIR)


def test_unknown_defect_key_rejected():
    gold = _good_gold()
    gold["defects"][0]["severity"] = "high"
    with pytest.raises(ContractError, match="unknown keys"):
        validate_gold(gold, _TASK_DIR)


# --- validate_extraction ---------------------------------------------------


def test_valid_extraction_passes():
    extraction = ClaimExtraction(claims=[_claim("c1")])
    result = validate_extraction(extraction, ["billing/charge.py", "billing/retry.py"])
    assert result.claims[0].id == "c1"


def test_extraction_file_not_in_diff_rejected():
    extraction = ClaimExtraction(
        claims=[Claim(id="c1", file="billing/other.py", quote="x", summary="x")]
    )
    with pytest.raises(ContractError, match="not in the diff"):
        validate_extraction(extraction, ["billing/charge.py"])


def test_extraction_general_sentinel_allowed():
    extraction = ClaimExtraction(
        claims=[Claim(id="c1", file="general", quote="x", summary="x")]
    )
    result = validate_extraction(extraction, ["billing/charge.py"])
    assert result.claims[0].file == "general"


def test_extraction_ids_must_be_dense():
    extraction = ClaimExtraction(claims=[_claim("c1"), _claim("c3")])
    with pytest.raises(ContractError, match="dense"):
        validate_extraction(extraction, ["billing/charge.py"])


def test_extraction_duplicate_claim_id_rejected_by_dense_rule():
    extraction = ClaimExtraction(claims=[_claim("c1"), _claim("c1")])
    with pytest.raises(ContractError, match="dense"):
        validate_extraction(extraction, ["billing/charge.py"])


def test_extraction_empty_quote_rejected():
    extraction = ClaimExtraction(
        claims=[Claim(id="c1", file="billing/charge.py", quote="", summary="x")]
    )
    with pytest.raises(ContractError, match="empty quote"):
        validate_extraction(extraction, ["billing/charge.py"])


def test_extraction_quote_must_be_verbatim_in_review():
    extraction = ClaimExtraction(claims=[_claim("c1")])
    with pytest.raises(ContractError, match="not verbatim"):
        validate_extraction(extraction, ["billing/charge.py"], review="a completely different review")


def test_extraction_quote_verbatim_passes():
    review = "the charge path double bills"
    extraction = ClaimExtraction(
        claims=[Claim(id="c1", file="billing/charge.py", quote="double bills", summary="x")]
    )
    result = validate_extraction(extraction, ["billing/charge.py"], review=review)
    assert result.claims[0].quote == "double bills"


def test_extraction_empty_summary_rejected():
    extraction = ClaimExtraction(
        claims=[Claim(id="c1", file="billing/charge.py", quote="x", summary="  ")]
    )
    with pytest.raises(ContractError, match="empty summary"):
        validate_extraction(extraction, ["billing/charge.py"])


# --- validate_matching -----------------------------------------------------


def test_valid_matching_passes():
    claims = [_claim("c1")]
    defects = [_defect("d1")]
    distractors = [_distractor()]
    result = MatchResult(verdicts=[Verdict(claim_id="c1", kind="matched", defect_id="d1")])
    assert validate_matching(result, claims, defects, distractors) is result


def test_matching_kind_is_case_folded():
    claims = [_claim("c1")]
    defects = [_defect("d1")]
    distractors = [_distractor()]
    result = MatchResult(verdicts=[Verdict(claim_id="c1", kind="Matched", defect_id="d1")])
    validate_matching(result, claims, defects, distractors)
    assert result.verdicts[0].kind == "matched"


def test_matching_unknown_claim_rejected():
    result = MatchResult(verdicts=[Verdict(claim_id="c9", kind="false_alarm")])
    with pytest.raises(ContractError, match="unknown claim"):
        validate_matching(result, [_claim("c1")], [_defect()], [_distractor()])


def test_matching_two_verdicts_for_one_claim_rejected():
    result = MatchResult(
        verdicts=[Verdict(claim_id="c1", kind="false_alarm"), Verdict(claim_id="c1", kind="matched", defect_id="d1")]
    )
    with pytest.raises(ContractError, match="more than one verdict"):
        validate_matching(result, [_claim("c1")], [_defect()], [_distractor()])


def test_matching_unknown_defect_rejected():
    result = MatchResult(verdicts=[Verdict(claim_id="c1", kind="matched", defect_id="d9")])
    with pytest.raises(ContractError, match="unknown defect"):
        validate_matching(result, [_claim("c1")], [_defect("d1")], [_distractor()])


def test_matching_unknown_distractor_file_rejected():
    result = MatchResult(verdicts=[Verdict(claim_id="c1", kind="distractor", distractor_file="billing/other.py")])
    with pytest.raises(ContractError, match="unknown file"):
        validate_matching(result, [_claim("c1")], [_defect()], [_distractor()])


def test_matching_uncovered_claim_rejected():
    result = MatchResult(verdicts=[])
    with pytest.raises(ContractError, match="claims with no verdict"):
        validate_matching(result, [_claim("c1")], [_defect()], [_distractor()])


def test_matching_invalid_kind_rejected():
    # the closed kind enum is enforced by the schema at construction time.
    with pytest.raises(ValidationError, match="literal_error"):
        Verdict(claim_id="c1", kind="maybe")


def test_matching_duplicate_defect_credit_rejected():
    result = MatchResult(
        verdicts=[Verdict(claim_id="c1", kind="matched", defect_id="d1", second_defect_id="d1")]
    )
    with pytest.raises(ContractError, match="same defect twice"):
        validate_matching(result, [_claim("c1")], [_defect("d1")], [_distractor()])
