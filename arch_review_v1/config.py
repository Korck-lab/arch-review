"""Task and judge configuration for arch-review v1.

The judge config is overridable from the CLI and TOML under
``env.taskset.task.judge.*``. Prompt paths are relative to
``prompts/judge/`` inside the package.
"""

from __future__ import annotations

import verifiers.v1 as vf
from pydantic import BaseModel, field_validator
from verifiers.v1.types import SamplingConfig

from arch_review_v1.budget import PRICE_T


class ArchReviewJudgeConfig(vf.JudgeConfig):
    """Settings for the two-judge pipeline."""

    model: str = "anthropic/claude-sonnet-5"
    sampling: SamplingConfig = SamplingConfig(temperature=0.0)
    extractor_prompt: str = "claim_extractor.v2.md"
    matcher_prompt: str = "matcher.v2.md"


class ArchReviewTaskConfig(vf.TaskConfig):
    """Per-task config; carries the judge block."""

    judge: ArchReviewJudgeConfig = ArchReviewJudgeConfig()


class ArchReviewBudgetConfig(BaseModel):
    """Run-level judge spend limits (issue #5): $10 target, $12 hard stop.

    ``prices`` maps a judge model id to a (input, output) USD-per-1M-token rate
    card. It is intentionally empty by default: the runner must supply the
    provider's published prices, which the smoke eval calibrates.
    """

    target: float = 10.0
    hard_stop: float = 12.0
    prices: dict[str, PRICE_T] = {}

    @field_validator("prices")
    @classmethod
    def _prices_non_negative(cls, value: dict[str, PRICE_T]) -> dict[str, PRICE_T]:
        for model, (input_per_1m, output_per_1m) in value.items():
            if input_per_1m < 0 or output_per_1m < 0:
                raise ValueError(f"rate card for {model!r} has a negative price")
        return value


class ArchReviewTasksetConfig(vf.TasksetConfig):
    """Taskset config; the task block carries the judge, the budget limits spend."""

    task: ArchReviewTaskConfig = ArchReviewTaskConfig()
    budget: ArchReviewBudgetConfig = ArchReviewBudgetConfig()
