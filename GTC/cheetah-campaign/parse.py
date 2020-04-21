#!/usr/bin/env python3

import os
import json
import csv

lines = []
with open("codar.workflow.stdout.gtc") as f:
    lines = f.readlines()

d = {}
csv_data = []
total_step_time = 0

# Create the label for the experiment
d2 = {}
label = ""
with open("codar.cheetah.run-params.json") as f:
    d2 = json.load(f)

if 'bb_to_pfs' in d2:
    ppn = int(d2['bb_to_pfs']['nprocs'])//512
    label = "{} ppn".format(ppn)
else:
    omp = int(d2['gtc']['openmp'])
    label = label + "pfs-omp: {}".format(omp)
    if d2['gtc']['perform_cr'] == 0:
        label = label + "-noio"

# Parse all lines of the gtc stdout
for line in lines:
    if 'Step' in line and 'cr time' in line:
        io_time = round(float(line.split('cr time:')[1].strip()),2)
        d['io_time'] = io_time
    elif 'Step' in line and 'time' in line:
        stepid = int(line.split(',')[0].split('Step')[1].strip())
        steptime = round(float(line.split('time:')[1].strip()),2)

        total_step_time = total_step_time + steptime
        csv_data.append([label, stepid, steptime])

d['Label'] = label
d['total_step_time'] = total_step_time

# Get the total workflow time
twtime = 0
if os.path.isfile("codar.workflow.walltime.bb_to_pfs"):
    with open("codar.workflow.walltime.bb_to_pfs") as f:
        twtime = round(float(f.readline().strip()),2)
else:
    with open("codar.workflow.walltime.gtc") as f:
        twtime = round(float(f.readline().strip()),2)

d['Total workflow time'] = twtime


# Get the output file size
fsize = ""
pp_file = "codar.workflow.stdout.post-process"
if os.path.isfile(pp_file):
    with open(pp_file) as f:
        fsize = f.readline()

fsize = fsize.strip()
if len(fsize) > 0:
    _fsize = fsize.split("restart")[0].strip()
    fsize = _fsize
d['output_file_size'] = fsize

# Write cheetah user report json file
with open("cheetah_user_report.json", "w") as f:
    json.dump(d, f)

# Write step data to csv
with open("data.csv", "w") as f:
    csvw = csv.writer(f)
    csvw.writerow(["Label", "Step id", "Step time"])
    csvw.writerows(csv_data)

