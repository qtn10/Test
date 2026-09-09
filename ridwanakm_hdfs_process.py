import pandas as pd

splits = {'train': 'data/train.csv', 'test': 'data/test.csv'}
df = pd.read_csv("hf://datasets/ridwanakm/hdfs-log-anomaly-dataset-lite/" + splits["train"])
# link: https://huggingface.co/datasets/ridwanakm/hdfs-log-anomaly-dataset-lite
