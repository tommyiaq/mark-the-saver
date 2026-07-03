from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from .config import COST_PLANE_COPY, COST_PLANE_TITLE
from .mitigation_analysis import BlendStats

COST_EFFECTIVE_COLOR = "#5bc0be"
REJECT_COLOR = "#e0655f"


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _signed_pct(value: float) -> str:
    return f"{value * 100:+.2f}%"


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


def build_plane_figure(stats: BlendStats) -> go.Figure:
    cost = stats.cost * 100.0
    effect = stats.geometric_effect * 100.0
    net = stats.net_effect
    cost_effective = net > 0.0

    points = [0.0, cost, effect]
    lo, hi = min(points), max(points)
    span = max(hi - lo, 0.5)
    pad = 0.28 * span
    rng = [lo - pad, hi + pad]

    figure = go.Figure()

    # Rejection region: below the y = x diagonal (net portfolio effect < 0).
    figure.add_trace(
        go.Scatter(
            x=[rng[0], rng[1], rng[1], rng[0]],
            y=[rng[0], rng[0], rng[1], rng[0]],
            fill="toself",
            fillcolor="rgba(224, 101, 95, 0.12)",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    # Baseline diagonal (100% base asset; net effect = 0).
    figure.add_shape(type="line", x0=rng[0], y0=rng[0], x1=rng[1], y1=rng[1], line=dict(color="rgba(255,255,255,0.45)", width=2, dash="dot"))
    # Axes through origin.
    figure.add_shape(type="line", x0=rng[0], y0=0, x1=rng[1], y1=0, line=dict(color="rgba(255,255,255,0.16)", width=1))
    figure.add_shape(type="line", x0=0, y0=rng[0], x1=0, y1=rng[1], line=dict(color="rgba(255,255,255,0.16)", width=1))
    # Net portfolio effect = vertical gap from the diagonal (cost, cost) up to the point (cost, effect).
    figure.add_shape(type="line", x0=cost, y0=cost, x1=cost, y1=effect, line=dict(color=(COST_EFFECTIVE_COLOR if cost_effective else REJECT_COLOR), width=2))

    # Baseline point: 100% base asset at the origin.
    figure.add_trace(
        go.Scatter(
            x=[0.0],
            y=[0.0],
            mode="markers",
            marker=dict(size=11, color="#edf5f9", symbol="circle-open", line=dict(width=2)),
            hovertemplate=f"100% {stats.pair.base_label}<br>baseline (net 0)<extra></extra>",
            showlegend=False,
        )
    )
    # The blend at the slider allocation.
    figure.add_trace(
        go.Scatter(
            x=[cost],
            y=[effect],
            mode="markers",
            marker=dict(size=17, color=(COST_EFFECTIVE_COLOR if cost_effective else REJECT_COLOR), symbol="circle", line=dict(color="#081018", width=1.5)),
            hovertemplate=(
                f"{round(stats.weight * 100)}% {stats.pair.strategy_label}<br>"
                f"arithmetic cost {_pct(stats.cost)}<br>"
                f"geometric effect {_pct(stats.geometric_effect)}<br>"
                f"net portfolio effect {_signed_pct(stats.net_effect)}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    verdict = "cost-effective" if cost_effective else "rejection region"
    verdict_color = COST_EFFECTIVE_COLOR if cost_effective else REJECT_COLOR
    figure.add_annotation(x=cost, y=effect, text=f"{verdict} ({_signed_pct(stats.net_effect)})", showarrow=False, yshift=18, font=dict(size=12, color=verdict_color))
    figure.add_annotation(x=rng[0] + 0.62 * span, y=rng[0] + 0.20 * span, text="rejection region", showarrow=False, font=dict(size=11, color="rgba(224,101,95,0.75)"))
    figure.add_annotation(x=rng[0] + 0.16 * span, y=rng[1] - 0.10 * span, text="baseline", showarrow=False, textangle=-45, font=dict(size=10, color="rgba(237,245,249,0.6)"))

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=18, r=18, t=14, b=40),
        height=420,
        xaxis_title="Arithmetic cost",
        yaxis_title="Geometric effect",
    )
    figure.update_xaxes(range=rng, ticksuffix="%", gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    figure.update_yaxes(range=rng, ticksuffix="%", gridcolor="rgba(255,255,255,0.08)", zeroline=False, scaleanchor="x", scaleratio=1)
    return figure


def build_plane_cards(stats: BlendStats) -> list[html.Div]:
    weight_pct = round(stats.weight * 100.0)
    verdict = "Cost-effective" if stats.net_effect > 0 else "Rejected (not cost-effective)"
    verdict_modifier = "plane-card--cash" if stats.net_effect > 0 else "plane-card--reject"

    return [
        html.Div(
            [
                html.Div(f"Baseline: 100% {stats.pair.base_label}", className="plane-card-title"),
                html.Div(
                    [
                        _summary_box("Arithmetic", _pct(stats.base_arithmetic)),
                        _summary_box("Geometric", _pct(stats.base_geometric)),
                    ],
                    className="plane-card-chip-grid",
                ),
                html.Div("The diagonal / reference point", className="plane-card-footer"),
            ],
            className="plane-card plane-card--baseline",
        ),
        html.Div(
            [
                html.Div(f"Blend: {weight_pct}% {stats.pair.strategy_label}", className="plane-card-title"),
                html.Div(
                    [
                        _summary_box("Arithmetic", _pct(stats.combined_arithmetic)),
                        _summary_box("Geometric", _pct(stats.combined_geometric)),
                    ],
                    className="plane-card-chip-grid",
                ),
                html.Div("Portfolio at the slider allocation", className="plane-card-footer"),
            ],
            className="plane-card plane-card--blend",
        ),
        html.Div(
            [
                html.Div(verdict, className="plane-card-title"),
                html.Div(
                    [
                        _summary_box("Arith. cost", _pct(stats.cost)),
                        _summary_box("Geom. effect", _pct(stats.geometric_effect)),
                        _summary_box("Net effect", _signed_pct(stats.net_effect)),
                    ],
                    className="plane-card-chip-grid",
                ),
                html.Div("Net effect = geometric effect − arithmetic cost", className="plane-card-footer"),
            ],
            className=f"plane-card {verdict_modifier}",
        ),
    ]


def build_cost_effectiveness_plane() -> html.Div:
    """Static shell; the figure and cards are filled by the panel callback."""
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
                    html.Div(dcc.Graph(id="plane-graph-fig", config={"displayModeBar": False}), className="plane-graph"),
                    html.Div(id="plane-cards", className="plane-summary-stack"),
                ],
                className="plane-grid",
            ),
        ],
    )
