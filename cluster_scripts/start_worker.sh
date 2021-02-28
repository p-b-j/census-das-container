#!/bin/bash

# Env setup
source cluster_scripts/setup_env.sh

# Start worker
spark-class org.apache.spark.deploy.worker.Worker -d spark_work $@
