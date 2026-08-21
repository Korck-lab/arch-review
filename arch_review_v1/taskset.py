"""arch-review v1 taskset: a model reviews a diff, a judge scores the review.

One ``@vf.reward`` (f1) drives the two judge calls and records every metric
inline via ``trace.record_metrics``. There are no ``@vf.metric`` hooks:
``Task.score()`` runs metrics before rewards, so hooks would force judge
memoization.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import verifiers.v1 as vf
import yaml

from arch_review_v1.config import ArchReviewTaskConfig, ArchReviewTasksetConfig
from arch_review_v1.contract import validate_gold
from arch_review_v1.judges import ClaimExtractorJudge, MatcherJudge
from arch_review_v1.schemas import Claim, Defect, Distractor, Verdict
from arch_review_v1.scoring import score_review

_TASK_DIR = Path(__file__).parent / "tasks"
# captures every file touched by the diff (--- and +++ sides, a/ and b/ prefixes),
# so deleted and renamed files stay in the gold-blind file list.
_DIFF_FILES = re.compile(r"^[+-]{3} (?:[ab]/)?(.+)$", re.MULTILINE)


class ReviewData(vf.TaskData):
    """One immutable review task: the diff, its context, and the parsed gold."""

    diff: str
    context: str
    file_list: list[str]
    seeded_defects: list[Defect]
    distractors: list[Distractor]
    difficulty: str
    source: dict
    prompt_notes: str


class ReviewTask(vf.Task[ReviewData, vf.State, ArchReviewTaskConfig]):
    """The behavior of one review: judge the review, then score it."""

    @vf.reward
    async def f1(self, trace: vf.Trace) -> float:
        data = self.data
        judge_cfg = self.config.judge

        review = (trace.last_reply or "").strip()
        # Empty or refused review, or an extraction with no claims: no matcher
        # call; score 0 naturally, flagged by claims = 0 (issue #3).
        claims: list[Claim] = []
        verdicts: list[Verdict] = []
        if review:
            extractor = ClaimExtractorJudge(judge_cfg, data.file_list)
            extractor.review = review
            extraction = await extractor.evaluate(
                trace=trace,
                review=review,
                files="\n".join(data.file_list),
            )
            claims = list(extraction.parsed.claims) if extraction.parsed is not None else []
            if claims:
                matcher = MatcherJudge(
                    judge_cfg, data.seeded_defects, data.distractors, claims
                )
                result = await matcher.evaluate(
                    trace=trace,
                    claims=json.dumps([c.model_dump() for c in claims]),
                    gold=json.dumps(_gold_view(data)),
                )
                verdicts = list(result.parsed.verdicts) if result.parsed is not None else []

        score = score_review(data.seeded_defects, claims, verdicts)
        trace.record_metrics(score.metrics)
        return score.f1


class ArchReviewTaskset(vf.Taskset[ReviewTask, ArchReviewTasksetConfig]):
    """Loads one ReviewTask per task directory under ``arch_review_v1/tasks``.

    A missing file or a contract-violating gold.yaml raises and fails the load;
    nothing is skipped silently (ADR-0003).
    """

    def load(self) -> list[ReviewTask]:
        tasks = []
        for task_dir in sorted(_TASK_DIR.glob("t[0-9][0-9][0-9]-*")):
            tasks.append(self._build_task(task_dir))
        return tasks

    def _build_task(self, task_dir: Path) -> ReviewTask:
        diff = (task_dir / "diff.patch").read_text()
        context = (task_dir / "context.md").read_text()
        gold_raw = yaml.safe_load((task_dir / "gold.yaml").read_text())
        gold = validate_gold(gold_raw, task_dir)

        file_list = sorted({p for p in _DIFF_FILES.findall(diff) if p != "/dev/null"})
        prompt = _review_prompt(context, gold["prompt_notes"], diff)

        data = ReviewData(
            prompt=prompt,
            diff=diff,
            context=context,
            file_list=file_list,
            seeded_defects=gold["defects"],
            distractors=gold["distractors"],
            difficulty=gold["difficulty"],
            source=gold["source"],
            prompt_notes=gold["prompt_notes"],
        )
        return ReviewTask(data, self.config.task)


def _gold_view(data: ReviewData) -> dict:
    return {
        "defects": [
            {
                "id": d.id,
                "category": d.category,
                "file": d.file,
                "lines": d.lines,
                "summary": d.summary,
            }
            for d in data.seeded_defects
        ],
        "distractors": [
            {
                "id": x.id,
                "file": x.file,
                "lines": x.lines,
                "concern": x.concern,
                "why_ok": x.why_ok,
            }
            for x in data.distractors
        ],
    }


def _review_prompt(context: str, prompt_notes: str, diff: str) -> str:
    return (
        "You are a senior software engineer performing a code review.\n\n"
        f"## System context\n{context}\n\n"
        f"## What the PR claims\n{prompt_notes or '(no description provided)'}\n\n"
        "## The diff\n"
        "```diff\n"
        f"{diff}\n"
        "```\n\n"
        "Write a code review. List every concrete issue you find, one per line, "
        "naming the file and the cause. Be specific about why each is a problem. "
        "Do not comment on style or formatting."
    )
