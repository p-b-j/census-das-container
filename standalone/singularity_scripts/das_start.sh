#!/bin/bash

source util/setup_env.sh

# Run standalone config
cd das_decennial
export DAS_RUN_UUID=$(cat /proc/sys/kernel/random/uuid)
spark-submit --conf spark.executor.memoryOverhead=1g \
    --conf spark.dynamicAllocation.enabled=true \
    --conf spark.python.worker.memory=11g \
    --driver-memory 11g \
    --num-executors 1 \
    --executor-memory 11g \
    das2020_driver.py ../configs/standalone.ini \
    --loglevel DEBUG \
    --logfilename ~/das_log.log

