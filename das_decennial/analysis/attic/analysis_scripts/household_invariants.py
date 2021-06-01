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


def hh_invar_mapper(node):
    return int(node['_invar']['gqhh_vect'][0])


def household_tvd(sdf, geolevels, queries, spark):  
    """
    Calculating 1-TVD for the Household information
    
    1 - [ (A + B) / C ], where
    
    A = SUM( L1( detailed(CEF_g), detailed(DAS_g) ) ) for all g in the geolevel
    
    B = SUM( L1( total(CEF_g), total(DAS_g) ) ) for all g in the geolevel
    
    C = 2 * SUM(_invar['gqhh_vect'][0]_g) <- household invariant total in the geolevel
    """
    results = {}

    # get the invariants path
    block_level_invar_path = sdf.runs[0].data_path
    
    # prep invar_df (household info only)
    invar_rdd = spark.sparkContext.pickleFile(block_level_invar_path)
    
    # since the household total invariant for the geolevel will be the same across all geolevels, we can just calculate the value
    invar_val = invar_rdd.map(hh_invar_mapper).reduce(operator.add)
    sdftools.print_item(invar_val, "Household Total Invariant")
    
    double_invar_val = 2 * invar_val
    sdftools.print_item(double_invar_val, "2 * Household Total Invariant")
    
    # compute, for each geolevel, the 1-TVD for household info
    
    # old way... compute each geolevel individually
    # for geolevel in du.aslist(geolevels) + [geolevels]:
    
    # new way... compute all geolevels at once
    for geolevel in [geolevels]:
        # A
        geosdf = sdf.clone()
        sdftools.print_item(geosdf, "Original SDF")
        
        geosdf = geosdf.getGeolevels(geolevel)
        sdftools.print_item(geosdf, f"Geolevel '{geolevel}'")
        
        geosdf = geosdf.getQueryAnswers(queries)
        sdftools.print_item(geosdf, f"Detailed Query at geolevel '{geolevel}'")
        
        geosdf = geosdf.L1(colname="L1_A")
        sdftools.print_item(geosdf, f"L1_A")
        
        geosdf = geosdf.sum(groupby=[AC.GEOCODE, AC.GEOLEVEL])
        sdftools.print_item(geosdf, "sum(L1_A)")
        
        # B
        geosdf = geosdf.L1(colname="L1_B")
        sdftools.print_item(geosdf, "L1_B")
        
        geosdf = geosdf.sum(groupby=[AC.GEOLEVEL])
        sdftools.print_item(geosdf, "sum(L1_B)")

        # 1-[(A+B)/C]
        geosdf.df = geosdf.df.withColumn("A+B", sf.col("L1_A") + sf.col("L1_B")).persist()
        sdftools.print_item(geosdf, "A+B")
        
        geosdf.df = geosdf.df.withColumn("2*geolevel_hh_invar", sf.lit(double_invar_val)).persist()
        
        geosdf.df = geosdf.df.withColumn("TVD", sf.col("A+B") / sf.col("2*geolevel_hh_invar")).persist()
        sdftools.print_item(geosdf, "TVD")
        
        geosdf.df = geosdf.df.withColumn("1-TVD", sf.lit(1) - sf.col("TVD")).persist()
        sdftools.print_item(geosdf, "1-TVD")
        
        
        if isinstance(geolevel, list):
            key = f"All_Geolevels_Household_1-TVD"
        else:
            key = f"{geolevel}_Household_1-TVD"
            
        results[key] = geosdf
    
    return results
        
        


if __name__ == "__main__":
    # setup tools will return the spark session and save location path for this run
    # NOTE: You will need to specify a location for the results to be saved
    #       It should be passed into setuptools.setup, where it will be altered to
    #       add a subdirectory matching the logfile's name
    
    # Recommended location: "/mnt/users/[your_jbid]/analysis_results/"
    save_location = "/mnt/users/moran331/large_scale_analysis/"

    # Most common options are "INFO" and "ERROR"
    # In addition to the analysis print statements...
    # "INFO" provides ALL spark statements, including stage and task info
    # "ERROR" provides only error statements from spark/python
    loglevel = "ERROR"

    analysis = setuptools.setup(save_location=save_location, spark_loglevel="ERROR")

    
    # Specify the experiment paths
    experiment_paths = [
        "s3://uscb-decennial-ite-das/users/sexto015/HDMM-Trial005/",
        "s3://uscb-decennial-ite-das/users/sexto015/experiments/VA-HDMM/eps8/",
        "s3://uscb-decennial-ite-das/users/sexto015/experiments/VA-HDMM/eps16/",

    ]
    schema_name = "Household2010"

    
    geolevels = [C.STATE, C.COUNTY, C.TRACT_GROUP, C.TRACT, C.BLOCK_GROUP, C.BLOCK]
    queries = ['detailed']
    
    # a metric builder object is needed for analysis, as experiments are built using it
    mb = sdftools.MetricBuilder()
    mb.add(
        desc = "Calculating Household 1-TVD",
        metric_function = lambda sdf: household_tvd(sdf, geolevels, queries, analysis.spark)
    )
    
    # build an experiment for each experiment path
    for i,path in enumerate(experiment_paths):
        analysis.add_experiment(
            name = f"Household2010_Invariant_Analysis_{i}_{path.split('/')[-2]}"
            runs = path,
            schema = schema_name,
            metric_builder = mb,
            mtype = AC.SPARSE
        )

    # run analysis
    analysis.run_analysis(save_results=True)
