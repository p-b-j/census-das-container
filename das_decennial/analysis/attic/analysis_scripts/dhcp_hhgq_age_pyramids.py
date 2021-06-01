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



if __name__ == "__main__":
    # setup tools will return the spark session and save location path for this run
    # NOTE: You will need to specify a location for the results to be saved
    #       It should be passed into setuptools.setup, where it will be altered to
    #       add a subdirectory matching the logfile's name
    
    # Recommended location: "/mnt/users/[your_jbid]/analysis_results/"
    save_location = "/mnt/users/moran331/age_pyramids/"
    loglevel = "INFO"
    analysis = setuptools.setup(save_location=save_location, spark_loglevel=loglevel)
    
    spark = analysis.spark
    

    # Specify the experiment paths
    experiment_paths = [
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/"
        
    ]
    schema_name = "DHCP_HHGQ"

    geolevels = [C.STATE, C.COUNTY]
    queries = ['sex * age']
    

    # a metric builder object is needed for analysis, as experiments are built using it
    mb = sdftools.MetricBuilder()
    mb.add(
        desc = "age pyramids",
        metric_function = lambda sdf: sdf.getGeolevels(geolevels).answerQueries(queries).fill(queries)
    )

    # add experiment to analysis
    analysis.add_experiment(
        name = f"{schema_name}_Analysis",
        runs = experiment_paths,
        schema = schema_name,
        metric_builder = mb,
        mtype = AC.SPARSE
    )

    # run analysis
    analysis.run_analysis(save_results=True)
    
    
