# data transformation program for bgl.log file
#
# program intends to bring common columns and headers from the BGL log into a new dataframe format
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
#   severity        - log severity as 0-3 (INFO=0, WARNING=1, SEVERE/ERROR=2, FAILURE/FATAL=3)
#   instance_id     - the BGL node the line is about (e.g. R02-M1-N0-C:J12-U11), empty if the node is NULL/UNKNOWN
#   event_id        - BGL_E# for each distinct event_template
#                     Unlike HDFS, there arent 29 E# in BGL, there are 600+
#   event_template  - LogHub's template for the message with its variable parts masked out as <*>
#   label           - 1 if the line has an alert tag in the first column, 0 if the tag is '-'
#
# differences from hdfs_transformed.py:
#   - BGL severity combines levels 2 and 3
#   - BGL labels each LINE directly (first column), so anomaly_label.csv (which is per time window) is not needed
#   - BGL templates already use <*> and are not wrapped in wildcards, so they are split on <*> and
#     matched against the WHOLE message with fullmatch instead of search
#   - placeholders are <*> for marking varying components of a template
#   - some BGL templates overlap (e.g. 'program <*>' and 'program <*>/<*>'), so templates are tried
#     fewest-placeholder_count first and the catch-all template '<*>' last
#
# dataset:
# BGL.log
# + Adam J. Oliner, Jon Stearley. [What Supercomputers Say: A Study of Five System Logs](http://ieeexplore.ieee.org/document/4273008/), in Proc. of IEEE/IFIP International Conference on Dependable Systems and Networks (DSN), 2007.
# + Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu.
# [Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics]
# (https://arxiv.org/abs/2008.06448). IEEE International Symposium on Software Reliability Engineering (ISSRE), 2023.

# import libraries
import pandas as pd
import re

BGL_DIR = 'data/BGL/'
BGL_PP = 'preprocessed/'
LOG_PATH = BGL_DIR + 'BGL.log'
TEMPLATES = BGL_DIR + BGL_PP + 'BGL.log_templates.csv'
MATRIX = BGL_DIR + BGL_PP + 'Event_occurrence_matrix.csv'

CHUNK_SIZE = 500000

# output path for final product
OUT_PATH   = 'data/processed/bgl_events.csv'

# BGL has 6 levels, grouped into the same 0-3 scale as hdfs and openstack
SEVERITY_MAP = {'INFO': 0, 'WARNING': 1, 'SEVERE': 2, 'ERROR': 2, 'FAILURE': 3, 'FATAL': 3}

# node values that are not a real node
# differs to HDFS because every HDFS line has a block ID, many BGL lines do not have one
NO_NODE = ['NULL', 'UNKNOWN_LOCATION', '-']

# regex for each line in BGL.log
# example BGL line: - 1117838570 2005.06.03 R02-M1-N0-C:J12-U11 2005-06-03-15.42.50.363779 R02-M1-N0-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected
LINE_PATTERN = re.compile(
    r'^(\S+) \d+ \S+ (\S+) (\d{4}-\d{2}-\d{2}-\d{2}\.\d{2}\.\d{2}\.\d+)(?: \S+)? \S+ (\S+) '
    r'(INFO|WARNING|SEVERE|ERROR|FAILURE|FATAL)(?: (.*))?$'
) 

# BGL templates use <*> (not [*] like hdfs)
def template_to_regex(template):
    pieces = template.split('<*>')
    escaped = [re.escape(p) for p in pieces]
    return re.compile('.*'.join(escaped))

templates = pd.read_csv(TEMPLATES)

# template logic slightly different to HDFS because there are way more templates in BGL
# BGL also has templates that overlap rather than fixed phrases
templates['placeholder_count'] = templates['EventTemplate'].str.count(re.escape('<*>'))
templates['fixed_text_length'] = templates['EventTemplate'].str.replace('<*>', '', regex=False).str.len()
templates['catch_all'] = templates['EventTemplate'] == '<*>'
templates = templates.sort_values(['catch_all', 'placeholder_count', 'fixed_text_length'],
                                  ascending=[True, True, False], kind='stable')

event_patterns = []
for event_id, template in zip(templates['EventId'], templates['EventTemplate']):
    event_patterns.append((event_id, template_to_regex(template)))

bgl_templates = dict(zip(templates['EventId'], templates['EventTemplate']))

# function for mapping E#
# so the whole message has to fit the template (different to HDFS)
def find_event(content):
    if content:  # empty messages have no event
        for event_id, pattern in event_patterns:
            if pattern.fullmatch(content):
                return event_id
    return None

def process_chunk(rows):
    df = pd.DataFrame(rows, columns=['tag', 'node', 'time', 'component', 'level', 'content'])
    df['content'] = df['content'].fillna('')  # lines with no message give None from the regex

    # e.g. 2005-06-03-15.42.50.363779, microseconds removed to match hdfs and openstack
    df['timestamp'] = pd.to_datetime(df['time'], format='%Y-%m-%d-%H.%M.%S.%f')
    df['timestamp'] = df['timestamp'].dt.floor('s')

    df['severity'] = df['level'].map(SEVERITY_MAP)

    df['instance_id'] = df['node']
    df.loc[df['node'].isin(NO_NODE), 'instance_id'] = pd.NA  # not a real node

    df['label'] = (df['tag'] != '-').astype(int)  # '-' = normal, any alert tag = anomaly

    df['event_id'] = df['content'].apply(find_event)
    df['event_template'] = df['event_id'].map(bgl_templates)
    df['event_id'] = 'BGL_' + df['event_id']  # stays empty for lines with no event

    # final columns, same order as openstack_events.csv
    df = df[['timestamp', 'component', 'severity', 'instance_id', 'event_id', 'event_template', 'label']]
    return df

# match object contains all details needed for analysis, fill it into rows
rows = []
first_chunk = True
skipped = 0

# done in chunks like HDFS
with open(LOG_PATH, 'r') as log:
    for line in log:
        line = line.strip() # remove new line issue
        match = LINE_PATTERN.match(line)
        if match:
            rows.append(match.groups())
        else:
            skipped += 1  
        if len(rows) == CHUNK_SIZE:
            df = process_chunk(rows)
            if first_chunk:
                df.to_csv(OUT_PATH, mode='w', header=True, index=False) # first line
            else:
                df.to_csv(OUT_PATH, mode='a', header=False, index=False) # change mode and header to ensure no overwrites or repeated headers
            first_chunk = False
            rows = []
            print('chunk written')

# process for last chunk
if rows:
    df = process_chunk(rows)
    if first_chunk:
        df.to_csv(OUT_PATH, mode='w', header=True, index=False)
    else:
        df.to_csv(OUT_PATH, mode='a', header=False, index=False)
    print('last chunk written')