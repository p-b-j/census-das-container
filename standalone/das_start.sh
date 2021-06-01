#!/usr/bin/bash

source util/load_config.sh

if [ -f ${HOME}/das_log.release.zip ]
then
    rm ${HOME}/das_log.release.zip
fi

${singularity_cmd} ./standalone/singularity_scripts/das_start.sh
