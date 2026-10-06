# data processing program for openstack log files
# Steps and purpose:
# This program was created to convert a combined openstack_combined.log file
# into a clean and parsed csv file with header columns organised based on
# features deemed necessary for data analysis and transformation to compare
# against the HDFS and BGL log data
# This program uses Logparser Drain rather than using regex completely manually
# 
# chosen columns and reasoning:
#   timestamp       - needed to track time ranges and comparing anomalies over time
#   component       - drain component e.g. nova.compute.manager
#   severity        - log severity as numbers 0-3 (INFO, WARNING, ERROR, CRITICAL)
#   instance_id     - the UUID of the VM this line is about
#   event_id        - hashid for each distinct event_template, not matching the style
#                     Loghub uses for HDFS and BGL
#   event_template  - the message with its variable parts masked out
#   label           - 1 if the VM is listed in anomaly_labels.txt, else 0
#
# Citation
# HasanB 2025, Anomaly Detection in HDFS Logs using Transformer Models and Machine Learning,
# 4 October, viewed 24 September 2026
# https://www.youtube.com/watch?v=2uR4amYOgB4

# import libraries
import re
import pandas as pd
from logparser.Drain import LogParser

DRAIN_IN = 'data/OpenStack/'
DRAIN_OUT = 'data/OpenStack/drain/'
OUTPUT_FOLDER = 'data/processed/'

# vm id identification in each line
# example vmid: 719832a5-1b99-41ab-81a2-4c9bc9c84e39
VMID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

parser = LogParser(
    # drain log format - extract features 
    log_format = '<SourceFile> <LogRecord> <Date> <Time> <pID> <Level> <component> \[<ADDR>\] <Content>',
    indir= DRAIN_IN,
    outdir= DRAIN_OUT,
    depth=12, # changed after multiple attempts as this change determines the amt of vm templates we get
    st=0.5,
    rex=[VMID,              # VM ids
     r'[0-9a-f]{32}',   # tenant/user ids in URLs
     r'((\d+\.){3}\d+,?)+',
     r'/.+?\s',
     r'\d+'],
)
parser.parse('openstack_combined.log')

# 3 diff ways instance id is mentioned per log line
instance_patterns = [
    re.compile(r'\[instance: (' + VMID + r')\]'),   
    re.compile(r'servers/(' + VMID + r')'),          
    re.compile(r'for instance (' + VMID + r')'),     
]

# check if message matches any instance_patterns, return VMID else None
def find_instance(message):
    for pattern in instance_patterns:
        match = pattern.search(message)
        if match:
            return match.group(1)    
    return None

# anomalous_vms definition based on anomaly_labels.txt
with open(DRAIN_IN + 'anomaly_labels.txt') as f:
    anomalous_vms = set(re.findall(VMID, f.read())) 

# need to make E instances actual events before making openstack_events.csv
# sorted by events occurrence count as it is similar with event_occurrence_matrix, using to
# create a openstack.log_templates.csv file that is easier to read
templates = pd.read_csv(DRAIN_OUT + 'openstack_combined.log_templates.csv')
templates = templates.sort_values('Occurrences', ascending=False).reset_index(drop=True)
templates['osevent_id'] = 'OS_E' + (templates.index + 1).astype(str) # OS_E = OpenStack_Event

os_events = dict(zip(templates['EventId'], templates['osevent_id']))

# adding our own columns as described above into a pandas DataFrame
df = pd.read_csv(DRAIN_OUT + 'openstack_combined.log_structured.csv')

df['timestamp'] = df['Date'] + ' ' + df['Time']
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S.%f')
df['timestamp'] = df['timestamp'].dt.floor('s')

df['severity'] = df['Level'].map({'INFO': 0, 'WARNING': 1, 'ERROR': 2, 'CRITICAL': 3})
df['instance_id'] = df['Content'].apply(find_instance)

df['label'] = df['instance_id'].isin(anomalous_vms).astype('Int64') # changed from int to Int64 because we need empty value
df.loc[df['instance_id'].isna(), 'label'] = pd.NA # label set to unkown

df = df.rename(columns={'EventId': 'event_id', 'EventTemplate': 'event_template'})
df['event_id'] = df['event_id'].map(os_events) # from templates

templates.to_csv(DRAIN_OUT + 'openstack_templates.csv', index=False) 

df = df[['timestamp', 'component', 'severity', 'instance_id', 'event_id', 'event_template', 'label']]
df.to_csv(OUTPUT_FOLDER + 'openstack_events.csv', index=False)
#print(df['label'].value_counts(dropna=False)) # testing line to confirm unknown values exist
#print(df['event_id'].nunique()) # confirm unique events
#print(df['event_id'].isna().sum()) # confirm how many events are empty
#print(templates.columns.tolist()) # list columns
