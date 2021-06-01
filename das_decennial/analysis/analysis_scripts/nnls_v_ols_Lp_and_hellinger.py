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
    
    geolevels = [
        C.STATE,
        C.COUNTY,
        C.TRACT_GROUP,
        C.TRACT,
        C.BLOCK_GROUP,
        C.BLOCK,
        C.SLDL,
        C.SLDU
    ]

    queries = [
        'total',
        'hhgq',
        'votingage * citizen',
        'numraces * hispanic',
        'cenrace * hispanic',
        'sex * age',
        'detailed'
    ]
    

    def queryLp(df, p, groupby=[AC.GEOLEVEL, AC.GEOCODE, AC.QUERY, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP]):
        """
        Calculates the L^p-norm for each unique (GEOLEVEL, GEOCODE, QUERY, RUN_ID, PLB, BUDGET_GROUP) group
        """
        sdftools.show(p, "Value of p in the L^p metric")
        if p == "inf":
            # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
            df = df.withColumn("L^inf_norm", sf.abs(sf.col(AC.PRIV) - sf.col(AC.ORIG))).persist()
            sdftools.show(df, "L^inf_norm as | protected - orig | before taking the max")
            df = df.groupBy(groupby).agg(sf.max(sf.col("L^inf_norm"))).persist()
            sdftools.show(df, "L^inf_norm after taking the max per group")
            df = sdftools.stripSQLFromColumns(df).persist()
        else:
            df = df.withColumn(f"L^{p}", sf.pow(sf.abs(sf.col(AC.PRIV) - sf.col(AC.ORIG)), sf.lit(p))).persist()
            sdftools.show(df, f"L^{p} after taking | protected - orig | ^ {p}")
            df = df.groupBy(groupby).sum().persist()
            sdftools.show(df, f"L^{p} after groupby and sum")
            df = sdftools.stripSQLFromColumns(df).persist()
            df = df.withColumn(f"L^{p}_norm", sf.pow(sf.col(f"L^{p}"), sf.lit(1/p))).persist()
            sdftools.show(df, f"L^{p} after taking {p}-th root of the sum")
            df = sdftools.stripSQLFromColumns(df).persist()
        return df


    def queryHellinger(df, groupby=[AC.GEOLEVEL, AC.GEOCODE, AC.QUERY, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP]):
        """
        Calculates the Hellinger metric for each unique (GEOLEVEL, GEOCODE, QUERY, RUN_ID, PLB, BUDGET_GROUP) group
        
        g = AC.ORIG = raw = CEF
        # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
        h = AC.PRIV = syn = MDF
        
        H(g,h) = sqrt(sum([sqrt(h_i) - sqrt(g_i)]^2) / [2*sum(g_i)])
        H(g,h) = sqrt( A / B )
        
        A = sum([sqrt(h_i) - sqrt(g_i)]^2)
        B = 2 * sum(g_i)
        """
        df = df.withColumn("H_A", sf.pow(sf.sqrt(sf.col(AC.PRIV)) - sf.sqrt(sf.col(AC.ORIG)), sf.lit(2))).persist()
        sdftools.show(df, "H_A = [sqrt(priv) - sqrt(orig)]^2")
        df = df.withColumn("H_B", sf.lit(2) * sf.col(AC.ORIG)).persist()
        sdftools.show(df, "H_B = 2 * orig")
        df = df.groupBy(groupby).sum().persist()
        sdftools.show(df, "H_A and H_B after summing over groups")
        df = sdftools.stripSQLFromColumns(df).persist()
        df = df.withColumn("H", sf.sqrt(sf.col("H_A") / sf.col("H_B"))).persist()
        sdftools.show(df, "H = sqrt(sum([sqrt(priv) - sqrt(orig)]^2) / [2*sum(orig)])")
        return df
        

    

    ########################################
    # Calculating L^p and Hellinger Metrics
    ########################################
    
    # 0a. Aggregate Blocks to get Geographic Units at all desired Geographic Levels
    geoleveldf = sdftools.aggregateGeolevels(spark, df, geolevels)
    
    # 0b. Answer Queries
    querydf = sdftools.answerQueries(geoleveldf, schema, queries, labels=True)
    
    # 1. Calculate L(orig, priv) and H(orig, priv) for
    #    detailed cells, marginals, total (for the queries listed in "queries")
    df_L1 = queryLp(querydf, 1)
    df_L2 = queryLp(querydf, 2)
    df_Linf = queryLp(querydf, "inf")
    
    sdftools.show(df_L1, "L^1 norm for the queries")
    sdftools.show(df_L2, "L^2 norm for the queries")
    sdftools.show(df_Linf, "L^inf norm for the queries")
    
    df_H = queryHellinger(querydf)
    
    sdftools.show(df_H, "Hellinger metric for the queries")
    
    # 2. Average L^p and H across geounits in the geolevel
    # removed AC.GEOCODE from the groupby to aggregate across all geounits
    groupby = [AC.GEOLEVEL, AC.QUERY, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP]
    df_L1_avg = df_L1.groupBy(groupby).agg(sf.avg(sf.col("L^1_norm"))).persist()
    df_L2_avg = df_L2.groupBy(groupby).agg(sf.avg(sf.col("L^2_norm"))).persist()
    df_Linf_avg = df_Linf.groupBy(groupby).agg(sf.avg(sf.col("L^inf_norm"))).persist()
    
    sdftools.show(df_L1_avg, "L^1 norm for the queries")
    sdftools.show(df_L2_avg, "L^2 norm for the queries")
    sdftools.show(df_Linf_avg, "L^inf norm for the queries")
    
    df_H_avg = df_H.groupBy(groupby).agg(sf.avg(sf.col("H"))).persist()
    
    sdftools.show(df_H_avg, "Hellinger metric for the queries")
    
