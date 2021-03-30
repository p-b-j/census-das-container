#!/bin/bash

source util/setup_env.sh

# Run standalone config
cd das_decennial
spark-submit das2020_driver.py ../config/standalone.ini --loglevel DEBUG --logfilename ~/das_log.log
