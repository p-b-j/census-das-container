#!/usr/bin/env bash

echo Running DAS on `date` $config

#zip the code
ZIPFILE=../to_send.zip
export ZIPFILE
zip -r -q $ZIPFILE . -i '*'

DEFAULT_OUTPUT=das_output.out

#output=$1
if [ x$output = x ]; then
  output="$DEFAULT_OUTPUT"
fi

export TERM=xterm

## This program runs the DAS framework driver with the config file specified.
echo starting at `date`
echo $PWD

export PATH=$PATH:$PWD

echo PID $$ starting at `date`

init_cmd="nohup 2>&1 spark-submit --files $ZIPFILE --driver-memory 5g --num-executors 360 --executor-memory 5g --executor-cores 4 --driver-cores 10  --conf spark.driver.maxResultSize=0g --conf spark.executor.memoryOverhead=5g --conf spark.local.dir='/mnt/tmp/' --conf spark.eventLog.enabled=true --conf spark.eventLog.dir='/mnt/tmp/logs/' --master yarn --conf spark.submit.deployMode=client --conf spark.network.timeout=3000 programs/validator/end2end_validator.py"
ouput="&> $output &"

cmd_to_run="$init_cmd $ouput"
echo $cmd_to_run
eval $cmd_to_run

echo PID $$ done at `date`
