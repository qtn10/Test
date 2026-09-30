# data transformation program for bgl.log files to unite them

# import libraries
import pandas as pd
import numpy as np
import datetime

with open(DATA_PATH, 'r') as log:
    lines = log.readlines()

for line in lines:
    print(line)
    
# 

# anonymise sensitive fields

# feature engineering: needs extra for high mark
