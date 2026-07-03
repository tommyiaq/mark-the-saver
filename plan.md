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

### [x] Step 3 — Strategy engine (`mitigation_analysis.py`)
- Empirical joint distribution per (base, strategy):
  - store-of-value → haven return 0.0 every month;
  - alpha → gold's same-month return;
  - insurance → crash threshold: base monthly return ≤ −5% (constant, configurable); payout multiple `M = (1−p)/p` from the base's empirical crash frequency `p` (standalone arithmetic ≈ 0); −100% in non-crash months.
- Allocation sweep generalized to empirical distributions: per-draw combined log-return mean/variance over the sample → median & 5th-percentile wealth/CAGR after 300 draws (same lognormal machinery as today, distribution swapped).
- Optima: median-max ("Kelly point") and 5th-pct-max, plus the capped default for the slider.
- Verify: numbers for (dice, store-of-value) reproduce today's 6.5% / 38% / 50-50 results exactly.
- **Done note:** engine rewritten around `StrategyPair` (joint equally-likely outcomes) + `build_strategy_pair(base, strategy)` + generalized `build_allocation_curve(pair)` whose sweep axis is now the **mitigation weight** (allocation panel axis flipped accordingly, labels dynamic). Constants `CRASH_THRESHOLD = −5%`, `MITIGATION_CAP = 50%` in config. Gate passed exactly: dice+store → mitigation 93.5% / 62% / 50% ⇔ dice stake 6.5% / 38% / 50%; legacy blend 50/50 (+1.67% arith, +0.57% geom) unchanged; dice insurance auto-calibrates to p=1/6, M=5.0 — reproducing the book's 500% side bet from the generic threshold rule. Real-data sanity (^GSPC monthly, per-draw CAGRs): store → selected 48% (cap not binding), median 0.51%→0.30%, p5 0.004%→0.04%; alpha (GLD, 259-month overlap) → 50%, median rises 0.72%→0.82% (gold-friendly window); insurance → **a 1% pinch**, median 0.51%→0.57% AND p5 0.004%→0.18% — the Petersburg merchant trade reproduced on real SPX data. App boots HTTP 200. Alpha with the dice base raises `ValueError` (no calendar) — UI will disable that combo in Step 4.

