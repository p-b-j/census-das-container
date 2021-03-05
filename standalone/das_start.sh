#!/usr/bin/bash

if [ ! -d "singularity_tmp" ]
then
    echo "Error: could not find singularity_tmp directory"
    echo "Create one by running 'mkdir singularity_tmp'"
    exit 1
fi

singularity exec \
    --home $HOME \
    --bind singularity_tmp:/tmp \
    census_das.img \
    ./standalone/singularity_scripts/das_start.sh
