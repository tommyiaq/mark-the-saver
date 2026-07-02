from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SimulationResult:
    rolls: np.ndarray
    returns: np.ndarray
    wealth_paths: np.ndarray
    final_wealth: np.ndarray
