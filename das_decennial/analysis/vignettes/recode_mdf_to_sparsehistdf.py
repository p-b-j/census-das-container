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

import analysis.constants as AC
import constants as C
from constants import CC

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

    schema = SchemaMaker.fromName(CC.SCHEMA_REDUCED_DHCP_HHGQ)
    
    mdf_path = "s3://uscb-decennial-ite-das/users/lecle301/cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries13_version7/data-run1.0-epsilon4.0-DHCP_MDF.txt"
    cef_path = "s3://uscb-decennial-ite-das/users/lecle301/cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries13_version7/data-run1.0-epsilon4.0-BlockNodeDicts/"
    budget_group = "4.0"
    plb = "4.0"
    run_id = "run_0001"
    
    df = datatools.Recode2020CensusMDFToSparseHistogramDF(analysis, schema, mdf_path, cef_path, budget_group, plb, run_id).df
    df.show()

    
 
