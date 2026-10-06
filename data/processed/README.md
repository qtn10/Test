# data/processed/

Output of `src/processing/`. All files share the schema `timestamp, component, severity, instance_id, event_id, event_template, label`.

- `hdfs_events.csv`, `bgl_events.csv`, `openstack_events.csv` — one file per dataset, one row per log line.
- `unified_events.csv` — the above 3 stacked together with an added `dataset` column, produced by `final_transformer.py`. This is what `src/models/` trains on.

Not checked into git (gitignored) — regenerate by running the scripts in `src/processing/` in order (see repo root README).
