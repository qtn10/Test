# clustering model: looks for structure within the anomaly class alone
#
# per the assignment spec, clustering must run within a single class and must
# not use the label column as a feature - so this clusters only the rows
# already labelled anomalous (label == 1), with label excluded from the
# feature matrix. every resulting cluster is therefore 100% anomalous by
# construction; that composition is reported below purely as a sanity check
# that no normal rows leaked in, not as a finding. the actual question each
# cluster answers is "what distinguishes this group of anomalies from the
# others", not "is this group anomalous"
#
# same feature set as model_classification.py (severity, component, event_id,
# hour_of_day, seconds_since_prev_event) so both models describe events the
# same way and results are comparable

import os
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import silhouette_score

DATA_PATH = 'data/processed/unified_events.csv'
if not os.path.exists(DATA_PATH):
    DATA_PATH = 'data/processed/openstack_events.csv'

df = pd.read_csv(DATA_PATH, parse_dates=['timestamp'])
df = df.dropna(subset=['label'])
df['label'] = df['label'].astype(int)

anomalies = df[df['label'] == 1].copy()
anomalies = anomalies.sort_values(['instance_id', 'timestamp'])
anomalies['seconds_since_prev_event'] = (
    anomalies.groupby('instance_id')['timestamp'].diff().dt.total_seconds().fillna(0)
)
anomalies['hour_of_day'] = anomalies['timestamp'].dt.hour

FEATURES = ['severity', 'component', 'event_id', 'hour_of_day', 'seconds_since_prev_event']
X_raw = anomalies[FEATURES]

preprocess = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['component', 'event_id']),
], remainder='passthrough')
X = preprocess.fit_transform(X_raw)

# pick k by silhouette score over a small candidate range instead of guessing blindly
# silhouette_score is O(n^2) on the full data, so it's computed on a capped random
# sample rather than every anomaly row once the anomaly class gets large
SILHOUETTE_SAMPLE = 5000
sample_size = min(SILHOUETTE_SAMPLE, X.shape[0])

best_k, best_score = 2, -1
max_k = min(6, len(anomalies) - 1)
for k in range(2, max_k + 1):
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)
    score = silhouette_score(X, labels, sample_size=sample_size, random_state=42)
    if score > best_score:
        best_k, best_score = k, score

print(f'chosen k={best_k} (silhouette={best_score:.3f})')
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
anomalies['cluster'] = kmeans.fit_predict(X)

print('\nlabel composition per cluster (sanity check - should all be label 1):')
print(anomalies.groupby('cluster')['label'].value_counts())

numeric_cols = ['severity', 'hour_of_day', 'seconds_since_prev_event']
overall_avg = anomalies[numeric_cols].mean()
print('\noverall anomaly-class averages:\n', overall_avg)

for cluster_id, group in anomalies.groupby('cluster'):
    print(f'\n--- cluster {cluster_id} (n={len(group)}) ---')
    diff = (group[numeric_cols].mean() - overall_avg).sort_values(key=abs, ascending=False)
    print('feature differences from the overall anomaly average:\n', diff)
    print('most common component:', group['component'].mode().iat[0])
    print('most common event_id:', group['event_id'].mode().iat[0])
    print('example rows:')
    print(group[['timestamp', 'component', 'event_id', 'event_template']].head(3).to_string(index=False))
