from __future__ import annotations

from dash import dcc, html

from .config import DEFAULT_PATHS, DEFAULT_SAMPLE_PATHS, DEFAULT_SEED, DEFAULT_THROWS


def build_control_panel() -> html.Div:
    shared_style = {
        "backgroundColor": "#050d14",
        "color": "#ffffff",
        "border": "1px solid rgba(255,255,255,0.32)",
    }

    return html.Div(
        [
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
