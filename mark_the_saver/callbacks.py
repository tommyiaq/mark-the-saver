from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State

from .analytics import summarize_result
from .figures import make_histogram_figure, make_path_figure
from .metrics import metric_card
from .simulation import simulate_die_paths


def register_callbacks(app) -> None:
    @app.callback(
        Output("paths-graph", "figure"),
        Output("histogram-graph", "figure"),
        Output("metrics-row", "children"),
        Input("generate-button", "n_clicks"),
        State("throws-input", "value"),
        State("paths-input", "value"),
        State("sample-input", "value"),
        State("seed-input", "value"),
    )
    def update_dashboard(n_clicks: int, throws: int, paths: int, sample_paths: int, seed: int | None):
        if not throws or not paths:
            empty_figure = go.Figure()
            empty_figure.update_layout(template="plotly_dark")
            return empty_figure, empty_figure, []

        result = simulate_die_paths(int(throws), int(paths), None if seed is None else int(seed))
        path_figure = make_path_figure(result, int(throws), int(sample_paths))
        histogram = make_histogram_figure(result.final_wealth)
        summary = summarize_result(result, int(throws))

        p05, p95 = summary["percentiles"]
        metrics = [
            metric_card("Mean roll return", f"{summary['expected_arithmetic_return'] * 100:,.2f}%", "Across the simulated payoff rule"),
            metric_card("Median final wealth", f"{summary['median_final']:,.3f}x", f"Implied CAGR {summary['median_cagr'] * 100:,.2f}%"),
            metric_card("5th percentile", f"{p05:,.3f}x", "Lower path boundary"),
            metric_card("95th percentile", f"{p95:,.3f}x", f"Std. dev. {summary['spread']:,.3f}x; geom. per throw {summary['geometric_mean_per_throw'] * 100:,.2f}%"),
        ]

        return path_figure, histogram, metrics
