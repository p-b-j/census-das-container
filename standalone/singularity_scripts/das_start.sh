#!/bin/bash

source util/singularity_scripts/setup_env.sh

# Run standalone config
cd das_decennial

LOGDIR=$HOME/das-log
mkdir -p $LOGDIR || exit 1

ZIPFILE=/tmp/das_decennial$$.zip
export ZIPFILE
zip -r -q $ZIPFILE . || exit 1

export DAS_RUN_UUID=$(cat /proc/sys/kernel/random/uuid)

spark-submit --py-files $ZIPFILE \
    --files $ZIPFILE \
    --conf spark.eventLog.enabled=true \
    --conf spark.eventLog.dir=$LOGDIR \
    --conf spark.executor.memoryOverhead=1g \
    --conf spark.dynamicAllocation.enabled=true \
    --conf spark.network.timeout=3000 \
    --conf spark.driver.maxResultSize=0g \
    --conf spark.python.worker.memory=5g \
    --driver-memory 5g \
    --num-executors 1 \
    --executor-memory 5g \
    das2020_driver.py ../configs/cef_test.ini \
    --loglevel DEBUG \
    --logfilename ~/das_log.log
