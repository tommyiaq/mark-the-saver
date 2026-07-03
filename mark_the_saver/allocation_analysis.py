from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html

from .config import (
    ALLOCATION_SECTION_COPY,
    ALLOCATION_SECTION_TITLE,
    MEDIAN_COLOR,
    PERCENTILE_LOW_COLOR,
)
from .mitigation_analysis import AllocationCurve


# Log-scale bounds for the ending-wealth axis (multiples of starting capital).
_Y_LOG_RANGE = (-2.5, 2.0)


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _signed_percent(value: float) -> str:
    return f"{value * 100:+.2f}%"


def _multiple(value: float) -> str:
    return f"{value:.2f}×"


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


def _interp(curve: AllocationCurve, weight: float, values: np.ndarray) -> float:
    return float(np.interp(weight, curve.weights, values))


def build_allocation_figure(curve: AllocationCurve, slider_weight: float) -> go.Figure:
    weights_pct = curve.weights * 100.0
    cap_x = curve.mitigation_cap * 100.0
    kelly_x = curve.kelly.weight * 100.0
    frac_x = curve.fractional.weight * 100.0
    slider_x = slider_weight * 100.0
    slider_p5 = _interp(curve, slider_weight, curve.p5_wealth)
    y_low, y_high = (10.0 ** _Y_LOG_RANGE[0], 10.0 ** _Y_LOG_RANGE[1])

    figure = go.Figure()

    # Region excluded by the cap: mitigation above 50% of the portfolio.
    figure.add_shape(
        type="rect",
        x0=cap_x,
        x1=100,
        y0=y_low,
        y1=y_high,
        fillcolor="rgba(255, 255, 255, 0.045)",
        line_width=0,
        layer="below",
    )
    figure.add_shape(type="line", x0=cap_x, x1=cap_x, y0=y_low, y1=y_high, line=dict(color="rgba(255,255,255,0.35)", width=1.5, dash="dash"))
    # Break-even (starting wealth) reference.
    figure.add_shape(type="line", x0=0, x1=100, y0=1.0, y1=1.0, line=dict(color="rgba(255,255,255,0.18)", width=1, dash="dot"))
    # Current slider position.
    figure.add_shape(type="line", x0=slider_x, x1=slider_x, y0=y_low, y1=y_high, line=dict(color="rgba(247,201,72,0.55)", width=2))

    figure.add_trace(
        go.Scatter(
            x=weights_pct,
            y=curve.median_wealth,
            mode="lines",
            name="Median",
            line=dict(color=MEDIAN_COLOR, width=3),
            hovertemplate="Mitigation %{x:.0f}%<br>Median %{y:.2f}×<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=weights_pct,
            y=curve.p5_wealth,
            mode="lines",
            name="5th percentile",
            line=dict(color=PERCENTILE_LOW_COLOR, width=2.5),
            hovertemplate="Mitigation %{x:.0f}%<br>5th pct %{y:.3f}×<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[frac_x],
            y=[curve.fractional.p5_wealth],
            mode="markers",
            showlegend=False,
            marker=dict(symbol="circle-open", size=12, color=PERCENTILE_LOW_COLOR, line=dict(width=2)),
            hovertemplate="Unconstrained 5th-pct max<br>Mitigation %{x:.1f}%<br>5th pct %{y:.3f}×<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[kelly_x],
            y=[curve.kelly.median_wealth],
            mode="markers",
            showlegend=False,
            marker=dict(symbol="circle-open", size=12, color=MEDIAN_COLOR, line=dict(width=2)),
            hovertemplate="Kelly point (median max)<br>Mitigation %{x:.1f}%<br>Median %{y:.2f}×<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[slider_x],
            y=[slider_p5],
            mode="markers",
            showlegend=False,
            marker=dict(symbol="circle", size=15, color=MEDIAN_COLOR, line=dict(color="#081018", width=2)),
            hovertemplate="Slider allocation<br>Mitigation %{x:.1f}%<br>5th pct %{y:.3f}×<extra></extra>",
        )
    )

    figure.add_annotation(x=(cap_x + 100.0) / 2.0, y=0.97, yref="paper", text=f"mitigation > {cap_x:.0f}% cap", showarrow=False, font=dict(size=11, color="rgba(237,245,249,0.55)"))
    figure.add_annotation(x=frac_x, y=curve.fractional.p5_wealth, text=f"5th-pct max {frac_x:.1f}%", showarrow=False, yshift=16, font=dict(size=11, color=PERCENTILE_LOW_COLOR))
    figure.add_annotation(x=kelly_x, y=curve.kelly.median_wealth, text=f"Kelly {kelly_x:.0f}%", showarrow=False, yshift=16, font=dict(size=11, color=MEDIAN_COLOR))
    figure.add_annotation(x=slider_x, y=0.03, yref="paper", text=f"slider {slider_x:.1f}%", showarrow=False, xanchor="left", xshift=4, font=dict(size=12, color="#edf5f9"))

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=18, r=18, t=14, b=40),
        height=420,
        xaxis_title=f"Allocation to {curve.pair.strategy_label} (rest in {curve.pair.base_label})",
        yaxis_title=f"Ending wealth after {curve.throws} draws (× start, log)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0, font=dict(size=11)),
    )
    figure.update_xaxes(
        range=[0, 100],
        ticksuffix="%",
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
    )
    figure.update_yaxes(
        type="log",
        range=list(_Y_LOG_RANGE),
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
    )
    return figure


