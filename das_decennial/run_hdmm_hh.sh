#!/bin/bash

export EXECUTOR_CORES=8
export EXECUTORS_PER_NODE=1
export DRIVER_CORES=10
export DRIVER_MEMORY=5g
export EXECUTOR_MEMORY=200g
export EXECUTOR_MEMORY_OVERHEAD=200g

usage() {
   echo please specify fast full_household 
   exit 1
}

# 60 seconds:
if [ x$1 = x ]; then
    usage
fi

if [ $1 = fast ]; then
    export NUM_EXECUTORS=6# for speed
  config=configs/garfi303/topdown_RI.ini 
elif [ $1 = full_household ]; then
  config=configs/full_household/hdmm_exp.ini
else
    usage
fi

config=$config ./run_cluster.sh
