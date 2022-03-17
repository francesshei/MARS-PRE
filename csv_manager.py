import pandas as pd 
import numpy as np
import os, re

dfs = []
n_rows = []
filenames = []

for f in os.listdir('./'):
    if re.search('.csv', f):
       temp = pd.read_csv(f)
       dfs.append(temp)
       filenames.append(f)
       n_rows.append(temp.shape[0])

diff_rows = np.array(n_rows) - min(n_rows)

for start,file, df in zip(diff_rows, filenames, dfs):
    df = df.iloc[start:,:]
    df.to_csv(file)

print("Dataframes shortened")
