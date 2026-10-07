# gradient boosting: a second model not covered in this unit, chosen to be
# structurally different from both other comparison models rather than just
# "another tree ensemble" for its own sake
#
# random forest (model_classification.py) builds many trees independently in
# parallel and averages them (bagging) - each tree sees a bootstrap sample and
# they don't know about each other's mistakes. gradient boosting (Friedman 2001)
# builds trees sequentially, where each new tree is trained specifically to
# correct the errors of the ensemble built so far. this is a genuinely different
# mechanism, not just a bigger/smaller version of the same idea, and it's the
# technique behind XGBoost/LightGBM, which dominate tabular ML in practice -
# including log-anomaly-detection systems built on structured event features
# like the ones used throughout this project
#
# HistGradientBoostingClassifier specifically (rather than plain
# GradientBoostingClassifier) is used because it bins continuous features into
# histograms before training (the approach popularised by LightGBM - Ke et al.
# 2017), which is both much faster and far less memory-hungry on a dataset this
# size - a direct, practical answer to the memory constraints documented in
# model_classification.py and REPORT.md
#
# same features, same train/test split as model_classification.py's random
# forest, so results are directly comparable
#
# unlike the OneHotEncoder used for the other models, categorical columns here
# are ordinal-encoded (integer codes) and passed via categorical_features -
# HistGradientBoostingClassifier bins categories internally rather than needing
# one-hot expansion. this isn't just a memory workaround (though it is one -
# one-hot would blow 700+ event_id categories x 2M rows past this machine's RAM
# as a dense array, which this classifier requires) - it's the idiomatic way to
# use this specific algorithm, and highlights a genuine practical difference
# from the other models: it doesn't pay the same dimensionality cost they do

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

DATA_PATH = 'data/processed/unified_events.csv'
if not os.path.exists(DATA_PATH):
    DATA_PATH = 'data/processed/openstack_events.csv'

df = pd.read_csv(DATA_PATH, parse_dates=['timestamp'])
df = df.dropna(subset=['label'])
df['label'] = df['label'].astype(int)

SAMPLE_SIZE = 2_000_000  # same cap and random_state as model_classification.py, for a like-for-like split
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

# HistGradientBoostingClassifier's native categorical support caps cardinality at
# 255, but event_id (and prev_event_id, drawn from the same vocabulary) has 491+
# distinct values across the 3 datasets. keeping the 254 most frequent events (fit
# on the training split only) and bucketing the long tail into 'OTHER' is a
# standard way to fit a high-cardinality categorical into that limit without
# falling back to one-hot encoding's dimensionality blow-up
TOP_K = 254
top_events = X_train['event_id'].value_counts().head(TOP_K).index
X_train = X_train.copy()
X_test = X_test.copy()
for col in ('event_id', 'prev_event_id'):
    X_train[col] = X_train[col].where(X_train[col].isin(top_events), 'OTHER')
    X_test[col] = X_test[col].where(X_test[col].isin(top_events), 'OTHER')

CAT_COLS = ['component', 'event_id', 'prev_event_id']
preprocess = ColumnTransformer([
    ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), CAT_COLS),
], remainder='passthrough')
# after the ColumnTransformer, the 3 ordinal-encoded columns come first, then the
# numeric passthrough columns - categorical_features is given as a boolean mask
# in that resulting column order
categorical_mask = [True] * len(CAT_COLS) + [False] * (len(FEATURES) - len(CAT_COLS))

# class_weight isn't available on HistGradientBoostingClassifier, so sample_weight
# is used instead to give the same imbalance-compensation effect as the random
# forest/logistic regression models' class_weight='balanced'
pos_rate = y_train.mean()
sample_weight = y_train.map({0: pos_rate, 1: 1 - pos_rate})

clf = HistGradientBoostingClassifier(max_iter=200, random_state=42, categorical_features=categorical_mask)
pipe = Pipeline([('prep', preprocess), ('clf', clf)])
pipe.fit(X_train, y_train, clf__sample_weight=sample_weight)
preds = pipe.predict(X_test)

print('gradient boosting (HistGradientBoostingClassifier)')
print(classification_report(y_test, preds, digits=3, zero_division=0))
print('confusion matrix:\n', confusion_matrix(y_test, preds))
