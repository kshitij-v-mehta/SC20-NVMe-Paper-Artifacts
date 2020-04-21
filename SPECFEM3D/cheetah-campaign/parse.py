#!/usr/bin/env python3
import pdb
import csv
import sys
import json
import os


with open("codar.workflow.stdout.forward") as f:
    lines = f.readlines()

step_data = {}
cur_step = {}
# Read all lines into the dict
for line in lines:
    line.strip()
    if 'iteration, start time:' in line:
        if 'run' not in line:
            sys.exit(0)
        run_id = int(line.split(' iteration')[0].strip().split('run')[1])
        iter_id = line.split('time: ')[1].strip().split(' ')[0].strip()
        iter_start_time = line.split(' ')[-1].strip()

        cur_step[run_id] = iter_id
        if run_id not in step_data:
            step_data[run_id] = {}
        if iter_id not in step_data[run_id]:
            step_data[run_id][iter_id] = {}
        step_data[run_id][iter_id]['iter_start_time'] = iter_start_time

    if 'arrays time:' in line:
        run_id = int(line.split('save_forward_arrays')[0].strip().split('run')[1])
        io_time = float(line.split(' ')[-1].strip())
        io_time = str(round(io_time,2))
        iter_id = cur_step[run_id]
        step_data[run_id][iter_id]['io_time'] = io_time
 

# Calculate the iter run time
for run_id in step_data:
    iter_ids = list(step_data[run_id].keys())
    iter_ids_i = [int(iter_id) for iter_id in iter_ids]
    iter_ids_i.sort()
    last_iter_id = str(iter_ids_i[-1])
    for iter_id in step_data[run_id]:
        if iter_id == last_iter_id:
            step_data[run_id][iter_id]['iter_time'] = 0
        else:
            iter_time = float(step_data[run_id][str(int(iter_id)+1)]['iter_start_time']) - float(step_data[run_id][iter_id]['iter_start_time'])
            iter_time = str(round(iter_time, 2))
            step_data[run_id][iter_id]['iter_time'] = iter_time


# Set the label so its easy to plot
label = ""
with open('codar.cheetah.run-params.json') as f:
    d = json.load(f)
if 'bb_to_pfs' in d:
    ppn = (int(d['bb_to_pfs']['nprocs'])) // 800
    label = label + str(ppn) + "ppn"
    if 'data-size-limit' in d['bb_to_pfs']:
        ds_limit = int(d['bb_to_pfs']['data-size-limit'])
        if ds_limit == -1:
            label = label + "-all"
        elif ds_limit >= 1073741824:
            label = label + "-" + str(ds_limit//1073741824) + "GB"
        else:
            label = label + "-" + str(ds_limit//1048576) + "MB"
        
        # Add the sleep interval to the label
        label = label + "-" +  str(d['bb_to_pfs']['sleep-interval']) + "sec"

    # This was flushed at the end
    else:
        label = label + "-flush-end"
elif 'false' in d['forward']['save_forward'].lower():
        label = "no-io"
else:
    label = "PFS"


# Sort the run ids
run_ids = list(step_data.keys())
run_ids.sort()

rows = []
for run_id in run_ids:
    iter_ids = list(step_data[run_id].keys())
    iter_ids_i = [int(iter_id) for iter_id in iter_ids]
    iter_ids_i.sort()

    for iter_id_i in iter_ids_i:
        iter_id = str(iter_id_i)
        iter_start_time = step_data[run_id][iter_id]['iter_start_time']
        iter_time = step_data[run_id][iter_id]['iter_time']
        io_time = step_data[run_id][iter_id].get('io_time', 0)
        other_time = round((float(iter_time) - float(io_time)), 2)
        if other_time < 0: other_time = ""
        other_time = str(other_time)
        if iter_time == 0: iter_time = ""
        row = [label, run_id, iter_id, iter_time, other_time, io_time]
        rows.append(row)


with open("data.csv", "w") as f:
    csvw = csv.writer(f)
    csvw.writerow(["Label", "Earthquake id", "Step id", "Step total time", "Non_io_time", "IO time"])
    csvw.writerows(rows)


# Get the output file size
outsize = ""
pp_stdout = "codar.workflow.stdout.post-process"
if os.path.isfile(pp_stdout):
    with open(pp_stdout) as f:
        lines = f.readlines()
    for line in lines:
        if ".\n" in line:
            outsize = line.split(".\n")[0].strip()

# Write cheetah_user_report.json
total_workflow_time = 0.0
forward_time = 0.0
bb_to_pfs_time = 0.0
if os.path.isfile("./codar.workflow.walltime.forward"):
    with open('codar.workflow.walltime.forward') as f:
        forward_time = round(float(f.readline().strip()),2)

if os.path.isfile("./codar.workflow.walltime.bb_to_pfs"):
    with open('codar.workflow.walltime.bb_to_pfs') as f:
        bb_to_pfs_time = round(float(f.readline().strip()),2)

if 'pfs' in label.lower():
    total_workflow_time = forward_time
elif 'flush' in label.lower():
    total_workflow_time = forward_time + bb_to_pfs_time
else:
    total_workflow_time = bb_to_pfs_time

d = {}
d['Label'] = label
d['Total workflow time'] = total_workflow_time
d['Output file size'] = outsize

with open('cheetah_user_report.json', 'w') as f:
    json.dump(d,f)

