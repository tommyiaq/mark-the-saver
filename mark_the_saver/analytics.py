from __future__ import annotations

import numpy as np

from .models import SimulationResult


def summarize_result(result: SimulationResult, throws: int) -> dict[str, float | tuple[float, float]]:
    expected_arithmetic_return = float(np.mean(result.returns))
    median_final = float(np.median(result.final_wealth))
    spread = float(np.std(result.final_wealth, ddof=1))
    p05, p95 = np.percentile(result.final_wealth, [5, 95])
    geometric_mean_per_throw = float(np.exp(np.mean(np.log1p(result.returns)))) - 1
    median_cagr = float(np.exp(np.log(median_final) / int(throws)) - 1)

    return {
        "expected_arithmetic_return": expected_arithmetic_return,
        "median_final": median_final,
        "spread": spread,
        "percentiles": (float(p05), float(p95)),
        "geometric_mean_per_throw": geometric_mean_per_throw,
        "median_cagr": median_cagr,
    }
