#!/bin/bash
# Run a DAS job with:
# [config=configfile] [output=outputfile] bash run_cluster.sh  [--all] [--fg] [--help] [config]
#
# --fg - run in the foreground
# --help - print help
# --all  - use all resources
#
#
# NOTE: This is the master script for running a cluster.
#       Your run scripts should just set variables and then call this one.

VERSION=1.5

## First make sure that there are no syntax or import errors
if ! python das2020_driver.py --help >/dev/null ; then
    echo das2020_driver.py contains syntax errors. STOP. >/dev/stderr
    exit 1
fi

### From run_dhcp.sh
#export EXECUTOR_CORES=48
#export EXECUTORS_PER_NODE=1
#export DRIVER_CORES=10
#export DRIVER_MEMORY=10g
#export EXECUTOR_MEMORY=250g
#export EXECUTOR_MEMORY_OVERHEAD=450g
#export DEFAULT_PARALLELISM=10000

# Set these variables if they are not set. Defaulting to parameters from run_dhcp.sh
if [ -z ${EXECUTOR_CORES+x} ]; then EXECUTOR_CORES=48 ; fi
if [ -z ${EXECUTORS_PER_NODE+x} ]; then EXECUTORS_PER_NODE=1 ; fi
if [ -z ${DRIVER_CORES+x} ]; then DRIVER_CORES=10 ; fi
if [ -z ${DRIVER_MEMORY+x} ]; then DRIVER_MEMORY=10g ; fi
if [ -z ${EXECUTOR_MEMORY+x} ]; then EXECUTOR_MEMORY=250g ; fi
if [ -z ${EXECUTOR_MEMORY_OVERHEAD+x} ]; then EXECUTOR_MEMORY_OVERHEAD=450g ; fi
if [ -z ${DEFAULT_PARALLELISM+x} ]; then DEFAULT_PARALLELISM=10000 ; fi

if [ -z ${JBID+x} ]; then
    echo Please set the JBID environment variable. Exiting...
    exit 1
fi

# Get these variables out of the config file if they are present.

yarn application -list > /tmp/yarnlist$$ 2>&1
if grep '^Total number.*:0' /tmp/yarnlist$$ ; then
    /bin/rm /tmp/yarnlist$$
    echo No other Yarn jobs are running.
else
    tput rev			# reverse video
    echo OTHER YARN JOBS ARE RUNNING
    tput sgr0			# regular video
    cat /tmp/yarnlist$$
    /bin/rm /tmp/yarnlist$$
    echo
    tput setaf 5		# purple
    echo Type return to continue execution, or control-C to abort.
    tput sgr0			# regular video
    read
fi


## Decide how many executors to run based on how many nodes are avaialble
NODES=`yarn node -list 2>/dev/null | grep RUNNING | wc -l`
echo AVAILABLE NODES: $NODES

# Note EXECUTOR_CORES * EXECUTORS_PER_NODE should be less than 64, which is how many cores we have per node
if [ $(($EXECUTOR_CORES * $EXECUTORS_PER_NODE > 92)) == 1 ] ; then
   echo WARNING: cores per node are over-provisioned.
   echo Type control-C now to stop....
   for i in 5 4 3 2 1 ; do
       echo $i ...
       sleep 1
   done
   echo Continuing with over-provisioned core nodes.
fi

if [ -z ${NUM_EXECUTORS+x} ]; then
   NUM_EXECUTORS=$(( $EXECUTORS_PER_NODE * $NODES ))
fi

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
   *) echo "Unknown parameter: $1";exit 1;;
esac; shift; done


## Set up the variables
##
CONFIG_DIR=configs
DEFAULT_OUTPUT=das_output.out

# for CORE=3 m4.16xlarge and MASTER = m4.2xlarge
# maxResultsSize is the max that will be sent to the driver. It must fit in memory

if [ x$SPARK_RESOURCES = x ]; then
    SPARK_RESOURCES="--driver-memory $DRIVER_MEMORY \
 --num-executors $NUM_EXECUTORS \
 --executor-memory $EXECUTOR_MEMORY --executor-cores $EXECUTOR_CORES \
 --driver-cores $DRIVER_CORES --conf spark.driver.maxResultSize=0g --conf spark.executor.memoryOverhead=$EXECUTOR_MEMORY_OVERHEAD"

    echo DRIVER_MEMORY: $DRIVER_MEMORY
    echo NUM_EXECUTORS: $NUM_EXECUTORS
    echo EXECUTOR_MEMORY: $EXECUTOR_MEMORY
    echo EXECUTOR_MEMORY_OVERHEAD: $EXECUTOR_MEMORY_OVERHEAD
    echo EXECUTOR_CORES: $EXECUTOR_CORES
    echo DRIVER_CORES: $DRIVER_CORES
else
    echo SPARK_RESOURCES: $SPARK_RESOURCES
fi

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
  echo Please specify a config file.
  exit 1
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

## Now that we have a config file, try to find the python
## Notice that we assume that we are using the same

## Make sure that das2020_driver.py supports --get
if ! python das2020_driver.py --get python:executable:$PYSPARK_PYTHON $config >/dev/null ; then
    echo das2020_driver.py does not support --get or an included config file not found >/dev/stderr
    exit 1
fi

export PYSPARK_PYTHON=`python das2020_driver.py --get python:executable:$DEFAULT_PYSPARK_PYTHON $config`
export PYSPARK_DRIVER_PYTHON=`python das2020_driver.py --get python:executable:$DEFAULT_PYSPARK_DRIVER_PYTHON $config`