### [x] Step 4 — Controls
- Base-asset dropdown (Dice demo / SPX / SPY / QQQ), strategy dropdown (Store-of-value / Alpha: gold / Insurance), allocation slider (0–100% mitigation, default = capped 5th-pct optimum), keep throws/paths/sample-paths/seed inputs.
- Slider auto-resets to the selected pair's default when base/strategy changes.
- Verify: controls render and fire; panels wired fully in Step 5.
- **Done note:** dropdowns + slider added to the hero control panel (`controls.py`; dark-themed via `.control-dropdown` / `.alloc-slider` CSS). Defaults `DEFAULT_BASE = ^GSPC`, `DEFAULT_STRATEGY = store` in config. Sync callback in `callbacks.py` (single circular callback: base/strategy in → options/strategy/slider out) disables alpha for the dice base and falls back to store. Verified slider defaults per pair: ^GSPC+store 48.0%, ^GSPC+alpha 50.0%, ^GSPC+insurance 1.0%, DICE+store 50.0%, DICE+insurance 9.5% (≈ the book's own 9% side-bet allocation, derived not hard-coded), SPY+insurance 1.0%, QQQ+store 7.0%. App boots HTTP 200, no callback errors.

### [x] Step 5 — Callback-driven panels
- Allocation panel: median + 5th-pct curves vs mitigation allocation for the selected pair; slider position marked; optima badges; cap line kept as reference only (slider is free).
- XO panel: binned payoff profiles (base-return bins, e.g. ≤−5%, −5–0%, 0–5%, >5%): base row, haven row, combined row at the slider allocation; arithmetic/geometric summary boxes plus Cost and Net vs 100% base.
- CE plane: book form per the locked decision above; plotted point = selected strategy at slider allocation; baseline = 100% base asset.
- Verify: moving the slider updates all three panels consistently; store/alpha/insurance switch works.
- **Done note:** panels converted to static shells filled by one `update_panels` callback in `callbacks.py` (Inputs: base/strategy/slider → 5 Outputs: allocation figure+cards, xo-body, plane figure+cards), with a dice+alpha guard for the transient before the sync callback settles. Allocation figure gained a live slider marker + slider card; sweep axis is the mitigation weight. XO panel rewritten to binned bar profiles over `XO_BIN_EDGES` (≤−5% / −5–0% / 0–5% / >5%) with base/haven/combined rows + Cost/Net boxes (data `build_xo_profile`/`XOProfile` in `mitigation_analysis`, rendering `build_xo_body`/`build_xo_panel` in `xo_profile`; shell renamed to avoid the name clash). CE plane rebuilt in **book form**: x=arithmetic cost, y=geometric effect, y=x baseline diagonal, shaded rejection region below, net-effect connector, verdict-colored point (`build_plane_figure`/`build_plane_cards`); `build_strategy_pair` memoized (`lru_cache`). All render paths exercised across 7 base×strategy combos; **the requested CE correction holds** — ^GSPC+cash net −0.21% lands below the baseline (rejected), ^GSPC+insurance +0.05% (1% pinch) and the dice cases above. All 8 callback IDs resolve against the layout; app boots HTTP 200, no exceptions. Browser drive not possible here (no `chromium-cli`); recommend a manual local check of live slider/dropdown updates. Hero paths/histogram still dice-driven until Step 6.

### [x] Step 6 — Hero charts on real data
- The top paths/histogram/metrics switch from the dice simulator to bootstrap draws of the selected base's monthly returns (dice kept when the demo base is selected). Blended portfolio overlay optional (out of scope unless requested).
- **Added per user request:** overlay the single **realized path** the base asset actually traveled over the same horizon (last `throws` months, true order) on top of the simulated cloud; mark its final wealth on the histogram and add a "Realized path" metric card with the annualized CAGR.
- Verify: SPX bootstrap median CAGR lands in a plausible historical range; dice demo reproduces today's figures.
- **Done note:** `simulation.py` generalized to `simulate_return_paths(pool, throws, paths, seed)` (bootstrap from any empirical return pool; dice pool = the 6 faces, so the dice game is reproduced) + `realized_path(returns, throws)` (compounds the last `throws` real months in order). `make_path_figure` gained a bold orange `Realized path (actual)` overlay; `make_histogram_figure` a realized-final marker; hero callback now takes `base-dropdown` as an Input, fetches the base's monthly returns, and adds a 5th "Realized path" metric card (annualized). `.metrics-row` switched to `auto-fit` so 4 (dice) or 5 (real) cards lay out. Verified across all bases: ^GSPC realized 6.13× over 300mo (7.5%/yr, price-only) vs sim median 4.66×; SPY 9.57× (9.5%/yr total-return); QQQ 19.12× (12.5%); GLD 8.16× over its 259 months (10.2%); DICE → median 0.01× (book's all-in ruin), no realized path. App boots HTTP 200, no exceptions. Caveat surfaced: ^GSPC (price-only, 1928→) and SPY (total-return, 1993→) give different medians — both dividends and sample window differ; to be documented in Step 7 README.

### [x] Step 7 — Docs & end-to-end verify
- README rewrite (data source, caching, controls, strategy definitions, CE-plane reading guide).
- Full run: fetch fresh data, exercise every dropdown/slider combination, confirm book-consistent behavior (SPX+cash below baseline; insurance at a small allocation plausibly above).
- `plan.md` fully checked off.
- **Done note:** README rewritten end-to-end (run, data + caching, ^GSPC-vs-SPY caveat, controls, the three strategies, all four panels incl. realized-path overlay, book-form CE-plane reading guide, refreshed module list, safe-haven framing). Combo/behavior verification already performed in Steps 3/5/6 (7 base×strategy combos exercised; SPX+cash net −0.21% below baseline, insurance above; app boots HTTP 200). No code changed in this step. **Recommended manual pass** (no `chromium-cli` here to drive a browser): run the app, switch base + strategy, drag the slider, confirm the four panels update live.

## Notes / open parameters (tune during steps, defaults stated)

- Insurance crash threshold: monthly ≤ −5% (roughly the worst ~5–7% of SPX months → fair multiple ≈ 13–20×). Configurable constant.
- XO bins for monthly returns: ≤−5%, −5–0%, 0–5%, >5%.
- ^GSPC is price-only (no dividends) back to 1927; ETFs (SPY/GLD/QQQ) are total-return via adjusted close. Noted in README.
- CE plane rejection band: plain "below diagonal" shading (no bootstrap confidence interval on the baseline for now; can be added later).
