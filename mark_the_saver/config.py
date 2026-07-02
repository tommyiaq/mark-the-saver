from __future__ import annotations

DEFAULT_THROWS = 300
DEFAULT_PATHS = 10_000
DEFAULT_SAMPLE_PATHS = 120
DEFAULT_SEED = 42

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
