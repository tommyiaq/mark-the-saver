from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from .config import (
    MEDIAN_COLOR,
    PATH_LINE_COLOR,
    PATH_LINE_WIDTH,
    PERCENTILE_HIGH_COLOR,
    PERCENTILE_LOW_COLOR,
    REALIZED_PATH_COLOR,
)
from .models import SimulationResult


def make_path_figure(
    result: SimulationResult,
    throws: int,
    sample_paths: int,
    realized_wealth: np.ndarray | None = None,
) -> go.Figure:
    path_count = result.wealth_paths.shape[0]
    sample_count = min(sample_paths, path_count)
    sample_indices = np.linspace(0, path_count - 1, sample_count, dtype=int)
    x_axis = np.arange(0, throws + 1)

    path_figure = go.Figure()
    for index in sample_indices:
        path_figure.add_trace(
            go.Scatter(
                x=x_axis,
                y=result.wealth_paths[index],
                mode="lines",
                line=dict(color=PATH_LINE_COLOR, width=PATH_LINE_WIDTH),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    quantiles = np.quantile(result.wealth_paths, [0.05, 0.5, 0.95], axis=0)
    path_figure.add_trace(
        go.Scatter(
            x=x_axis,
            y=quantiles[2],
            mode="lines",
            line=dict(color=PERCENTILE_HIGH_COLOR, width=2, dash="dot"),
            hoverinfo="skip",
            showlegend=True,
            name="95th percentile",
        )
    )
    path_figure.add_trace(
        go.Scatter(
            x=x_axis,
            y=quantiles[0],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(91, 192, 190, 0.18)",
            line=dict(color=PERCENTILE_LOW_COLOR, width=2.5),
            hoverinfo="skip",
            showlegend=True,
            name="5th percentile",
        )
    )
    path_figure.add_trace(
        go.Scatter(
            x=x_axis,
            y=quantiles[1],
            mode="lines",
            line=dict(color=MEDIAN_COLOR, width=3),
            name="Median path",
        )
    )
    if realized_wealth is not None:
        path_figure.add_trace(
            go.Scatter(
                x=np.arange(0, len(realized_wealth)),
                y=realized_wealth,
                mode="lines",
                line=dict(color=REALIZED_PATH_COLOR, width=3.5),
                name="Realized path (actual)",
                hovertemplate="Draw %{x}<br>Wealth %{y:.2f}×<extra>Realized</extra>",
            )
        )
    path_figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=30, b=40),
        height=520,
        xaxis_title="Draw number (months); starting wealth = 1 unit at t=0",
        yaxis_title="Wealth multiple",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis_type="log",
    )
    path_figure.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    path_figure.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    return path_figure


def make_histogram_figure(final_wealth: np.ndarray, realized_final: float | None = None) -> go.Figure:
    median = float(np.median(final_wealth))
    p05, p95 = np.percentile(final_wealth, [5, 95])
    histogram = go.Figure()
    histogram.add_trace(
        go.Histogram(
            x=final_wealth,
            nbinsx=45,
            marker=dict(color="#5bc0be"),
            opacity=0.9,
        )
    )
    histogram.add_vrect(x0=p05, x1=p95, fillcolor="rgba(91, 192, 190, 0.12)", line_width=0)
    histogram.add_vline(x=median, line_width=3, line_color="#f7c948", line_dash="dash")
    if realized_final is not None:
        histogram.add_vline(x=realized_final, line_width=3, line_color=REALIZED_PATH_COLOR)
        histogram.add_annotation(x=realized_final, yref="paper", y=1.0, text="realized", showarrow=False, yshift=-2, xshift=2, xanchor="left", font=dict(size=11, color=REALIZED_PATH_COLOR))
    histogram.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=30, b=40),
        height=420,
        xaxis_title="Final wealth multiple",
        yaxis_title="Path count",
        yaxis_type="log",
    )
    histogram.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    histogram.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    return histogram
