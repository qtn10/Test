# Assignment 2 Progress Tracker — Log Anomaly Detection (Group 7)

**Internal team checklist only — not a submitted deliverable.** Maps current repo state to the assignment spec and rubric so the team can see what's done and what's left.

**Due: Sunday 11:59pm AEST, 07/10/2026 (Week 8)** — *last updated 2026-10-06.*

> ⚠️ Still very tight on time. Core pipeline + both required models now run end-to-end on the real, full dataset (16.1M rows across HDFS/BGL/OpenStack). Report, readme, analysis/visualizations, innovation items, meeting minutes, and contribution form are still outstanding.

---

## 1. Submission checklist (Section 4 of spec)

| Item | Format | Status |
|---|---|---|
| Report (≤4000 words) | PDF | 🟡 `REPORT.md` started — Data Collection & Data Processing sections written, rest marked TODO for team |
| Processed datasets | CSV/JSON in zip | 🟢 `data/processed/unified_events.csv` — real unified data, 16.1M rows, all 3 sources |
| Readme (how to run code) | PDF or MD | 🟢 `README.md` written (setup, structure, run order) — convert to PDF before submission |
| Source code + final model(s) | in zip | 🟢 Classification + clustering models exist and run on real data |
| Meeting Minutes | PDF | ❓ Unknown — need at least 1/week since team formation |
| Contribution Form | PDF | ❌ Not started — needs all members to discuss & sign together |

File naming reminder: submit as `session-xx-group-7-AssignmentName.pdf` etc. (per group name).

---

## 2. Rubric-mapped status

### Report criteria (12 pts)
| Criterion | Pts | Status |
|---|---|---|
| Data collection & processing explanation | 3 | 🟢 Written up in `REPORT.md` with real figures from the actual run |
| Data analysis explanation | 2 | ❌ No analysis/visualization write-up yet (anomaly rate, anomalies over time, severity vs label, etc.) |
| Model selection justification | 2 | 🟡 Models exist and run; the *why* (why random forest/logistic regression, why KMeans, alternatives considered) still needs writing in the report by the team |
| Writing quality & structure | 1 | 🟡 In progress |
| Harvard referencing | 1 | 🟢 Dataset citations in `REPORT.md` bibliography |
| Completeness (all sections) | 1 | ❌ Several sections still TODO for team (intro, problem framing, implementation, conclusion) |

### Source code execution (15 pts)
| Criterion | Pts | Status |
|---|---|---|
| Core functionality (data pipeline + both model types) | 7 | 🟢 **Both required model types now implemented and verified running on the real unified dataset.** Classification: logistic regression + random forest, precision/recall/F1 reported (label is ~4% positive after unification, less extreme than OpenStack alone at ~0.2%). Clustering: KMeans within the anomaly class only (label excluded from features), k picked by silhouette score, found a real distinction — a small cluster (5,205 rows) of rare high-severity BGL kernel panics after long idle gaps vs. a large cluster (631,617 rows) of frequent, tighter-interval anomalies. |
| Datasets (clean, relevant, correct format) | 3 | 🟢 `unified_events.csv` built from real raw logs (not samples), consistent schema, `dataset` column added |
| Readme | 1 | 🟢 Done, needs PDF/MD export check before submission |
| Code comments | 2 | 🟢 Strong — scripts are well-commented with column rationale |
| Code structure | 2 | 🟢 Reorganized into `src/processing/` + `src/models/`, duplicate root-level `BGL/`/`HDFS_v1/`/`OpenStack/` folders (405MB) + dead `openstack_transformed.py` staged for deletion (`git rm` already run, not yet committed). READMEs added in every folder. |

### Innovation (15 pts) — still the main gap
| Criterion | Pts | Status |
|---|---|---|
| Additional data + transformation | 4 | ❌ **Confirmed**: HDFS/BGL/OpenStack are all inside the one Zenodo base bundle (record 8196385) — doesn't count as "additional". Email tutor to confirm this reading; don't chase a 4th dataset unless they say otherwise. |
| Feature extraction research | 4 | 🟡 Current features (severity, component, event_id, hour_of_day, **seconds_since_prev_event**) go slightly beyond the raw schema — the time-gap feature is loosely justified by log-anomaly literature (DeepLog-style timing signals) but not yet written up with citations. Still room to add more (event-count windows per instance, sequence features). |
| Model beyond the unit | 4 | ❌ Only models taught in the unit so far (logistic regression, random forest, KMeans). Needs a non-taught model compared against baseline if time allows. |
| Evaluation design + error analysis | 3 | ❌ Current evaluation is a single stratified random split with precision/recall/F1 — no deliberately hard split (e.g. held-out dataset, held-out time period) and no manual false positive/negative inspection yet. |

---

## 3. What's actually built right now (verified 2026-10-06, after rerun)

- `src/processing/openstack_combiner.py`, `openstack_processor.py`, `hdfs_transformed.py`, `bgl_transformed.py` — all **run successfully end-to-end on the real raw logs** (downloaded HDFS_v1.zip/BGL.zip from Zenodo since the raw logs aren't in git). Produced `hdfs_events.csv` (11.17M rows), `bgl_events.csv` (4.75M rows), `openstack_events.csv` (207k rows).
- `src/processing/final_transformer.py` — **done**, stacks the 3 outputs into `data/processed/unified_events.csv` (16.1M rows, ~636k labelled anomalies, ~150k unknown-label OpenStack rows). No semantic template matching needed across datasets since event IDs are already namespaced (`HDFS_E#`, `BGL_E#`, `OS_E#`) and the systems don't share event meanings anyway.
- `src/models/model_classification.py` — **done and verified**, trains logistic regression + random forest, reports precision/recall/F1 (not accuracy, given the class imbalance).
- `src/models/model_clustering.py` — **done and verified**, clusters the anomaly class only, reports a real, describable 2-cluster split (see above).
- Repo reorganized: `src/processing/`, `src/models/`, READMEs in every folder, `mise.toml` + `requirements.txt` for environment setup, duplicate data folders removed (staged).

## 4. Immediate next steps (suggested order)

1. **Commit the current working tree** — cleanup (`git rm`), reorg (`git mv`), new scripts, new READMEs are all staged/untracked but not committed yet.
2. **Data analysis write-up** — anomaly rate, anomalies over time, common events, severity vs label, anomalies per component — turn the model outputs already produced into the report's Data Analysis section with a couple of charts.
3. **Write Model Selection + Implementation sections in `REPORT.md`** — the *why* behind the model choices, now that there's real output to describe.
4. **Harder evaluation + error analysis** (Innovation #4, 3 pts) — e.g. split by dataset (train on HDFS+BGL, test on OpenStack) or by time period, then manually inspect a handful of false positives/negatives.
5. **Second untaught model** (Innovation #3, 4 pts) if time allows — compare against the random forest baseline on the same test set.
6. **Readme, meeting minutes, contribution form** — finalize formats (PDF) for submission.

## 5. Open questions to raise with the team / tutor

- Train on each dataset individually or combined? (Already flagged — now moot in practice since `unified_events.csv` trains combined; worth confirming this was the intended answer.)
- Does unifying HDFS/BGL/OpenStack count as the "additional dataset" innovation point, or do we need a 4th source entirely? (Current read: no — see Innovation table above.)
- Confirm with tutor (per the assignment's AI-use allowance) what's acceptable for AI-assisted work on this repo, and keep a record of that confirmation.
