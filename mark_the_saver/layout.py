from __future__ import annotations

from dash import dcc, html

from .config import HERO_COPY, TITLE_TEXT
from .controls import build_control_panel
from .kelly_profile import build_kelly_profile


def build_layout() -> html.Div:
    return html.Div(
        className="page-shell",
        children=[
            html.Div(
                className="hero-panel",
                children=[
                    html.Div(
                        [
                            html.Div("Dice Path Laboratory", className="eyebrow"),
                            html.H1(TITLE_TEXT, className="hero-title"),
                            html.P(HERO_COPY, className="hero-copy"),
                        ],
                        className="hero-copy-block",
                    ),
                    build_control_panel(),
                ],
            ),
            dcc.Loading(
                className="loading-wrap",
                children=[
                    html.Div(id="metrics-row", className="metrics-row"),
                    html.Div(
                        className="chart-grid",
                        children=[
                            html.Div(dcc.Graph(id="paths-graph", config={"displayModeBar": False}), className="chart-card"),
                            html.Div(dcc.Graph(id="histogram-graph", config={"displayModeBar": False}), className="chart-card"),
                        ],
                    ),
                ],
                type="default",
            ),
            build_kelly_profile(),
        ],
    )
