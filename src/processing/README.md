# src/processing/

Run in this order:

1. `openstack_combiner.py` — merges the 3 raw OpenStack log files into one, so Drain learns one consistent set of templates.
2. `openstack_processor.py` — Drain-parses the combined log, extracts VM instance IDs, labels against `anomaly_labels.txt` -> `data/processed/openstack_events.csv`.
3. `hdfs_transformed.py` — re-parses raw `HDFS.log` line-by-line against Loghub's pre-supplied event templates -> `data/processed/hdfs_events.csv`.
4. `bgl_transformed.py` — same idea as HDFS, adapted for BGL's larger/overlapping template set and inline per-line labels -> `data/processed/bgl_events.csv`.
5. `final_transformer.py` — stacks the 3 outputs above into one unified CSV with a `dataset` column -> `data/processed/unified_events.csv`.
