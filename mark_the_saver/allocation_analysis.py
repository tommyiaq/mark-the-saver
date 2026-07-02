from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html

from .config import (
    ALLOCATION_SECTION_COPY,
    ALLOCATION_SECTION_TITLE,
    MEDIAN_COLOR,
    PERCENTILE_LOW_COLOR,
)
from .kelly_analysis import AllocationCurve, build_allocation_curve


# Log-scale bounds for the ending-wealth axis (multiples of starting capital).
_Y_LOG_RANGE = (-2.5, 1.0)


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


def _build_curve_figure(curve: AllocationCurve) -> go.Figure:
    weights_pct = curve.weights * 100.0
    cap_x = (1.0 - curve.mitigation_cap) * 100.0
    kelly_x = curve.kelly.weight * 100.0
    frac_x = curve.fractional.weight * 100.0
    sel_x = curve.selected.weight * 100.0
    y_low, y_high = (10.0 ** _Y_LOG_RANGE[0], 10.0 ** _Y_LOG_RANGE[1])

    figure = go.Figure()

    # Region excluded by the cap: mitigation (cash) above 50% of the portfolio.
    figure.add_shape(
        type="rect",
        x0=0,
        x1=cap_x,
        y0=y_low,
        y1=y_high,
        fillcolor="rgba(255, 255, 255, 0.045)",
        line_width=0,
        layer="below",
    )
    figure.add_shape(type="line", x0=cap_x, x1=cap_x, y0=y_low, y1=y_high, line=dict(color="rgba(255,255,255,0.35)", width=1.5, dash="dash"))
    # Break-even (starting wealth) reference.
    figure.add_shape(type="line", x0=0, x1=100, y0=1.0, y1=1.0, line=dict(color="rgba(255,255,255,0.18)", width=1, dash="dot"))

    figure.add_trace(
        go.Scatter(
            x=weights_pct,
            y=curve.median_wealth,
            mode="lines",
            name="Median",
            line=dict(color=MEDIAN_COLOR, width=3),
            hovertemplate="Stake %{x:.0f}%<br>Median %{y:.2f}×<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=weights_pct,
            y=curve.p5_wealth,
            mode="lines",
            name="5th percentile",
            line=dict(color=PERCENTILE_LOW_COLOR, width=2.5),
            hovertemplate="Stake %{x:.0f}%<br>5th pct %{y:.3f}×<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[frac_x],
            y=[curve.fractional.p5_wealth],
            mode="markers",
            showlegend=False,
            marker=dict(symbol="circle-open", size=12, color=PERCENTILE_LOW_COLOR, line=dict(width=2)),
            hovertemplate="Unconstrained 5th-pct max<br>Stake %{x:.1f}% (cash 93.5% > cap)<br>5th pct %{y:.3f}×<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[kelly_x],
            y=[curve.kelly.median_wealth],
            mode="markers",
            showlegend=False,
            marker=dict(symbol="circle-open", size=12, color=MEDIAN_COLOR, line=dict(width=2)),
            hovertemplate="Kelly (median max)<br>Stake %{x:.1f}% (cash 62% > cap)<br>Median %{y:.2f}×<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[sel_x],
            y=[curve.selected.p5_wealth],
            mode="markers",
            showlegend=False,
            marker=dict(symbol="circle", size=15, color=PERCENTILE_LOW_COLOR, line=dict(color="#081018", width=2)),
            hovertemplate="Selected: 5th-pct max within cap<br>Stake %{x:.0f}% / cash %{customdata:.0f}%<br>5th pct %{y:.3f}×<extra></extra>",
            customdata=[100.0 - sel_x],
        )
    )

    figure.add_annotation(x=cap_x / 2.0, y=0.97, yref="paper", text="cash > 50% cap", showarrow=False, font=dict(size=11, color="rgba(237,245,249,0.55)"))
    figure.add_annotation(x=frac_x, y=curve.fractional.p5_wealth, text=f"5th-pct max {frac_x:.1f}%", showarrow=False, yshift=16, font=dict(size=11, color=PERCENTILE_LOW_COLOR))
    figure.add_annotation(x=kelly_x, y=curve.kelly.median_wealth, text=f"Kelly {kelly_x:.0f}%", showarrow=False, yshift=16, font=dict(size=11, color=MEDIAN_COLOR))
    figure.add_annotation(x=sel_x, y=curve.selected.p5_wealth, text=f"selected {sel_x:.0f}%", showarrow=False, yshift=-18, font=dict(size=12, color="#edf5f9"))

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=18, r=18, t=14, b=40),
        height=420,
        xaxis_title="Stake on the dice bet (rest in cash)",
        yaxis_title=f"Ending wealth after {curve.throws} rolls (× start, log)",
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


def build_allocation_analysis() -> html.Div:
    curve = build_allocation_curve()
    selected = curve.selected
    fractional = curve.fractional
    kelly = curve.kelly

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
                    html.Div(dcc.Graph(figure=_build_curve_figure(curve), config={"displayModeBar": False}), className="plane-graph"),
                    html.Div(
                        [
                            _optimum_card(
                                "Selected: 5th-pct max within cap",
                                [
                                    _summary_box("Dice stake", _percent(selected.weight)),
                                    _summary_box("5th-pct wealth", _multiple(selected.p5_wealth)),
                                    _summary_box("Median wealth", _multiple(selected.median_wealth)),
                                    _summary_box("Median CAGR", _signed_percent(selected.median_cagr)),
                                ],
                                "Best 5th percentile with cash capped at 50%; this stake feeds the panels below.",
                                "plane-card--cash",
                            ),
                            _optimum_card(
                                "Unconstrained 5th-pct max",
                                [
                                    _summary_box("Dice stake", _percent(fractional.weight)),
                                    _summary_box("5th-pct wealth", _multiple(fractional.p5_wealth)),
                                ],
                                "Would hold 93.5% cash - above the 50% mitigation cap, so it is excluded.",
                                "plane-card--baseline",
                            ),
                            _optimum_card(
                                "Kelly (median max)",
                                [
                                    _summary_box("Dice stake", _percent(kelly.weight)),
                                    _summary_box("Median wealth", _multiple(kelly.median_wealth)),
                                ],
                                "Maximizes the median path, but its 62% cash also exceeds the cap.",
                                "plane-card--blend",
                            ),
                        ],
                        className="plane-summary-stack",
                    ),
                ],
                className="plane-grid",
            ),
        ],
    )
