"""Judge spend budget (spec #9, issue #15, runner layer).

The run targets $10 of judge spend and stops at a $12 hard stop. The budget
prices token usage against a rate card the runner supplies — prices are not
fabricated here, because a wrong rate card would misreport the credential's
cost. Target and hard stop are configurable; only the hard stop raises.
"""

from __future__ import annotations

PRICE_T = tuple[float, float]  # (input per 1M tokens, output per 1M tokens), USD


class BudgetExceeded(RuntimeError):
    """Cumulative judge spend crossed the run's hard stop."""


def cost_from_usage(input_tokens: int, output_tokens: int, price: PRICE_T) -> float:
    """Cost in USD of one judge call under a per-1M-token rate card."""
    input_per_1m, output_per_1m = price
    return (input_tokens / 1_000_000) * input_per_1m + (
        output_tokens / 1_000_000
    ) * output_per_1m


class JudgeBudget:
    """Accumulates judge spend and enforces target and hard stop.

    ``remaining`` counts down to the target (floored at zero). ``record`` raises
    ``BudgetExceeded`` the moment cumulative spend crosses the hard stop, so a
    runaway run stops instead of silently over-spending (ADR-0003).
    """

    def __init__(
        self,
        target: float,
        hard_stop: float,
        prices: dict[str, PRICE_T] | None = None,
    ) -> None:
        self.target = target
        self.hard_stop = hard_stop
        self.prices = prices if prices is not None else {}
        self._spend = 0.0

    @property
    def spend(self) -> float:
        return self._spend

    @property
    def remaining(self) -> float:
        return max(0.0, self.target - self._spend)

    @property
    def exceeded(self) -> bool:
        return self._spend > self.hard_stop

    def record(self, cost: float) -> None:
        self._spend += cost
        if self.exceeded:
            raise BudgetExceeded(
                f"judge spend ${self._spend:.2f} exceeds hard stop ${self.hard_stop:.2f}"
            )

    def record_model(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Price one judge call from the rate card and record it."""
        if model not in self.prices:
            raise KeyError(f"no rate card entry for judge model {model!r}")
        self.record(cost_from_usage(input_tokens, output_tokens, self.prices[model]))
