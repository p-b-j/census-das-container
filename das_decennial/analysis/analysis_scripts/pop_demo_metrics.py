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
    
    
    ##############################
    # Accuracy Metrics
    ##############################
    """
    Mean / Median Absolute Error (MAE):
        1. Calculate total population at County geographic level
        2. Calculate |MDF-CEF| for the total populations for each county
        3. Calculate the mean or median across all county total populations
    """
    # 1a. Aggregate to County geographic level
    county_df = sdftools.aggregateGeolevels(spark, df, [C.COUNTY])
    sdftools.show(county_df, "Counties")
    
    # 1b. Answer the "total" query for all counties 
    county_totals_df = sdftools.answerQueries(county_df, schema, "total", labels=True)
    sdftools.show(county_totals_df, "County total pops")
    
    # 2. Calculate L1(MDF, CEF)
    # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
    abs_error_county_totals_df = sdftools.getL1(county_totals_df, colname="AbsError", col1=AC.PRIV, col2=AC.ORIG)
    sdftools.show(abs_error_county_totals_df, "L1 between MDF and CEF County total pops")
    
    # 3a. Calculate the mean of L1 across all county total pops
    groupby = [AC.GEOLEVEL, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP, AC.QUERY]
    mae_county_totals_df = abs_error_county_totals_df.groupBy(groupby).avg().persist()
    mae_county_totals_df = sdftools.stripSQLFromColumns(mae_county_totals_df).persist()
    sdftools.show(mae_county_totals_df, "Mean Absolute Error of total population counts at the County level")
    
    
    
    
    
    #geolevels = [
    #    C.STATE,
    #    C.COUNTY,
    #    C.TRACT_GROUP,
    #    C.TRACT,
    #    C.BLOCK_GROUP,
    #    C.BLOCK,
    #    C.SLDL,
    #    C.SLDU
    #]

    #queries = [
    #    'total',
    #    'hhgq',
    #    'votingage * citizen',
    #    'numraces * hispanic',
    #    'cenrace * hispanic',
    #    'sex * age',
    #    'detailed'
    #]
    

