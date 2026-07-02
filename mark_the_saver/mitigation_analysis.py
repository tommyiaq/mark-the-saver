from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np

from .config import (
    DEFAULT_THROWS,
    DICE_STATE_PROBABILITIES,
    DICE_STATE_RETURNS,
)

# One-sided z-score for the 5th percentile of a normal distribution.
Z_5TH = 1.6448536269514722


@dataclass(frozen=True)
class StrategyStats:
    label: str
    returns: np.ndarray
    returns_pct: np.ndarray
    arithmetic: float
    geometric: float


@dataclass(frozen=True)
class BlendProfileData:
    dice: StrategyStats
    cash: StrategyStats
    combined: StrategyStats
    dice_weight: float
    cash_weight: float


@dataclass(frozen=True)
class PlanePoint:
    label: str
    cost: float
    effect: float
    arithmetic: float
    geometric: float
    description: str


def _build_stats(label: str, returns: np.ndarray, probabilities: np.ndarray) -> StrategyStats:
    returns_pct = returns * 100.0
    arithmetic = float(np.sum(returns * probabilities))
    geometric = float(exp(np.sum(probabilities * np.log1p(returns))) - 1)
    return StrategyStats(
        label=label,
        returns=returns,
        returns_pct=returns_pct,
        arithmetic=arithmetic,
        geometric=geometric,
    )


def build_blend_profile_data(dice_weight: float | None = None) -> BlendProfileData:
    """Build the dice / cash / combined profile at ``dice_weight``.

    When ``dice_weight`` is ``None`` the allocation defaults to the weight that
    maximizes the 5th-percentile outcome (see :func:`optimal_dice_weight`), so
    the Xs and Os panel and the cost-effectiveness plane both track that single,
    downside-optimal allocation.
    """
    if dice_weight is None:
        dice_weight = optimal_dice_weight()
    cash_weight = 1.0 - dice_weight

    dice_returns = np.array(DICE_STATE_RETURNS, dtype=float)
    probabilities = np.array(DICE_STATE_PROBABILITIES, dtype=float)
    cash_returns = np.zeros_like(dice_returns)
    combined_returns = dice_weight * dice_returns + cash_weight * cash_returns

    return BlendProfileData(
        dice=_build_stats("Dice", dice_returns, probabilities),
        cash=_build_stats("Cash", cash_returns, probabilities),
        combined=_build_stats("Risk-mitigated blend", combined_returns, probabilities),
        dice_weight=dice_weight,
        cash_weight=cash_weight,
    )


def build_cost_effectiveness_points(profile_data: BlendProfileData) -> list[PlanePoint]:
    baseline = profile_data.dice
    points = [
        PlanePoint(
            label="Dice baseline",
            cost=0.0,
            effect=0.0,
            arithmetic=baseline.arithmetic,
            geometric=baseline.geometric,
            description="Reference strategy",
        ),
        PlanePoint(
            label="Cash",
            cost=profile_data.cash.arithmetic - baseline.arithmetic,
            effect=profile_data.cash.geometric - baseline.geometric,
            arithmetic=profile_data.cash.arithmetic,
            geometric=profile_data.cash.geometric,
            description="Risk mitigation only",
        ),
        PlanePoint(
            label=f"{profile_data.dice_weight * 100:.0f}% dice / {profile_data.cash_weight * 100:.0f}% cash",
            cost=profile_data.combined.arithmetic - baseline.arithmetic,
            effect=profile_data.combined.geometric - baseline.geometric,
            arithmetic=profile_data.combined.arithmetic,
            geometric=profile_data.combined.geometric,
            description="Risk-mitigated blend",
        ),
    ]
    return points


@dataclass(frozen=True)
class AllocationPoint:
    weight: float
    median_wealth: float
    p5_wealth: float
    median_cagr: float
    p5_cagr: float


@dataclass(frozen=True)
class AllocationCurve:
    weights: np.ndarray
    median_wealth: np.ndarray
    p5_wealth: np.ndarray
    p95_wealth: np.ndarray
    median_cagr: np.ndarray
    p5_cagr: np.ndarray
    throws: int
    mitigation_cap: float
    kelly: AllocationPoint       # unconstrained median maximum (accuracy)
    fractional: AllocationPoint  # unconstrained 5th-percentile maximum (precision)
    selected: AllocationPoint    # 5th-pct max subject to mitigation <= cap; used downstream


def build_allocation_curve(steps: int = 201, mitigation_cap: float = 0.5) -> AllocationCurve:
    """Sweep the stake on the dice bet (0-100%) and score each allocation.

    For every weight the remaining capital sits in cash (0% return). Under
    multiplicative compounding the log of ending wealth after ``DEFAULT_THROWS``
    rolls is approximately normal, so the median is the geometric mean compounded
    over all rolls and the 5th percentile follows from the per-roll log variance.

    The ``selected`` allocation maximizes the 5th-percentile outcome subject to
    the book's cap on the risk-mitigation (cash) allocation: cash <= 50% of the
    portfolio, i.e. dice stake >= 50%. The unconstrained median maximum (Kelly)
    and 5th-percentile maximum (fractional Kelly) are also reported for context.
    """
    returns = np.array(DICE_STATE_RETURNS, dtype=float)
    probabilities = np.array(DICE_STATE_PROBABILITIES, dtype=float)
    throws = DEFAULT_THROWS
    weights = np.linspace(0.0, 1.0, steps)

    # Growth factor per state per weight; > 0 for every weight in [0, 1].
    growth = 1.0 + np.outer(weights, returns)
    log_growth = np.log(growth)
    mean_log = log_growth @ probabilities
    mean_sq = (log_growth ** 2) @ probabilities
    var_log = np.clip(mean_sq - mean_log ** 2, 0.0, None)
    sd_total = np.sqrt(throws * var_log)

    median_log = throws * mean_log
    p5_log = median_log - Z_5TH * sd_total
    p95_log = median_log + Z_5TH * sd_total

    median_wealth = np.exp(median_log)
    p5_wealth = np.exp(p5_log)
    p95_wealth = np.exp(p95_log)
    median_cagr = np.expm1(mean_log)
    p5_cagr = np.expm1(p5_log / throws)

    def _point(index: int) -> AllocationPoint:
        return AllocationPoint(
            weight=float(weights[index]),
            median_wealth=float(median_wealth[index]),
            p5_wealth=float(p5_wealth[index]),
            median_cagr=float(median_cagr[index]),
            p5_cagr=float(p5_cagr[index]),
        )

    allowed = weights >= (1.0 - mitigation_cap)
    allowed_p5 = np.where(allowed, p5_wealth, -np.inf)

    return AllocationCurve(
        weights=weights,
        median_wealth=median_wealth,
        p5_wealth=p5_wealth,
        p95_wealth=p95_wealth,
        median_cagr=median_cagr,
        p5_cagr=p5_cagr,
        throws=throws,
        mitigation_cap=mitigation_cap,
        kelly=_point(int(np.argmax(median_wealth))),
        fractional=_point(int(np.argmax(p5_wealth))),
        selected=_point(int(np.argmax(allowed_p5))),
    )


def optimal_dice_weight() -> float:
    """Dice stake maximizing the 5th percentile, with mitigation capped at 50%."""
    return build_allocation_curve().selected.weight
