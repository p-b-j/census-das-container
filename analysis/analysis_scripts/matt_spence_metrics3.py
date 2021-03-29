# This script file implements Matt Spence's metrics, including MAE, MAPE, MALPE, CoV, RMS, for Executive Priority Tabulations #1, US+PR Run
# AnalyzeQuery function has been edited to include these metrics



######################################################
# To Run this script:
#
# cd into das_decennial/analysis/
# analysis=[path to analysis script] bash run_analysis.sh
#
# More info on analysis can be found here:
# https://github.ti.census.gov/CB-DAS/das_decennial/blob/master/analysis/readme.md
######################################################

import analysis.tools.sdftools as sdftools
import analysis.tools.datatools as datatools
import analysis.tools.setuptools as setuptools
import analysis.constants as AC
from pyspark.sql import functions as sf
from pyspark.sql import Row
import math as mathy

import constants as C
from constants import CC

import das_utils as du
import programs.datadict as dd
from programs.schema.schemas.schemamaker import SchemaMaker

import numpy as np
import matplotlib
print(f"matplotlib has methods: {dir(matplotlib)}")
print(f"matplotlib version: {matplotlib.__version__}")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas

import os, math
from collections import defaultdict

"""
Example target location:

abdat-ITE-MASTER:hadoop@ip-10-252-44-211$ aws s3 ls s3://uscb-decennial-ite-das/users/heiss002/cnstatDdpSchema_SinglePassRegular_va_cnstatDpqueries_cnstatGeolevels_version2/data-run | grep .*BlockNodeDicts.*\/
                           PRE data-run1.0-epsilon4.0-BlockNodeDicts/
                           PRE data-run10.0-epsilon4.0-BlockNodeDicts/
"""

tabledict_EPT_no1 = {
     #   "Table 1"           :   ["total"],
     #   "Table 2"            :   ["total"],
#         "Table 3"               :   ["total"],
#         "Table 10"               :   ["hispanic"],
#         "Table 11"                 :   ["hispanic"],
 #        "Table 12"              : ["hispanic"],
#          "Table 13"              :["hispanic"],
#           "Table 14a"            :["hispanic * whiteAlone"],
#           "Table 14b"            :["hispanic * blackAlone"],
#            "Table 14c"            :["hispanic * aianAlone"],
#             "Table 14d"            :["hispanic * asianAlone"],
#            "Table 14e"            :["hispanic * nhopiAlone"],
#             "Table 14f"            :["hispanic * sorAlone"],
#             "Table 14g"            :["hispanic * tomr"],
              "Table 15a"            :["hispanic * whiteAlone"],
              "Table 15b"            :["hispanic * blackAlone"],
              "Table 15c"            :["hispanic * aianAlone"],
              "Table 15d"            :["hispanic * asianAlone"],
              "Table 15e"            :["hispanic * nhopiAlone"],
              "Table 15f"            :["hispanic * sorAlone"],
              "Table 15g"            :["hispanic * tomr"]

}
tabledict_EPT_no2 = {
#        "EPT2_P1"           :   ["numraces","cenrace"],
 #       "EPT2_P2"           :   ["hispanic","hispanic * numraces","hispanic * cenrace"],
  #      "EPT2_P3"           :   ["votingage","votingage * numraces","votingage * cenrace"],
   #     "EPT2_P4"           :   ["votingage * hispanic","votingage * hispanic * numraces","votingage * hispanic * cenrace"],
    #    "EPT2_P5"           :   ["instlevels","gqlevels"],
}
tabledict_EPT_no3 = {
    #    "EPT3_ROW2_TOMR"    :   ["tomr * hispanic * sex * agecat100plus"],
     #   "EPT3_ROW2_6RACES"  :   ["allraces * hispanic * sex * agecat100plus"],
      #  "EPT3_ROW8_TOMR"    :   ["tomr * hispanic * sex * agecat85plus"],
   #     "EPT3_ROW8_6RACES"  :   ["allraces * hispanic * sex * agecat85plus"],
    #    "EPT3_ROW12_TOMR"   :   ["tomr * sex * agecat85plus"],
     #   "EPT3_ROW12_6RACES" :   ["allraces * sex * agecat85plus"],
     #   "EPT3_ROW14_TOMR"   :   ["tomr * sex * hispanic * agePopEst18groups"],
    #    "EPT3_ROW14_6RACES" :   ["allraces * sex * hispanic * agePopEst18groups"],
      #  "EPT3_ROW15"        :   ["sex * agePopEst18groups"],
}
tabledict_H1 = {"H1":["h1"],}

