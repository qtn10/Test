# data processing program for hdfs.log files

# import libraries
import pandas as pd
import numpy as np
from datetime import datetime
#import matplotlib.pilot as plt

# load file 
DATA_PATH = 'data/HDFS_v1/hdfs.log'
with open(DATA_PATH, 'r') as log:
    lines = log.readlines()

for line in lines:
    print(line)
    
# 

# anonymise sensitive fields

# feature engineering: needs extra for high mark
