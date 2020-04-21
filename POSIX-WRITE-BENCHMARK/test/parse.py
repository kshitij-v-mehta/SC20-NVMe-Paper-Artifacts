#!/usr/bin/env python3

import statistics
import csv

lines = []
steps = {}
csv_data = []
infile = "bench-sleep.out"
with open(infile) as f:
    lines = f.readlines()

# Read all lines and get the step and io time
for line in lines:
    if 'Rank' in line and 'step:' in line and 'io time' in line:
        step = int(line.split('step:')[1].split(',')[0])
        if step not in steps:
            steps[step] = []
        iotime = float(line.split('io time:')[1].strip())
        steps[step].append(iotime)

# For each step, average the io time across all ranks as they are similar
for step in steps:
    avgtime = round(float(statistics.mean(steps[step])),2)
    csv_data.append([step, avgtime])

# Write to csv
with open('{}.csv'.format(infile),'w') as f:
    csvw = csv.writer(f)
    csvw.writerow(["Step", "Time"])
    csvw.writerows(csv_data)

