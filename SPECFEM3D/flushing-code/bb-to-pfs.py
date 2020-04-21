#!/usr/bin/env python3

from mpi4py import MPI
import os
import glob
import shutil
import platform
import subprocess
import sys
import time
import argparse

#----------------------------------------------------------------------------#
class DataFile:
    """
    Represents a subfile of the save_forward_arrays_undoatt.bp file.
    """
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest


#----------------------------------------------------------------------------#
class FlushMan:
    """
    My superpower is that I flush NVMes to parallel file systems.
    I can do that post-hoc or in the background.
    """
    
    #------------------------------------------------------------------------#
    def __init__(self, wakeup_interval, ds):
        # MPI Initializations
        hostname = platform.node()
        comm = MPI.COMM_WORLD
        comm_size = comm.Get_size()
        self.global_rank = comm.Get_rank()

        # Create node-local communicators
        color = "".join(c if c.isdigit() else str(ord(c)) for c in hostname)
        self.local_comm = comm.Split(int(color), self.global_rank)
        self.local_commsize = self.local_comm.Get_size()
        self.local_rank = self.local_comm.Get_rank()

        # Set my identity
        self.name = "{} on {}".format(self.local_rank, hostname)

        # Set my wakeup interval for flushing the NVMe
        self.wakeup_interval = wakeup_interval

        # Max data that must be written by a flusher rank per adios subfile
        # every time it wakes up. Useful for limiting how much data is
        # flushed every epoch
        self.data_size_limit = ds

        # List of data files on the NVMe assigned to me
        self.data_files = []
        
        # I will call this C routine to do the actual copy of data from NVMe-->PFS
        self.cexe = "/ccs/proj/csc299/kmehta/specfem3d_globe/specfem3d_globe-devel-01.06.20/cheetah/continuous-flush/bb-to-pfs-serial-positional"

        # Path to the NVME
        self.nvme_root = "/mnt/bb/kmehta/"

    #------------------------------------------------------------------------#
    def get_data_files(self, adios_wpn):
        """
        Get a list of data files on the NVME that I must be tasked with for
        flushing to the PFS.
        Distributes adios subfiles amongst node-local ranks.
        """

        # Check if data has been written to the NVMe
        _data_files = glob.glob(self.nvme_root+"*save_forward_arrays_undoatt.bp/data*")
        while(len(_data_files) < adios_wpn):  # specfem has not written data yet
            time.sleep(1)
            _data_files = glob.glob(self.nvme_root+"*save_forward_arrays_undoatt.bp/data*")

        # Sort the data files as the output of glob.glob is arbitrary
        adios_dir = glob.glob(self.nvme_root+"*save_forward_arrays_undoatt.bp")[0]
        subfile_indexes = [int(df.split('data.')[1]) for df in _data_files]
        subfile_indexes.sort()
        data_files = [adios_dir+"/data.{}".format(i) for i in subfile_indexes]
        
        # Distribute files amongst ranks on the node
        self.data_files = []
        num_files_per_rank = len(data_files)//self.local_commsize
        start_index = self.local_rank * num_files_per_rank
        runid = os.path.basename(adios_dir).split('-')[0]
        destdir = "./" + runid + "/DATABASES_MPI/save_forward_arrays_undoatt.bp/"

        # Create DataFile objects for your files
        for df in data_files[start_index:start_index+num_files_per_rank]:
            src = df
            src_basename = os.path.basename(src)
            dest = destdir + src_basename
            self.data_files.append(DataFile(src,dest))

        print("{} assigned {}".format(self.name, [df.src for df in self.data_files]))

    #------------------------------------------------------------------------#
    def _wake(self, data_size):
        """
        Wake up and flush your list of data files from the NVMe to the target FS.
        Read and write only the new data written since your previous wake.
        """
        
        # Now iterate over your data files and copy them to the pfs
        for df in self.data_files:
            args = [self.cexe, '-i', df.src, '-o', df.dest, '-s', str(data_size)]
            print(args)
            completed_proc = subprocess.run(args)
            retval = completed_proc.returncode

            # Abort if an error was returned
            # if bytes_copied < 0:
            #     print("{} has received {} for bytes_copied. Aborting program ...".format(self.name, bytes_copied))
            #     self._terminate()

            #print("{} copied {} bytes from {} to {}".format(self.name, bytes_copied, df.src, df.dest), flush=True)
            
    #------------------------------------------------------------------------#
    def do_your_business(self):
        """
        Wake up after every wakeup_interval and call your wakeup function.
        Quit if the quit condition is met.
        """

        # Loop and wake up every wakeup_interval seconds and flush data
        prev_ts = int(time.time())
        while not self._end_of_run():
            cur_ts = int(time.time())
            elapsed = cur_ts - prev_ts
            if elapsed < self.wakeup_interval:
                print("{} sleeping for {}".format(self.name, self.wakeup_interval-elapsed))
                time.sleep(self.wakeup_interval - elapsed)

            # wake up
            print("{} woke up after sleep".format(self.name))
            prev_ts = int(time.time())
            self._wake(self.data_size_limit)

        # End of run. Flush whatever's remaining
        self._wake(-1)

        # Node-local root checks if adios metadata file lives on this node
        if self.local_rank == 0:
            self._copy_adios_md_file()

        # Wait for local ranks to finish flushing
        self.local_comm.barrier()

        # Node-local root clears out NVMe
        if self.local_rank == 0:
            self._cleanup()

    #------------------------------------------------------------------------#
    def _end_of_run(self):
        """
        Check if end of run has been signalled.
        Check for the presence of the empty DONE.txt file in the NVME
        """

        return os.path.isfile(self.nvme_root+"DONE.txt")

    #------------------------------------------------------------------------#
    def _copy_adios_md_file(self):
        """
        Check for the existence of the adios metadata file on this node, and
        copy it to the pfs if it exists.
        """
        adios_dir = os.path.dirname(self.data_files[0].src)
        md_idx = adios_dir+"/md.idx"
        md_idx_dest = os.path.dirname(self.data_files[0].dest) + "/md.idx"
        if os.path.isfile(md_idx):
            print("{} found md.idx".format(self.name))
            args = [self.cexe, '-i', md_idx, '-o', md_idx_dest, '-s', "-1"]
            completed_proc = subprocess.run(args)
            retval = completed_proc.returncode

    #------------------------------------------------------------------------#
    def _cleanup(self):
        """
        Node-local root removes the adios bp file from the BB
        """
        adios_dir = glob.glob(self.nvme_root+"*save_forward_arrays_undoatt.bp")[0]
        print("{} deleting {}".format(self.name, adios_dir))
        shutil.rmtree(adios_dir)
        os.remove(self.nvme_root+"DONE.txt")

    #------------------------------------------------------------------------#
    def _terminate(self):
        """
        A fatal error has occured. Maybe the C code for flushing returned
        an error. Abort.
        """
        MPI.COMM_WORLD.Abort(-1)

#----------------------------------------------------------------------------#
def read_args():
    parser = argparse.ArgumentParser(usage='Run as -w <wakeup interval> -a <adios writers per node> -s <data size per flush call per file per writer>')
    parser = argparse.ArgumentParser()
    parser.add_argument('-w','--wakeup-interval', required=True)
    parser.add_argument('-s','--data-size-per-write', required=True)
    parser.add_argument('-a','--adios-writers-per-node', required=True)
    args = parser.parse_args()

    wakeup_interval = int(args.wakeup_interval)
    adios_wpn = int(args.adios_writers_per_node)
    ds = int(args.data_size_per_write)

    return (wakeup_interval, ds, adios_wpn)


if __name__ == '__main__':
    (wakeup_interval, ds, adios_wpn) = read_args()

    # Lets give it a real name
    billy = FlushMan(wakeup_interval, ds)
    
    # Assign data files from the NVME to local ranks
    billy.get_data_files(adios_wpn)

    # All set, lets go
    billy.do_your_business()
    
