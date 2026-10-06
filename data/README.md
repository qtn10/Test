# data/

Raw and processed log data for all 3 datasets.

- `BGL/`, `HDFS_v1/` — raw logs (gitignored, too large for git) + Loghub-provided preprocessed files. See each folder's own README for dataset citation.
- `OpenStack/` — raw logs (checked into git, small enough) + Drain parser output.
- `processed/` — output of the `src/processing/` scripts: one CSV per dataset plus the unified cross-dataset CSV used for modelling.
