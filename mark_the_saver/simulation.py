from __future__ import annotations

import numpy as np

from .models import SimulationResult


def simulate_return_paths(returns, throws: int, paths: int, seed: int | None) -> SimulationResult:
    """Bootstrap ``paths`` compounded paths of ``throws`` draws (with replacement)
    from an empirical return pool.

    For the dice base the pool is the six equally likely die outcomes, so this
    reproduces the original dice game exactly; for a real asset it is the
    monthly return history.
    """
    pool = np.asarray(returns, dtype=float)
    if pool.size == 0:
        raise ValueError("return pool is empty")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, pool.size, size=(paths, throws))
    drawn = pool[idx]
    growth = np.cumprod(1.0 + drawn, axis=1)
    wealth_paths = np.concatenate([np.ones((paths, 1), dtype=float), growth], axis=1)
    return SimulationResult(rolls=idx, returns=drawn, wealth_paths=wealth_paths, final_wealth=growth[:, -1])


def realized_path(returns, throws: int) -> np.ndarray:
    """Compound the most recent ``throws`` returns in their actual order.

    Returns the wealth series (starting at 1.0) of the single path the asset
    truly traveled. Uses ``min(throws, len(returns))`` months when history is
    shorter than the horizon.
    """
    pool = np.asarray(returns, dtype=float)
    n = min(int(throws), pool.size)
    recent = pool[-n:]
    return np.concatenate([[1.0], np.cumprod(1.0 + recent)])
