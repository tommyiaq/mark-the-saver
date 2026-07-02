from __future__ import annotations

from dash import html


def metric_card(label: str, value: str, note: str) -> html.Div:
    return html.Div(
        [
            html.Div(label, className="metric-label"),
            html.Div(value, className="metric-value"),
            html.Div(note, className="metric-note"),
        ],
        className="metric-card",
    )
