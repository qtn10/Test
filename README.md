# COS30049-Project

Project for Session 10 Group 7's Log Anomaly Detection Project.

Datasets used: HDFS_v1, BGL, OpenStack (all via Loghub / Zenodo record 8196385).

## Structure

```
data/
  BGL/, HDFS_v1/, OpenStack/   raw logs + Loghub-provided preprocessed files
  processed/                   output of src/processing/ scripts (per-dataset + unified events)
src/
  processing/                  parses each dataset's raw logs into a shared schema, then unifies them
  models/                      classification + clustering models trained on the unified data
```

## Setup

This project uses [mise](https://mise.jdx.dev/) to pin Python 3.14 and manage a `.venv`. From the repo root:

```
mise install
.venv/bin/pip install -r requirements.txt
```

## Running the pipeline

Raw `HDFS.log` and `BGL.log` are too large for git — download `HDFS_v1.zip` / `BGL.zip` from https://zenodo.org/records/8196385 and place the `.log` files at `data/HDFS_v1/HDFS.log` / `data/BGL/BGL.log`. OpenStack's raw logs are already in the repo.

All commands run from the repo root (scripts reference `data/...` relative to the current directory, not their own location):

```
.venv/bin/python src/processing/openstack_combiner.py    # merges the 3 OpenStack log files
.venv/bin/python src/processing/openstack_processor.py   # Drain-parses OpenStack -> data/processed/openstack_events.csv
.venv/bin/python src/processing/hdfs_transformed.py       # -> data/processed/hdfs_events.csv
.venv/bin/python src/processing/bgl_transformed.py        # -> data/processed/bgl_events.csv
.venv/bin/python src/processing/final_transformer.py      # unifies all 3 -> data/processed/unified_events.csv

.venv/bin/python src/models/model_classification.py       # trains + evaluates classification models
.venv/bin/python src/models/model_clustering.py           # clusters the anomaly class, describes each cluster
```
