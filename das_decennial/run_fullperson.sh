#!/bin/bash
# Run a DAS job with:
# [config=configfile] [output=outputfile] bash run_cluster.sh  [--all] [--fg] [--help] [config]
#
# --fg - run in the foreground 
# --help - print help
# --all  - use all resources
# 

VERSION=1.1

## Option processing
# https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
# Process arguments
FG=N
ALL=N
while [[ "$#" > 0 ]];
do case $1 in
   --bg) FG=N;;
   --fg) FG=Y;;
   --help) head -10 $0; exit 0;;
   --all)  ALL=Y;;
   *) echo "Unknown parameter: $1";exit 1;;
esac; shift; done

# Set up the variables
# 
CONFIG_DIR=configs
DEFAULT_CONFIG=test_RA_config_cluster.ini
DEFAULT_OUTPUT=das_output.out

# for CORE=3 m4.16xlarge and MASTER = m4.2xlarge
# maxResultsSize is the max that will be sent to the driver. It must fit in memory
[[ -v SPARK_RESOURCES ]] ||
  SPARK_RESOURCES="--driver-memory 5g --num-executors 18 --executor-memory 400g --executor-cores 5 --driver-cores 10 --conf spark.dynamicAllocation.maxExecutors=20 --conf spark.driver.maxResultSize=0g --conf spark.executor.memoryOverhead=300g"

##
## Process the command-line options that are passed in as variables
## 
#output=$2
if [ x$output = x ]; then
  output="$DEFAULT_OUTPUT"
  echo using default output $output
fi

#config=$1
if [ x$config = x ]; then
  config="$DEFAULT_CONFIG"
  echo using default config file $config
fi

#
# If a slash was not provided in the config file name, prepend the CONFIG_DIR
#
if [[ $config == */* ]] ; then
  echo Path provided for config file $config
else
  config=$CONFIG_DIR/$config
fi

## Check to make sure the config file exists
if [ ! -r "$config" ]; then
  echo Cannot read DAS config file $config
  exit 1
fi

echo Running DAS with config $config
echo starting at `date` in $PWD
export PATH=$PATH:$PWD

## Create the DAS command

cmd="spark-submit $SPARK_RESOURCES --conf spark.local.dir=/mnt/tmp/ --conf spark.eventLog.enabled=true --conf spark.eventLog.dir=/mnt/tmp/logs/ --master yarn --conf spark.submit.deployMode=client --conf spark.network.timeout=10000 das2020_driver.py $config --loglevel DEBUG"
echo $cmd

if [ $FG == Y ]; then
  echo "Running in foreground"
  $cmd
  echo $0: PID $$ done at `date`. DAS is finished.
else
  nohup $cmd 2>&1 &> $output &
  echo PID $$ done at `date`. DAS continues executing...
  echo watch output with:
  echo tail -f $output
fi


