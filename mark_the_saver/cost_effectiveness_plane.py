from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html

from .config import COST_PLANE_COPY, COST_PLANE_TITLE
from .kelly_analysis import build_kelly_profile_data


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _percent_points(value: float) -> str:
    return f"{value:.1f}%"


def _summary_box(label: str, value: str, *, muted: bool = False) -> html.Div:
    classes = ["plane-card-chip"]
    if muted:
        classes.append("plane-card-chip--muted")
    return html.Div(
        [
            html.Div(label, className="plane-card-chip-label"),
            html.Div(value, className="plane-card-chip-value"),
        ],
        className=" ".join(classes),
    )


def _build_plane_figure(cost: float, effect: float, blend_label: str) -> go.Figure:
    high = max(cost, effect) * 1.2
    high = max(2.5, round(high + 0.2, 1))
    ticks = [round(value, 1) for value in np.arange(0.0, high + 0.001, 0.5)]

    figure = go.Figure()
    figure.add_shape(type="rect", x0=0, y0=0, x1=high, y1=high, fillcolor="rgba(255,255,255,0.03)", line_width=0)
    figure.add_shape(
        type="line",
        x0=0,
        y0=0,
        x1=high,
        y1=high,
        line=dict(color="rgba(255,255,255,0.24)", width=2, dash="dot"),
    )
    figure.add_shape(type="line", x0=0, y0=0, x1=0, y1=high, line=dict(color="rgba(255,255,255,0.16)", width=1))
    figure.add_shape(type="line", x0=0, y0=0, x1=high, y1=0, line=dict(color="rgba(255,255,255,0.16)", width=1))
    figure.add_shape(type="line", x0=0, y0=0, x1=cost, y1=effect, line=dict(color="rgba(255,255,255,0.12)", width=1, dash="dash"))
    figure.add_shape(type="line", x0=0, y0=0, x1=cost, y1=0, line=dict(color="rgba(255,255,255,0.22)", width=2))
    figure.add_shape(type="line", x0=cost, y0=0, x1=cost, y1=effect, line=dict(color="rgba(255,255,255,0.22)", width=2))

    figure.add_trace(
        go.Scatter(
            x=[cost],
            y=[effect],
            mode="markers+text",
            text=[blend_label],
            textposition="top center",
            marker=dict(size=18, color="#edf5f9", symbol="circle", line=dict(color="#081018", width=1.5)),
            hovertemplate=f"{blend_label}<br>Cost: {_percent(cost)}<br>Effect: {_percent(effect)}<extra></extra>",
            showlegend=False,
        )
    )

    figure.add_annotation(x=high * 0.18, y=high * 0.86, text="dice baseline", showarrow=False, font=dict(size=11, color="rgba(237,245,249,0.8)"))
    figure.add_annotation(x=cost * 0.5, y=-0.08 * high, text="cost", showarrow=False, font=dict(size=11, color="rgba(237,245,249,0.8)"))
    figure.add_annotation(x=-0.05 * high, y=effect * 0.55, text="effect", showarrow=False, font=dict(size=11, color="rgba(237,245,249,0.8)"), textangle=-90)

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=18, r=18, t=12, b=22),
        height=360,
        xaxis_title="Arithmetic cost vs dice",
        yaxis_title="Geometric effect vs dice",
    )
    figure.update_xaxes(
        range=[0, high],
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
        tickmode="array",
        tickvals=ticks,
        ticktext=[_percent_points(value) for value in ticks],
    )
    figure.update_yaxes(
        range=[0, high],
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
        tickmode="array",
        tickvals=ticks,
        ticktext=[_percent_points(value) for value in ticks],
    )
    return figure


def build_cost_effectiveness_plane() -> html.Div:
    profile_data = build_kelly_profile_data()
    dice_arithmetic = round(profile_data.dice.arithmetic * 100.0, 1)
    dice_geometric = round(profile_data.dice.geometric * 100.0, 1)
    combined_arithmetic = round(profile_data.combined.arithmetic * 100.0, 1)
    combined_geometric = round(profile_data.combined.geometric * 100.0, 1)

    dice_pct = round(profile_data.dice_weight * 100.0)
    cash_pct = round(profile_data.cash_weight * 100.0)
    blend_label = f"{dice_pct}% dice / {cash_pct}% cash"

    cost = dice_arithmetic - combined_arithmetic
    effect = combined_geometric - dice_geometric
    figure = _build_plane_figure(cost, effect, blend_label)

    return html.Div(
        className="plane-panel",
        children=[
            html.Div(
                [
                    html.Div("Cost-effectiveness plane", className="plane-eyebrow"),
                    html.H2(COST_PLANE_TITLE, className="plane-title"),
                    html.P(COST_PLANE_COPY, className="plane-copy"),
                ],
                className="plane-header",
            ),
            html.Div(
                [
                    html.Div(dcc.Graph(figure=figure, config={"displayModeBar": False}), className="plane-graph"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div("Baseline: Dice", className="plane-card-title"),
                                    html.Div([_summary_box("Arithmetic", _percent_points(dice_arithmetic)), _summary_box("Geometric", _percent_points(dice_geometric), muted=True)], className="plane-card-chip-grid"),
                                    html.Div("Reference point", className="plane-card-footer"),
                                ],
                                className="plane-card plane-card--baseline",
                            ),
                            html.Div(
                                [
                                    html.Div(f"Strategy: {blend_label}", className="plane-card-title"),
                                    html.Div([_summary_box("Arithmetic", _percent_points(combined_arithmetic)), _summary_box("Geometric", _percent_points(combined_geometric))], className="plane-card-chip-grid"),
                                    html.Div("Risk-mitigated blend used for the plotted point", className="plane-card-footer"),
                                ],
                                className="plane-card plane-card--blend",
                            ),
                            html.Div(
                                [
                                    html.Div("Difference vs dice", className="plane-card-title"),
                                    html.Div([_summary_box("Cost", _percent_points(cost)), _summary_box("Effect", _percent_points(effect))], className="plane-card-chip-grid"),
                                    html.Div("Positive magnitudes relative to dice", className="plane-card-footer"),
                                ],
                                className="plane-card plane-card--cash",
                            ),
                        ],
                        className="plane-summary-stack",
                    ),
                ],
                className="plane-grid",
            ),
        ],
    )