#all_geolevels = [C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD, C.STATE, C.PLACE] # For 1-state runs
#all_geolevels = [C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD, C.STATE, C.US, C.PLACE] # For US runs
# For patching 'missing' geolevels in already saved analyses:
all_geolevels = [C.COUNTY]
#all_geolevels = [C.PLACE]
#all_geolevels = [C.STATE]   # Just for quick tests
def listDefault():
    return all_geolevels
geolevels_dict = defaultdict(listDefault)

geolevels_dict["Table 1"]        = [C.COUNTY]
geolevels_dict["Table 2"]         = [C.PLACE]
geolevels_dict["Table 3"]             = [C.TRACT]
geolevels_dict["Table 10"]             = [C.STATE, C.COUNTY, C.PLACE]
geolevels_dict["Table 11"]             = [C.COUNTY]
geolevels_dict["Table 12"]            = [C.PLACE]
geolevels_dict["Table 13"]            = [C.TRACT]
geolevels_dict["Table 13"]            = [C.TRACT]
geolevels_dict["Table 14a"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14b"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14c"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14d"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14e"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14f"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14g"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14a"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 15a"]          = [C.COUNTY]
geolevels_dict["Table 15b"]          = [C.COUNTY]
geolevels_dict["Table 15c"]          = [C.COUNTY]
geolevels_dict["Table 15d"]          = [C.COUNTY]
geolevels_dict["Table 15e"]          = [C.COUNTY]
geolevels_dict["Table 15f"]          = [C.COUNTY]
geolevels_dict["Table 15g"]          = [C.COUNTY]

# Only needed for US (but most current runs State-only)
#geolevels_dict["EPT3_ROW2_6RACES"]      = [C.STATE]
#geolevels_dict["EPT3_ROW8_TOMR"]        = [C.STATE]
#geolevels_dict["EPT3_ROW8_6RACES"]      = [C.STATE]

geolevels_dict["EPT3_ROW2_TOMR"]        = [C.STATE, C.US] # For US runs
geolevels_dict["EPT3_ROW2_6RACES"]      = [C.STATE, C.US]
geolevels_dict["EPT3_ROW8_TOMR"]        = [C.STATE, C.US]
geolevels_dict["EPT3_ROW8_6RACES"]      = [C.STATE, C.US]

geolevels_dict["EPT3_ROW12_TOMR"]       = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW12_6RACES"]     = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW14_TOMR"]       = [C.COUNTY]
geolevels_dict["EPT3_ROW14_6RACES"]     = [C.COUNTY]
geolevels_dict["EPT3_ROW15"]            = [C.COUNTY]    # Also for PR Municipios
geolevels_dict["H1"]                    = all_geolevels + [C.US]
#geolevels_dict["H1"]                    = [C.STATE, C.US]  # Only for quick tests
#geolevels_dict["H1"]                    = [C.US]           # Only for very quick tests

default_buckets         = ["[0-1000)", "[1000-5000)", "[5000-10000)", "[10000-50000)", "[50000-100000)", "100000 +"]
table_default_bucket_list = ['Table 1', 'Table 2']
default_buckets2         = ["[0-10)", "[10-100)", "100 +"]
table_default_bucket_list2 = ['Table 11', 'Table 12', 'Table 15a', 'Table 15b', 'Table 15c', 'Table 15d', 'Table 15e', 'Table 15f', 'Table 15g']
race_list    = ['White','Black','American Indian','Asian','Native','Some', 'Two']
table_race_list = ['Table 14a', 'Table 14b', 'Table 14c', 'Table 14d', 'Table 14e', 'Table 14f', 'Table 14g','Table 15a', 'Table 15b', 'Table 15c', 'Table 15d', 'Table 15e', 'Table 15f', 'Table 15g']
race_queries = ['white','black','aian','asian','nhopi','sor', 'tomr']


