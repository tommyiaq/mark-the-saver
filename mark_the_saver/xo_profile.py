from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html

from .config import MEDIAN_COLOR, PERCENTILE_LOW_COLOR, XO_SECTION_COPY, XO_SECTION_TITLE
from .mitigation_analysis import XOProfile

COMBINED_COLOR = "#edf5f9"


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _bin_figure(labels: tuple[str, ...], values: np.ndarray, shares: np.ndarray, color: str) -> go.Figure:
    figure = go.Figure(
        go.Bar(
            x=list(labels),
            y=[v * 100.0 for v in values],
            marker_color=color,
            marker_line_width=0,
            customdata=shares * 100.0,
            hovertemplate="%{x}<br>mean return %{y:.1f}%<br>%{customdata:.0f}% of months<extra></extra>",
        )
    )
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=34, r=10, t=8, b=24),
        height=170,
        bargap=0.35,
    )
    figure.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(size=10))
    figure.update_yaxes(ticksuffix="%", gridcolor="rgba(255,255,255,0.08)", zeroline=True, zerolinecolor="rgba(255,255,255,0.25)", title_standoff=4)
    return figure


def _summary_box(label: str, value: str, *, muted: bool = False) -> html.Div:
    classes = ["xo-summary-box"]
    if muted:
        classes.append("xo-summary-box--muted")
    return html.Div(
        [
            html.Div(label, className="xo-summary-label"),
            html.Div(value, className="xo-summary-value"),
        ],
        className=" ".join(classes),
    )


def _top_summary(caption: str, arithmetic: float, geometric: float) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    _summary_box("Arithm Avg", _percent(arithmetic)),
                    _summary_box("Geom Avg", _percent(geometric)),
                ],
                className="xo-summary-grid",
            ),
            html.Div(caption, className="xo-summary-caption"),
        ],
        className="xo-summary-stack",
    )


def _combined_summary(arithmetic: float, geometric: float, cost: float, net: float, caption: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    _summary_box("Arithm Avg", _percent(arithmetic)),
                    _summary_box("Geom Avg", _percent(geometric)),
                ],
                className="xo-summary-grid",
            ),
            html.Div(caption, className="xo-summary-caption xo-summary-caption--tight"),
            html.Div(
                [
                    _summary_box("Cost", _percent(cost)),
                    _summary_box("Net", _percent(net)),
                ],
                className="xo-summary-grid",
            ),
        ],
        className="xo-summary-stack",
    )


def _row(label: str, figure: go.Figure, summary: html.Div, *, combined: bool = False) -> html.Div:
    label_class = "xo-row-label xo-row-label--combined" if combined else "xo-row-label"
    return html.Div(
        [
            html.Div(label, className=label_class),
            dcc.Graph(figure=figure, config={"displayModeBar": False}, className="xo-row-figure"),
            summary,
        ],
        className="xo-row",
    )


def build_xo_body(profile: XOProfile) -> list[html.Div]:
    stats = profile.stats
    pair = stats.pair
    labels = profile.bin_labels
    shares = profile.bin_shares
    weight_pct = round(stats.weight * 100.0)

    combined_caption = f"{weight_pct}% {pair.strategy_label} / {100 - weight_pct}% {pair.base_label}"

    return [
        _row(
            "Base asset",
            _bin_figure(labels, profile.base_bin_means, shares, MEDIAN_COLOR),
            _top_summary(pair.base_label, stats.base_arithmetic, stats.base_geometric),
        ),
        _row(
            "Risk mitigation",
            _bin_figure(labels, profile.haven_bin_means, shares, PERCENTILE_LOW_COLOR),
            _top_summary(pair.strategy_label, stats.haven_arithmetic, stats.haven_geometric),
        ),
        _row(
            "Combined",
            _bin_figure(labels, profile.combined_bin_means, shares, COMBINED_COLOR),
            _combined_summary(stats.combined_arithmetic, stats.combined_geometric, stats.cost, stats.net_effect, combined_caption),
            combined=True,
        ),
    ]


def build_xo_panel() -> html.Div:
    """Static shell; the three payoff rows are filled by the panel callback."""
    return html.Div(
        className="xo-panel",
        children=[
            html.Div(
                [
                    html.Div(XO_SECTION_TITLE, className="xo-eyebrow"),
                    html.H2("Payoff profile, by market bin", className="xo-title"),
                    html.P(XO_SECTION_COPY, className="xo-copy"),
                ],
                className="xo-header",
            ),
            html.Div(id="xo-body"),
        ],
    )
