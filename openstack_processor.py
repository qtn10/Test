# data processing program for openstack log files
# Steps and purpose:
# This program was created to convert a combined openstack_combined.log file
# into a clean and parsed csv file with header columns organised based on
# features deemed necessary for data analysis and transformation to compare
# against the HDFS and BGL log data
# This program uses Logparser Drain rather than using regex completely manually
# 
# Final columns and why each one exists:
#   timestamp       - needed to ORDER events and measure time gaps between them
#   source_file     - which of the 3 input files the line came from
#   service         - nova-api / nova-compute / nova-scheduler
#   severity        - log severity as numbers 0-3 (INFO, WARNING, ERROR, CRITICAL)
#   instance_id     - the UUID of the VM this line is about
#   event_id        - hashid for each distinct event_template,
#                     matching the style Loghub uses for HDFS and BGL, will be converted
#                     to E# when all 3 datasets are transformed to fit each other
#   event_template  - the message with its variable parts masked out
#   label           - 1 if the VM is listed in anomaly_labels.txt, else 0
#
# Citation
# HasanB 2025, Anomaly Detection in HDFS Logs using Transformer Models and Machine Learning,
# 4 October, viewed 24 September 2026
# https://www.youtube.com/watch?v=2uR4amYOgB4

# import libraries
import os
import re
import pandas as pd
from logparser.Drain import LogParser

# vm id identification in each line
# example vmid: 719832a5-1b99-41ab-81a2-4c9bc9c84e39
VMID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

parser = LogParser(
    # drain log format - extract features 
    log_format = '<SourceFile> <LogRecord> <Date> <Time> <pID> <Level> <Component> \[<ADDR>\] <Content>',
    indir='data/OpenStack/',
    outdir='OpenStack/drain/',
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

# for each line with vmid in it, store it in variable match
def find_instance(message):
    for pattern in instance_patterns:
        match = pattern.search(message)
        if match:
            return match.group(1)    
    return None

# anomalous_vms definition based on anomaly_labels.txt
with open('OpenStack/anomaly_labels.txt') as f:
    anomalous_vms = set(re.findall(VMID, f.read())) 

# adding our own columns as described above into a pandas DataFrame
df = pd.read_csv('OpenStack/drain/openstack_combined.log_structured.csv')
df['timestamp'] = df['Date'] + ' ' + df['Time']
df['source_file'] = df['SourceFile']
df['service'] = df['LogRecord'].str.split('.log').str[0]
df['severity'] = df['Level'].map({'INFO': 0, 'WARNING': 1, 'ERROR': 2, 'CRITICAL': 3})
df['instance_id'] = df['Content'].apply(find_instance)
df['label'] = df['instance_id'].isin(anomalous_vms).astype(int)
df = df.rename(columns={'EventId': 'event_id', 'EventTemplate': 'event_template'})

df = df[['timestamp', 'source_file', 'service', 'severity', 'instance_id', 'event_id', 'event_template', 'label']]
df.to_csv('OpenStack/openstack_events.csv', index=False)

