# one-off script to generate the Data Analysis section's charts for REPORT.md
# not part of the modelling pipeline - run manually, writes PNGs to ../figures/
#
# colors: validated categorical palette (blue/orange/aqua - the first 3 slots of
# the reference palette, which clear colorblind-safety checks for all pairwise
# comparisons, not just adjacent ones) for the 3-dataset comparison; a single
# sequential blue for magnitude-only charts; red reserved for the anomaly/normal
# status split since that's a status distinction, not an arbitrary category

import pandas as pd
import matplotlib.pyplot as plt

BLUE, ORANGE, AQUA, RED = '#2a78d6', '#eb6834', '#1baf7a', '#e34948'
FIG_DIR = '../../figures/'  # code/COS30049-Project -> code -> assignment-023/figures

df = pd.read_csv('data/processed/unified_events.csv', parse_dates=['timestamp'])
labelled = df.dropna(subset=['label']).copy()
labelled['label'] = labelled['label'].astype(int)

plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})

# 1. anomaly rate by dataset
rates = labelled.groupby('dataset')['label'].mean().sort_values(ascending=False) * 100
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(rates.index, rates.values, color=[BLUE, ORANGE, AQUA], width=0.6)
ax.set_ylabel('Anomaly rate (%)')
ax.set_title('Anomaly rate by dataset')
for b, v in zip(bars, rates.values):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.1, f'{v:.2f}%', ha='center', va='bottom')
fig.tight_layout()
fig.savefig(FIG_DIR + 'anomaly_rate_by_dataset.png', dpi=150)
plt.close(fig)

# 2. anomaly rate by severity
sev_rates = labelled.groupby('severity')['label'].mean() * 100
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(sev_rates.index.astype(str), sev_rates.values, color=BLUE, width=0.6)
ax.set_xlabel('Severity level (0=INFO .. 3=FATAL-equivalent)')
ax.set_ylabel('Anomaly rate (%)')
ax.set_title('Anomaly rate by severity level')
for b, v in zip(bars, sev_rates.values):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f'{v:.1f}%', ha='center', va='bottom')
fig.tight_layout()
fig.savefig(FIG_DIR + 'anomaly_rate_by_severity.png', dpi=150)
plt.close(fig)

# 3. top event_ids among anomalies
top_events = labelled[labelled['label'] == 1]['event_id'].value_counts().head(8).sort_values()
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.barh(top_events.index, top_events.values, color=BLUE)
ax.set_xlabel('Anomalous row count')
ax.set_title('Most common event types among anomalies')
fig.tight_layout()
fig.savefig(FIG_DIR + 'top_anomalous_events.png', dpi=150)
plt.close(fig)

# 4. top components among anomalies
top_components = labelled[labelled['label'] == 1]['component'].value_counts().head(8).sort_values()
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.barh(top_components.index, top_components.values, color=BLUE)
ax.set_xlabel('Anomalous row count')
ax.set_title('Most common components among anomalies')
fig.tight_layout()
fig.savefig(FIG_DIR + 'top_anomalous_components.png', dpi=150)
plt.close(fig)

print('wrote 4 charts to', FIG_DIR)
