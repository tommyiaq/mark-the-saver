from __future__ import annotations

import numpy as np

from .config import LOSS_RETURN, MID_RETURN, WIN_RETURN
from .models import SimulationResult


def simulate_die_paths(throws: int, paths: int, seed: int | None) -> SimulationResult:
    rng = np.random.default_rng(seed)
    rolls = rng.integers(1, 7, size=(paths, throws))
    returns = np.where(
        rolls == 1,
        LOSS_RETURN,
        np.where(rolls == 6, WIN_RETURN, MID_RETURN),
    )
    growth = np.cumprod(1.0 + returns, axis=1)
    wealth_paths = np.concatenate([np.ones((paths, 1), dtype=float), growth], axis=1)
    final_wealth = growth[:, -1]
    return SimulationResult(rolls=rolls, returns=returns, wealth_paths=wealth_paths, final_wealth=final_wealth)
