"""Regression tests for the judge retry/degrade policy (ADR-0027).

A judge response can be unusable in two ways: a contract violation, or
invalid/truncated JSON from the model. Both must retry once, then degrade to an
empty result instead of raising a TaskError that crashes the episode. Run 11
lost one t001 episode to a truncated extractor JSON that escaped as a
ValidationError.
"""

from __future__ import annotations

import asyncio

import verifiers.v1 as vf
from pydantic import ValidationError

from arch_review_v1.config import ArchReviewJudgeConfig
from arch_review_v1.judges import ClaimExtractorJudge, MatcherJudge
from arch_review_v1.schemas import (
    Claim,
    ClaimExtraction,
    Defect,
    Distractor,
    MatchResult,
    Verdict,
)


def _config() -> ArchReviewJudgeConfig:
    return ArchReviewJudgeConfig()


def test_extractor_retries_once_on_truncated_json_then_succeeds(monkeypatch):
    calls = {"n": 0}

    async def fake_evaluate(self, *, trace=None, **fields):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValidationError.from_exception_data("ClaimExtraction", [])
        parsed = ClaimExtraction(
            claims=[
                Claim(id="c1", file="billing/charge.py", quote="a bug", summary="a bug")
            ]
        )
        return vf.JudgeResponse(text='{"claims":[...]}', parsed=parsed)

    monkeypatch.setattr(vf.Judge, "evaluate", fake_evaluate)
    judge = ClaimExtractorJudge(_config(), ["billing/charge.py"])
    judge.review = "the code has a bug"
    out = asyncio.run(
        judge.evaluate(trace=None, review="the code has a bug", files="billing/charge.py")
    )
    assert calls["n"] == 2
    assert len(out.parsed.claims) == 1
    assert "not valid schema JSON" in judge.prompt


def test_extractor_degrades_to_empty_after_two_bad_outputs(monkeypatch):
    async def fake_evaluate(self, *, trace=None, **fields):
        raise ValidationError.from_exception_data("ClaimExtraction", [])

    monkeypatch.setattr(vf.Judge, "evaluate", fake_evaluate)
    judge = ClaimExtractorJudge(_config(), ["billing/charge.py"])
    judge.review = "the code has a bug"
    out = asyncio.run(
        judge.evaluate(trace=None, review="the code has a bug", files="billing/charge.py")
    )
    assert out.parsed == ClaimExtraction(claims=[])


def test_matcher_retries_once_on_truncated_json_then_succeeds(monkeypatch):
    calls = {"n": 0}

    async def fake_evaluate(self, *, trace=None, **fields):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValidationError.from_exception_data("MatchResult", [])
        parsed = MatchResult(
            verdicts=[Verdict(claim_id="c1", kind="matched", defect_id="d1")]
        )
        return vf.JudgeResponse(text='{"verdicts":[...]}', parsed=parsed)

    monkeypatch.setattr(vf.Judge, "evaluate", fake_evaluate)
    defects = [Defect(
        id="d1", category="concurrency", file="billing/charge.py",
        lines=[25, 27], summary="a seeded defect", rationale="hand-written",
    )]
    claims = [Claim(id="c1", file="billing/charge.py", quote="a bug", summary="a bug")]
    judge = MatcherJudge(_config(), defects, [Distractor(
        id="x1", file="billing/retry.py", lines=[13, 27],
        concern="duplicate charge on retry", why_ok="the gateway dedups",
    )], claims)
    out = asyncio.run(judge.evaluate(trace=None))
    assert calls["n"] == 2
    assert out.parsed.verdicts[0].defect_id == "d1"


def test_matcher_degrades_to_empty_after_two_bad_outputs(monkeypatch):
    async def fake_evaluate(self, *, trace=None, **fields):
        raise ValidationError.from_exception_data("MatchResult", [])

    monkeypatch.setattr(vf.Judge, "evaluate", fake_evaluate)
    judge = MatcherJudge(_config(), [], [], [])
    out = asyncio.run(judge.evaluate(trace=None))
    assert out.parsed == MatchResult(verdicts=[])
