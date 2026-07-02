# Mark the Saver

Dash dashboard for simulating 300 throws across 10,000 Monte Carlo paths with the payoff rule:

- Roll `1`: `-50%`
- Roll `2-5`: `+5%`
- Roll `6`: `+50%`

Each path starts with `1` unit of capital, and the main visualization focuses on median wealth with the `5th` and `95th` percentile bounds.

## Run

Use the project virtual environment and start the app from the repository root:

```powershell
t:/venv/Scripts/python.exe app.py
```

Then open the local Dash server URL printed in the terminal.

## Project Structure

The code is split so each module has one job:

- `app.py` - thin entrypoint that creates the Dash app and registers callbacks
- `mark_the_saver/config.py` - constants and shared configuration
- `mark_the_saver/models.py` - shared data models
- `mark_the_saver/simulation.py` - Monte Carlo die simulation and wealth compounding
- `mark_the_saver/analytics.py` - summary metrics for median and percentile reporting
- `mark_the_saver/figures.py` - Plotly figure construction
- `mark_the_saver/controls.py` - control panel widgets
- `mark_the_saver/layout.py` - overall page layout
- `mark_the_saver/kelly_profile.py` - Kelly criterion Xs and Os panel
- `mark_the_saver/metrics.py` - metric card rendering
- `mark_the_saver/callbacks.py` - Dash callback registration and dashboard updates
- `assets/styles.css` - visual styling

## Safe Haven Framing

The dashboard is intentionally aligned with the safe-haven / compounding lens used in the project conversation:

- Look at the realized path, not just the average.
- Prioritize median outcome and downside bounds over mean wealth.
- Keep the simulation mechanics explicit so the payoff shape is easy to inspect and modify.

The Kelly criterion is the first chart-level idea to keep in view when reading the book's path-dependent argument: the question is not just whether a bet has positive arithmetic edge, but whether it improves long-run geometric growth on the realized path.

The lower Kelly panel now mirrors the book's Xs and Os profile with the investing row, the cash row, and the combined 40% dice / 60% cash row.

That makes the project easier to use as a reference when exploring path dependence, compounding, and downside protection.
