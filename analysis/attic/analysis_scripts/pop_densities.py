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
import programs.datadict as dd

from programs.schema.schemas.schemamaker import SchemaMaker

#import analysis.plotting.report_plots as rp

import operator


if __name__ == "__main__":

    ################################
    # define experiments to analyze
    ################################
    S3_BASE = "s3://uscb-decennial-ite-das/users"
    
    #################
    # setup analysis
    #################
    analysis_results_save_location = f"/mnt/users/moran331/analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
    spark = analysis.spark
        
    path = [
        f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td4/run_0000/"
    ]

    runs = treetools.getDASRuns(path)
    
    schema_name = "DHCP_HHGQ"
    
    schema = SchemaMaker.fromName(name=schema_name)

    sdf = sdftools.getSDF(spark, path, schema, with_crosswalk=True)

    geolevels = [C.STATE, C.COUNTY, C.TRACT_GROUP, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU]

    popdf = sdftools.population_density(spark, sdf, geolevels)
    sdftools.print_item(popdf.columns, "Population Density columns")
    sdftools.print_item(popdf, "Population Density DF")
    
    # split data into each geolevel
    #popdf.write.partitionBy(AC.GEOLEVEL).format('csv').save(f"{S3_BASE}/moran331/population_densities/DHCP_HHGQ/danVariant1-2_td4_run_0000_VA_pop_densities")
    
    # try repartition and/or coalesce to get smaller numbers of part files
    popdf.repartition(1).write.format('csv').option('header', 'true').save(f"{S3_BASE}/moran331/population_densities/DHCP_HHGQ/danVariant1-2_td4_run_0000_VA_pop_densities2")
        

    
    
      
