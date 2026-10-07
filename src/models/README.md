# src/models/

All scripts read `data/processed/unified_events.csv` (falling back to `openstack_events.csv` alone if the unified file doesn't exist yet).

- `model_classification.py` — trains logistic regression + random forest to predict the `label` column; reports precision/recall/F1 (not raw accuracy, since anomalies are a small minority of rows). Also writes `data/processed/training_sample.csv`, the actual sampled, feature-engineered data the models train on — this is what belongs in the submission zip, not the full unified dataset.
- `model_clustering.py` — clusters only the anomaly rows (label excluded from the features), picks k by silhouette score, then describes each cluster by how its feature averages differ from the anomaly-wide average.
- `model_isolation_forest.py` — an unsupervised classifier (not taught in the unit) on the identical train/test split as `model_classification.py`, for a like-for-like comparison against the supervised baseline.
- `model_gradient_boosting.py` — a second non-taught classifier (`HistGradientBoostingClassifier`), structurally different from random forest (boosting vs. bagging). Uses frequency-bucketed categorical encoding instead of one-hot, since its native categorical support caps at 255 categories per feature.
- `error_analysis.py` — a deliberately harder evaluation: trains on HDFS+BGL only, tests on OpenStack (a fully held-out dataset), then prints example false positives/negatives for manual inspection.
