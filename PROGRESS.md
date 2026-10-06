# Assignment 2 Progress Tracker — Log Anomaly Detection (Group 7)

**Internal team checklist only — not a submitted deliverable.** Maps current repo state to the assignment spec and rubric so the team can see what's done and what's left.

**Due: 11:59pm AEST, 07/10/2026** — *last updated 2026-10-06 ~21:45 AEDT (note: deadline is stated in AEST but we're currently on AEDT/daylight time, 1hr ahead — don't cut it to the literal last minute on your local clock).*

> All 4 rubric-graded pieces of code work are done with real results: core pipeline, both required models, the error-analysis/held-out evaluation, and a non-taught model (Isolation Forest) — plus 2 extra engineered features (`prev_event_id`, `avg_gap_last_3`) that measurably improved the random forest (F1 0.613→0.666). Report has real content for everything except the team-owned sections. **Not yet committed/pushed** — this latest round (feature additions, re-run results) is still sitting locally, see §4 item 7. **Everything after that is either team-only writing (Introduction, Problem Framing, Conclusion, cover info) or non-coding deliverables (readme PDF export, meeting minutes, contribution form)** — there isn't much more I can usefully do solo from here.

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
| Data analysis explanation | 2 | 🟢 Done — `REPORT.md` §5, 4 charts in `../figures/` (anomaly rate by dataset, by severity, top anomalous events/components), all generated from the real unified dataset |
| Model selection justification | 2 | 🟢 Written up in `REPORT.md` §5 — why RF over LR (non-linear feature interactions), why KMeans restricted to the anomaly class, with real comparison numbers |
| Writing quality & structure | 1 | 🟡 Finished sections read cleanly; still has visible TODO markers for team-owned sections |
| Harvard referencing | 1 | 🟢 Dataset + method citations (Loghub, DeepLog, Drain) in `REPORT.md` bibliography |
| Completeness (all sections) | 1 | 🟡 Data Collection/Processing/Model Selection/Implementation done; Intro, Problem Framing, Data Analysis, Conclusion, cover info still TODO (team-owned — motivation/reflection isn't something to fill in for them) |

### Source code execution (15 pts)
| Criterion | Pts | Status |
|---|---|---|
| Core functionality (data pipeline + both model types) | 7 | 🟢 **Both required model types implemented, verified, and committed, with real results.** Classification: RF beats LR on the anomaly class (F1 0.666 vs 0.361, precision 0.700 vs 0.265, recall 0.635 vs 0.566) on a stratified 2M-row sample (full 16M rows exceeded this machine's RAM — justified compute trade-off, written up in §7.1). Clustering: KMeans within the anomaly class only, k=2 by silhouette (0.981) — a small cluster (5,205 rows) of rare high-severity BGL kernel panics after ~47-day gaps vs. a large cluster (631,617 rows) of frequent, near-average-severity anomalies. |
| Datasets (clean, relevant, correct format) | 3 | 🟢 `unified_events.csv` (1.9GB, gitignored) is the full build; `model_classification.py` now also writes `data/processed/training_sample.csv` — the actual 2M-row stratified sample the final model trains/evaluates on, with engineered features included. That's the file that belongs in the submission zip's dataset folder, not the full dump. |
| Readme | 1 | 🟢 Done, needs PDF/MD export check before submission |
| Code comments | 2 | 🟢 Strong — scripts are well-commented with column rationale |
| Code structure | 2 | 🟢 Reorganized into `src/processing/` + `src/models/`, duplicate root-level `BGL/`/`HDFS_v1/`/`OpenStack/` folders (405MB) + dead `openstack_transformed.py` staged for deletion (`git rm` already run, not yet committed). READMEs added in every folder. |

### Innovation (15 pts) — still the main gap
| Criterion | Pts | Status |
|---|---|---|
| Additional data + transformation | 4 | ❌ **Confirmed**: HDFS/BGL/OpenStack are all inside the one Zenodo base bundle (record 8196385) — doesn't count as "additional". Email tutor to confirm this reading; don't chase a 4th dataset unless they say otherwise. |
| Feature extraction research | 4 | 🟢 **Done.** 4 engineered features beyond the raw schema (`hour_of_day`, `seconds_since_prev_event`, `prev_event_id`, `avg_gap_last_3`), each justified against DeepLog's sequence/timing approach in `REPORT.md` §4. Not just theoretical — adding the last two measurably improved random forest F1 from 0.613 to 0.666 on the same test set, real evidence the features capture structure rather than noise. |
| Model beyond the unit | 4 | 🟢 **Done.** Isolation Forest (`src/models/model_isolation_forest.py`) added and compared against the random forest baseline on the identical train/test split — F1 0.026 vs 0.666. The gap is explained, not hand-waved: Isolation Forest is unsupervised (no labels during training) so it's a structurally harder task, and interestingly it got *worse* (not better) with the extra features that helped random forest — a real, explained finding about high-dimensional categorical data diluting its random splits. Written up in `REPORT.md` §6 + §7.2. |
| Evaluation design + error analysis | 3 | 🟢 **Done.** `src/models/error_analysis.py` trains on HDFS+BGL only, tests on the fully held-out OpenStack dataset — anomaly precision/recall/F1 all drop to 0.000 (model predicts zero anomalies), vs. 0.998 accuracy, a clear illustration of why accuracy is misleading here. Manual inspection of the false negatives explains why: `component`/`event_id` are dataset-specific one-hot categories with zero vocabulary overlap across systems, so the model has no usable signal left for an unseen system. Written up in `REPORT.md` §6.2. |

---

## 3. What's actually built right now (verified 2026-10-06, after rerun)

- `src/processing/openstack_combiner.py`, `openstack_processor.py`, `hdfs_transformed.py`, `bgl_transformed.py` — all **run successfully end-to-end on the real raw logs** (downloaded HDFS_v1.zip/BGL.zip from Zenodo since the raw logs aren't in git). Produced `hdfs_events.csv` (11.17M rows), `bgl_events.csv` (4.75M rows), `openstack_events.csv` (207k rows).
- `src/processing/final_transformer.py` — **done**, stacks the 3 outputs into `data/processed/unified_events.csv` (16.1M rows, ~636k labelled anomalies, ~150k unknown-label OpenStack rows). No semantic template matching needed across datasets since event IDs are already namespaced (`HDFS_E#`, `BGL_E#`, `OS_E#`) and the systems don't share event meanings anyway.
- `src/models/model_classification.py` — **done and verified**, trains logistic regression + random forest, reports precision/recall/F1 (not accuracy, given the class imbalance).
- `src/models/model_clustering.py` — **done and verified**, clusters the anomaly class only, reports a real, describable 2-cluster split (see above).
- `src/models/error_analysis.py` — **done and verified**, held-out-dataset evaluation (train HDFS+BGL, test OpenStack) + manual false positive/negative inspection.
- `src/models/model_isolation_forest.py` — **done and verified**, unsupervised comparison model, same split/features as the random forest.
- `src/analysis_charts.py` — **done**, generates the 4 Data Analysis charts into `../figures/`.
- Repo reorganized: `src/processing/`, `src/models/`, READMEs in every folder, `mise.toml` + `requirements.txt` for environment setup, duplicate data folders removed (committed and pushed).

## 4. Immediate next steps (suggested order)

1. ~~Commit the current working tree~~ — done and pushed (`origin/main`).
2. ~~Write Model Selection + Implementation sections in `REPORT.md`~~ — done, with real numbers.
3. ~~Decide what goes in the submission zip's dataset folder~~ — done, `training_sample.csv`.
4. ~~Harder evaluation + error analysis~~ (Innovation #4, 3 pts) — done, see §7.2 in `REPORT.md`.
5. ~~Data analysis write-up~~ — done, see §5 + `../figures/` in `REPORT.md`.
6. ~~Second untaught model~~ (Innovation #3, 4 pts) — done, Isolation Forest, see §6 + §7.2 in `REPORT.md`.
7. **Commit + push these latest changes** (error analysis, isolation forest, charts, report updates) — not yet done, see below.
8. **Team-owned writing** — Introduction, Problem Framing, Conclusion, cover info in `REPORT.md`. This is genuinely the main thing left.
9. **Readme, meeting minutes, contribution form** — finalize formats (PDF) for submission.

## 5. Open questions to raise with the team / tutor

- Train on each dataset individually or combined? (Already flagged — now moot in practice since `unified_events.csv` trains combined; worth confirming this was the intended answer.)
- Does unifying HDFS/BGL/OpenStack count as the "additional dataset" innovation point, or do we need a 4th source entirely? (Current read: no — see Innovation table above.)
- Confirm with tutor (per the assignment's AI-use allowance) what's acceptable for AI-assisted work on this repo, and keep a record of that confirmation.
