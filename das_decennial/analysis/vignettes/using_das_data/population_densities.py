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
import operator
import os

import analysis.tools.setuptools as setuptools
import analysis.tools.datatools as datatools
import analysis.tools.sdftools as sdftools
import analysis.tools.graphtools as graphtools
import analysis.tools.crosswalk as crosswalk

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf
from pyspark.sql import Row

from programs.schema.schemas.schemamaker import SchemaMaker

import programs.sparse as sp
import scipy.sparse as ss


if __name__ == "__main__":
    ################################################################
    # Set the save_location to your own JBID (and other folder(s))
    # it will automatically find your JBID
    # if something different is desired, just pass what is needed 
    # into the setuptools.setup function.
    ################################################################
    jbid = os.environ.get('JBID', 'temp_jbid')
    save_folder = "analysis_results/"

    save_location = du.addslash(f"{jbid}/{save_folder}")
    
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=save_location, spark_loglevel=spark_loglevel)

    # save the analysis script?
    # toggle to_linux=True|False to save|not save this analysis script locally
    # toggle to_s3=True|False to save|not save this analysis script to s3
    analysis.save_analysis_script(to_linux=False, to_s3=False)
    
    # save/copy the log file?
    analysis.save_log(to_linux=False, to_s3=False)
    
    # zip the local results to s3?
    analysis.zip_results_to_s3(flag=False)

    spark = analysis.spark


    #######################################################
    # Create an experiment using one or more DAS Run paths
    #######################################################
    paths = [
        f"{AC.S3_BASE}kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td4/run_0000/"
    ]

    experiment = analysis.make_experiment("danVariant1-2", paths)
    sdftools.print_item(experiment.__dict__, "Experiment Attributes")
    
    ##############################
    # Work with the Experiment DF
    ##############################
    df = experiment.getDF()
    schema = experiment.schema
    sdftools.print_item(df, "Experiment DF")
    
    
    #################################
    # Calculate Population Densities
    #################################
    geolevels = [C.STATE, C.COUNTY]
    popdf = sdftools.population_density(spark, df, schema, geolevels)
    sdftools.print_item(popdf, "Population Density DF", 1000)
    
    
    