def _optimum_card(title: str, chips: list[html.Div], footer: str, modifier: str) -> html.Div:
    return html.Div(
        [
            html.Div(title, className="plane-card-title"),
            html.Div(chips, className="plane-card-chip-grid"),
            html.Div(footer, className="plane-card-footer"),
        ],
        className=f"plane-card {modifier}",
    )


def build_allocation_cards(curve: AllocationCurve, slider_weight: float) -> list[html.Div]:
    selected = curve.selected
    kelly = curve.kelly
    cap_pct = f"{curve.mitigation_cap * 100:.0f}%"

    slider_median = _interp(curve, slider_weight, curve.median_wealth)
    slider_p5 = _interp(curve, slider_weight, curve.p5_wealth)
    slider_median_cagr = _interp(curve, slider_weight, curve.median_cagr)
    slider_p5_cagr = _interp(curve, slider_weight, curve.p5_cagr)

    return [
        _optimum_card(
            "Slider allocation (drives the panels below)",
            [
                _summary_box("Mitigation", _percent(slider_weight)),
                _summary_box("Median wealth", _multiple(slider_median)),
                _summary_box("5th-pct wealth", _multiple(slider_p5)),
                _summary_box("Median CAGR", _signed_percent(slider_median_cagr)),
                _summary_box("5th-pct CAGR", _signed_percent(slider_p5_cagr)),
            ],
            "Move the slider in the controls to explore other allocations.",
            "plane-card--blend",
        ),
        _optimum_card(
            "5th-pct optimum within cap (slider default)",
            [
                _summary_box("Mitigation", _percent(selected.weight)),
                _summary_box("5th-pct wealth", _multiple(selected.p5_wealth)),
            ],
            f"Best worst-case path with mitigation capped at {cap_pct}.",
            "plane-card--cash",
        ),
        _optimum_card(
            "Kelly point (median max)",
            [
                _summary_box("Mitigation", _percent(kelly.weight)),
                _summary_box("Median wealth", _multiple(kelly.median_wealth)),
            ],
            "Maximizes the median path (accuracy), unconstrained by the cap.",
            "plane-card--baseline",
        ),
    ]


def build_allocation_analysis() -> html.Div:
    """Static shell; the figure and cards are filled by the panel callback."""
    return html.Div(
        className="alloc-panel",
        children=[
            html.Div(
                [
                    html.Div("Allocation analysis", className="alloc-eyebrow"),
                    html.H2(ALLOCATION_SECTION_TITLE, className="plane-title"),
                    html.P(ALLOCATION_SECTION_COPY, className="plane-copy"),
                ],
                className="plane-header",
            ),
            html.Div(
                [
                    html.Div(dcc.Graph(id="allocation-graph", config={"displayModeBar": False}), className="plane-graph"),
                    html.Div(id="allocation-cards", className="plane-summary-stack"),
                ],
                className="plane-grid",
            ),
        ],
    )
