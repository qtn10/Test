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
#   timestamp       - needed to ORDER events and measure time gaps between them
#                    
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

###
# TO DO: 
# make loop into HDFS.log to check for LINE_PATTERN.match in HDFS.log
# checking hdfs file first before going thru whole file
###
with open(LOG_PATH, 'r') as log:
    for i, line in enumerate(log):
        if i == 3: # only checking 3 log lines
           break
        line = line.strip() # remove new line issue
        match = LINE_PATTERN.match(line)
        if match:
            date, time, pid, level, component, content = match.groups()
            print(date, time, '\n', pid, '\n', level, '\n', component, '\n', content)
