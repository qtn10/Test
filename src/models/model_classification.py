# classification model: predicts whether a log line's instance is anomalous
#
# the labelled data is severely imbalanced (e.g. ~112 anomalous lines out of
# ~57,700 labelled lines in openstack_events.csv alone), so accuracy alone
# would be meaningless - precision/recall/F1 and a stratified train/test split
# are used instead, and class_weight='balanced' compensates both models for
# the imbalance during training
#
# features chosen and what each is meant to capture:
#   severity                  - already numeric (0-3), direct signal of message severity
#   component                 - one-hot, which service/log the line came from
#   event_id                  - one-hot, which log template fired; this is the core
#                                structural feature used in log anomaly detection
#                                literature (e.g. DeepLog treats the event ID sequence
#                                as its primary input)
#   hour_of_day                - time-of-day pattern; ops incidents often cluster
#                                around maintenance windows or peak load
#   seconds_since_prev_event   - time gap since this instance's previous log line;
#                                unusually long stalls or bursts of activity are a
#                                known anomaly signal in distributed system logs
#
# two models are trained and compared: logistic regression as an interpretable
# baseline, random forest as the stronger non-linear model

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

DATA_PATH = 'data/processed/unified_events.csv'
if not os.path.exists(DATA_PATH):
    DATA_PATH = 'data/processed/openstack_events.csv'  # fallback while hdfs/bgl csvs aren't generated on this machine

df = pd.read_csv(DATA_PATH, parse_dates=['timestamp'])
df = df.dropna(subset=['label'])  # lines with no resolvable instance_id have unknown label, can't train on them
df['label'] = df['label'].astype(int)

# this machine has 14GB RAM - one-hot encoding ~700+ event_id categories across the
# full 16M rows, then training a parallel random forest on top of that, swaps hard and
# grinds to a halt. a stratified subsample keeps the class balance while fitting
# comfortably in memory; 2M rows is still far more than enough data for a baseline model
SAMPLE_SIZE = 2_000_000
if len(df) > SAMPLE_SIZE:
    df, _ = train_test_split(df, train_size=SAMPLE_SIZE, stratify=df['label'], random_state=42)

df = df.sort_values(['instance_id', 'timestamp'])
df['seconds_since_prev_event'] = (
    df.groupby('instance_id')['timestamp'].diff().dt.total_seconds().fillna(0)
)
df['hour_of_day'] = df['timestamp'].dt.hour

FEATURES = ['severity', 'component', 'event_id', 'hour_of_day', 'seconds_since_prev_event']
X = df[FEATURES]
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

preprocess = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['component', 'event_id']),
], remainder='passthrough')

models = {
    # liblinear converges faster than the lbfgs default on large sparse binary problems
    'logistic_regression': LogisticRegression(max_iter=1000, class_weight='balanced', solver='liblinear'),
    # n_jobs capped at 4 rather than -1 (all 16 cores): each parallel worker holds its
    # own copy of the training data, so full parallelism multiplies memory use and
    # swaps on a 14GB machine instead of actually going faster. max_depth caps how big
    # any single tree can grow, which also caps memory per tree
    'random_forest': RandomForestClassifier(
        n_estimators=200, max_depth=20, class_weight='balanced', random_state=42, n_jobs=4
    ),
}

for name, clf in models.items():
    pipe = Pipeline([('prep', preprocess), ('clf', clf)])
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    print(f'--- {name} ---')
    print(classification_report(y_test, preds, digits=3, zero_division=0))
    print('confusion matrix:\n', confusion_matrix(y_test, preds))
