# harder evaluation split + manual error analysis for the classification model
#
# model_classification.py evaluates on a random stratified split of all 3
# datasets mixed together - that's an easy test, since the model can lean on
# patterns from the same systems it trained on. a more honest test of
# generalisation is a held-out *dataset*: train only on HDFS + BGL, then test
# on OpenStack, a system the model has never seen a single row of. this is
# the kind of deliberately harder split the assignment asks for, rather than
# just reporting a single accuracy number on an easy random split
#
# same feature set and same random forest configuration as
# model_classification.py, so results are comparable

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

DATA_PATH = 'data/processed/unified_events.csv'
if not os.path.exists(DATA_PATH):
    DATA_PATH = 'data/processed/openstack_events.csv'

df = pd.read_csv(DATA_PATH, parse_dates=['timestamp'])
df = df.dropna(subset=['label'])
df['label'] = df['label'].astype(int)

TRAIN_SAMPLE_SIZE = 1_500_000  # keep memory bounded, same reasoning as model_classification.py

train_df = df[df['dataset'].isin(['hdfs', 'bgl'])] if 'dataset' in df.columns else df
test_df = df[df['dataset'] == 'openstack'] if 'dataset' in df.columns else df.sample(frac=0.2, random_state=42)

if 'dataset' not in df.columns:
    print('unified_events.csv not found - falling back to a random split on openstack_events.csv alone, '
          'so this is NOT the held-out-dataset test described in the report, just a placeholder run')

if len(train_df) > TRAIN_SAMPLE_SIZE:
    train_df, _ = train_test_split(
        train_df, train_size=TRAIN_SAMPLE_SIZE, stratify=train_df['label'], random_state=42
    )

for part in (train_df, test_df):
    part.sort_values(['instance_id', 'timestamp'], inplace=True)
    part['seconds_since_prev_event'] = (
        part.groupby('instance_id')['timestamp'].diff().dt.total_seconds().fillna(0)
    )
    part['hour_of_day'] = part['timestamp'].dt.hour
    part['prev_event_id'] = part.groupby('instance_id')['event_id'].shift(1).fillna('NONE')
    part['avg_gap_last_3'] = (
        part.groupby('instance_id')['seconds_since_prev_event']
            .rolling(window=3, min_periods=1).mean()
            .reset_index(level=0, drop=True)
    )
    # rows with no resolvable instance_id are dropped entirely by groupby before rolling,
    # then come back as NaN on reassignment - fillna has to run after alignment
    part['avg_gap_last_3'] = part['avg_gap_last_3'].fillna(0)

FEATURES = [
    'severity', 'component', 'event_id', 'hour_of_day',
    'seconds_since_prev_event', 'prev_event_id', 'avg_gap_last_3',
]
X_train, y_train = train_df[FEATURES], train_df['label']
X_test, y_test = test_df[FEATURES], test_df['label']

preprocess = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['component', 'event_id', 'prev_event_id']),
], remainder='passthrough')

clf = RandomForestClassifier(n_estimators=200, max_depth=20, class_weight='balanced', random_state=42, n_jobs=4)
pipe = Pipeline([('prep', preprocess), ('clf', clf)])
pipe.fit(X_train, y_train)
preds = pipe.predict(X_test)

print(f'trained on {len(train_df):,} rows (HDFS+BGL only), tested on {len(test_df):,} rows (OpenStack only)')
print(classification_report(y_test, preds, digits=3, zero_division=0))
print('confusion matrix:\n', confusion_matrix(y_test, preds))

# manual error analysis: pull out a handful of false positives and false negatives
# and look at what they actually are, not just how many there are
test_df = test_df.copy()
test_df['pred'] = preds
false_positives = test_df[(test_df['label'] == 0) & (test_df['pred'] == 1)]
false_negatives = test_df[(test_df['label'] == 1) & (test_df['pred'] == 0)]

cols = ['timestamp', 'component', 'severity', 'event_id', 'event_template', 'seconds_since_prev_event']

print(f'\n--- {len(false_positives)} false positives, 5 examples ---')
print(false_positives[cols].head(5).to_string(index=False))
print('\nmost common event_id among false positives:')
print(false_positives['event_id'].value_counts().head(5))

print(f'\n--- {len(false_negatives)} false negatives, 5 examples ---')
print(false_negatives[cols].head(5).to_string(index=False))
print('\nmost common event_id among false negatives:')
print(false_negatives['event_id'].value_counts().head(5))
