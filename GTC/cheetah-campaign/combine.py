#!/usr/bin/env python3

import glob
import pandas as pd

all_files = glob.glob("kmehta/*/*/data.csv")

df_l = []
for f in all_files:
    df = pd.read_csv(f, index_col=None, header=0)
    df_l.append(df)

df = pd.concat(df_l, axis=0, ignore_index=True)

# Save as a new csv to upload to google colab
df.to_csv("gtc_all_step_data.csv", index=False)

