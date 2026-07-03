from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State

from .allocation_analysis import build_allocation_cards, build_allocation_figure
from .analytics import summarize_result
from .controls import strategy_options
from .cost_effectiveness_plane import build_plane_cards, build_plane_figure
from .figures import make_histogram_figure, make_path_figure
from .market_data import DICE_TICKER, fetch_monthly_returns
from .metrics import metric_card
from .mitigation_analysis import (
    STRATEGY_ALPHA,
    STRATEGY_STORE,
    build_allocation_curve,
    build_strategy_pair,
    build_xo_profile,
    default_mitigation_weight,
)
from .simulation import realized_path, simulate_return_paths
from .xo_profile import build_xo_body


def register_callbacks(app) -> None:
    @app.callback(
        Output("strategy-dropdown", "options"),
        Output("strategy-dropdown", "value"),
        Output("allocation-slider", "value"),
        Input("base-dropdown", "value"),
        Input("strategy-dropdown", "value"),
    )
    def sync_strategy_controls(base_ticker: str, strategy: str):
        # The dice base cannot be paired with a real fund (no calendar).
        if base_ticker == DICE_TICKER and strategy == STRATEGY_ALPHA:
            strategy = STRATEGY_STORE
        options = strategy_options(base_ticker)
        allocation = round(default_mitigation_weight(base_ticker, strategy) * 100.0, 1)
        return options, strategy, allocation

    @app.callback(
        Output("allocation-graph", "figure"),
        Output("allocation-cards", "children"),
        Output("xo-body", "children"),
        Output("plane-graph-fig", "figure"),
        Output("plane-cards", "children"),
        Output("allocation-value", "children"),
        Input("base-dropdown", "value"),
        Input("strategy-dropdown", "value"),
        Input("allocation-slider", "value"),
    )
    def update_panels(base_ticker: str, strategy: str, slider_pct: float | None):
        # Guard against the transient dice+alpha combo before the sync callback
        # settles (the dice base has no calendar to pair with a fund).
        if base_ticker == DICE_TICKER and strategy == STRATEGY_ALPHA:
            strategy = STRATEGY_STORE

        pair = build_strategy_pair(base_ticker, strategy)
        curve = build_allocation_curve(pair)
        weight = max(0.0, min(1.0, (slider_pct or 0.0) / 100.0))

        profile = build_xo_profile(pair, weight)
        allocation_figure = build_allocation_figure(curve, weight)
        allocation_cards = build_allocation_cards(curve, weight)
        xo_body = build_xo_body(profile)
        plane_figure = build_plane_figure(profile.stats)
        plane_cards = build_plane_cards(profile.stats)

        return allocation_figure, allocation_cards, xo_body, plane_figure, plane_cards, f"{weight * 100:g}%"

    @app.callback(
        Output("paths-graph", "figure"),
        Output("histogram-graph", "figure"),
        Output("metrics-row", "children"),
        Input("generate-button", "n_clicks"),
        Input("base-dropdown", "value"),
        State("throws-input", "value"),
        State("paths-input", "value"),
        State("sample-input", "value"),
        State("seed-input", "value"),
    )
    def update_dashboard(n_clicks: int, base_ticker: str, throws: int, paths: int, sample_paths: int, seed: int | None):
        if not throws or not paths:
            empty_figure = go.Figure()
            empty_figure.update_layout(template="plotly_dark")
            return empty_figure, empty_figure, []

        base_ticker = base_ticker or DICE_TICKER
        is_dice = base_ticker == DICE_TICKER
        pool = fetch_monthly_returns(base_ticker).returns

        result = simulate_return_paths(pool, int(throws), int(paths), None if seed is None else int(seed))
        # The dice base has no calendar, so there is no single realized path.
        realized = None if is_dice else realized_path(pool, int(throws))
        realized_final = None if realized is None else float(realized[-1])

        path_figure = make_path_figure(result, int(throws), int(sample_paths), realized_wealth=realized)
        histogram = make_histogram_figure(result.final_wealth, realized_final=realized_final)
        summary = summarize_result(result, int(throws))

        draw_label = "Mean roll return" if is_dice else "Mean monthly return"
        p05, p95 = summary["percentiles"]
        metrics = [
            metric_card(draw_label, f"{summary['expected_arithmetic_return'] * 100:,.2f}%", "Across the sampled base returns"),
            metric_card("Median final wealth", f"{summary['median_final']:,.3f}x", f"Implied CAGR {summary['median_cagr'] * 100:,.2f}%/mo"),
            metric_card("5th percentile", f"{p05:,.3f}x", "Lower path boundary"),
            metric_card("95th percentile", f"{p95:,.3f}x", f"Geom. per draw {summary['geometric_mean_per_throw'] * 100:,.2f}%"),
        ]
        if realized is not None:
            steps = len(realized) - 1
            annualized = realized_final ** (12.0 / steps) - 1.0 if steps > 0 else 0.0
            metrics.append(
                metric_card(
                    "Realized path (actual)",
                    f"{realized_final:,.3f}x",
                    f"Last {steps} months · {annualized * 100:,.1f}%/yr",
                )
            )

        return path_figure, histogram, metrics
