#!/bin/bash

export EXECUTOR_CORES=7
export EXECUTORS_PER_NODE=12
export DRIVER_CORES=10
export DRIVER_MEMORY=5g
export EXECUTOR_MEMORY=16g

usage() {
   echo please specify fast full_person 
   exit 1
}

# 60 seconds:
if [ x$1 = x ]; then
    usage
fi

if [ $1 = fast ]; then
  export NUM_EXECUTORS=4	# for speed
  config=configs/garfi303/topdown_RI.ini 
elif [ $1 = full_person ]; then
  config=configs/full_person/test_lecle.ini
else
    usage
fi

config=$config  ./run_cluster.sh
