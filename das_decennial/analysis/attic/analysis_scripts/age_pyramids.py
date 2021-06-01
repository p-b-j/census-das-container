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
import analysis.tools.crosswalk as crosswalk

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf
from pyspark.sql import Row

import analysis.tools.setuptools as setuptools

from programs.schema.schemas.schemamaker import SchemaMaker

import analysis.plotting.report_plots as rp

import operator


def testdata_random_geounit_generator(geocode, schema, density=0.01, scale=10):
    raw_mat = np.round(ss.random(1, schema.size, format='csr', density=density) * scale)
    syn_mat = np.round(ss.random(1, schema.size, format='csr', density=density) * scale)
    raw_sparse = sp.multiSparse(raw_mat, schema.shape)
    syn_sparse = sp.multiSparse(syn_mat, schema.shape)
    return { 'geocode': geocode, 'raw': raw_sparse, 'syn': syn_sparse }


if __name__ == "__main__":

    ################################
    # define experiments to analyze
    ################################
    S3_BASE = "s3://uscb-decennial-ite-das/users"
    
    #################
    # setup analysis
    #################
    #analysis_results_save_location = f"/mnt/users/moran331/analysis_reports/"
    analysis_results_save_location = f"{S3_BASE}/moran331/analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
    spark = analysis.spark
        
    # path = [
    #     f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td4/run_0000/"
    # ]

    schema_name = "DHCP_HHGQ"  
    schema = SchemaMaker.fromName(name=schema_name)
    
    num_geocodes = 5
    geocodes = [str(x).zfill(16) for x in range(num_geocodes)]
    geounits = [testdata_random_geounit_generator(x, schema, density=0.00001, scale=10) for x in geocodes]

    

    sdf = sdftools.getSDF(spark, path, schema, with_crosswalk=True)

    geolevels = [C.STATE, C.COUNTY]
    queries = ["sex * age"]
    
    saveloc = "/mnt/users/moran331/age_pyramids/danVariant1-2_td4_run_0000_VA_age_pyramids.csv"
    sdf = sdf.getGeolevels(geolevels)
    df = sdf.df
    df = sdftools.answerQuery(df, schema, queries[0], labels=False)
    df.toPandas().to_csv(saveloc, index=False)
    
    
    
