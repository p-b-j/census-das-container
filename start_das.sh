#!/bin/bash

# Env setup
export DAS_VERSION="Standalone"
export GRB_LICENSE_FILE="${HOME}/gurobi.lic"
export GUROBI_HOME="/usr/local/gurobi911/linux64"
export LD_LIBRARY_PATH="/usr/local/gurobi911/linux64/lib:/usr/local/hadoop-3.1.4/lib/native"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/spark/spark-2.4.7-bin-hadoop2.7/bin:/usr/local/anaconda3/bin:/usr/local/gurobi911/linux64/bin:/usr/local/gurobi911/linux64/bin:/usr/local/anaconda3/bin"
export PYSPARK_DRIVER_PYTHON="/usr/local/anaconda3/bin/python3.6"
export PYSPARK_PYTHON="/usr/local/anaconda3/bin/python3.6"
export PYTHONPATH="/usr/local/spark/spark-2.4.7-bin-hadoop2.7/python:"
export SPARK_HOME="/usr/local/spark/spark-2.4.7-bin-hadoop2.7"

# Run standalone config
cd census2020-das-e2e
./run_1940_standalone.sh
