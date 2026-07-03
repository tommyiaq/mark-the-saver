from __future__ import annotations

DEFAULT_THROWS = 300
DEFAULT_PATHS = 10_000
DEFAULT_SAMPLE_PATHS = 120
DEFAULT_SEED = 42

DICE_STATE_RETURNS = (-0.50, 0.05, 0.50)
DICE_STATE_PROBABILITIES = (1 / 6, 4 / 6, 1 / 6)

# A "crash" outcome is a base-asset monthly return at or below this threshold.
# The insurance payoff multiple is auto-calibrated from the empirical crash
# frequency p so the standalone insurance arithmetic return is exactly zero
# (fairly priced): M = (1 - p) / p. For the dice base only the -50% face is a
# crash (p = 1/6, M = 5), which reproduces the book's insurance side bet.
CRASH_THRESHOLD = -0.05

# The book caps the risk-mitigation allocation at 50% of the portfolio.
MITIGATION_CAP = 0.50

# Default (base asset, mitigation strategy) selection for the controls.
DEFAULT_BASE = "^GSPC"
DEFAULT_STRATEGY = "store"

# Base-return bin edges for the Xs and Os payoff profiles:
# (-inf, -5%], (-5%, 0%], (0%, 5%], (5%, inf)
XO_BIN_EDGES = (-0.05, 0.0, 0.05)

LOSS_RETURN = -0.50
MID_RETURN = 0.05
WIN_RETURN = 0.50

PATH_LINE_COLOR = "rgba(247, 201, 72, 0.34)"
PATH_LINE_WIDTH = 1.5
PERCENTILE_LOW_COLOR = "#5bc0be"
PERCENTILE_HIGH_COLOR = "rgba(255, 255, 255, 0.7)"
MEDIAN_COLOR = "#f7c948"
REALIZED_PATH_COLOR = "#f5a25d"

TITLE_TEXT = "300 draws, 10,000 paths"
HERO_COPY = (
    "Each path starts with 1 unit of capital. We bootstrap the selected base asset's monthly returns to simulate "
    "many possible paths, then overlay the single realized path the asset actually traveled over the same horizon. "
    "The dice demo keeps the book's game: -50% on a 1, +5% on 2-5, +50% on a 6."
)

XO_SECTION_TITLE = "Xs and Os Profile"
XO_SECTION_COPY = (
    "The lower panel mirrors the book's Xs and Os profile: the base bet, the risk mitigation, and the blend "
    "at the selected allocation. The point is the same safe-haven question: does the hedge improve the "
    "realized path, not just the average?"
)

COST_PLANE_TITLE = "The Cost-Effectiveness Plane"
COST_PLANE_COPY = (
    "The baseline is the un-hedged base asset (the diagonal, where geometric effect equals arithmetic cost). "
    "The blend at the slider allocation is plotted by its arithmetic cost (x) and geometric effect (y): above the "
    "diagonal the net portfolio effect is positive and the mitigation is cost-effective; the shaded region below "
    "is the rejection region - risk was reduced, wealth was not."
)

ALLOCATION_SECTION_TITLE = "Finding the optimal allocation"
ALLOCATION_SECTION_COPY = (
    "Sweep the allocation to the risk-mitigation payoff before blending. The median path (gold) peaks at the "
    "Kelly point; the 5th-percentile path (teal) - the worst case, or precision - usually peaks at a different "
    "allocation. The slider defaults to the 5th-percentile optimum subject to the book's cap (risk mitigation at "
    "most 50% of the portfolio), and you are free to move it: the Xs and Os profile and the cost-effectiveness "
    "plane below follow the slider."
)


