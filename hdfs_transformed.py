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
#   event_id        - E# for each distinct event_template, openstack's hashes will be converted
#                     to E# when all 3 datasets are transformed to fit each other
#   event_template  - the message template with its variable parts masked out
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
import numpy as np
import re
import datetime

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

# match object contains all details needed for analysis, fill it into rows
rows = []

with open(LOG_PATH, 'r') as log:
    for i, line in enumerate(log):
        line = line.strip() # remove new line issue
        if i == 10000: ## for testing, remove when done
            break ## for testing, remove when done
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
