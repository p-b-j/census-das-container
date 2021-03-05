#!/usr/bin/bash

if [ ! -d "singularity_tmp" ]
then
    echo "Error: could not find singularity_tmp directory"
    echo "Create one by running 'mkdir singularity_tmp'"
    exit 1
fi

if [ ! -f "coord_hostname.txt" ]
then
    echo "Error: could note find coord_hostname.txt"
    echo "See instructions in cluster/README.md for setting up this file"
    exit 1
fi

singularity exec \
    --home $HOME \
    --bind singularity_tmp:/tmp \
    census_das.img \
    ./cluster/singularity_scripts/das_start.sh "spark://$(cat coord_hostname.txt | xargs):7077"