## Get a mission name if one has not yet been set
if [ -z ${MISSION_NAME+x} ]; then
    export MISSION_NAME=`python programs/random_mission.py`
else
    echo using MISSION_NAME=$MISSION_NAME
fi

echo === Running DAS ===
echo config=$config
echo PYSPARK_PYTHON=$PYSPARK_PYTHON
echo START=`date -I`
echo CWD=$PWD
echo ===================
export PATH=$PATH:$PWD

## Come up with a logfile
seconds_after_midnight=`date -d "1970-01-01 UTC $(date +%T)" +%s`
minutes_after_midnight=$((seconds_after_midnight/60))
export LOGFILE_NAME="logs/DAS-`date -I`_`printf %04d $minutes_after_midnight`_$MISSION_NAME.log"


## Create the DAS command
# https://stackoverflow.com/questions/45269660/apache-spark-garbage-collection-logs-for-driver
#Add for verbose Java gargage collection (the output will be in stdout on worker nodes)
#-XX:+PrintGCDetails,-XX:+PrintGCTimeStamps
#-XX:+UseG1GC - this is a different collector, can help in some situations where garbage collection is the bottleneck.
#Note that with large executor heap sizes, it may be important to increase the G1 region size with -XX:G1HeapRegionSize
#-Xmn=4/3*E where E is estimated Eden size sets the memory dedicated to the Young generation (extra 1/3 is for Survivor1 and Survivor2)

#--conf spark.memory.fraction=0.2
#--conf spark.executor.pyspark.memory=100K

#--conf spark.default.parallelism=1000
#--conf spark.sql.execution.arrow.enabled=true
#--conf spark.serializer=org.apache.spark.serializer.KryoSerializer
#--conf spark.default.parallelism=$DEFAULT_PARALLELISM

spark_submit="spark-submit $SPARK_RESOURCES
    --conf spark.local.dir=/mnt/tmp/
    --conf spark.eventLog.enabled=true
    --conf spark.eventLog.dir=hdfs:///var/log/spark/apps/
    --conf spark.submit.deployMode=client
    --conf spark.network.timeout=3000
    --conf spark.driver.extraJavaOptions=-Dlog4j.configuration=file:log4j.configuration.xml
    --conf spark.executor.extraJavaOptions=-Dlog4j.configuration=file:log4j.configuration.xml
    --conf spark.driver.extraJavaOptions=-Dlog4j.configuration=file:log4j.properties
    --conf spark.executor.extraJavaOptions=-Dlog4j.configuration=file:log4j.properties
    --conf spark.task.maxFailures=8
    --conf spark.scheduler.listenerbus.eventqueue.capacity=50000
    --conf spark.serializer=org.apache.spark.serializer.KryoSerializer
    --conf spark.sql.execution.arrow.enabled=true
    --files "./log4j.configuration.xml"
    --files "./log4j.properties"
    --master yarn
    --name $JBID:$MISSION_NAME"
python_cmd="das2020_driver.py $config --loglevel DEBUG --logfilename $LOGFILE_NAME"

#extra_java_options="-XX:+PrintGCTimeStamps -XX:+PrintGCDetails -verbose:gc "
extra_java_options="-XX:+UseG1GC -XX:+UnlockDiagnosticVMOptions -XX:+G1SummarizeConcMark -XX:InitiatingHeapOccupancyPercent=35 -verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps -XX:OnOutOfMemoryError='kill -9 %p'"

echo
echo
echo $spark_submit --conf "spark.executor.extraJavaOptions=$extra_java_options"  $python_cmd
echo
echo

## mission failure command
mission_failure() {
    echo =========================
    echo ==== MISSION FAILURE ====
    echo =========================
    date
    echo $MISSION_NAME failed with exit code $1
    echo processing stops.
    echo
    echo Incomplete spark logs might be found at /mnt/tmp/logs/{applicationId}{inProgressFlag}
    echo
    python programs/dashboard.py --exit_code=$1
    exit 1
}



## The command to run the cluster
runcluster() {
    MAX_FILE_SIZE=20000000
    echo $spark_submit --conf "spark.executor.extraJavaOptions=$extra_java_options" $python_cmd | python programs/dashboard.py --spark_submit
    $spark_submit --conf "spark.executor.extraJavaOptions=$extra_java_options" $python_cmd || mission_failure $?
    echo $0: PID $$ done at `date`. DAS is finished. Uploading Yarn logs...
    ZIPFILE=`echo $LOGFILE_NAME | sed 's/.log$/.zip/'`
    YARN_LOGFILE=`echo $LOGFILE_NAME | sed 's/.log$/_yarnlog.txt/'`
    APPLICATION_ID=`grep applicationId: $LOGFILE_NAME | head -1 | cut --delimiter=" " --fields=6`
    yarn logs -applicationId $APPLICATION_ID > $YARN_LOGFILE
    head -10000 $YARN_LOGFILE > $YARN_LOGFILE.head.txt
    tail -10000 $YARN_LOGFILE > $YARN_LOGFILE.tail.txt
    gzip -1 $YARN_LOGFILE
    (cd logs; zip -uv `basename $ZIPFILE` `basename $YARN_LOGFILE`*)
    aws s3 cp $ZIPFILE $DAS_S3ROOT/rpc/upload/logs/
}

if [ $FG == Y ]; then
    echo "Running in foreground"
    runcluster
else
    # No longer uses nohup because nohup cannot handle functions
    runcluster >$output 2>&1 </dev/null &
    echo PID $$ done at `date`. DAS continues executing...
    echo watch output with:
    echo tail -f $output
fi
