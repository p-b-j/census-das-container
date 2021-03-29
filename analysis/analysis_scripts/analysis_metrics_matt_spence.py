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
        "EPT1_P1"           :   ["total"],
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

#geolevels_dict["EPT3_ROW2_TOMR"]        = [C.STATE]     # Only needed for US (but most current runs State-only)
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
major_omb_race_names    = ['white','black','aian','asian','nhopi','sor']

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

"""
def sepBounds(rows, column, buckets):
    pandas_df = pandas.DataFrame(rows)
    for bindex in range(0, len(buckets)):
        pandas_df[f"Bin{bindex}"] = (buckets[bindex][0] <= pandas_df[column]) & (pandas_df[column] <= buckets[bindex][1])
    rows = pandas_df.to_dict('records')
    return rows

def binIndexToInteger(row, buckets):
    for bindex, bucket in enumerate(buckets):
        if row[f"Bin{bindex}"] == True:
            return str(bucket)
"""

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


def getCountBins(df, column=AC.ORIG, bins=[0,1000,5000,10000,50000,100000]):
    udf = makeCountBinsFunction(bins, udf=True)
    df = df.withColumn(f"{column}_count_bin", udf(sf.col(column)))
    return df


def makeCountBinsFunction(bins, udf=False):
    def countbins(val):
        mybin = None
        for i,b in enumerate(bins[1:]):
            #print(f"{val} < {b} | {val < b}")
            if val < b:
                mybin = f"[{bins[i]}-{bins[i+1]})"
                break
        if mybin is None:
            mybin = f"{bins[-1]} +"
        return mybin
    if udf:
        fxn = sf.udf(lambda val: countbins(val))
    else:
        fxn = countbins
    return fxn

def analyzeQuery(query, table_name, analysis, spark, geolevels, buckets=default_buckets, schema="DHCP_HHGQ"):
    """
        Main plotting fxn.

            query           : str, name of a valid query for the target experiment's schema
            table_name      : str, name of a table (used for file-naming conventions)
            analysis        : Analysis setuptools.setup object, organizes Analysis metadata
            spark           : SparkSession object, attached to analysis object
            geolevels       : [str, ...], geolevels to compute over for the current query
            buckets         : [(int,int), ...], list of mutually exclusive bucket boundaries for Tab(CEF) bucketing

        Note, also, major control parameters hard-coded in getPaths for setting experiment ingest locations from s3.
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
    #spark_df = sdftools.getAvgAbsErrorByTrueCountRuns(spark_df, bins=[0,1,10,100,1000,10000]).persist()
    print("Here it is stupid:")

    spark_df.show()

    u=spark_df.withColumn('diff',sf.col('priv')-sf.col('orig'))
    u=u.withColumn('abs diff', sf.abs(sf.col('diff')))
    u = getCountBins(u, column=AC.ORIG, bins=[0,1000,5000,10000,50000,100000]).persist()
#    z=u.toPandas()
    for b in default_buckets: # calculate MAE, RMS, M
        ze=u[u['orig_count_bin']==b]
        rows_no=ze.count()
        sum_absdiff = ze.groupBy().agg(sf.sum('abs diff')).collect()[0][0]
        #print(rows_no)
        #print(sum_absdiff)
        q=(sum_absdiff/rows_no)
        print("Bucket size is", b)
        print("MAE value is", q)
        ze=ze.withColumn('sq lit',sf.lit(2))
        ze=ze.withColumn('sq abs diff', sf.pow(sf.col('abs diff'),sf.col('sq lit')))

        sum_sqabsdiff = ze.groupBy().agg(sf.sum('sq abs diff')).collect()[0][0]
        r = (sum_sqabsdiff/rows_no)
        r = mathy.sqrt(r)
        print("RMS value is", r)
        avg_geo = ze.groupBy().avg('orig').collect()[0][0]
        COV = 100*r/(avg_geo)
        print("Cov value is", COV)
        ze=ze.withColumn('abs diff div cef', sf.col('abs diff')/sf.col('orig'))
        sum_absdivcef = ze.groupBy().agg(sf.sum('abs diff div cef')).collect()[0][0]
        mape = 100*(sum_absdivcef/rows_no)

        print("MAPE value is", mape)

        ze=ze.withColumn('diff div cef', sf.col('diff')/sf.col('orig'))
        sum_diffdivcef = ze.groupBy().agg(sf.sum('diff div cef')).collect()[0][0]
        malpe = 100*(sum_diffdivcef/rows_no)

        print("MALPE value is", malpe)
        print("Counts of percent differences between 5 and 10 percent")
       # ze.groupBy().agg(sf.count(sf.when(sf.col("abs diff div cef")>0.05, True)),sf.count(sf.when(sf.col("abs diff div cef")<0.1,True))).show()
      #  ze.groupBy().agg(sf.count(sf.when(sf.col("abs diff div cef")>0.05 and sf.col("abs diff div cef")<0.1),True)).show()
        print("Counts of percent differences greater than 10 percent")
        ze.groupBy().agg(sf.count(sf.when(sf.col("abs diff div cef")>0.1, True))).show()




    print(u.show(100))

    pandas_df = u.toPandas()
    csv_savepath = experiment.save_location_linux + f"humbug.csv"
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
                analyzeQuery(query, table_name, analysis, spark, geolevels, schema=schema)

if __name__ == "__main__":
    main()
