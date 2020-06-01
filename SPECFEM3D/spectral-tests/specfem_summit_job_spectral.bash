#!/bin/bash
# LSF scheduler options
#BSUB -P CSC143
#BSUB -J specfem3d_globe
#BSUB -o spectral-%J.out
#BSUB -e spectral-%J.err
#BSUB -N
#BSUB -u mehtakv@ornl.gov
#BSUB -alloc_flags "gpumps spectral"

#BSUB -W 00:30
#BSUB -nnodes 800


module load xl cuda/9.2.148 hdf5/1.8.18 spectral

export LD_LIBRARY_PATH=/sw/summit/cuda/9.2.148/lib64:$LD_LIBRARY_PATH

mkdir -p DATABASES_MPI OUTPUT_FILES

MESHER_ROOT=/gpfs/alpine/proj-shared/csc143/kmehta/specfem3d_globe/forward-simulations/256-mesher-data

# ln -sf $MESHER_ROOT/DATABASES_MPI/* DATABASES_MPI/.
# cp -r $MESHER_ROOT/OUTPUT_FILES/* OUTPUT_FILES/.

./change_simulation_type.pl -F

###################################################

export PERSIST_DIR=/mnt/bb/kmehta
export PFS_DIR=./


STARTTIME=$(date +%s)
echo "start time is : $(date +"%T")"


echo "running simulation: `date`"
echo "directory: `pwd`"
echo
module list
echo

# runs mesher
# echo
# echo "running mesher..."
# echo `date`
# jsrun -n96 -r6 -g1 -a4 -c4 ./bin/xmeshfem3D
# if [[ $? -ne 0 ]]; then exit 1; fi

# echo "Copy mesh data to run folders"
# bash copy_data.sh

# runs simulation
echo
echo "running forward solver..." 
echo `date`
# jsrun -n 192 -r6 -g1 -a4 -c4 ./bin/xspecfem3D pfs
jsrun -n 4800 -r6 -g1 -a4 -c4 ./bin/xspecfem3D bb
if [[ $? -ne 0 ]]; then exit 1; fi

echo
echo "done: `date`"
ENDTIME=$(date +%s)
Ttaken=$(($ENDTIME - $STARTTIME))
echo
echo "finish time is : $(date +"%T")"
echo "RUNTIME is :  $(($Ttaken / 3600)) hours ::  $(($(($Ttaken%3600))/60)) minutes  :: $(($Ttaken % 60)) seconds."

STARTTIME=$(date +%s)
spectral_wait.py
ENDTIME=$(date +%s)
Ttaken=$(($ENDTIME - $STARTTIME))
echo
echo "finish time is : $(date +"%T")"
echo "RUNTIME for spectral is :  $(($Ttaken / 3600)) hours ::  $(($(($Ttaken%3600))/60)) minutes  :: $(($Ttaken % 60)) seconds."

