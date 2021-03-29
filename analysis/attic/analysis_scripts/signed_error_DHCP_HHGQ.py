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
    results[SEABR] = sdf.df.groupBy(groupby).agg(sf.avg("re")).persist()

    return results


def getGeolevelTVD(sdf, geolevels, queries):
    """ 
    Calculates the following:
    0. Query answers at the specified geolevels
    1. Per-geolevel TVD
    """
    sdf = sdf.getGeolevels(geolevels).getQueryAnswers(queries)
    sdf = sdf.geolevel_tvd(groupby=[AC.GEOLEVEL, AC.RUN_ID, AC.QUERY, AC.PLB])
    return sdf
    
if __name__ == "__main__":
    S3_BASE = "s3://uscb-decennial-ite-das/users"
    
    experiments = {
        'defaultManualStrategy': [
            # <--- Input locations for VA data from runs using historically default manual strategy --->
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP/td001/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP/td01/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td1/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td2/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td4/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td8/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td16/"
        ],
        
        "danVariant1-2": [
            # <--- Input Locations for VA data from runs with Dan's new post-processing (not sure how this works) --->
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td001/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td01/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td1/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td2/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td4/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td8/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td16/"
        ],
        
        "danVariant1": [
            # <--- Input Locations for VA data with simple HB tree branchFactor4 age-range queries added to workload --->
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td001/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td01/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td1/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td2/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td4/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td8/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td16/"
        ],
        
        "scqSimpleAgeSexQ": [
            # <--- Input Locations for VA data with small-cell-query at both State & County levels --->
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps0.1/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ/full_person/", # 1.0
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps2/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps4/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps8.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps16.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps20.0/full_person/"
        ],
        
        "scqCOnly_SimpleAgeSexQ": [
            # <--- Input Locations for VA data with small-cell-query at County level only --->
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps0.1/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps1.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps2.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps4.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps8.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps16.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps20.0/full_person/"
        ]
    }


    ### Intended to be used for a single query at a time, looping over all desired experiments ###

    queries = ['total', 'hhgq', 'votingage * citizen', 'numraces * hispanic', 'cenrace * hispanic', 'sex * age', 'detailed']

    #experimentDesignators = ["danVariant1", "danVariant1-2"]
    experimentDesignators = ["defaultManualStrategy", "danVariant1", "danVariant1-2", "scqSimpleAgeSexQ", "scqCOnly_SimpleAgeSexQ"]

    trialsPerExperiment = {}
    trialsPerExperiment["defaultManualStrategy"] = 3
    trialsPerExperiment["danVariant1"] = 3
    trialsPerExperiment["danVariant1-2"] = 3
    trialsPerExperiment["scqSimpleAgeSexQ"] = 1
    trialsPerExperiment["scqCOnly_SimpleAgeSexQ"] = 1

    for d in experimentDesignators:
        experimentDesignator = d
        numTrials = trialsPerExperiment[d]

        ###############################################
        # <--- Primary Control Parameters --->
        experimentName = f"VA_analyses/{experimentDesignator}_{numTrials}Trial_allPLBs"
        
        schema_name = "DHCP_HHGQ"
        geolevels = [C.STATE, C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK]
        
        loglevel = "ERROR" # spark log level / INFO, ERROR are common choices
        # <--- End Primary Control Parameters --->
        ###############################################

        save_location = f"/mnt/users/moran331/{experimentName}/"
        analysis = setuptools.setup(save_location=save_location, spark_loglevel="ERROR")
        spark = analysis.spark

        # Specify the input data locations
        experiment_paths = experiments[experimentDesignator]

        # a metric builder object is needed for analysis, as experiments are built using it
        mb = sdftools.MetricBuilder()
        mb.add(
            desc = "bias by true counts",
            metric_function = lambda sdf: getSignedError(sdf, geolevels, queries)
        )
        # mb.add(
        #     desc = "geolevel 1-TVD",
        #     metric_function = lambda sdf: getGeolevelTVD(sdf, geolevels, queries)
        # )

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
