from __future__ import annotations

DEFAULT_THROWS = 300
DEFAULT_PATHS = 10_000
DEFAULT_SAMPLE_PATHS = 120
DEFAULT_SEED = 42

DICE_STATE_RETURNS = (-0.50, 0.05, 0.50)
DICE_STATE_PROBABILITIES = (1 / 6, 4 / 6, 1 / 6)

LOSS_RETURN = -0.50
MID_RETURN = 0.05
WIN_RETURN = 0.50

PATH_LINE_COLOR = "rgba(247, 201, 72, 0.34)"
PATH_LINE_WIDTH = 1.5
PERCENTILE_LOW_COLOR = "#5bc0be"
PERCENTILE_HIGH_COLOR = "rgba(255, 255, 255, 0.7)"
MEDIAN_COLOR = "#f7c948"

TITLE_TEXT = "300 throws, 10,000 paths"
HERO_COPY = (
    "Each path starts with 1 unit of capital. Every roll pays -50% on 1, +5% on 2-5, and +50% on 6. "
    "The charts show compounding wealth across 10,000 simulated paths."
)

XO_SECTION_TITLE = "Xs and Os Profile"
XO_SECTION_COPY = (
    "The lower panel mirrors the book's Xs and Os profile: the base bet, the risk mitigation, and the blend "
    "at the selected allocation. The point is the same safe-haven question: does the hedge improve the "
    "realized path, not just the average?"
)

COST_PLANE_TITLE = "The Cost-Effectiveness Plane"
COST_PLANE_COPY = (
    "The baseline for this version is the dice bet. Cash and the risk-mitigated blend (the 5th-percentile-optimal "
    "stake) are plotted as cost/effect deltas relative to dice, so the question stays tied to realized compounding."
)

ALLOCATION_SECTION_TITLE = "Finding the optimal allocation"
ALLOCATION_SECTION_COPY = (
    "Sweep how much of each roll to stake before blending. The median path (gold) peaks at the Kelly stake; the "
    "5th-percentile path (teal) - the worst case, or precision - peaks at a much smaller, fractional-Kelly stake. "
    "The strategy is sized to maximize that 5th percentile, but with the book's cap: the risk-mitigation (cash) "
    "allocation may not exceed 50% of the portfolio. Here the unconstrained optimum would hold 93.5% cash, so the "
    "cap binds and the selected stake is 50% dice / 50% cash - the stake reused by the panels below."
)


