# Plan — From Dice to Real Market Data

Goal: replace the dice generator with real fund/index returns downloaded from an API,
bootstrap 10k paths from those returns, make the risk-mitigation strategy selectable
(store-of-value / alpha / insurance), let the allocation be a user slider, and propagate
the selected (base, strategy, allocation) triple through the allocation analysis, the
Xs-and-Os profile, and a corrected book-form cost-effectiveness plane. Remove the
"Kelly" naming everywhere since cash/Kelly is just one strategy among three.

## Decisions locked (from Q&A)

- **Data source:** yfinance, no API key; downloads cached to local CSV (`data/`) so the app works offline after first fetch.
- **Frequency:** monthly returns; 300 draws per path (= 25 years), 10,000 paths, sampling with replacement (bootstrap).
- **Strategies (book-style trio):**
  - *Store-of-value* — cash at 0% per month (rename of the current Kelly case).
  - *Alpha* — a real fund (gold) sampled **jointly** with the base (same-month pairs, so crash behavior is preserved).
  - *Insurance* — synthetic convex payoff: pays a large multiple in base "crash" months, −100% otherwise; the multiple is auto-calibrated so the standalone arithmetic return ≈ 0 (fairly priced insurance, like the book's cartoon).
- **Allocation:** user slider (0–100% mitigation). The optima (median-max "Kelly point" and 5th-pct-max) are computed and marked on the allocation chart; the slider defaults to the 5th-pct optimum capped at 50%, but the user is free to move it.
- **CE plane semantics (correction):** book form — x = arithmetic cost, y = geometric effect, diagonal `y = x` = baseline (100% base asset), **shaded rejection region below the diagonal**. Points land wherever the math puts them: above = cost-effective. Expectation with real SPX data: cash and most alpha havens fall *below* (as in the book); insurance may land above.

## Steps

Each step needs explicit approval before implementation. Status: `[ ]` pending → `[x]` done (with a short done-note added at completion).

### [x] Step 1 — Data layer (`market_data.py`)
- Install `yfinance` into `t:/venv`.
- New module `mark_the_saver/market_data.py`:
  - `fetch_monthly_returns(ticker)` — monthly adjusted-close returns via yfinance, cached as CSV in `data/<ticker>.csv`; refresh only when the cache is missing/stale (>30 days) or on `force=True`; offline fallback to cache.
  - `load_pair(base_ticker, haven_ticker)` — aligned same-month return pairs over the overlapping window.
  - Synthetic `dice` series kept available so the original book demo remains selectable as a base.
- Base tickers offered: `Dice (book demo)`, `^GSPC` (SPX, default), `SPY`, `QQQ`. Alpha haven fund: `GLD` (gold).
- Verify: script prints series lengths, date ranges, first/last returns for each ticker.
- **Done note:** yfinance 1.5.1 installed. Daily data resampled to month-end (yfinance's `1mo` interval only reached 1985 for ^GSPC; daily reaches 1928). Verified live: ^GSPC 1,182 months (1928-01 → 2026-06, min −29.9%), SPY 401, QQQ 327, GLD 259; (^GSPC, GLD) pair 259 aligned months. Incomplete current month dropped. Offline fallback tested (simulated network failure → served from cache). `data/` added to `.gitignore`. Empirical note: P(SPX month ≤ −5%) = 10.9%, close to the book's annual crash-bin frequency (11/120) — supports the −5% monthly crash threshold for insurance.

### [x] Step 2 — De-Kelly rename (no behavior change)
- `kelly_analysis.py` → `mitigation_analysis.py`; `kelly_profile.py` → `xo_profile.py`.
- Rename symbols/labels: `KellyStrategyStats` → `StrategyStats`, `KellyProfileData` → `BlendProfileData`, `build_kelly_profile*` → `build_xo_profile*`, config constants `KELLY_STATE_*` → `DICE_STATE_*`, CSS `kelly-*` classes → `xo-*`.
- Copy updated: "Kelly" only remains where it genuinely refers to the median-max point on the allocation curve.
- Verify: app boots, panels identical to today.
- **Done note:** files moved with `git mv` (history preserved); symbols renamed (`StrategyStats`, `BlendProfileData`, `build_blend_profile_data`, `build_xo_profile`, `DICE_STATE_*`, `XO_SECTION_*`); CSS `kelly-*` → `xo-*`; README module list refreshed. Remaining "Kelly" tokens verified by grep to refer only to the median-max point. App boots HTTP 200; numbers unchanged (selected 50% dice, Kelly 38%, fractional 6.5%, blend arith +1.67% / geom +0.57%).

### [ ] Step 3 — Strategy engine (`mitigation_analysis.py`)
- Empirical joint distribution per (base, strategy):
  - store-of-value → haven return 0.0 every month;
  - alpha → gold's same-month return;
  - insurance → crash threshold: base monthly return ≤ −5% (constant, configurable); payout multiple `M = (1−p)/p` from the base's empirical crash frequency `p` (standalone arithmetic ≈ 0); −100% in non-crash months.
- Allocation sweep generalized to empirical distributions: per-draw combined log-return mean/variance over the sample → median & 5th-percentile wealth/CAGR after 300 draws (same lognormal machinery as today, distribution swapped).
- Optima: median-max ("Kelly point") and 5th-pct-max, plus the capped default for the slider.
- Verify: numbers for (dice, store-of-value) reproduce today's 6.5% / 38% / 50-50 results exactly.

### [ ] Step 4 — Controls
- Base-asset dropdown (Dice demo / SPX / SPY / QQQ), strategy dropdown (Store-of-value / Alpha: gold / Insurance), allocation slider (0–100% mitigation, default = capped 5th-pct optimum), keep throws/paths/sample-paths/seed inputs.
- Slider auto-resets to the selected pair's default when base/strategy changes.
- Verify: controls render and fire; panels wired fully in Step 5.

### [ ] Step 5 — Callback-driven panels
- Allocation panel: median + 5th-pct curves vs mitigation allocation for the selected pair; slider position marked; optima badges; cap line kept as reference only (slider is free).
- XO panel: binned payoff profiles (base-return bins, e.g. ≤−5%, −5–0%, 0–5%, >5%): base row, haven row, combined row at the slider allocation; arithmetic/geometric summary boxes plus Cost and Net vs 100% base.
- CE plane: book form per the locked decision above; plotted point = selected strategy at slider allocation; baseline = 100% base asset.
- Verify: moving the slider updates all three panels consistently; store/alpha/insurance switch works.

### [ ] Step 6 — Hero charts on real data
- The top paths/histogram/metrics switch from the dice simulator to bootstrap draws of the selected base's monthly returns (dice kept when the demo base is selected). Blended portfolio overlay optional (out of scope unless requested).
- Verify: SPX bootstrap median CAGR lands in a plausible historical range; dice demo reproduces today's figures.

### [ ] Step 7 — Docs & end-to-end verify
- README rewrite (data source, caching, controls, strategy definitions, CE-plane reading guide).
- Full run: fetch fresh data, exercise every dropdown/slider combination, confirm book-consistent behavior (SPX+cash below baseline; insurance at a small allocation plausibly above).
- `plan.md` fully checked off.

## Notes / open parameters (tune during steps, defaults stated)

- Insurance crash threshold: monthly ≤ −5% (roughly the worst ~5–7% of SPX months → fair multiple ≈ 13–20×). Configurable constant.
- XO bins for monthly returns: ≤−5%, −5–0%, 0–5%, >5%.
- ^GSPC is price-only (no dividends) back to 1927; ETFs (SPY/GLD/QQQ) are total-return via adjusted close. Noted in README.
- CE plane rejection band: plain "below diagonal" shading (no bootstrap confidence interval on the baseline for now; can be added later).
