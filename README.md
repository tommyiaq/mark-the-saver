# Mark the Saver

An interactive lab for the safe-haven / compounding argument from Mark Spitznagel's
*Safe Haven*: bootstrap 10,000 possible paths from a real asset's monthly returns (or the
book's dice game), pick a risk-mitigation strategy and allocation, and see whether the
blend is **cost-effective** — i.e. whether it raises the compound growth rate (median CAGR),
not just lowers volatility.

## Run

```powershell
t:/venv/Scripts/python.exe app.py
```

Then open the local Dash server URL printed in the terminal.

## Data

Monthly returns are downloaded from Yahoo Finance via `yfinance` (no API key) and cached as
CSV under `data/<ticker>.csv`. The cache is reused for 30 days and is the offline fallback if
a download fails; delete a file (or the folder) to force a refresh. Daily prices are resampled
to month-end so history goes as far back as the source allows.

- `^GSPC` (S&P 500 index) is **price-only** (no dividends) but reaches back to 1928.
- ETFs (`SPY`, `QQQ`, `GLD`) are **total-return** (adjusted close) from their inception.
- Because of that, `^GSPC` and `SPY` are the same index but show different medians — different
  dividend treatment **and** different sample windows (1928+ vs 1993+).
- `Dice (book demo)` is synthetic (the six die faces), so it has no realized path and cannot be
  paired with a fund.

## Controls

- **Base asset** — Dice demo / SPX / SPY / QQQ. Drives the hero charts and the analysis below.
- **Risk mitigation** — the safe-haven strategy (see below). Alpha is disabled for the dice base.
- **Mitigation allocation** — slider, 0–100%. Defaults to the 5th-percentile-optimal allocation
  (capped at 50%, the book's cap); move it freely to explore. The Xs and Os profile and the
  cost-effectiveness plane follow the slider.
- **Throws / paths / sample / seed** — bootstrap horizon (months), number of paths, paths drawn
  on the chart, and RNG seed. Click **Generate paths** to re-simulate the hero with new settings.

## Strategies

All three are sampled jointly with the base month-by-month, so crash behavior is preserved.

- **Store-of-value (cash)** — 0% every month; just dilutes risk.
- **Alpha (gold)** — GLD's same-month return, aligned to the base's calendar.
- **Insurance (convex)** — pays a multiple `M` in crash months (base return ≤ −5%) and −100%
  otherwise, with `M = (1 − p) / p` from the base's empirical crash frequency `p`, so the
  standalone arithmetic return is ~0 (fairly priced). For the dice base this auto-calibrates to
  `p = 1/6`, `M = 5` — exactly the book's "+500% on a 1" side bet.

## Panels

1. **Hero (paths / histogram / metrics)** — the bootstrap cloud with median and 5th/95th bands,
   plus the single **realized path** the asset actually traveled over the same horizon (bold
   orange), its final wealth marked on the histogram, and a realized-CAGR metric card.
2. **Allocation analysis** — median (gold) and 5th-percentile (teal) ending wealth across every
   allocation; marks the Kelly point (median max), the 5th-percentile max, and the slider.
3. **Xs and Os profile** — binned payoff profiles (base bins ≤−5% / −5–0% / 0–5% / >5%) for the
   base, the mitigation, and the blend, with arithmetic/geometric summaries and Cost / Net.
4. **Cost-effectiveness plane** — x = arithmetic cost, y = geometric effect. The diagonal `y = x`
   is the un-hedged base baseline. **Above** the diagonal the net portfolio effect is positive
   and the mitigation is cost-effective; the shaded region **below** is the rejection region —
   risk was reduced but wealth was not. This reproduces the book's finding that cash and most
   alpha havens fall below the line, while a small pinch of convex insurance can rise above it.

## Project Structure

- `app.py` - thin entrypoint that creates the Dash app and registers callbacks
- `mark_the_saver/config.py` - constants and copy
- `mark_the_saver/market_data.py` - monthly returns from yfinance with local CSV cache
- `mark_the_saver/models.py` - shared data models
- `mark_the_saver/simulation.py` - bootstrap paths + realized-path compounding
- `mark_the_saver/analytics.py` - summary metrics
- `mark_the_saver/figures.py` - hero Plotly figures (paths + histogram)
- `mark_the_saver/mitigation_analysis.py` - strategy pairs, allocation sweep, blend/XO stats
- `mark_the_saver/allocation_analysis.py` - allocation sweep panel
- `mark_the_saver/xo_profile.py` - Xs and Os payoff-profile panel
- `mark_the_saver/cost_effectiveness_plane.py` - book-form cost-effectiveness plane
- `mark_the_saver/controls.py` - control panel widgets
- `mark_the_saver/layout.py` - overall page layout
- `mark_the_saver/metrics.py` - metric card rendering
- `mark_the_saver/callbacks.py` - Dash callbacks (hero sim + linked panels)
- `assets/styles.css` - visual styling

## Safe Haven Framing

- Look at the realized path, not just the average — you get `N = 1`, not the multiverse.
- Prioritize the median outcome and downside bounds over mean wealth (geometric, not arithmetic).
- Judge a hedge by its **net portfolio effect** (does it raise the whole portfolio's CAGR?),
  which is what the cost-effectiveness plane makes visible.
