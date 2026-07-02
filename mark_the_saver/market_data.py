from __future__ import annotations

"""Market data layer: monthly returns from yfinance with a local CSV cache.

Real tickers are downloaded once and cached under ``data/<ticker>.csv`` so the
dashboard works offline after the first fetch. The synthetic ``DICE`` series
keeps the book's demo game available as a base asset: it is not a time series,
just the six equally likely die outcomes, so bootstrap-sampling it with
replacement reproduces the original dice game exactly.

Pairing note: ``load_pair`` aligns two real tickers on their common months.
The synthetic dice base has no calendar, so it cannot be paired with a real
fund (the UI disables the alpha strategy for the dice base).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_MAX_AGE = timedelta(days=30)

DICE_TICKER = "DICE"
DICE_RETURNS = (-0.50, 0.05, 0.05, 0.05, 0.05, 0.50)

BASE_TICKERS = (DICE_TICKER, "^GSPC", "SPY", "QQQ")
ALPHA_HAVEN_TICKER = "GLD"

TICKER_LABELS = {
    DICE_TICKER: "Dice (book demo)",
    "^GSPC": "S&P 500 (SPX)",
    "SPY": "SPY (S&P 500 ETF)",
    "QQQ": "QQQ (Nasdaq 100 ETF)",
    ALPHA_HAVEN_TICKER: "Gold (GLD)",
}


@dataclass(frozen=True)
class ReturnSeries:
    ticker: str
    label: str
    returns: np.ndarray
    months: tuple[str, ...] | None  # "YYYY-MM" per return; None for synthetic
    is_synthetic: bool

    @property
    def start(self) -> str | None:
        return self.months[0] if self.months else None

    @property
    def end(self) -> str | None:
        return self.months[-1] if self.months else None


def _cache_path(ticker: str) -> Path:
    safe = ticker.replace("^", "_").replace("/", "_")
    return DATA_DIR / f"{safe}.csv"


def _read_cache(path: Path) -> tuple[list[str], list[float]]:
    months: list[str] = []
    returns: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        month, value = line.split(",")
        months.append(month)
        returns.append(float(value))
    return months, returns


def _write_cache(path: Path, months: list[str], returns: list[float]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["month,return"] + [f"{m},{r:.10f}" for m, r in zip(months, returns)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _cache_is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age <= CACHE_MAX_AGE


def _download_monthly_returns(ticker: str) -> tuple[list[str], list[float]]:
    # Daily data reaches much further back than yfinance's "1mo" interval
    # (e.g. ^GSPC: 1927 vs 1985), so fetch daily and resample to month-end.
    import yfinance as yf

    frame = yf.download(ticker, period="max", interval="1d", auto_adjust=True, progress=False)
    if frame is None or frame.empty:
        raise RuntimeError(f"yfinance returned no data for {ticker!r}")
    close = frame["Close"]
    if hasattr(close, "columns"):  # multi-index frame for a single ticker
        close = close.iloc[:, 0]
    close = close.dropna().resample("ME").last().dropna()

    # Drop the current, incomplete month.
    this_month = datetime.now().strftime("%Y-%m")
    keep = [ts for ts in close.index if ts.strftime("%Y-%m") != this_month]
    close = close.loc[keep]

    returns = close.pct_change().dropna()
    months = [ts.strftime("%Y-%m") for ts in returns.index]
    return months, [float(r) for r in returns.to_numpy()]


def fetch_monthly_returns(ticker: str, force: bool = False) -> ReturnSeries:
    """Monthly returns for ``ticker``, cached to CSV; offline falls back to cache."""
    if ticker == DICE_TICKER:
        return ReturnSeries(
            ticker=DICE_TICKER,
            label=TICKER_LABELS[DICE_TICKER],
            returns=np.array(DICE_RETURNS, dtype=float),
            months=None,
            is_synthetic=True,
        )

    path = _cache_path(ticker)
    if force or not _cache_is_fresh(path):
        try:
            months, returns = _download_monthly_returns(ticker)
            _write_cache(path, months, returns)
        except Exception:
            if not path.exists():
                raise
    months, returns = _read_cache(path)
    return ReturnSeries(
        ticker=ticker,
        label=TICKER_LABELS.get(ticker, ticker),
        returns=np.array(returns, dtype=float),
        months=tuple(months),
        is_synthetic=False,
    )


def load_pair(base_ticker: str, haven_ticker: str) -> tuple[ReturnSeries, ReturnSeries]:
    """Same-month aligned return pairs for two real tickers."""
    base = fetch_monthly_returns(base_ticker)
    haven = fetch_monthly_returns(haven_ticker)
    if base.is_synthetic or haven.is_synthetic:
        raise ValueError("the synthetic dice series has no calendar and cannot be paired")

    base_map = dict(zip(base.months, base.returns))
    haven_map = dict(zip(haven.months, haven.returns))
    common = [m for m in base.months if m in haven_map]
    if not common:
        raise ValueError(f"no overlapping months between {base_ticker!r} and {haven_ticker!r}")

    def _restrict(series: ReturnSeries, source: dict[str, float]) -> ReturnSeries:
        return ReturnSeries(
            ticker=series.ticker,
            label=series.label,
            returns=np.array([source[m] for m in common], dtype=float),
            months=tuple(common),
            is_synthetic=False,
        )

    return _restrict(base, base_map), _restrict(haven, haven_map)
