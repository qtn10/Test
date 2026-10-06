# src/

- `processing/` — turns the 3 raw datasets into one shared schema and unifies them.
- `models/` — trains/evaluates the classification and clustering models on the unified data.

Run everything from the repo root, not from inside `src/` — scripts reference `data/...` relative to the current working directory.
