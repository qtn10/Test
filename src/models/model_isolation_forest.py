# isolation forest: a second classifier, not covered in this unit, chosen
# specifically because it's purpose-built for anomaly detection rather than a
# general-purpose classifier repurposed for it (Liu, Ting & Zhou 2008)
#
# why it suits this problem: random forest/logistic regression (model_classification.py)
# are supervised - they need the label column and learn "what does an anomaly look
# like" from examples of both classes. isolation forest is unsupervised: it isolates
# points by repeatedly splitting on random features/thresholds, and anomalies are
# the points that take fewer splits to isolate because they sit in sparse regions
# of the feature space. this matters for log anomaly detection specifically because
# real-world deployments often have far fewer labelled anomalies than this project's
# 636k - isolation forest doesn't need labels to fit at all, only a rough estimate
# of what fraction of the data is anomalous (the contamination rate), which is a
# much weaker requirement than needing a labelled example of every anomaly type
#
# comparison: same train/test split, same features, same preprocessing as
# model_classification.py's random forest, so the numbers are directly comparable

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, confusion_matrix

DATA_PATH = 'data/processed/unified_events.csv'
if not os.path.exists(DATA_PATH):
    DATA_PATH = 'data/processed/openstack_events.csv'

df = pd.read_csv(DATA_PATH, parse_dates=['timestamp'])
df = df.dropna(subset=['label'])
df['label'] = df['label'].astype(int)

SAMPLE_SIZE = 2_000_000  # same cap and same random_state as model_classification.py, for a like-for-like split
if len(df) > SAMPLE_SIZE:
    df, _ = train_test_split(df, train_size=SAMPLE_SIZE, stratify=df['label'], random_state=42)

df = df.sort_values(['instance_id', 'timestamp'])
df['seconds_since_prev_event'] = (
    df.groupby('instance_id')['timestamp'].diff().dt.total_seconds().fillna(0)
)
df['hour_of_day'] = df['timestamp'].dt.hour
df['prev_event_id'] = df.groupby('instance_id')['event_id'].shift(1).fillna('NONE')
df['avg_gap_last_3'] = (
    df.groupby('instance_id')['seconds_since_prev_event']
      .rolling(window=3, min_periods=1).mean()
      .reset_index(level=0, drop=True)
)
# rows with no resolvable instance_id are dropped entirely by groupby before rolling,
# then come back as NaN on reassignment - fillna has to run after alignment
df['avg_gap_last_3'] = df['avg_gap_last_3'].fillna(0)

FEATURES = [
    'severity', 'component', 'event_id', 'hour_of_day',
    'seconds_since_prev_event', 'prev_event_id', 'avg_gap_last_3',
]
X = df[FEATURES]
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

preprocess = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['component', 'event_id', 'prev_event_id']),
], remainder='passthrough')

X_train_enc = preprocess.fit_transform(X_train)
X_test_enc = preprocess.transform(X_test)

contamination = y_train.mean()  # the known historical anomaly rate - calibrates the decision threshold only,
                                 # the tree-building itself never sees y_train
clf = IsolationForest(n_estimators=200, contamination=contamination, random_state=42, n_jobs=4)
clf.fit(X_train_enc)

raw_preds = clf.predict(X_test_enc)  # -1 = anomaly, 1 = normal
preds = (raw_preds == -1).astype(int)

print(f'isolation forest (unsupervised, contamination={contamination:.4f})')
print(classification_report(y_test, preds, digits=3, zero_division=0))
print('confusion matrix:\n', confusion_matrix(y_test, preds))
