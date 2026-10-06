# final transformer to bring the 3 processed datasets together
#
# event_id is already namespaced per dataset (HDFS_E#, BGL_E#, OS_E#), so there
# is no shared event vocabulary to reconcile - HDFS, BGL and OpenStack are
# different systems with unrelated event meanings. instead this just stacks
# the 3 already-unified-schema csvs into one table and tags each row with
# which dataset it came from, so models can train on all 3 or filter to one

import pandas as pd

INPUTS = {
    'hdfs': 'data/processed/hdfs_events.csv',
    'bgl': 'data/processed/bgl_events.csv',
    'openstack': 'data/processed/openstack_events.csv',
}

OUT_PATH = 'data/processed/unified_events.csv'

frames = []
for dataset, path in INPUTS.items():
    df = pd.read_csv(path)
    df['dataset'] = dataset
    frames.append(df)

unified = pd.concat(frames, ignore_index=True)
unified = unified[['dataset', 'timestamp', 'component', 'severity', 'instance_id', 'event_id', 'event_template', 'label']]
unified.to_csv(OUT_PATH, index=False)

print(f'wrote {len(unified)} rows to {OUT_PATH}')
print(unified['dataset'].value_counts())
print(unified['label'].value_counts(dropna=False))
