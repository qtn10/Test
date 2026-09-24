# data processing program for openstack log files

# import libraries
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# load file 1
DATA_PATH = 'data/openstack/openstack_normal1.log'
with open(DATA_PATH, 'r') as log:
    lines = log.readlines()

for line in lines:
    print(line)
    
# 

# anonymise sensitive fields

# feature engineering: needs extra for high mark
