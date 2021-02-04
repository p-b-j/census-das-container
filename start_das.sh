#!/bin/bash

export DAS_VERSION="Standalone"
export GRB_LICENSE_FILE="${HOME}/gurobi.lic"
export GUROBI_HOME="/usr/local/gurobi911/linux64"
export LD_LIBRARY_PATH="/usr/local/gurobi911/linux64/lib:/usr/local/hadoop-3.1.4/lib/native"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/spark/spark-2.4.7-bin-hadoop2.7/bin:/usr/local/anaconda3/bin:/usr/local/gurobi911/linux64/bin:/usr/local/gurobi911/linux64/bin:/usr/local/anaconda3/bin"
export PYSPARK_DRIVER_PYTHON="/usr/local/anaconda3/bin/python3.6"
export PYSPARK_PYTHON="/usr/local/anaconda3/bin/python3.6"
export PYTHONPATH="/usr/local/spark/spark-2.4.7-bin-hadoop2.7/python:"
export SPARK_HOME="/usr/local/spark/spark-2.4.7-bin-hadoop2.7"

mkdir -p singularity_tmp/spark_tmp
mkdir -p ~/spark-2.4.7-bin-hadoop2.7/conf/

SPARK_CONF_LINE="spark.local.dir ${PWD}/singularity_tmp/spark_tmp"
SPARK_CONF_FILE="${HOME}/spark-2.4.7-bin-hadoop2.7/conf/spark-defaults.conf"
touch $SPARK_CONF_FILE
grep -qxF $SPARK_CONF_LINE $SPARK_CONF_FILE || echo $SPARK_CONF_LINE > $SPARK_CONF_FILE
cd census2020-das-e2e
./run_1940_standalone.sh
