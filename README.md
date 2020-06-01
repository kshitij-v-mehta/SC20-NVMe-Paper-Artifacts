# SC20-NVMe-Paper-Artifacts
All artifacts created for the Supercomputing 2020 paper "Co-design Evaluation of HPC I/O Middleware forMulti-Tier Storage Architectures"

In this repository, we have campaign data for experiments with the SPECFEM3D and GTC applications. They are placed under separate directories. Each sub-directory consists of the campaign directory and the source code used for flushing data from the node-local NVMe to the parallel file system. All experiments were run on the Summit supercomputer at ORNL.

## Source codes
The [SPECFEM3D documentation portal](https://specfem3d-globe.readthedocs.io/en/latest) contains necessary information about obtaining the source code and inputs for SPECFEM3D. For our experiments, 
SPECFEM3D code version: git hash 907abeb5a2b89493f5fd73e7c44104a0686ccba4 in branch 'devel' was used. Additional instrumentation was performed by the authors to obtain performance information and diagnostics output.

The GTC source code is from the closed-source repository from the [research group led by Zhihong Lin at University of California, Irvine](http://phoenix.ps.uci.edu/zlin).

POSIX-WRITE-BENCHMARK contains the source code and data for the POSIX write test used to benchmark the NVMe performance for fast writes vs. streaming writes with a time delay between write calls.

## Experiment Campaigns
The campaign directory follows the format of the [CODAR Cheetah campaign management tool](https://github.com/CODARcode/cheetah/tree/1a33c90b2cda737d844dd8051545874a88da90bf). Please consult the [Cheetah documentation](https://codarcode.github.io/cheetah) to understand the campaign directory structure. The instructions below describe some of the campaign directory structure.

#### Performance data
Inside a campaign directory (`SPECFEM3D/cheetah-campaign/` and `GTC/cheetah-campaign/`), we have a `campaign_results.csv` file which provide overall runtime information for all experiments in the campaign. Additional csv files may be found for per-experiment step runtimes.
Python scripts are provided to extract information from stdout and other files for each experiment (e.g. time to compute each step in SPECFEM3D and GTC).

#### Parsing the campaign directory
In the campaign directory, there is a subdirectory for the members who ran experiments (`kmehta` in this case). Each subdirectory within it represents a group of experiments submitted as a batch job to Summit. For example, `SPECFEM3D/cheetah-campaign/kmehta/256-50-6GBpn-flush-continous-1sec-all-1ppn` is a Cheetah (Sweep) group. The `fobs.json` file in a Sweep group directory is a manifest of all experiments in the group. Within a group we have experiments with independent workspaces named as `run-x.iteration-y`. Multiple runs of the same experiment may be in different Sweep groups.

There are several files inside an experiment workspace. The experiment configuration is stated in `codar.cheetah.run-params.*` file.
`codar.workflow.stdout.*` is a stdout file for the applications run in the experiment.

## DOI
[![DOI](https://zenodo.org/badge/257544106.svg)](https://zenodo.org/badge/latestdoi/257544106)

