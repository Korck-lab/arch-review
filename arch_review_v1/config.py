"""Task and judge configuration for arch-review v1.

The judge config is overridable from the CLI and TOML under
``env.taskset.task.judge.*``. Prompt paths are relative to
``prompts/judge/`` inside the package.
"""

from __future__ import annotations

import verifiers.v1 as vf
from verifiers.v1.types import SamplingConfig


class ArchReviewJudgeConfig(vf.JudgeConfig):
    """Settings for the two-judge pipeline."""

    model: str = "anthropic/claude-sonnet-5"
    sampling: SamplingConfig = SamplingConfig(temperature=0.0)
    extractor_prompt: str = "claim_extractor.v1.md"
    matcher_prompt: str = "matcher.v1.md"


class ArchReviewTaskConfig(vf.TaskConfig):
    """Per-task config; carries the judge block."""

    judge: ArchReviewJudgeConfig = ArchReviewJudgeConfig()


class ArchReviewTasksetConfig(vf.TasksetConfig):
    """Taskset config; the task block carries the judge."""

    task: ArchReviewTaskConfig = ArchReviewTaskConfig()
