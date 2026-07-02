from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html

from .config import KELLY_SECTION_COPY, KELLY_SECTION_TITLE
from .kelly_analysis import build_kelly_profile_data


OUTCOME_LABELS = ("-50%", "+5%", "+50%")
DICE_MARKER = "x"
CASH_MARKER = "circle-open"
COMBINED_MARKER = "circle-x"


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _percent_points(value: float) -> str:
    return f"{value:.1f}%"


def _build_profile_figure(title: str, returns_pct: np.ndarray, marker_symbol: str, y_range: tuple[float, float], y_ticks: list[float]) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[0, 1, 2],
            y=returns_pct,
            mode="lines+markers",
            line=dict(color="rgba(225, 225, 225, 0.7)", width=2, dash="dot"),
            marker=dict(symbol=marker_symbol, size=14, color="#edf5f9", line=dict(color="#edf5f9", width=2)),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=28, r=14, t=12, b=30),
        height=180,
        title=dict(text=title, x=0.02, xanchor="left", y=0.98, font=dict(size=15)),
    )
    figure.update_xaxes(
        tickmode="array",
        tickvals=[0, 1, 2],
        ticktext=OUTCOME_LABELS,
        showgrid=False,
        zeroline=False,
    )
    figure.update_yaxes(
        range=list(y_range),
        tickmode="array",
        tickvals=y_ticks,
        ticktext=[_percent_points(value) for value in y_ticks],
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
        title_standoff=4,
    )
    return figure


def _summary_box(label: str, value: str, *, muted: bool = False) -> html.Div:
    classes = ["kelly-summary-box"]
    if muted:
        classes.append("kelly-summary-box--muted")
    return html.Div(
        [
            html.Div(label, className="kelly-summary-label"),
            html.Div(value, className="kelly-summary-value"),
        ],
        className=" ".join(classes),
    )


def _top_summary(title: str, arithmetic: float, geometric: float | None) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    _summary_box("Arithm Avg", _percent(arithmetic)),
                    _summary_box("Geom Avg", _percent(geometric) if geometric is not None else "", muted=geometric is None),
                ],
                className="kelly-summary-grid",
            ),
            html.Div(title, className="kelly-summary-caption"),
        ],
        className="kelly-summary-stack",
    )


def _combined_summary(arithmetic: float, geometric: float, delta_arithmetic: float, delta_geometric: float) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    _summary_box("Arithm Avg", _percent(arithmetic)),
                    _summary_box("Geom Avg", _percent(geometric)),
                ],
                className="kelly-summary-grid",
            ),
            html.Div("40% bet / 60% cash vs Dice Roll", className="kelly-summary-caption kelly-summary-caption--tight"),
            html.Div(
                [
                    _summary_box("Cost", _percent(delta_arithmetic)),
                    _summary_box("Net", _percent(delta_geometric)),
                ],
                className="kelly-summary-grid",
            ),
        ],
        className="kelly-summary-stack",
    )


def build_kelly_profile() -> html.Div:
    kelly_data = build_kelly_profile_data()

    dice_arithmetic = round(kelly_data.dice.arithmetic * 100.0, 1)
    dice_geometric = round(kelly_data.dice.geometric * 100.0, 1)
    combined_arithmetic = round(kelly_data.combined.arithmetic * 100.0, 1)
    combined_geometric = round(kelly_data.combined.geometric * 100.0, 1)

    delta_arithmetic = combined_arithmetic - dice_arithmetic
    delta_geometric = combined_geometric - dice_geometric

    return html.Div(
        className="kelly-panel",
        children=[
            html.Div(
                [
                    html.Div(KELLY_SECTION_TITLE, className="kelly-eyebrow"),
                    html.H2("Kelly blend, path by path", className="kelly-title"),
                    html.P(KELLY_SECTION_COPY, className="kelly-copy"),
                ],
                className="kelly-header",
            ),
            html.Div(
                [
                    html.Div("Investing", className="kelly-row-label"),
                    dcc.Graph(
                        figure=_build_profile_figure(
                            "", kelly_data.dice.returns_pct, DICE_MARKER, (-60, 60), [-50, 0, 50]
                        ),
                        config={"displayModeBar": False},
                        className="kelly-row-figure",
                    ),
                    _top_summary("Dice roll distribution", kelly_data.dice.arithmetic, kelly_data.dice.geometric),
                ],
                className="kelly-row",
            ),
            html.Div(
                [
                    html.Div("Risk Mitigation", className="kelly-row-label"),
                    dcc.Graph(
                        figure=_build_profile_figure(
                            "", kelly_data.cash.returns_pct, CASH_MARKER, (-20, 20), [-20, -10, 0, 10, 20]
                        ),
                        config={"displayModeBar": False},
                        className="kelly-row-figure",
                    ),
                    _top_summary("Risk mitigation", kelly_data.cash.arithmetic, None),
                ],
                className="kelly-row",
            ),
            html.Div(
                [
                    html.Div("Combined", className="kelly-row-label kelly-row-label--combined"),
                    dcc.Graph(
                        figure=_build_profile_figure(
                            "", kelly_data.combined.returns_pct, COMBINED_MARKER, (-50, 60), [-50, 0, 50]
                        ),
                        config={"displayModeBar": False},
                        className="kelly-row-figure",
                    ),
                    _combined_summary(kelly_data.combined.arithmetic, kelly_data.combined.geometric, delta_arithmetic / 100.0, delta_geometric / 100.0),
                ],
                className="kelly-row",
            ),
        ],
    )
