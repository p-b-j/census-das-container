#!/bin/bash
# Run a DAS job with:
# [config=configfile] [output=outputfile] bash run_cluster.sh  [--all] [--fg|--bg] [--help]
#
# --fg   - run DAS in the foreground
# --bg   - run DAS in background withoutput to $output
# --fgo  - run DAS in foreground with no capture of output
# --help - print help
# --all  - use all resources
# --dry-run - specify the --dry-run option
# --pdf_config - only generate a PDF certificate of the config file
# --dry-read - specifies the --dry-read file
# --dry-write  - specifies the --dry-write file
#
# NOTE: This is the master script for running a cluster.
#       Your run scripts should just set variables and then call this one.
#
#ENDOFHELP

VERSION=1.6

show_help() {
    SCRIPT=$(readlink -f $0)  # script fill path
    HELPLINES=$(grep -nhT ENDOFHELP $SCRIPT | head -1 | cut -f 1) # line number help appears on
    head --lines ${HELPLINES} $SCRIPT
    exit 0
}

PYTHON=$PYSPARK_DRIVER_PYTHON
SPARK_SUBMIT=/usr/bin/spark-submit
LOGLEVEL="--loglevel DEBUG"

# A righteous umask
umask 022


#
# Process the command-line options that are passed in as variables
#

# Option processing
# https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
# Process arguments
RUNMODE=fg
ALL=N
DEFAULT_OUTPUT=das_output.out
DRY=''
PDF_ONLY=''
SPARK=YES

while [[ "$#" > 0 ]];
do
    case $1 in
   --bg)      RUNMODE=bg;;
   --fg)      RUNMODE=fg;;
   --fgo)     RUNMODE=fgo;;
   --dry-run)   DRY="$DRY--dry-run";;
   --dry-read)  DRY="$DRY --dry-read $2"  ; shift ;;
   --dry-write) DRY="$DRY --dry-write $2" ; shift ;;
   --pdf_only)  PDF_ONLY='--pdf_only certificate.pdf' ;;
   --pdf_only) PDF_ONLY='--pdf_only certificate.pdf' ;;
   --help)      show_help; exit 0;;
   *) echo "Unknown parameter: $1"; show_help; exit 1;;
    esac;
    shift;
done

#
# check to see if the 'output' and 'config' environment variables were not set.
# If they were not set, generate an appropriate error.
# Note that these environment variables are lower case for historical reasons.
#
if [ x$output = x ]; then
  output="$DEFAULT_OUTPUT"
  echo using default output $output
fi


################################################################
#
# Run enviornment
CLUSTER_INFO=../bin/cluster_info.py
if [ ! -r $CLUSTER_INFO ]; then
    CLUSTER_INFO=/mnt/gits/das-vm-config/bin/cluster_info.py
fi
get_ci() {
    $PYTHON $CLUSTER_INFO --get $1
}

if [ -z ${DAS_ENVIRONMENT+x} ]; then
    echo Please set the DAS_ENVIRONMENT variable. Exiting...
    exit 1
fi

if [ $DAS_ENVIRONMENT != ITE ]; then
    # Note in ITE
    echo operating in $DAS_ENVIRONMENT
    export JBID=bond007
    export DAS_HOME=/mnt/gits/das-vm-config
else
    if [ -z ${JBID+x} ]; then
        echo Please set the JBID environment variable. Exiting...
        exit 1
    fi

    if [ -z ${DAS_HOME+x} ]; then
        echo DAS_HOME not set. Assuming /mnt/gits/das-vm-config
        export DAS_HOME=/mnt/gits/das-vm-config
    fi
fi

export DAS_OBJECT_CACHE=$(get_ci DAS_S3MGMT)/$(get_ci DAS_OBJECT_CACHE_BASE)
export DVS_OBJECT_CACHE=$(get_ci DAS_S3MGMT)/$(get_ci DVS_OBJECT_CACHE_BASE)
export DAS_S3MGMT_ACL=$(get_ci DAS_S3MGMT_ACL)
export DVS_AWS_S3_ACL=$(get_ci DAS_S3MGMT_ACL)
MISSION_REPORT="https://dasexperimental.ite.ti.census.gov/app/mission"


# Command to send things to the dashboard:
send_dashboard() {
    $PYTHON programs/dashboard.py $* || exit 1
}


################################################################
# Validation

## First make sure that there are no syntax or import errors
if ! $PYTHON das2020_driver.py --help >/dev/null ; then
    echo das2020_driver.py contains syntax errors. STOP. >/dev/stderr
    exit 1
fi

if [ x$config = x ]; then
  echo Please specify a config file.
  exit 1
fi

################################################################
#
# Config file validation.
# Make sure we have a config file and that it is valid.
#
CONFIG_DIR=configs

