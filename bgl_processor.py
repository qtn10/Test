# data processing program for BGL log files

# import libraries
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import re

# load file 1
DATA_PATH = 'data/bgl.log'
with open(DATA_PATH, 'r') as log:
    lines = log.readlines()

for line in lines:
    print(line)
    
# 

# anonymise sensitive fields

# feature engineering: needs extra for high mark
