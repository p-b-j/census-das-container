#!/bin/bash

source util/setup_env.sh

# Run standalone config
cd census2020-das-e2e
./run_1940_cluster.sh $1
