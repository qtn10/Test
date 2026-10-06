# src/

- `processing/` — turns the 3 raw datasets into one shared schema and unifies them.
- `models/` — trains/evaluates the classification, clustering, and comparison models on the unified data.
- `analysis_charts.py` — one-off script, generates the Data Analysis section's charts into `figures/` at the repo root.

Run everything from the repo root, not from inside `src/` — scripts reference `data/...`/`figures/` relative to the current working directory.
