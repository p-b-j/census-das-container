######################################################
# To Run this script:
#
# cd into das_decennial/analysis/
# analysis=[path to analysis script] bash run_analysis.sh
#
# More info on analysis can be found here:
# https://github.ti.census.gov/CB-DAS/das_decennial/blob/master/analysis/readme.md
######################################################

import das_utils as du
import pandas
import numpy as np

import analysis.tools.sdftools as sdftools
import analysis.tools.treetools as treetools
import analysis.tools.metric_functions as mf

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf
from pyspark.sql import Row

import analysis.tools.setuptools as setuptools
import programs.datadict as dd

import operator


if __name__ == "__main__":
    # setup tools will return the analysis object
    # the analysis object contains the spark session and save location path for this run
    # NOTE: You will need to specify a location for the results to be saved
    #       It should be passed into setuptools.setup, where it will be altered to
    #       add a subdirectory matching the logfile's name

    # Recommended location: "/mnt/users/[your_jbid]/analysis_results/"
    save_location = "/mnt/users/moran331/PL94_P12_Geolevel_TVD/"

    # Most common options are "INFO" and "ERROR"
    # In addition to the analysis print statements...
    # "INFO" provides ALL spark statements, including stage and task info
    # "ERROR" provides only error statements from spark/python
    loglevel = "ERROR"

    analysis = setuptools.setup(save_location=save_location, spark_loglevel="ERROR")

    spark = analysis.spark

    # Specify the experiment paths
    experiment_paths = [
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td10_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td1_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td3_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td025_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td05_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td001_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td01_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td2_1/"
    ]
    schema = C.CC.SCHEMA_PL94_P12

    geolevels = [C.US, C.STATE, C.COUNTY, C.TRACT_GROUP, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDU, C.SLDL, C.CD]

    queries = ["Geolevel_TVD"]
    tvd_groupby = [AC.GEOLEVEL, AC.RUN_ID, AC.PLB, AC.QUERY]

    # a metric builder object is needed for analysis, as experiments are built using it
    mb = sdftools.MetricBuilder()
    mb.add(
        desc = "Geolevel 1-TVD by query",
        metric_function = lambda sdf: sdf.getGeolevels(geolevels).answerQueries(queries).geolevel_tvd(groupby=tvd_groupby)
    )

    # build an experiment and add it to analysis
    analysis.add_experiment(
        name = "PL94_P12_Analysis", # need a unique name for each experiment
        runs = experiment_paths,    # can be either the string paths, or the DASRun objects themselves
        schema = schema,            # the schema (or its name) for the data provided
        metric_builder = mb,        # the metric builder object constructed above
        mtype = AC.SPARSE           # mapper type: we almost always will want to use AC.SPARSE
    )

    # run analysis
    analysis.run_analysis(save_results=True)
