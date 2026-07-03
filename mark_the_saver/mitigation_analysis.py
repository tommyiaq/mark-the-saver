from __future__ import annotations

"""Strategy engine: joint (base, mitigation) distributions and allocation math.

A ``StrategyPair`` holds the joint empirical outcome distribution of a base
asset and a risk-mitigation payoff, sampled together (all outcomes equally
likely, matching the bootstrap). Three strategies are supported:

- ``store``     - cash: the haven returns 0% in every outcome;
- ``alpha``     - a real fund (gold), aligned same-month with the base so the
                  crash behavior is preserved;
- ``insurance`` - a synthetic convex payoff: pays a multiple ``M`` in crash
                  outcomes (base return <= CRASH_THRESHOLD) and -100%
                  otherwise, with ``M = (1 - p) / p`` from the empirical crash
                  frequency ``p`` so the standalone arithmetic return is
                  exactly zero (fairly priced insurance). For the dice base the
                  crash is the -50% face (p = 1/6, M = 5), which reproduces the
                  book's insurance side bet exactly.

``build_allocation_curve`` sweeps the mitigation weight ``w`` (combined return
= (1 - w) * base + w * haven per outcome) and scores median and 5th-percentile
wealth after ``DEFAULT_THROWS`` compounded draws, using the same lognormal
machinery as the original dice version - only the distribution is swapped.
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .config import (
    CRASH_THRESHOLD,
    DEFAULT_THROWS,
    MITIGATION_CAP,
    XO_BIN_EDGES,
)
from .market_data import ALPHA_HAVEN_TICKER, DICE_TICKER, fetch_monthly_returns, load_pair

# One-sided z-score for the 5th percentile of a normal distribution.
Z_5TH = 1.6448536269514722

STRATEGY_STORE = "store"
STRATEGY_ALPHA = "alpha"
STRATEGY_INSURANCE = "insurance"

STRATEGY_LABELS = {
    STRATEGY_STORE: "Store-of-value (cash)",
    STRATEGY_ALPHA: "Alpha (gold)",
    STRATEGY_INSURANCE: "Insurance (convex)",
}

# Floor for growth factors so log() stays finite at the w = 1 insurance edge
# (100% insurance loses everything in any non-crash outcome).
_GROWTH_FLOOR = 1e-12


@dataclass(frozen=True)
class StrategyPair:
    base_ticker: str
    base_label: str
    strategy: str
    strategy_label: str
    base_returns: np.ndarray   # joint outcomes, all equally likely
    haven_returns: np.ndarray
    months: tuple[str, ...] | None  # None for the synthetic dice base
    crash_probability: float
    insurance_multiple: float | None  # set only for the insurance strategy

    @property
    def outcomes(self) -> int:
        return len(self.base_returns)


@lru_cache(maxsize=16)
def build_strategy_pair(base_ticker: str, strategy: str) -> StrategyPair:
    """Joint (base, haven) outcome distribution for a mitigation strategy."""
    if strategy not in STRATEGY_LABELS:
        raise ValueError(f"unknown strategy {strategy!r}")

    if strategy == STRATEGY_ALPHA:
        if base_ticker == DICE_TICKER:
            raise ValueError("the dice base has no calendar and cannot be paired with a fund")
        base_series, haven_series = load_pair(base_ticker, ALPHA_HAVEN_TICKER)
        base = base_series.returns
        haven = haven_series.returns
        months = base_series.months
    else:
        base_series = fetch_monthly_returns(base_ticker)
        base = base_series.returns
        months = base_series.months
        if strategy == STRATEGY_STORE:
            haven = np.zeros_like(base)
        else:  # insurance
            crash = base <= CRASH_THRESHOLD
            p = float(np.mean(crash))
            if p <= 0.0:
                raise ValueError(f"{base_ticker!r} has no outcomes at or below {CRASH_THRESHOLD:.0%}")
            multiple = (1.0 - p) / p
            haven = np.where(crash, multiple, -1.0)

    crash_probability = float(np.mean(base <= CRASH_THRESHOLD))
    return StrategyPair(
        base_ticker=base_ticker,
        base_label=base_series.label,
        strategy=strategy,
        strategy_label=STRATEGY_LABELS[strategy],
        base_returns=np.asarray(base, dtype=float),
        haven_returns=np.asarray(haven, dtype=float),
        months=months,
        crash_probability=crash_probability,
        insurance_multiple=(1.0 - crash_probability) / crash_probability if strategy == STRATEGY_INSURANCE else None,
    )


@dataclass(frozen=True)
class AllocationPoint:
    weight: float  # allocation to the mitigation payoff
    median_wealth: float
    p5_wealth: float
    median_cagr: float
    p5_cagr: float


@dataclass(frozen=True)
class AllocationCurve:
    pair: StrategyPair
    weights: np.ndarray  # mitigation allocations, 0..1
    median_wealth: np.ndarray
    p5_wealth: np.ndarray
    p95_wealth: np.ndarray
    median_cagr: np.ndarray
    p5_cagr: np.ndarray
    throws: int
    mitigation_cap: float
    kelly: AllocationPoint       # unconstrained median maximum (accuracy)
    fractional: AllocationPoint  # unconstrained 5th-percentile maximum (precision)
    selected: AllocationPoint    # 5th-pct max subject to weight <= cap; slider default


def build_allocation_curve(
    pair: StrategyPair | None = None,
    steps: int = 201,
    mitigation_cap: float = MITIGATION_CAP,
    throws: int = DEFAULT_THROWS,
) -> AllocationCurve:
    """Sweep the mitigation allocation 0-100% and score each blend.

    Per draw the combined return is ``(1 - w) * base + w * haven`` over the
    joint outcome distribution. The log of ending wealth after ``throws``
    draws is approximately normal, so the median is the geometric mean
    compounded over all draws and the 5th percentile follows from the
    per-draw log variance. ``selected`` maximizes the 5th percentile subject
    to ``w <= mitigation_cap`` (the book's 50% cap on the safe haven
    allocation); the unconstrained median max (Kelly point) and 5th-pct max
    are also reported.
    """
    if pair is None:
        pair = build_strategy_pair(DICE_TICKER, STRATEGY_STORE)

    weights = np.linspace(0.0, 1.0, steps)
    combined = (1.0 - weights[:, None]) * pair.base_returns + weights[:, None] * pair.haven_returns
    growth = np.clip(1.0 + combined, _GROWTH_FLOOR, None)
    log_growth = np.log(growth)
    mean_log = log_growth.mean(axis=1)
    var_log = np.clip((log_growth ** 2).mean(axis=1) - mean_log ** 2, 0.0, None)
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

    allowed_p5 = np.where(weights <= mitigation_cap, p5_wealth, -np.inf)

    return AllocationCurve(
        pair=pair,
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


def default_mitigation_weight(base_ticker: str, strategy: str) -> float:
    """Slider default: 5th-pct-optimal mitigation weight, capped at 50%."""
    return build_allocation_curve(build_strategy_pair(base_ticker, strategy)).selected.weight


# --- Blend statistics and binned XO profiles for the panels ---


def _arithmetic(returns: np.ndarray) -> float:
    return float(np.mean(returns))


def _geometric(returns: np.ndarray) -> float:
    growth = np.clip(1.0 + returns, _GROWTH_FLOOR, None)
    return float(np.exp(np.mean(np.log(growth))) - 1.0)


@dataclass(frozen=True)
class BlendStats:
    """Per-outcome arithmetic/geometric stats of base, haven, and their blend."""

    pair: StrategyPair
    weight: float  # allocation to the mitigation payoff
    base_arithmetic: float
    base_geometric: float
    haven_arithmetic: float
    haven_geometric: float
    combined_arithmetic: float
    combined_geometric: float

    @property
    def cost(self) -> float:
        """Arithmetic cost of the mitigation (positive = drag on the mean)."""
        return self.base_arithmetic - self.combined_arithmetic

    @property
    def net_effect(self) -> float:
        """Net portfolio effect: change in the geometric (median) growth rate."""
        return self.combined_geometric - self.base_geometric

    @property
    def geometric_effect(self) -> float:
        """Book identity: geometric effect = arithmetic cost + net effect."""
        return self.cost + self.net_effect


def build_blend_stats(pair: StrategyPair, weight: float) -> BlendStats:
    combined = (1.0 - weight) * pair.base_returns + weight * pair.haven_returns
    return BlendStats(
        pair=pair,
        weight=weight,
        base_arithmetic=_arithmetic(pair.base_returns),
        base_geometric=_geometric(pair.base_returns),
        haven_arithmetic=_arithmetic(pair.haven_returns),
        haven_geometric=_geometric(pair.haven_returns),
        combined_arithmetic=_arithmetic(combined),
        combined_geometric=_geometric(combined),
    )


@dataclass(frozen=True)
class XOProfile:
    """Binned payoff profiles (by base-asset return bin) for the XO panel."""

    stats: BlendStats
    bin_labels: tuple[str, ...]
    bin_shares: np.ndarray       # fraction of outcomes per bin
    base_bin_means: np.ndarray   # NaN where a bin is empty
    haven_bin_means: np.ndarray
    combined_bin_means: np.ndarray


def _bin_labels() -> tuple[str, ...]:
    edges = [f"{edge * 100:g}%" for edge in XO_BIN_EDGES]
    labels = [f"≤{edges[0]}"]
    labels += [f"{a} to {b}" for a, b in zip(edges, edges[1:])]
    labels.append(f">{edges[-1]}")
    return tuple(labels)


def build_xo_profile(pair: StrategyPair, weight: float) -> XOProfile:
    stats = build_blend_stats(pair, weight)
    combined = (1.0 - weight) * pair.base_returns + weight * pair.haven_returns

    edges = np.array(XO_BIN_EDGES, dtype=float)
    # Bins: (-inf, e0], (e0, e1], ..., (e_last, inf)
    bin_index = np.searchsorted(edges, pair.base_returns, side="left")
    n_bins = len(edges) + 1

    shares = np.zeros(n_bins)
    base_means = np.full(n_bins, np.nan)
    haven_means = np.full(n_bins, np.nan)
    combined_means = np.full(n_bins, np.nan)
    for i in range(n_bins):
        mask = bin_index == i
        shares[i] = float(np.mean(mask))
        if mask.any():
            base_means[i] = float(np.mean(pair.base_returns[mask]))
            haven_means[i] = float(np.mean(pair.haven_returns[mask]))
            combined_means[i] = float(np.mean(combined[mask]))

    return XOProfile(
        stats=stats,
        bin_labels=_bin_labels(),
        bin_shares=shares,
        base_bin_means=base_means,
        haven_bin_means=haven_means,
        combined_bin_means=combined_means,
    )
