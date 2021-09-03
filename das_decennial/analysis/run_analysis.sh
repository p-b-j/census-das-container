# Example run command: analysis=analysis_scripts/lecle301/Executive_Priority_Tabulations.py bash run_analysis.sh

echo ""
echo "Starting Analysis..."
echo ""
echo "Zipping das_decennial..."
echo ""

if [ ! -r run_analysis.sh ]; then
    echo "Start this script when run_analysis.sh is the current directory."
    exit 1
fi

# zip the code
cd ..

ZIPFILE=/mnt/users/$JBID/das_analysis.zip
export ZIPFILE
#export MISSION_NAME="temp_mission_name"
#export LOGFILE_NAME="/mnt/users/${JBID}/geolevel_dependen_queries/das_decennial/analysis/temp_log3.txt"
#export DAS_RUN_UUID='temp_uuid_123'

# added -FS option to add new files, update existing files, and delete old files when creating the zip file
# https://superuser.com/questions/350991/how-to-overwrite-existing-zip-file-instead-of-updating-it-in-info-zip
zip -FS -r -q $ZIPFILE . -i '*.py' '*.sh' '*.ini'

## Get a mission name

if [ -d analysis ]; then
    echo cd analysis
    cd analysis
fi

DASHBOARD="../programs/dashboard.py"

## Start the mission.
## This creates MISSION_NAME, LOGFILE_NAME and DAS_RUN_UUID
##
$(python3 $DASHBOARD --mission_start --mission_type analysis)


# make the logs directory (if it doesn't exist)
mkdir -p $(dirname $LOGFILE_NAME)

export ANALYSIS_SCRIPT=$analysis

echo "  Zip file being sent to Spark:  ${ZIPFILE}"
echo "  Analysis Script to run:        ${ANALYSIS_SCRIPT}"
echo "  Log file location:             ${LOGFILE_NAME}"
echo "  Mission Name:                  ${MISSION_NAME}"

RUN_BG=TRUE                     # run in the background

# 200g
DRIVER_MEMORY=100g
# 60
NUM_EXECUTORS=
# 10g
EXECUTOR_MEMORY=24g
# 60
EXECUTOR_CORES=
# 50
DRIVER_CORES=
# 10g
MEMORY_OVERHEAD=24g
# 200
SHUFFLE_PARTITIONS=750
# 10000
LISTENER_BUS=100000

cmd="spark-submit --py-files ${ZIPFILE} "

if [ ! -z $DRIVER_MEMORY ]
then
    cmd+="--driver-memory $DRIVER_MEMORY "
fi

if [ ! -z $NUM_EXECUTORS ]
then
    cmd+="--num-executors $NUM_EXECUTORS "
fi

if [ ! -z $EXECUTOR_MEMORY ]
then
    cmd+="--executor-memory $EXECUTOR_MEMORY "
fi

if [ ! -z $EXECUTOR_CORES ]
then
    cmd+="--executor-cores $EXECUTOR_CORES "
fi

if [ ! -z $DRIVER_CORES ]
then
    cmd+="--driver-cores $DRIVER_CORES "
fi

if [ ! -z $MEMORY_OVERHEAD ]
then
    cmd+="--conf spark.executor.memoryOverhead=$MEMORY_OVERHEAD "
fi

if [ ! -z $SHUFFLE_PARTITIONS ]
then
    cmd+="--conf spark.sql.shuffle.partitions=$SHUFFLE_PARTITIONS "
fi

if [ ! -z $LISTENER_BUS ]
then
    cmd+="--conf spark.scheduler.listenerbus.eventqueue.capacity=$LISTENER_BUS "
fi

NODES=`yarn node -list 2>/dev/null | grep RUNNING | wc -l`

#cmd+="--conf spark.driver.maxResultSize=0g --conf spark.local.dir='/mnt/tmp/' --conf spark.eventLog.enabled=true --conf spark.eventLog.dir='/mnt/tmp/logs/' --master yarn --conf spark.submit.deployMode=client --conf spark.network.timeout=100000000 $ANALYSIS_SCRIPT --logname $LOGFILE_NAME --num_core_nodes $NODES --analysis_script $ANALYSIS_SCRIPT &> $LOGFILE_NAME &"

SPARK_LOCAL_DIR="/mnt/tmp"
SPARK_EVENTLOG_DIR="/mnt/tmp/logs/"

cmd+="--conf spark.driver.maxResultSize=0g --conf spark.local.dir=$SPARK_LOCAL_DIR --conf spark.eventLog.enabled=true --conf spark.eventLog.dir=$SPARK_EVENTLOG_DIR --master yarn --conf spark.submit.deployMode=client --conf spark.network.timeout=100000000 --conf spark.scheduler.listenerbus.eventqueue.capacity=100000000 $ANALYSIS_SCRIPT --logname $LOGFILE_NAME --num_core_nodes $NODES --analysis_script $ANALYSIS_SCRIPT"

echo Spark Submit command used:
echo $cmd
echo


## The command to run the cluster
runcluster() {
    echo $cmd | python3 $DASHBOARD --spark_submit --mission_type=analysis
    $cmd
    echo spark-submit finished at `date`
    python3 $DASHBOARD --mission_stop --mission_type=analysis

    echo $0: PID $$ done at `date`. Analysis is finished.

    # get the s3 save location
    save_location_s3="___ANALYSIS_RESULTS_LOCATION_S3___: "
    check="grep $save_location_s3 $LOGFILE_NAME"
    loc=$($check)
    save_location_s3=${loc:${#save_location_s3}}
    echo
    echo The S3 location for this Analysis is:
    echo $save_location_s3
    echo

    # get the linux save location
    save_location_linux="___ANALYSIS_RESULTS_LOCATION_LINUX___: "
    check="grep $save_location_linux $LOGFILE_NAME"
    loc=$($check)
    echo
    save_location_linux=${loc:${#save_location_linux}}
    echo The Linux location for this Analysis is:
    echo $save_location_linux
    echo

    save_log_to_s3="___SAVE_LOG_TO_S3___"
    check="grep -q $save_log_to-s3 $LOGFILE_NAME"
    if $check; then
        logloc="${save_location_s3}log.log"
        echo
        echo Saving the log in S3 here:
        echo $logloc
        echo
        aws s3 cp $LOGFILE_NAME $logloc
    fi

    save_log_to_linux="___SAVE_LOG_TO_LINUX___"
    check="grep -q $save_log_to_linux $LOGFILE_NAME"
    if $check; then
        logloc="${save_location_linux}log.log"
        echo
        echo Saving the log in Linux here:
        echo $logloc
        echo
        cp $LOGFILE_NAME $logloc
    fi

    zip_results_to_s3="___ZIP_RESULTS_TO_S3___"
    check="grep -q $zip_results_to_s3 $LOGFILE_NAME"
    if $check; then
        reszip="${save_location_linux}zip.zip"
        echo
        echo Zipping the analysis results here:
        echo $reszip
        echo
        zip -r $reszip $save_location_linux
        awszip="${save_location_s3}local_results.zip"
        echo Copying the zip file to S3 here:
        echo $awszip
        echo
        aws s3 cp $reszip $awszip
    fi

    echo End of Analysis Run Script at `date`
}

if [ $RUN_BG = TRUE ]; then
    runcluster >$LOGFILE_NAME 2>&1 </dev/null &
    echo PID $$ done at `date`. Analysis continues running...
    echo
    echo Use the following command to look at the log:
    echo tail -f $LOGFILE_NAME
    echo
else
    echo "Running in foreground"
    runcluster
fi
