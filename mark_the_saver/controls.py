from __future__ import annotations

from dash import dcc, html

from .config import (
    DEFAULT_BASE,
    DEFAULT_PATHS,
    DEFAULT_SAMPLE_PATHS,
    DEFAULT_SEED,
    DEFAULT_STRATEGY,
    DEFAULT_THROWS,
)
from .market_data import BASE_TICKERS, DICE_TICKER, TICKER_LABELS
from .mitigation_analysis import STRATEGY_ALPHA, STRATEGY_LABELS, default_mitigation_weight


def base_options() -> list[dict]:
    return [{"label": TICKER_LABELS[ticker], "value": ticker} for ticker in BASE_TICKERS]


def strategy_options(base_ticker: str) -> list[dict]:
    # The dice base has no calendar, so it cannot be paired with a real fund.
    return [
        {
            "label": label,
            "value": key,
            "disabled": key == STRATEGY_ALPHA and base_ticker == DICE_TICKER,
        }
        for key, label in STRATEGY_LABELS.items()
    ]


def build_control_panel() -> html.Div:
    shared_style = {
        "backgroundColor": "#050d14",
        "color": "#ffffff",
        "border": "1px solid rgba(255,255,255,0.32)",
    }
    default_allocation = round(default_mitigation_weight(DEFAULT_BASE, DEFAULT_STRATEGY) * 100.0, 1)

    return html.Div(
        [
            html.Label("Base asset", className="control-label"),
            dcc.Dropdown(
                id="base-dropdown",
                options=base_options(),
                value=DEFAULT_BASE,
                clearable=False,
                searchable=False,
                className="control-dropdown",
            ),
            html.Label("Risk mitigation", className="control-label"),
            dcc.Dropdown(
                id="strategy-dropdown",
                options=strategy_options(DEFAULT_BASE),
                value=DEFAULT_STRATEGY,
                clearable=False,
                searchable=False,
                className="control-dropdown",
            ),
            html.Div(
                [
                    html.Span("Mitigation allocation", className="control-label"),
                    html.Span(f"{default_allocation:g}%", id="allocation-value", className="control-value"),
                ],
                className="control-label-row",
            ),
            html.Div(
                dcc.Slider(
                    id="allocation-slider",
                    min=0,
                    max=100,
                    step=0.5,
                    value=default_allocation,
                    marks={0: "0%", 25: "25%", 50: "50%", 75: "75%", 100: "100%"},
                ),
                className="alloc-slider",
            ),
            html.Label("Throws per path", className="control-label"),
            dcc.Input(
                id="throws-input",
                type="number",
                min=30,
                max=300,
                step=10,
                value=DEFAULT_THROWS,
                className="numeric-input",
                style=shared_style,
            ),
            html.Label("Paths to simulate", className="control-label"),
            dcc.Input(
                id="paths-input",
                type="number",
                min=1000,
                max=10000,
                step=1000,
                value=DEFAULT_PATHS,
                className="numeric-input",
                style=shared_style,
            ),
            html.Label("Sample paths shown", className="control-label"),
            dcc.Input(
                id="sample-input",
                type="number",
                min=10,
                max=200,
                step=10,
                value=DEFAULT_SAMPLE_PATHS,
                className="numeric-input",
                style=shared_style,
            ),
            html.Label("Random seed", className="control-label"),
            dcc.Input(
                id="seed-input",
                type="number",
                step=1,
                value=DEFAULT_SEED,
                className="numeric-input",
                style=shared_style,
            ),
            html.Button("Generate paths", id="generate-button", n_clicks=0, className="generate-button"),
        ],
        className="control-panel",
    )
