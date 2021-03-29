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

import analysis.plotting.report_plots as rp

import operator

def getSignedError(sdf, geolevels, queries):
    sdf = sdf.getGeolevels(geolevels).answerQueries(queries)
    
    sdf.df = sdftools.getSignedErrorByTrueCountRuns(sdf.df)

    groupby = ['orig_count_bin', AC.GEOLEVEL, AC.QUERY, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP]
    results = {}
    # quantiles within groups
    SEQBG = "signed_error_quantiles_by_group"
    REQBG = "re_quantiles_by_group"
    quantiles = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    results[SEQBG] = sdftools.getGroupQuantiles2(sdf.df, columns=['signed_error'], groupby=groupby, quantiles=quantiles).persist()
    results[REQBG] = sdftools.getGroupQuantiles2(sdf.df, columns=['re'], groupby=groupby, quantiles=quantiles).persist()
    
    # average within groups
    SEABR = "signed_error_average_by_run" # formerly "avg(avg(signed_error))_by_run"
    REABR = "re_average_by_run"           # formerly "avg(avg(re))_by_run"
    results[SEABR] = sdf.df.groupBy(groupby).agg(sf.avg("signed_error")).persist()
    results[REABR] = sdf.df.groupBy(groupby).agg(sf.avg("re")).persist()

    return results


def getGeolevelTVD(sdf, geolevels, queries, product, state, plot=False):
    """ 
    Calculates the following:
    0. Query answers at the specified geolevels
    1. Per-geolevel TVD
    """
    sdf = sdf.getGeolevels(geolevels).getQueryAnswers(queries)
    sdf = sdf.geolevel_tvd(groupby=[AC.GEOLEVEL, AC.RUN_ID, AC.QUERY, AC.PLB])
    
    if plot:
        saveloc = du.getdir(sdf.metric_save_location)
        geolevel_tvd_pandas_df = sdf.toPandas()
        rp.geolevel_tvd_lineplot(geolevel_tvd_pandas_df, saveloc, product, state)
        rp.geolevel_tvd_heatmap(geolevel_tvd_pandas_df, saveloc, product, state)
    
    return sdf


def getAgeSexQuantiles(sdf, geolevels, queries):
    pass
    


if __name__ == "__main__":

    ################################
    # define experiments to analyze
    ################################
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

    trialsPerExperiment = {}
    trialsPerExperiment["RI_PL94_P12"] = 25
    product = "PL94-P12"
    state = "RI"
    
    #################
    # setup analysis
    #################
    analysis_results_save_location = f"/mnt/users/moran331/RI_analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)

    # list of experiments to analyze
    experimentDesignators = ["RI_PL94_P12"]
    
    ##############################
    # add experiments to analysis
    #############################
    for d in experimentDesignators:
        numTrials = trialsPerExperiment[d]
        experiment_name = f"{d}_{numTrials}Trial_allPLBs"
        experiment_paths = experiments[d]
      
        schema_name = "PL94_P12"

        #######################
        # setup metric builder
        #######################
        geolevels = [C.STATE, C.COUNTY, C.TRACT_GROUP, C.TRACT, C.BLOCK_GROUP, C.BLOCK]
        queries = ['total', 'hhgq', 'numraces * hispanic', 'cenrace * hispanic', 'detailed']
        
        # a metric builder object is needed for analysis, as experiments are built using it
        mb = sdftools.MetricBuilder()
        mb.add(
            desc = f"bias by true counts for queries: {queries} and geolevels: {geolevels}",
            filename = "bias_metric",
            metric_function = lambda sdf: getSignedError(sdf, geolevels, queries)
        )
        mb.add(
            desc = f"geolevel 1-TVD for queries: {queries} and geolevels: {geolevels}",
            filename = "geolevel_tvd_metric",
            metric_function = lambda sdf: getGeolevelTVD(sdf, geolevels, queries, product=product, state=state, plot=True)
        )
        
        #############################################
        # build an experiment and add it to analysis
        #############################################
        analysis.add_experiment(
            name = experiment_name,     # need a unique name for each experiment
            runs = experiment_paths,    # can be either the string paths, or the DASRun objects themselves
            schema = schema_name,       # the name of the schema for the runs provided (must all be data from the same schema)
            metric_builder = mb,        # the metric builder object constructed above
            mtype = AC.SPARSE           # mapper type: we almost always will want to use AC.SPARSE
        )
        
    ###############
    # run analysis
    ###############
    analysis.run_analysis(save_results=True)
    #spark.stop()
