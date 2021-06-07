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
    --master $1 \
    --files $ZIPFILE \
    --conf spark.eventLog.enabled=true \
    --conf spark.eventLog.dir=$LOGDIR \
    --conf spark.executor.memoryOverhead=1g \
    --conf spark.driver.maxResultSize=0g \
    --num-executors 1 \
    --executor-cores 1 \
    --conf spark.network.timeout=3000 \
    das2020_driver.py ../configs/cef_test.ini \
    --loglevel DEBUG \
    --logfilename ~/das_log.log