def schemaDefault():
    return "DHCP_HHGQ"
schema_dict = defaultdict(schemaDefault)
schema_dict["H1"] = "H1_SCHEMA"         # For H1-only internal runs as of 4/2/2020
#schema_dict["H1"] = "Household2010"    # For CNSTAT DDP Run

def getSparkDFWithAbsDiff(spark, df, geolevels, queries, schema):
    sparkDFWithAnswers = sdftools.getAnswers(spark, df, geolevels, schema, queries)
    sparkDFWithDiff = sparkDFWithAnswers.withColumn('diff',sf.col('priv')-sf.col('orig'))
    sparkDFWithAbsDiff = sparkDFWithDiff.withColumn('abs diff', sf.abs(sf.col('diff')))
    return sparkDFWithAbsDiff


def largestIntInStr(bucket_name):
    if '[' in bucket_name:
        integerStr = bucket_name[1:-1].split('-')[1]
    else:
        integerStr = bucket_name[:-1].strip()
    return int(integerStr)

def setup():
    jbid = os.environ.get('JBID', 'temp_jbid')
    analysis_results_save_location = f"{jbid}/analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
    analysis.save_log(to_linux=False, to_s3=True)
    spark = analysis.spark
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
    return analysis, spark

def getPathsAndName(schema_name):
    """
        Copy and re-name to switch input locations.
    """
    print(f"Get paths received schema {schema_name}")

    S3_BASE="s3://uscb-decennial-ite-das/users"
    eps = 4.0
    num_trials = 1
    JBID = "lecle301"   # JBID used in s3 paths for saved runs (not necessarily your JBID)
    if schema_name == "DHCP_HHGQ":
        # Example:
        # s3://uscb-decennial-ite-das/users/lecle301/cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries4_version7/
        # cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_National_dpQueries1_officialCNSTATrun
        experiment_name = "cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_National_dpQueries1_officialCNSTATrun"
        #experiment_name = "cnstatDdpSchema_SinglePassRegular_va_dpQueries1_version2"
        #experiment_name = "cnstatDdpSchema_TwoPassBigSmall_va_dpQueries2_AllChildFilter"
        #experiment_name = "cnstatDdpSchema_InfinityNorm_va_dpQueries2_AllChildFilter"
        #experiment_name = "cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries13_version7"
        #experiment_name = "cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries1_version2"
        partial_paths = [f"data-run{RUN}.0-epsilon{eps:.1f}-BlockNodeDicts/" for RUN in range(1,num_trials+1)]
        path_prefix = f"{S3_BASE}/{JBID}/{experiment_name}/"
        paths = [path_prefix + partial_path for partial_path in partial_paths]
        remainder_paths = []
    elif schema_name == "Household2010":
        raise NotImplementedError(f"Schema {schema_name} input locations not yet implemented.")
    elif schema_name == "H1_SCHEMA":
        # Example:
        # s3://uscb-decennial-ite-das/users/lecle301/cnstatDdpSchema_SinglePassRegular_natH1_Only_withMeasurements_v8/
        experiment_name = "cnstatDdpSchema_SinglePassRegular_nat_H1_Only_withMeasurements_v8"
        partial_paths = [f"MDF_UNIT-run{RUN}.0-epsilon{eps:.1f}-BlockNodeDicts/" for RUN in range(1,num_trials+1)]
        path_prefix = f"{S3_BASE}/{JBID}/{experiment_name}/"
        paths = [path_prefix + partial_path for partial_path in partial_paths]
        remainder_paths = []
    else:
        raise ValueError(f"Schema {schema_name} not recognized when getting s3 ingest paths.")
    paths = paths + remainder_paths
    return paths, experiment_name, f"{eps:.1f}" # Change this for eps<0.1