#
# If a slash was not provided in the config file name, prepend the CONFIG_DIR
#
if [[ $config == */* ]] ; then
  echo Config specified with full path: $config
else
  config=$CONFIG_DIR/$config
fi

## Check to make sure the config file exists
if [ ! -r "$config" ]; then
  echo Cannot read DAS config file $config
  exit 1
else
    echo Using config file: $config
fi

if [ -z $NO_CHECK_CLEAN ]; then
    unclean=$(git status --porcelain| grep -v das_framework | grep -v '^\?')
    if [ ! -z "$unclean" ]; then
        echo
        python3 programs/colors.py CBLUEBG CWHITE --message="git is not clean. Will not run DAS."
        echo
        git status | grep -v das_framework
        echo
        python3 programs/colors.py CBLUEBG CWHITE --message="Please commit modified files."
        echo
        echo NOTE: You can suppress this check by setting the environment variable NO_CHECK_CLEAN
        exit 1
    fi
fi

# Make sure that there are no syntax or import errors in the python code
if ! $PYTHON das2020_driver.py --help >/dev/null ; then
    echo das2020_driver.py contains syntax or import errors. STOP. >/dev/stderr
    exit 1
fi

################################################################
#
# Spark configuration
#
# Set these variables if they are not set

YARNLIST=/tmp/yarnlist$$
yarn application -list > $YARNLIST 2>&1
if grep '^Total number.*:0' $YARNLIST ; then
    /bin/rm $YARNLIST
    echo No other Yarn jobs are running.
else
    tput rev          # reverse video
    echo OTHER YARN JOBS ARE RUNNING
    tput sgr0         # regular video
    cat $YARNLIST
    echo

    # See if we are running in LightsOut
    LightsOut=$(HTTPS_PROXY=$BCC_HTTPS_PROXY aws emr describe-cluster --cluster-id $CLUSTERID \
        --query 'Cluster.[Tags[?Key==`LightsOut`].Value[][]]' --output text)
    if [ "${LightsOut:0:1}" = "T" ]; then
        echo RUNNING LIGHTS OUT. CONTINUING
    else
        tput setaf 5  # purple
        echo Type return to continue execution, or control-C to abort.
        tput sgr0     # regular video
        read
    fi
fi
/bin/rm -f $YARNLIST

#
if [ -z ${EXECUTOR_CORES+x} ];           then EXECUTOR_CORES=4 ; fi
if [ -z ${EXECUTORS_PER_NODE+x} ];       then EXECUTORS_PER_NODE=4 ; fi
if [ -z ${DRIVER_CORES+x} ];             then DRIVER_CORES=10 ; fi
if [ -z ${DRIVER_MEMORY+x} ];            then DRIVER_MEMORY=5g ; fi
if [ -z ${EXECUTOR_MEMORY+x} ];          then EXECUTOR_MEMORY=16g ; fi
if [ -z ${EXECUTOR_MEMORY_OVERHEAD+x} ]; then EXECUTOR_MEMORY_OVERHEAD=20g ; fi
if [ -z ${DEFAULT_PARALLELISM+x} ];      then DEFAULT_PARALLELISM=1000 ; fi


## Decide how many executors to run based on how many nodes are avaialble
NODES=`yarn node -list 2>/dev/null | grep RUNNING | wc -l`
echo AVAILABLE NODES: $NODES

# Note EXECUTOR_CORES * EXECUTORS_PER_NODE should be less than 96, which is how many cores we have per node
if [ $(($EXECUTOR_CORES * $EXECUTORS_PER_NODE > 96)) == 1 ] ; then
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

# for CORE=3 m4.16xlarge and MASTER = m4.2xlarge
# maxResultsSize is the max that will be sent to the driver. It must fit in memory

# If SPARK_RESOURCES is set, use that.
# Otherwise create the string based on our values set above

if [ x$SPARK_RESOURCES = x ]; then
    SPARK_RESOURCES="--driver-memory $DRIVER_MEMORY
 --num-executors $NUM_EXECUTORS
 --executor-memory $EXECUTOR_MEMORY --executor-cores $EXECUTOR_CORES
 --driver-cores $DRIVER_CORES --conf spark.driver.maxResultSize=0g
 --conf spark.executor.memoryOverhead=$EXECUTOR_MEMORY_OVERHEAD"

    echo DRIVER_MEMORY: $DRIVER_MEMORY
    echo NUM_EXECUTORS: $NUM_EXECUTORS
    echo EXECUTOR_MEMORY: $EXECUTOR_MEMORY
    echo EXECUTOR_MEMORY_OVERHEAD: $EXECUTOR_MEMORY_OVERHEAD
    echo EXECUTOR_CORES: $EXECUTOR_CORES
    echo DRIVER_CORES: $DRIVER_CORES
else
    echo SPARK_RESOURCES: $SPARK_RESOURCES
fi


#
# Now that we have a config file, try to find the python
# Notice that we assume that we are using the same
#
# Make sure that das2020_driver.py supports --get
#
if ! $PYTHON das2020_driver.py --get python:executable:$PYSPARK_PYTHON $config >/dev/null ; then
    echo das2020_driver.py does not support --get or an included config file not found >/dev/stderr
    exit 1
fi

# get_config():
# get a value out of the config file
# usage:
# get_config <section>:<option>:<default>
get_config() {
    $PYTHON das2020_driver.py --get $1 $config
}

export PYSPARK_PYTHON=$(get_config python:executable:$PYSPARK_PYTHON)
export PYSPARK_DRIVER_PYTHON=$(get_config python:executable:$PYSPARK_DRIVER_PYTHON)

echo PYSPARK_PYTHON: $PYSPARK_PYTHON


if [ ! -r $PYSPARK_PYTHON ]; then
    echo "Specified PYSPARK_PYTHON version is not installed: $PYSPARK_PYTHON "
    exit 1
fi

if [ ! -r $PYSPARK_DRIVER_PYTHON ]; then
    echo "Specified PYSPARK_DRIVER_PYTHON version is not installed: $PYSPARK_PYTHON "
    exit 1
fi

################################################################
## Resize the cluster if requested
##
resize_cmd=''
emr_task_nodes=$(get_config setup:emr_task_nodes:"")
echo emr_task_nodes: $emr_task_nodes
if [[ ! -z $emr_task_nodes ]]; then
    resize_cmd+=" --task $emr_task_nodes "
fi

emr_core_nodes=$(get_config setup:emr_core_nodes:"")
if [[ ! -z $emr_core_nodes ]]; then
    resize_cmd+=" --core $emr_core_nodes "
fi

if [[ ! -z $emr_core_nodes ]]; then
    echo resizing cluster $resize_cmd
    $PYTHON programs/emr_control.py $resize_cmd | tee /tmp/resize$$
    grep RESIZE /tmp/resize$$ && (echo Initiating cluster resizing. Waiting 60 seconds; sleep 60)
    /bin/rm -f /tmp/resize$$
fi


################################################################
## Run the DAS
##

## Start the mission
$($PYTHON programs/dashboard.py --mission_start)

echo
echo === Running DAS ===
echo config=$config
echo START=`date -I`
echo CWD=$PWD
echo ===================
export PATH=$PATH:$PWD

send_dashboard --log MISSION $MISSION_NAME $config

# If logs does not exist, make it a symlink to /mnt/logs
if [ ! -e logs ] ; then
    mkdir -p /mnt/logs || exit 1
    ln -s /mnt/logs logs || exit 1
fi

TESTFILE=logs/test-$$
# Verify we can write to logs
echo Verifying we can write to logs
touch $TESTFILE
rm $TESTFILE
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

#extra_java_options="-XX:+PrintGCTimeStamps -XX:+PrintGCDetails -verbose:gc "
javaconf="--conf"
extra_java_options="-XX:+UseG1GC -XX:+UnlockDiagnosticVMOptions -XX:+G1SummarizeConcMark -XX:InitiatingHeapOccupancyPercent=35 -verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps -XX:OnOutOfMemoryError='kill -9 %p'"
echo Starting spark
spark_submit="$SPARK_SUBMIT $SPARK_RESOURCES
    --conf spark.driver.extraJavaOptions=-Dlog4j.configuration=file:log4j.configuration.xml
    --conf spark.driver.extraJavaOptions=-Dlog4j.configuration=file:log4j.properties
    --conf spark.eventLog.dir=hdfs:///var/log/spark/apps/
    --conf spark.eventLog.enabled=true
    --conf spark.executor.extraJavaOptions=-Dlog4j.configuration=file:log4j.configuration.xml
    --conf spark.executor.extraJavaOptions=-Dlog4j.configuration=file:log4j.properties
    --conf spark.hadoop.fs.s3.maxRetries=50
    --conf spark.local.dir=/mnt/tmp/
    --conf spark.network.timeout=3000
    --conf spark.scheduler.listenerbus.eventqueue.capacity=50000
    --conf spark.serializer=org.apache.spark.serializer.KryoSerializer
    --conf spark.sql.execution.arrow.enabled=true
    --conf spark.submit.deployMode=client
    --conf spark.task.maxFailures=8
    --files ./log4j.configuration.xml
    --files ./log4j.properties
    --master yarn
    --deploy-mode client
    --name $JBID:$MISSION_NAME "

python_cmd="das2020_driver.py $config $LOGLEVEL --logfilename $LOGFILE_NAME $DRY $PDF_ONLY"

# Print the command line and send it to the dashboard:

COMMAND_LINE=$(echo $spark_submit --conf "spark.executor.extraJavaOptions=$extra_java_options" $python_cmd)
echo
echo $COMMAND_LINE
echo $COMMAND_LINE | send_dashboard --spark_submit
echo

## save yarn logs
save_yarn_logs() {
    YARN_LOGFILE=`echo $LOGFILE_NAME | sed 's/.log$/_yarnlog.txt/'`
    APPLICATION_ID=`grep applicationId: $LOGFILE_NAME | head -1 | cut --delimiter=" " --fields=6`
    echo Saving yarn logs to local $YARN_LOGFILE
    yarn logs -applicationId $APPLICATION_ID > $YARN_LOGFILE
    ls -l $YARN_LOGFILE
    echo Compressing yarn logs...
    head -10000 $YARN_LOGFILE > $YARN_LOGFILE.head.txt
    tail -10000 $YARN_LOGFILE > $YARN_LOGFILE.tail.txt
    gzip -1 $YARN_LOGFILE
    ls -l $YARN_LOGFILE*
}

upload_logs() {
    echo upload_logs
    # nicely format the DFXML file for viewing
    DFXML_FILE=logs/$(basename $LOGFILE_NAME .zip).dfxml
    DFXML_PP_FILE=logs/$(basename $LOGFILE_NAME .zip).pp.dfxml
    xmllint -format $DFXML_FILE > $DFXML_PP_FILE

    # Add the log files to the zip file
    ZIP_FILENAME=$(basename $LOGFILE_NAME .log).zip
    (cd logs; zip -uv $ZIP_FILENAME $(basename $LOGFILE_NAME .log)*)

    # Show the contents of the ZIP file
    echo
    unzip -l logs/$ZIP_FILENAME

    # These individual POINTs may seem odd, but when I took them out the mission report didn't
    # show up. I think that it's some buffer not getting flushed before the monitoring program
    # exists. So just leave them in. There is so much other junk.

    echo POINT1

    # Upload to s3
    aws s3 cp --no-progress logs/$ZIP_FILENAME $DAS_S3ROOT/rpc/upload/logs/

    echo POINT2

    DAS_S3=$(echo $DAS_S3ROOT | sed 's;s3://;;')

    echo POINT3

    END_TIME=$(date -Iseconds)

    echo POINT4

    # Get S3 errors from AWS CloudWatch, print them, and optionally send them to the log
    python3 programs/aws_errors.py $START_TIME $END_TIME --upload
    echo ===
    echo ===
    echo mission report:   $MISSION_REPORT/$MISSION_NAME/report
    echo ===
    echo ===
}

##
## mission failure command
## Todo: refactor this so that we always save_yarn_logs and upload_logs and *then* check the ailure code.
##
mission_failure() {
    echo =========================
    echo ==== MISSION FAILURE ====
    echo =========================
    date
    echo $MISSION_NAME failed with exit code $1
    echo processing stops.
    echo
    save_yarn_logs
    echo Incomplete spark logs might be found at /mnt/tmp/logs/{applicationId}{inProgressFlag}
    echo
    upload_logs
    echo
    send_dashboard --exit_code=$1
    echo mission report:   $MISSION_REPORT/$MISSION_NAME/report
    exit 1
}

## The command to run the cluster, make the zipfile, and upload the zipfile to S3
runcluster() {
    mkdir -p /mnt/logs
    START_TIME=$(date -Iseconds)
    mkdir -p $(dirname $LOGFILE_NAME)
    $spark_submit $python_cmd || mission_failure $?
    save_yarn_logs

    echo $0: PID $$ done at `date`. DAS is finished. Uploading Yarn logs...
    upload_logs
    echo runcluster finished
}

case $RUNMODE in
    bg)
        echo running in background
        (runcluster > >(send_dashboard --tee --code CODE_STDOUT) \
            2> >(send_dashboard --tee --red --code CODE_STDERR)) \
            >$output 2>&1 </dev/null &
        echo PID $$ done at `date`. DAS continues executing...
        echo watch output with:
        echo tail -f $output
        ;;
    fg)
        echo "Running in foreground. Logfile: $LOGFILE_NAME"
        runcluster \
             > >(send_dashboard --tee       --code CODE_STDOUT --stdout --write logs/$(basename $LOGFILE_NAME .log).stdout) \
            2> >(send_dashboard --tee --red --code CODE_STDERR --stderr --write logs/$(basename $LOGFILE_NAME .log).stderr)
        ;;
    fgo)
        echo "Running in foreground with no stdout or stderr capture."
        runcluster
        ;;
    *)
        echo "Unknown run mode: $RUNMODE"
        exit 1
esac

# Finally wait for all subprocesses to finish, so that the prompt is visible
wait
