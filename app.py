from __future__ import annotations

import dash

from mark_the_saver.callbacks import register_callbacks
from mark_the_saver.layout import build_layout


app = dash.Dash(__name__, title="Die Path Dashboard")
server = app.server
app.layout = build_layout()
register_callbacks(app)


if __name__ == "__main__":
    app.run(debug=True)