def MattsMetrics(query, table_name, analysis, spark, geolevels, buckets=default_buckets, schema="DHCP_HHGQ"):
    """
    This function computes metrics for MAE, MALPE, CoV, RMS, MAPE, and percent thresholds"

    """
    print(f"For table {table_name}, analyzing query {query} at geolevels {geolevels} with schema {schema}")
    schema_name = schema
    paths, experiment_name, eps_str = getPathsAndName(schema_name)
    experiment = analysis.make_experiment(experiment_name, paths, schema_name=schema_name, dasruntype=AC.EXPERIMENT_FRAMEWORK_FLAT)
    sdftools.print_item(experiment.__dict__, "Experiment Attributes")

    spark_df = experiment.getDF()
    print("df looks like:")
    spark_df.show()
    schema = experiment.schema
    sdftools.print_item(spark_df, "Flat Experiment DF")

    queries = [query]
    spark_df = sdftools.aggregateGeolevels(spark, spark_df, geolevels)
    spark_df = sdftools.answerQueries(spark_df, schema, queries)


    #spark_df.show(spark_df.count(), False)

    spark_df = sdftools.getL1(spark_df, colname = "L1", col1=AC.PRIV, col2=AC.ORIG)
    spark_df = sdftools.getL2(spark_df, colname = "L2", col1=AC.PRIV, col2=AC.ORIG)
    # apply bin functions for particular tables
    if (table_name in table_default_bucket_list):
        spark_df = sdftools.getCountBins(spark_df, column=AC.ORIG, bins=[0,1000,5000,10000,50000,100000]).persist()
    if (table_name in table_default_bucket_list2):
        spark_df = sdftools.getCountBins(spark_df, column=AC.ORIG, bins=[0,10,100]).persist()
    # This finds overall metrics
    #spark_df.show(spark_df.count(), False)

    for g in geolevels:
        spark_df=spark_df[spark_df['geolevel']==g]
        print("This has all levels")
        spark_df.show(150, False)

        metrics_dataframe = sdftools.mattsmetrics(spark_df,spark)
        Counts = spark_df.count()
        print("Counts are", Counts)
        newRow = spark.createDataFrame([(Counts, "Counts")])
        metrics_dataframe = metrics_dataframe.union(newRow)
        pandas_df =metrics_dataframe.toPandas()
        csv_savepath = experiment.save_location_linux + f"{table_name}_{g}.csv"
        du.makePath(du.getdir(csv_savepath))
        pandas_df.to_csv(csv_savepath, index=False)
        if table_name in table_default_bucket_list2: # If data needs bucketing

            for b in default_buckets2: # calculate Metrics at each bucket
                subset_sparkdf =spark_df[spark_df['orig_count_bin']==b] #subset into bins
                subset_sparkdf=subset_sparkdf.subtract(subset_sparkdf.filter(subset_sparkdf.level.rlike("Not"))) # Removes instances of Not Hispanic..from dataframe
                subset_sparkdf.show(100, False)
                print("Make sure its bucketed and without 'Not' values")
                subset_metrics = sdftools.mattsmetrics(subset_sparkdf,spark)
                Counts = subset_sparkdf.count()
                newRow = spark.createDataFrame([(b, "Bucket")])
                newRow1 = spark.createDataFrame([(Counts, "Counts")])
                subset_metrics = subset_metrics.union(newRow).union(newRow1)
                pandas_df =subset_metrics.toPandas()
                csv_savepath = experiment.save_location_linux + f"{table_name}_{g}_{b}.csv"
                du.makePath(du.getdir(csv_savepath))
                pandas_df.to_csv(csv_savepath, index=False)
def main():
    analysis, spark = setup()
    #table_dicts = [tabledict_EPT_no3]
    #table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2]
    table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2, tabledict_EPT_no3]
    #table_dicts = [tabledict_H1]
    #table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2]
    for table_dict in table_dicts:
        for table_name, queries in table_dict.items():
            geolevels = geolevels_dict[table_name]
            schema = schema_dict[table_name]
            print(f"For table {table_name}, using schema {schema}")
            for query in queries:
                MattsMetrics(query, table_name, analysis, spark, geolevels, schema=schema)

if __name__ == "__main__":
    main()
