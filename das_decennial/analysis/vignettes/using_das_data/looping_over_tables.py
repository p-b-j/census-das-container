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


    ######################################################
    # Looping over the P1-P4 + P42 tables in PL94
    ######################################################
    path = f"{AC.S3_BASE}lecle301/withRawForBrett_topdown_ri44/"
    experiment = analysis.make_experiment("pl94_tables", path)


    # P1-P4, P42 table definitions
    tabledict = {
        "P1": [
            "total",
            "numraces",
            "cenrace"
        ],

        "P2": [
            "total",
            "hispanic",
            "numraces",
            "cenrace",
            "hispanic * numraces",
            "hispanic * cenrace"
        ],

        "P3": [
            "votingage",
            "votingage * numraces",
            "votingage * cenrace"
        ],

        "P4": [
            "votingage",
            "votingage * hispanic",
            "votingage * numraces",
            "votingage * cenrace",
            "votingage * hispanic * numraces",
            "votingage * hispanic * cenrace"
        ],

        "P42": [
            "household",
            "institutionalized",
            "gqlevels"
        ],
    }

    # Get the DF and schema
    schema = experiment.schema
    df = experiment.getDF()

    # Get the geolevels (faster to do this before looping if the queries
    # are to be answered over the same geolevels; otherwise, can perform this
    # step in the loop)
    geolevels = [C.US, C.STATE, C.COUNTY, C.TRACT_GROUP, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU]
    df_geolevel = sdftools.aggregateGeolevels(spark, df, geolevels)

    # loop over each table, calculating the queries for each one
    for table_name, queries in tabledict.items():
        sdftools.show(queries, f"The queries associated with table '{table_name}'")

        # answer the queries within the table
        df_table = sdftools.answerQueries(df_geolevel, schema, queries, labels=True).persist()
        sdftools.show(df_table, f"The DF with answers for the table '{table_name}'")

        # further computations...

        # plot and/or save the results
