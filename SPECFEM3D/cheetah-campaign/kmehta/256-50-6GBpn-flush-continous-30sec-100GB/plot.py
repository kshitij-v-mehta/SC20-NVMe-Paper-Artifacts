#!/usr/bin/env python3

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

plt.get_current_fig_manager().show()
#plt.figure(figsize=(10,6))

df = pd.read_csv('run-0.iteration-2/data.csv')
print(df.head())

# sns set to default
sns.set(font_scale=1.5)

sns.set_style('whitegrid')

#ax = sns.boxplot(y=df['Non_io_time'], x=df['Step id'])
ax = sns.scatterplot(y=df['Non_io_time'], x=df['Step id'], s=50)
#ax = sns.scatterplot(y=df['Non_io_time'], x=df['Earthquake id'], s=50)
#ax = sns.distplot(df['Non_io_time'])
# ax = sns.catplot(y='Non_io_time', x='Step id', data=df, kind='violin')

#ax.set_xscale('log', basex=2)
#ax.set_yscale('log', basey=2)
#ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())

# ax.set_xlabel("Step #", fontsize=15)
# ax.set_ylabel("Step runtime in seconds", fontsize=15)
plt.title("", fontsize=15)
plt.show()

# bbox_inches removes whitespace around the figure
# plt.savefig('512-substreams.png', bbox_inches='tight')

