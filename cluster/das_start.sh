#!/usr/bin/bash

source util/load_config.sh

# Memory and cores configurable in das_container.conf 
${singularity_cmd} ./cluster/singularity_scripts/das_start.sh \
    "spark://${coord_hostname}:7077" \
    ${config_file} \
    "${cluster_coord_memory}" \
    "${cluster_coord_overhead}" \
    "${cluster_coord_cores}" \
    "${cluster_worker_memory}" \
    "${cluster_worker_overhead}"
