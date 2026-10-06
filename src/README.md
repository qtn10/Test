# src/

- `processing/` — turns the 3 raw datasets into one shared schema and unifies them.
- `models/` — trains/evaluates the classification, clustering, and comparison models on the unified data.
- `analysis_charts.py` — one-off script, generates the Data Analysis section's charts into `../figures/` (one level above the repo root, alongside `REPORT.md`).

Run everything from the repo root, not from inside `src/` — scripts reference `data/...` (and `analysis_charts.py` references `../../figures/`) relative to the current working directory.
