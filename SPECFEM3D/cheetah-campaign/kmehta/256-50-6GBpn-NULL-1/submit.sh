#!/bin/bash

cd "$(dirname $0)"
source ../campaign-env.sh
source group-env.sh

if [ -f "$CODAR_CHEETAH_MACHINE_CONFIG" ]; then
    source "$CODAR_CHEETAH_MACHINE_CONFIG"
fi

# Don't submit job if all experiments have been run
if [ -f codar.workflow.status.json ]; then
    grep state codar.workflow.status.json | grep -q 'not_started'
    if [ $? != 0 ]; then
        echo "No more experiments remaining. Skipping group .."
        exit
    fi
fi

# Gather flags for gpumps and SMT level to be passed on to -alloc_flags
alloc_flags=

# convert walltime from seconds to HH:MM format needed by LSF
secs=$CODAR_CHEETAH_GROUP_WALLTIME
LSF_WALLTIME=$(printf '%02d:%02d\n' $(($secs/3600)) $(($secs%3600/60)))

OUTPUT=$(bsub \
        -P $CODAR_CHEETAH_SCHEDULER_ACCOUNT \
        -J "$CODAR_CHEETAH_CAMPAIGN_NAME-$CODAR_CHEETAH_GROUP_NAME" \
        -nnodes $CODAR_CHEETAH_GROUP_NODES \
        -W $LSF_WALLTIME \
        -alloc_flags "gpumps nvme maximizegpfs" \
        -u mehtakv@ornl.gov \
        run-group.lsf)

rval=$?

if [ $rval != 0 ]; then
    echo "SUBMIT FAILED:"
    echo $OUTPUT
    exit $rval
fi

JOBID=$OUTPUT

echo "LSF:$JOBID" > codar.cheetah.jobid.txt

