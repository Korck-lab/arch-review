"""Pydantic schemas for the arch-review dataset and judge output.

These models are the wire contract between the deterministic layer and the
model layer (ADR-0008). The dataset models mirror gold.yaml; the claim and
verdict models are the structured output of the two judges. Field validators
normalize at the seam (ADR-0022): whitespace is stripped from paths and the
verdict kind is case-folded before validation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _strip(value: str | None) -> str | None:
    return value.strip() if value else value


class Defect(BaseModel):
    """One seeded defect from gold.yaml."""

    id: str
    category: str
    file: str
    lines: list[int] = Field(min_length=2, max_length=2)
    summary: str
    rationale: str

    @field_validator("file")
    @classmethod
    def _strip_file(cls, value: str) -> str:
        return value.strip()


class Distractor(BaseModel):
    """One correct-but-suspicious block from gold.yaml."""

    id: str
    file: str
    lines: list[int] | None = None
    concern: str
    why_ok: str

    @field_validator("file")
    @classmethod
    def _strip_file(cls, value: str) -> str:
        return value.strip()


class Claim(BaseModel):
    """One issue the model under eval raised in its review."""

    id: str
    file: str  # a path in file_list, or the literal sentinel "general"
    quote: str  # verbatim evidence from the review
    summary: str

    @field_validator("file")
    @classmethod
    def _strip_file(cls, value: str) -> str:
        return value.strip()

    @field_validator("quote")
    @classmethod
    def _strip_quote(cls, value: str) -> str:
        return value.strip()


class ClaimExtraction(BaseModel):
    """Structured output of the gold-blind ClaimExtractorJudge."""

    claims: list[Claim]


class Verdict(BaseModel):
    """The MatcherJudge's verdict on one claim.

    Exactly one verdict per claim. A matched verdict may credit up to two
    defects; status is full when the claim captures cause and location.
    ``unsure`` routes the verdict to the human review-required audit queue.
    """

    claim_id: str
    kind: Literal["matched", "distractor", "false_alarm"]
    # kind == matched:
    defect_id: str | None = None
    second_defect_id: str | None = None
    status: Literal["full", "partial"] = "full"
    # kind == distractor:
    distractor_file: str | None = None
    unsure: bool = False

    @field_validator("kind", mode="before")
    @classmethod
    def _fold_kind(cls, value) -> str:
        return value.lower() if isinstance(value, str) else value

    @field_validator("distractor_file")
    @classmethod
    def _strip_file(cls, value: str | None) -> str | None:
        return _strip(value)


class MatchResult(BaseModel):
    """Structured output of the MatcherJudge."""

    verdicts: list[Verdict]
