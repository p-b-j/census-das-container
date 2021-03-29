# Run a DAS job with:
# [config=configfile] [output=outputfile] bash run_cluster.sh
#
# This uses all resources

echo Running DAS on `date` $config

#zip the code
ZIPFILE=../das_decennial.zip
export ZIPFILE
zip -r -q $ZIPFILE . -i '*.py' '*.sh' '*.ini'

CONFIG_DIR=configs
DEFAULT_CONFIG=test_RA_config_cluster.ini

DEFAULT_OUTPUT=das_output.out


#output=$2
if [ x$output = x ]; then
  output="$DEFAULT_OUTPUT"
fi

#config=$1
if [ x$config = x ]; then
  config="$DEFAULT_CONFIG"
fi

# If a slash was not provided, prepend the CONFIG_DIR
if [[ "$config" == *\/* ]] || [[ "$config" == *\\* ]]
then
  echo full path provided for config file $config
else
  config=$CONFIG_DIR/$config
fi

echo Running DAS with config $config
## Check to make sure the config file exists
if [ ! -r "$config" ]; then
  echo Cannot read DAS config file $config
  exit 1
fi

export TERM=xterm

## This program runs the DAS framework driver with the config file specified.
## We use qsub because of the memory and CPU requirements. Otherwise, the job
## can be killed.  --py-files das_framework/driver.py
echo starting at `date`
echo $PWD

export PATH=$PATH:$PWD

echo PID $$ starting at `date`

#nohup 2>&1 spark-submit --py-files $ZIPFILE --driver-memory 200g --num-executors 72 --executor-memory 50g --executor-cores 10 --driver-cores 50  --conf spark.driver.maxResultSize=0g --conf spark.executor.memoryOverhead=10g --conf spark.local.dir="/mnt/tmp/" --conf spark.eventLog.enabled=true --conf spark.eventLog.dir="/mnt/tmp/logs/" --master yarn --conf spark.submit.deployMode=client --conf spark.network.timeout=3000 das_framework/driver.py $config --loglevel DEBUG &> $output &

nohup 2>&1 spark-submit --py-files $ZIPFILE --driver-memory 200g --num-executors 6 --executor-memory 50g --executor-cores 10 --driver-cores 50  --conf spark.driver.maxResultSize=0g --conf spark.executor.memoryOverhead=10g --conf spark.local.dir="/mnt/tmp/" --conf spark.eventLog.enabled=true --conf spark.eventLog.dir="/mnt/tmp/logs/" --master yarn --conf spark.submit.deployMode=client --conf spark.network.timeout=3000 das_framework/driver.py $config --loglevel DEBUG &> $output &

echo PID $$ done at `date`
