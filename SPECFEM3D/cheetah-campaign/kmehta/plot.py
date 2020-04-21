#!/usr/bin/env python3

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import glob
import pdb

#plt.figure(figsize=(10,6))

all_files = glob.glob("256-50*/run-0.iteration-*/data.csv")

df_l = []
for f in all_files:
    df = pd.read_csv(f, index_col=None, header=0)
    df_l.append(df)

df = pd.concat(df_l, axis=0, ignore_index=True)

# Save as a new csv to upload to google colab
df.to_csv("step_data.csv", index=False)

print(df.head())
print(df['Label'].unique())
print(df['Non_io_time'].max())

# sns set to default
sns.set(font_scale=1.5)

sns.set_style('whitegrid')

#ax = sns.boxplot(y=df['Non_io_time'], x=df['Step id'])
#ax = sns.scatterplot(y=df['Non_io_time'], x=df['Step id'], s=50)
#ax = sns.scatterplot(y=df['Non_io_time'], x=df['Earthquake id'], s=50)
# ax = sns.distplot(df['Non_io_time'])
#ax = sns.catplot(y='Non_io_time', x='Step id', data=df, kind='box')

# for ulabel in df['Label'].unique():
#     subdf = df.loc[df['Label'] == ulabel]
#     sns.distplot(df['Non_io_time'], hist=False, rug=True)

# ['4ppn-all-10sec' '8ppn-1GB-5sec' '8ppn-128MB-5sec' '1ppn-all-1sec'
#  '2ppn-all-1sec' '8ppn-100GB-30sec']

subdf = df.loc[df['Label'] == '8ppn-1GB-5sec']
sns.distplot(subdf['Non_io_time'])

#ax.set_xscale('log', basex=2)
#ax.set_yscale('log', basey=2)
#ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())

# ax.set_xlabel("Step #", fontsize=15)
# ax.set_ylabel("Step runtime in seconds", fontsize=15)
plt.title("", fontsize=15)
#plt.show()

# bbox_inches removes whitespace around the figure
# plt.savefig('512-substreams.png', bbox_inches='tight')

