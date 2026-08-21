"""Tests for the judge spend budget (spec #9, issue #15, runner layer).

The budget is a pure accumulator: it prices token usage with a rate card and
raises past the hard stop. Prices are not fabricated in code; the runner must
supply the provider's rate card before the full run.
"""

from __future__ import annotations

import pytest

from arch_review_v1.budget import BudgetExceeded, JudgeBudget, cost_from_usage


def test_cost_from_usage_prices_input_and_output():
    assert cost_from_usage(1_000_000, 1_000_000, (3.0, 15.0)) == 18.0
    assert cost_from_usage(1_000_000, 0, (3.0, 15.0)) == 3.0
    assert cost_from_usage(0, 1_000_000, (3.0, 15.0)) == 15.0


def test_budget_tracks_spend_and_remaining():
    budget = JudgeBudget(target=10.0, hard_stop=12.0)
    budget.record(2.0)
    assert budget.spend == 2.0
    assert budget.remaining == 8.0
    assert not budget.exceeded


def test_reaching_the_target_is_not_hard_exceeded():
    budget = JudgeBudget(target=10.0, hard_stop=12.0)
    budget.record(10.0)
    assert not budget.exceeded


def test_crossing_the_hard_stop_raises():
    budget = JudgeBudget(target=10.0, hard_stop=12.0)
    budget.record(11.0)
    with pytest.raises(BudgetExceeded):
        budget.record(2.0)  # 13.0 > 12.0


def test_exactly_at_the_hard_stop_raises():
    budget = JudgeBudget(target=10.0, hard_stop=12.0)
    with pytest.raises(BudgetExceeded):
        budget.record(12.0)  # hard stop is the ceiling, inclusive


def test_negative_rate_card_price_rejected_at_the_seam():
    from pydantic import ValidationError

    from arch_review_v1.config import ArchReviewBudgetConfig

    with pytest.raises(ValidationError, match="negative"):
        ArchReviewBudgetConfig(prices={"m-a": (-3.0, 15.0)})


def test_remaining_is_floored_at_zero():
    budget = JudgeBudget(target=10.0, hard_stop=12.0)
    budget.record(11.0)  # past target, still under the hard stop
    assert budget.remaining == 0.0


def test_record_model_uses_the_rate_card():
    budget = JudgeBudget(target=10.0, hard_stop=12.0, prices={"m-a": (3.0, 15.0)})
    budget.record_model("m-a", input_tokens=1_000_000, output_tokens=0)
    assert budget.spend == 3.0


def test_unknown_model_price_raises():
    budget = JudgeBudget(target=10.0, hard_stop=12.0, prices={})
    with pytest.raises(KeyError):
        budget.record_model("m-unknown", input_tokens=1, output_tokens=0)
