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

    queryNames = ['total', 'hhgq', 'votingage * citizen', 'numraces * hispanic', 'cenrace * hispanic', 'sex * age', 'detailed']

    #experimentDesignators = ["danVariant1", "danVariant1-2"]
    experimentDesignators = ["scqSimpleAgeSexQ", "scqCOnly_SimpleAgeSexQ"]

    trialsPerExperiment = {}
    trialsPerExperiment["defaultManualStrategy"] = 3
    trialsPerExperiment["danVariant1"] = 3
    trialsPerExperiment["danVariant1-2"] = 3
    trialsPerExperiment["scqSimpleAgeSexQ"] = 1
    trialsPerExperiment["scqCOnly_SimpleAgeSexQ"] = 1

    for q in queryNames:
        for d in experimentDesignators:
            queryName = q
            experimentDesignator = d
            numTrials = trialsPerExperiment[d]

            ###############################################
            # <--- Primary Control Parameters --->
            experimentName = f"analyses/{queryName}/VA_{experimentDesignator}_{numTrials}Trial_allPLBs"

            schema_name = "DHCP_HHGQ"
            geolevels = [C.STATE, C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK]

            loglevel = "ERROR" # spark log level / INFO, ERROR are common choices
            # <--- End Primary Control Parameters --->
            ###############################################

            queries = [queryName]
            save_location = f"/mnt/users/lecle301/{experimentName}/"
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
