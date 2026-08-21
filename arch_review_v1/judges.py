"""The two vf.Judge subclasses that map a review to gold.

ClaimExtractorJudge is gold-blind by construction: it sees only the review text
and the diff file list. MatcherJudge sees the extracted claims plus gold. Both
use structured output (a pydantic schema) with contract validators in parse(); a
raised ContractError parks the trace as a TaskError (ADR-0003). The judge prompt
is versioned in the file name; a prompt change is a new file plus a config bump.
"""

from __future__ import annotations

from pathlib import Path

import verifiers.v1 as vf

from arch_review_v1.config import ArchReviewJudgeConfig
from arch_review_v1.contract import validate_extraction, validate_matching
from arch_review_v1.schemas import Claim, ClaimExtraction, Defect, Distractor, MatchResult

_PROMPT_DIR = Path(__file__).parent / "prompts" / "judge"


class ClaimExtractorJudge(vf.Judge[ClaimExtraction, ArchReviewJudgeConfig]):
    """Gold-blind claim extractor."""

    schema = ClaimExtraction

    def __init__(
        self, config: ArchReviewJudgeConfig, file_list: list[str]
    ) -> None:
        super().__init__(config)
        self.file_list = list(file_list)
        self.review: str | None = None
        self.prompt = (_PROMPT_DIR / config.extractor_prompt).read_text()

    def parse(self, response: vf.JudgeResponse[ClaimExtraction]) -> ClaimExtraction:
        return validate_extraction(response.parsed, self.file_list, review=self.review)


class MatcherJudge(vf.Judge[MatchResult, ArchReviewJudgeConfig]):
    """Maps extracted claims to gold defects."""

    schema = MatchResult

    def __init__(
        self,
        config: ArchReviewJudgeConfig,
        defects: list[Defect],
        distractors: list[Distractor],
        claims: list[Claim],
    ) -> None:
        super().__init__(config)
        self.prompt = (_PROMPT_DIR / config.matcher_prompt).read_text()
        self._defects = list(defects)
        self._distractors = list(distractors)
        self._claims = list(claims)

    def parse(self, response: vf.JudgeResponse[MatchResult]) -> MatchResult:
        return validate_matching(response.parsed, self._claims, self._defects, self._distractors)
