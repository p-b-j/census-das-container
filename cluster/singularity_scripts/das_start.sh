#!/bin/bash

source util/singularity_scripts/setup_env.sh

# Run standalone config
source util/singularity_scripts/prep_das_run.sh

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
    das2020_driver.py $2 \
    --loglevel DEBUG \
    --logfilename ~/das_log.log
