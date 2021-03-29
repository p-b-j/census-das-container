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

def geolevel_tvd(sdf, geolevels, queries, groupby=[AC.GEOLEVEL, AC.RUN_ID]):
    """ 
    Calculates the following:
    0. Query answers at the specified geolevels
    1. Per-geolevel TVD
    """
    sdf = sdf.getGeolevels(geolevels).getQueryAnswers(queries)
    sdf = sdf.geolevel_tvd(groupby=groupby)
    return sdf


if __name__ == "__main__":
    S3_BASE = "s3://uscb-decennial-ite-das/users"
    
    experiments = {
        'RI_PL94_P12': [
            # <--- Input locations for RI data from runs using PL94_P12 schema and manual topdown strategy --->
            "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td10_1/",
            "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td1_1/",
            "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td3_1/",
            "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td025_1/",
            "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td05_1/",
            "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td001_1/",
            "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td01_1/",
            "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td2_1/"
        ],
    }


    ### Intended to be used for a single query at a time, looping over all desired experiments ###

    queryNames = ['total', 'hhgq', 'votingage', 'numraces * hispanic', 'cenrace * hispanic', 'sex * agecat', 'detailed']

    experimentDesignators = ["RI_PL94_P12"]

    trialsPerExperiment = {}
    trialsPerExperiment["RI_PL94_P12"] = 25

    for q in queryNames:
        for d in experimentDesignators:
            queryName = q
            experimentDesignator = d
            numTrials = trialsPerExperiment[d]

            ###############################################
            # <--- Primary Control Parameters --->
            experimentName = f"analyses/{queryName}/VA_{experimentDesignator}_{numTrials}Trial_allPLBs"

            schema_name = "PL94_P12"
            geolevels = [C.STATE, C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK]

            loglevel = "ERROR" # spark log level / INFO, ERROR are common choices
            # <--- End Primary Control Parameters --->
            ###############################################

            queries = [queryName]
            save_location = f"/mnt/users/moran331/{experimentName}/"
            analysis = setuptools.setup(save_location=save_location, spark_loglevel="ERROR")
            spark = analysis.spark

            # Specify the input data locations
            experiment_paths = experiments[experimentDesignator]

            # a metric builder object is needed for analysis, as experiments are built using it
            mb = sdftools.MetricBuilder()
            mb.add(
                desc = "geolevel_tvd",
                metric_function = lambda sdf: geolevel_tvd(sdf, geolevels, queries, groupby=[AC.GEOLEVEL, AC.RUN_ID, AC.PLB])
            )
            
            # build an experiment and add it to analysis
            analysis.add_experiment(
                name = experimentName, # need a unique name for each experiment
                runs = experiment_paths,    # can be either the string paths, or the DASRun objects themselves
                schema = schema_name,       # the name of the schema for the runs provided (must all be data from the same schema)
                metric_builder = mb,        # the metric builder object constructed above
                mtype = AC.SPARSE           # mapper type: we almost always will want to use AC.SPARSE
            )

            # run analysis
            analysis.run_analysis(save_results=True)
            spark.stop()
