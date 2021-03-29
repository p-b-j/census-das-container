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

import analysis.tools.setuptools as setuptools
import programs.datadict as dd



def L1_quantile_rdd(sdf, geolevels):
    male_recode = sdf.schema.addRecode("male", groupings={ 'sex': { 'Male': [0] } })
    female_recode = sdf.schema.addRecode("female", groupings={ 'sex': { 'Female': [1] } })
    
    queries = ['male * age', 'female * age', 'sex * age']
    
    sdf = sdf.copy().getGeolevels(geolevels).answerQueries(queries)
    sdftools.print_item(sdf, f"df of queries {queries}", show=1000)
    
    quantiles = AC.DECILES
    groupby = [AC.GEOLEVEL, AC.GEOCODE, AC.PLB, AC.BUDGET_GROUP]
    sdf = sdf.group_quantiles(columns=[AC.ORIG, AC.PRIV], groupby=



if __name__ == "__main__":
    # setup tools will return the spark session and save location path for this run
    # NOTE: You will need to specify a location for the results to be saved
    #       It should be passed into setuptools.setup, where it will be altered to
    #       add a subdirectory matching the logfile's name
    
    # Recommended location: "/mnt/users/[your_jbid]/analysis_results/"
    save_location = "/mnt/users/moran331/sex_age_quantiles/"
    analysis = setuptools.setup(save_location=save_location)
    
    spark = analysis.spark
    

    # Specify the experiment paths
    experiment_paths = [
        "s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1"
    ]
    schema_name = "DHCP_HHGQ"

            
    geolevels = [C.STATE, C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK]
    queries = ['age * sex']
    

    # a metric builder object is needed for analysis, as experiments are built using it
    mb = sdftools.MetricBuilder()
    mb.add(
        desc = "Average L1 Age Range Deciles across Geounits",
        metric_function = lambda sdf: L1_quantile_rdd(sdf, geolevels)
    )

    # add experiment to analysis
    strategy_name = "hierarchical_age_range_danVariant1"
    analysis.add_experiment(
        name = f"{schema_name}_{strategy_name}_Analysis",
        runs = experiment_paths,
        schema = schema_name,
        metric_builder = mb,
        mtype = AC.SPARSE
    )

    # run analysis
    analysis.run_analysis(save_results=True)
    
