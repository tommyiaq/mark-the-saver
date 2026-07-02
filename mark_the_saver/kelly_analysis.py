from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np

from .config import (
    KELLY_CASH_WEIGHT,
    KELLY_DICE_WEIGHT,
    KELLY_STATE_PROBABILITIES,
    KELLY_STATE_RETURNS,
)


@dataclass(frozen=True)
class KellyStrategyStats:
    label: str
    returns: np.ndarray
    returns_pct: np.ndarray
    arithmetic: float
    geometric: float


@dataclass(frozen=True)
class KellyProfileData:
    dice: KellyStrategyStats
    cash: KellyStrategyStats
    combined: KellyStrategyStats
    dice_weight: float
    cash_weight: float


@dataclass(frozen=True)
class KellyPlanePoint:
    label: str
    cost: float
    effect: float
    arithmetic: float
    geometric: float
    description: str


def _build_stats(label: str, returns: np.ndarray, probabilities: np.ndarray) -> KellyStrategyStats:
    returns_pct = returns * 100.0
    arithmetic = float(np.sum(returns * probabilities))
    geometric = float(exp(np.sum(probabilities * np.log1p(returns))) - 1)
    return KellyStrategyStats(
        label=label,
        returns=returns,
        returns_pct=returns_pct,
        arithmetic=arithmetic,
        geometric=geometric,
    )


def build_kelly_profile_data() -> KellyProfileData:
    dice_returns = np.array(KELLY_STATE_RETURNS, dtype=float)
    probabilities = np.array(KELLY_STATE_PROBABILITIES, dtype=float)
    cash_returns = np.zeros_like(dice_returns)
    combined_returns = KELLY_DICE_WEIGHT * dice_returns + KELLY_CASH_WEIGHT * cash_returns

    return KellyProfileData(
        dice=_build_stats("Dice", dice_returns, probabilities),
        cash=_build_stats("Cash", cash_returns, probabilities),
        combined=_build_stats("Kelly blend", combined_returns, probabilities),
        dice_weight=KELLY_DICE_WEIGHT,
        cash_weight=KELLY_CASH_WEIGHT,
    )


def build_cost_effectiveness_points(profile_data: KellyProfileData) -> list[KellyPlanePoint]:
    baseline = profile_data.dice
    points = [
        KellyPlanePoint(
            label="Dice baseline",
            cost=0.0,
            effect=0.0,
            arithmetic=baseline.arithmetic,
            geometric=baseline.geometric,
            description="Reference strategy",
        ),
        KellyPlanePoint(
            label="Cash",
            cost=profile_data.cash.arithmetic - baseline.arithmetic,
            effect=profile_data.cash.geometric - baseline.geometric,
            arithmetic=profile_data.cash.arithmetic,
            geometric=profile_data.cash.geometric,
            description="Risk mitigation only",
        ),
        KellyPlanePoint(
            label="40% dice / 60% cash",
            cost=profile_data.combined.arithmetic - baseline.arithmetic,
            effect=profile_data.combined.geometric - baseline.geometric,
            arithmetic=profile_data.combined.arithmetic,
            geometric=profile_data.combined.geometric,
            description="Kelly blend",
        ),
    ]
    return points
