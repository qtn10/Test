# src/models/

Both scripts read `data/processed/unified_events.csv` (falling back to `openstack_events.csv` alone if the unified file doesn't exist yet).

- `model_classification.py` — trains logistic regression + random forest to predict the `label` column; reports precision/recall/F1 (not raw accuracy, since anomalies are a small minority of rows).
- `model_clustering.py` — clusters only the anomaly rows (label excluded from the features), picks k by silhouette score, then describes each cluster by how its feature averages differ from the anomaly-wide average.
