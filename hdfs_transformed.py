# data transformation program for hdfs_v1.log file
# 
# program intends to bring common columns and headers from the HDFS csv files into a new dataframe format
# when done it will produce a csv whose columns names and meanings match openstack_events.csv
# that is suitable to fit across all 3 processed datasets (HDFS, BGL and OpenStack)
# 
# i chose to use the log file from the start despite being provided
# with csv files because i felt that the event data can be combined
# and timestamps could have patterns that will be useful for 
# clustering accuracy in later stages of the model's creation
#
# chosen columns and reasoning:
#   timestamp       - needed to track time ranges and comparing anomalies over time
#   component       - hdfs bgl and openstack have it (component field in raw log of hdfs and bgl, service in openstack)
#   severity        - log severity as 0-3 (INFO, WARN, ERROR, FATAL)
#   instance_id     - the HDFS block ID
#   event_id        - HDFS_E# for each distinct event_template
#   event_template  - the message template with its variable parts masked out (including IPs and file paths)
#   label           - 1 if the block is 'Anomaly' in anomaly_label.csv, else 0
# 
# 
# dataset: 
# HDFS_v1
# + Wei Xu, Ling Huang, Armando Fox, David Patterson, Michael Jordan.
# [Detecting Large-Scale System Problems by Mining Console Logs](https://people.eecs.berkeley.edu/~jordan/papers/xu-etal-sosp09.pdf),
# in Proc. of the 22nd ACM Symposium on Operating Systems Principles (SOSP), 2009.
# + Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu.
# [Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics](https://arxiv.org/abs/2008.06448).
# IEEE International Symposium on Software Reliability Engineering (ISSRE), 2023.

# import libraries
import pandas as pd
import re

HDFS_DIR = 'data/HDFS_v1/'
HDFS_PP = 'preprocessed/'
LOG_PATH = HDFS_DIR + 'HDFS.log'
TRACES = HDFS_DIR + HDFS_PP + 'Event_traces.csv'
TEMPLATES = HDFS_DIR + HDFS_PP + 'HDFS.log_templates.csv'
LABELS = HDFS_DIR + HDFS_PP + 'anomaly_label.csv'
MATRIX = HDFS_DIR + HDFS_PP + 'Event_occurrence_matrix.csv'

# output path for final product
OUT_PATH   = 'data/processed/hdfs_events.csv'

BLOCK_ID   = r'blk_-?\d+'
SEVERITY_MAP = {'INFO': 0, 'WARN': 1, 'ERROR': 2, 'FATAL': 3}

labels = pd.read_csv(LABELS)
labels['label'] = (labels['Label'] == 'Anomaly').astype(int) # convert anomaly=1 normal=0
block_labels = dict(zip(labels['BlockId'], labels['label']))

LINE_PATTERN = re.compile(r'^(\d{6}) (\d{6}) (\d+) (\w+) ([^:]+): (.*)$') # regex for each line in HDFS.log

# previous test runs had problems with using regex to translate the template
# as the template has [*] inside, which is a indicator in regex
# must first change [*] for each template and then compile it 
def template_to_regex(template):
    pieces = template.split('[*]')
    escaped = [re.escape(p) for p in pieces]
    return re.compile('.*'.join(escaped))

#test = template_to_regex('[*]Receiving block[*]src:[*]dest:[*]')
#print(test.pattern)

# match object contains all details needed for analysis, fill it into rows
rows = []

with open(LOG_PATH, 'r') as log:
    for i, line in enumerate(log):
        line = line.strip() # remove new line issue
        match = LINE_PATTERN.match(line)
        if match:
            rows.append(match.groups())

df = pd.DataFrame(rows, columns=['date', 'time', 'pid', 'level', 'component', 'content'])

df['timestamp'] = df['date'] + ' ' + df['time']
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%y%m%d %H%M%S')

df['severity'] = df['level'].map(SEVERITY_MAP)
# print(df.head())

# pull out the block id into instance_id
df['instance_id'] = df['content'].str.extract('(' + BLOCK_ID + ')', expand=False)
# print(df[['content', 'instance_id']].head())

df['label'] = df['instance_id'].map(block_labels)
# print(df.head())

# mapping the E#
templates = pd.read_csv(TEMPLATES)
event_patterns = []
for event_id, template in zip(templates['EventId'], templates['EventTemplate']):
    event_patterns.append((event_id, template_to_regex(template)))

# if this pattern (defined regex pattern) is in event_patterns,
# return the event_id - that is the event_id for the event_template
# if no event found then it will be empty (None)
def find_event(content):
    for event_id, pattern in event_patterns:
        if pattern.search(content):
            return event_id
    return None

df['event_id'] = df['content'].apply(find_event) # use find_event function return the E# for the event in 'content'
#print(df['event_id'].value_counts())

hdfs_templates = dict(zip(templates['EventId'], templates['EventTemplate']))
df['event_template'] = df['event_id'].map(hdfs_templates)
df['event_id'] = 'HDFS_' + df['event_id'] # event id will be HDFS_E# as all log files have different events
#print(df['event_template'].value_counts())

df['event_template'] = df['event_template'].str.replace('[*]', '<*>', regex=False) # converting [*] to <*> to match openstack
#print(df[['event_id', 'event_template']].drop_duplicates().head(10))

# final columns, same order as openstack_events.csv
df = df[['timestamp', 'component', 'severity', 'instance_id', 'event_id', 'event_template', 'label']]
df.to_csv(OUT_PATH, index=False)