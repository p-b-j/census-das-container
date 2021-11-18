#!/usr/bin/bash

source util/load_config.sh

# Memory and cores configurable in das_container.conf 
${singularity_cmd} ./cluster/singularity_scripts/worker_start_spark.sh \
    -m "${cluster_worker_memory}" \
    -c "${cluster_worker_cores}" \
    "${coord_hostname}:7077"