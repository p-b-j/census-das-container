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


def mf01(sdf, geolevels, queries):
    """ Answers queries at the geolevels specified """
    sdf = sdf.getGeolevels(geolevels).answerQueries(queries)
    sdftools.print_item(sdf, f"Query answers for geolevels {geolevels} and queries {queries}")
    return sdf


def mf02(sdf, geolevels, queries):
    """ 
    Calculates the following:
    0. Query answers at the specified geolevels
    1. L1(orig, priv) for every row
    2. Sum of the L1 across QUERY and LEVEL, grouped by PLB, GEOCODE, GEOLEVEL, and RUN_ID (i.e. marginalizes the QUERY/LEVEL dimensions)
    3. Average L1 Sum across RUN_ID, grouped by PLB, GEOCODE, and GEOLEVEL (i.e. average across the runs)
    4. Quantiles across GEOCODE, grouped by PLB and GEOLEVEL (i.e. quantiles of average L1 across runs, queries, and geounits)
    """
    # 0.
    sdf = sdf.getGeolevels(geolevels).getQueryAnswers(queries).fill(queries)
    
    # 1.
    sdf = sdf.L1()
    
    # 2.
    sdf = sdf.sum(groupby=[AC.PLB, AC.GEOCODE, AC.GEOLEVEL, AC.RUN_ID])
    
    # 3.
    sdf = sdf.average("L1", groupby=[AC.PLB, AC.GEOCODE, AC.GEOLEVEL])
    
    # 4.
    sdf = sdf.group_quantiles("L1", groupby=[AC.PLB, AC.GEOLEVEL], quantiles=[0.0, 0.25, 0.5, 0.75, 1.0])
    
    return sdf


def mf03(sdf, geolevels, queries):
    """ 
    Calculates the following:
    0. Query answers at the specified geolevels
    1. L1(orig, priv) for every row
    2. Sum of the L1 across QUERY and LEVEL, grouped by PLB, GEOCODE, GEOLEVEL, and RUN_ID (i.e. marginalizes the QUERY/LEVEL dimensions)
    3. Average L1 Sum across RUN_ID, grouped by PLB, GEOCODE, and GEOLEVEL (i.e. average across the runs)
    4. Quantiles across GEOCODE, grouped by PLB and GEOLEVEL (i.e. quantiles of average L1 across runs, queries, and geounits)
    """
    results = {}
    # 0.
    sdf = sdf.getGeolevels(geolevels).getQueryAnswers(queries).fill(queries)
    results['query_answers'] = sdf.copy()
    
    # 1.
    sdf = sdf.L1()
    results['L1'] = sdf.copy()
    
    # 2.
    sdf = sdf.sum(groupby=[AC.PLB, AC.GEOCODE, AC.GEOLEVEL, AC.RUN_ID])
    results['L1_sum'] = sdf.copy()
    
    # 3.
    sdf = sdf.average("L1", groupby=[AC.PLB, AC.GEOCODE, AC.GEOLEVEL])
    results['avg_L1_sum'] = sdf.copy()
    
    # 4.
    sdf = sdf.group_quantiles("L1", groupby=[AC.PLB, AC.GEOLEVEL], quantiles=[0.0, 0.25, 0.5, 0.75, 1.0])
    results['avg_L1_sum_quantiles'] = sdf.copy()
    
    return results


if __name__ == "__main__":
    # setup tools will return the analysis object
    # the analysis object contains the spark session and save location path for this run
    # NOTE: You will need to specify a location for the results to be saved
    #       It should be passed into setuptools.setup, where it will be altered to
    #       add a subdirectory matching the logfile's name
    
    # Recommended location: "/mnt/users/[your_jbid]/analysis_results/"
    save_location = "/mnt/users/moran331/testing_analysis_v2/"
    
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
    schema_name = "PL94_P12"
        
    geolevels = [C.STATE, C.COUNTY, C.TRACT_GROUP, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDU, C.SLDL, C.CD]
    queries = ['hhgq * numraces', 'votingage * cenrace', 'total']

    # a metric builder object is needed for analysis, as experiments are built using it
    mb = sdftools.MetricBuilder()
    mb.add(
        desc = "mf01",
        metric_function = lambda sdf: mf01(sdf, geolevels, queries)
    )
    
    mb.add(
        desc = "mf02",
        metric_function = lambda sdf: mf02(sdf, geolevels, queries)
    )
    
    mb.add(
        desc = "mf03",
        metric_function = lambda sdf: mf03(sdf, geolevels, queries)
    )
    
    # build an experiment and add it to analysis
    analysis.add_experiment(
        name = "PL94_P12_Analysis", # need a unique name for each experiment
        runs = experiment_paths,    # can be either the string paths, or the DASRun objects themselves
        schema = schema_name,       # the name of the schema for the runs provided (must all be data from the same schema)
        metric_builder = mb,        # the metric builder object constructed above
        mtype = AC.SPARSE           # mapper type: we almost always will want to use AC.SPARSE
    )

    # run analysis
    analysis.run_analysis(save_results=True)
    
