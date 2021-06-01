######################################################
# To Run this script:
#
# cd into das_decennial/analysis/
# analysis=analysis_scripts/relative_l1_error.py bash run_analysis.sh
#
# More info on analysis can be found here:
# https://github.ti.census.gov/CB-DAS/das_decennial/blob/master/analysis/readme.md
######################################################
import csv

import analysis.tools.sdftools as sdftools
import analysis.tools.datatools as datatools
import analysis.tools.setuptools as setuptools
import analysis.constants as AC
from pyspark.sql import Row

from pyspark.sql.types import DoubleType

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

#queries = [CC.CENRACE_7LEV_TWO_COMB + " * hispanic"]
queries = ["cenrace_7lev_two_comb * hispanic * voting"]
#denom_query = "total"
#denom_level = "total"
denom_query="votingage"
denom_level="18 and over"

all_geolevels =  ["OSE", C.BLOCK_GROUP, C.PLACE] #'STATE', 'AIAN_AREAS', 'OSE', 'AIANTract', 'AIANState', 'AIANBlock', C.TRACT, C.STATE, C.BLOCK]

POPULATION_CUTOFF = 500
POPULATION_BIN_STARTS = np.arange(51, dtype=int) * 50
QUANTILES = [xi / 20. for xi in np.arange(20)] + [.975, .99, 1.]
THRESHOLD = 0.05


def listDefault():
    return all_geolevels

geolevels_dict = defaultdict(listDefault)

geolevels_dict["EPT3_ROW12_TOMR"]       = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW12_6RACES"]     = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW14_TOMR"]       = [C.COUNTY]
geolevels_dict["EPT3_ROW14_6RACES"]     = [C.COUNTY]
geolevels_dict["EPT3_ROW15"]            = [C.COUNTY]    # Also for PR Municipios
geolevels_dict["H1"]                    = all_geolevels + [C.US]
major_omb_race_names    = ['white','black','aian','asian','nhopi','sor']
def schemaDefault():
    return "PL94"
schema_dict = defaultdict(schemaDefault)
schema_dict["H1"] = "H1_SCHEMA"         # For H1-only internal runs as of 4/2/2020

paths = ['s3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2c-MultipassRounder-aian_spine-eps2-dynamic_geolevel-20201231-110811/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1a-MultipassRounder-opt_spine-eps4-dynamic_geolevel-20201228-115337/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1a-MultipassRounder-opt_spine-eps10-dynamic_geolevel-20201228-115337/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1a-MultipassRounder-opt_spine-eps50-dynamic_geolevel-20201228-115337/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1b-MultipassRounder-opt_spine-eps10-dynamic_geolevel-20201228-115337/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2b-MultipassRounder-aian_spine-eps10-dynamic_geolevel-20201228-142548/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2b-MultipassRounder-aian_spine-eps20-dynamic_geolevel-20201228-142548/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2b-MultipassRounder-opt_spine-eps10-dynamic_geolevel-20201228-142548/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2b-MultipassRounder-opt_spine-eps20-dynamic_geolevel-20201228-142548/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1c-MultipassRounder-aian_spine-eps4-dynamic_geolevel-20201228-142933/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1c-MultipassRounder-aian_spine-eps10-dynamic_geolevel-20201228-142933/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1c-MultipassRounder-aian_spine-eps20-dynamic_geolevel-20201228-142933/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1c-MultipassRounder-opt_spine-eps10-dynamic_geolevel-20201228-142933/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2a-MultipassRounder-aian_spine-eps10-dynamic_geolevel-20201228-142933/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2a-MultipassRounder-opt_spine-eps4-dynamic_geolevel-20201228-142933/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2a-MultipassRounder-opt_spine-eps10-dynamic_geolevel-20201228-142933/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2a-MultipassRounder-opt_spine-eps20-dynamic_geolevel-20201228-142933/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1a-MultipassRounder-aian_spine-eps2-dynamic_geolevel-20201229-184746/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1a-MultipassRounder-aian_spine-eps4-dynamic_geolevel-20201229-184746/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1a-MultipassRounder-aian_spine-eps10-dynamic_geolevel-20201229-184746/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2b-MultipassRounder-aian_spine-eps10-dynamic_geolevel-20201229-190456/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2b-MultipassRounder-opt_spine-eps10-dynamic_geolevel-20201229-190456/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2c-MultipassRounder-aian_spine-eps10-dynamic_geolevel-20201229-190456/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2c-MultipassRounder-opt_spine-eps2-dynamic_geolevel-20201229-190456/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1c-MultipassRounder-aian_spine-eps4-dynamic_geolevel-20201229-185422/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1c-MultipassRounder-aian_spine-eps10-dynamic_geolevel-20201229-185422/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1c-MultipassRounder-opt_spine-eps4-dynamic_geolevel-20201229-185422/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/']


run_ids = []
for path in paths:
    run_id_str = path.split("dsep_experiments_dec_2020/DSEP-DEC2020-")[1]
    run_id = ""
    while run_id_str[:4] != "/mdf":
        run_id += run_id_str[0]
        run_id_str = run_id_str[1:]
    run_ids.append(run_id)


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


def analyzeQuery(query, analysis, spark, geolevel, schema_name, path):
    """
        Main plotting fxn.
            query           : str, name of a valid query for the target experiment's schema
            table_name      : str, name of a table (used for file-naming conventions)
            analysis        : Analysis setuptools.setup object, organizes Analysis metadata
            spark           : SparkSession object, attached to analysis object
            geolevels       : [str, ...], geolevels to compute over for the current query
            buckets         : [(int,int), ...], list of mutually exclusive bucket boundaries for Tab(CEF) bucketing
            schema          : str, name of ../programs/schema/schemas/schemamaker.py schema associated with target data
        Note, also, major control parameters hard-coded in getPaths for setting experiment ingest locations from s3.
    """
    # To avoid cases in which max(numerator_query_levels)/denom_query_level >= 1:
    assert query != denom_query

    experiment_name = "NA"
    experiment = analysis.make_experiment(experiment_name, [path], schema_name=schema_name, dasruntype=AC.EXPERIMENT_FRAMEWORK_FLAT, budget_group='1', run_id='run1.0')
    spark_df = experiment.getDF()
    sdftools.print_item(experiment.__dict__, "Experiment Attributes")

    schema = experiment.schema
    sdftools.print_item(spark_df, "Flat Experiment DF")

    spark_df = sdftools.aggregateGeolevels(spark, spark_df, geolevel)
    spark_df = sdftools.remove_not_in_area(spark_df, [geolevel])
    spark_df = sdftools.answerQueries(spark_df, schema, [query, denom_query])

    spark_df = sdftools.getL1Relative(spark_df, colname="L1Relative", denom_query=denom_query, denom_level=denom_level).persist()
    query_counts = spark_df.rdd.map(lambda row: (row[AC.QUERY],)).countByKey()
    query_counts_keys = list(query_counts.keys())
    assert len(query_counts_keys) == 1 and query_counts_keys[0] == query

    spark_rdd_prop_lt = spark_df.rdd.map(lambda row: (int(np.digitize(row["orig"], POPULATION_BIN_STARTS)), 1. if row["L1Relative"] <= THRESHOLD else 0.))
    spark_df_prop_lt = spark_rdd_prop_lt.toDF(["pop_bin", "prop_lt"])

    # Find the proportion of geounits that have L1Relative errors less than threshold for each bin:
    grouped_df_prop_lt = spark_df_prop_lt.groupBy("pop_bin").agg({"prop_lt":"avg", "*":"count"})
    prop_lt = grouped_df_prop_lt.collect()
    n_bins = len(POPULATION_BIN_STARTS) + 1
    prop_lt_list = [None] * n_bins
    prop_lt_counts = [0] * n_bins
    for row in prop_lt:
        prop_lt_list[int(row["pop_bin"])] = np.round(row["avg(prop_lt)"], 5)
        prop_lt_counts[int(row["pop_bin"])] = int(row["count(1)"])
    print(prop_lt_list)
    print(f"geounits counts for each bin: {[(POPULATION_BIN_STARTS[k], prop_lt_counts[k]) for k in range(len(POPULATION_BIN_STARTS))]}")

    population_bin_starts = np.concatenate(([-np.inf], POPULATION_BIN_STARTS, [np.inf]))
    ranges = list(zip(population_bin_starts[:-1], population_bin_starts[1:] - 1))
    assert len(prop_lt_list) == (len(population_bin_starts) - 1)
    prop_lt_reformat = list(zip(ranges, prop_lt_list))

    spark_df = spark_df.filter(spark_df.orig >= POPULATION_CUTOFF)
    # Count above POPULATION_CUTOFF
    count = spark_df.count()
    # For the quantiles and the avg, we will omit geounits that would not have had a well defined L1Relative metric well defined
    # due to division by zero: (See the comments in the UDF used in sdftools.getL1Relative() for more detail.)
    spark_df = spark_df.filter(spark_df.L1Relative != 2.)
    count_correct_sign = spark_df.count()

    quantiles_df = sdftools.getGroupQuantiles(spark_df, columns=["L1Relative"], groupby=[AC.QUERY, AC.GEOLEVEL], quantiles=QUANTILES).collect()
    avg = spark_df.groupBy([AC.QUERY, AC.GEOLEVEL]).avg("L1Relative").collect()

    quantiles_dict = {}
    for row in quantiles_df:
        quantiles_dict[float(row["quantile"])] = np.round(row["L1Relative"], 5)
    quantiles_reformat = [(quant, quantiles_dict[quant]) for quant in QUANTILES]
    error_metrics = [np.round(avg[0]["avg(L1Relative)"], 5), count, count_correct_sign] + [quantiles_reformat] + [prop_lt_reformat]

    print("error_metrics:", error_metrics)
    return error_metrics


def main():
    with open('relative_l1_metrics.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Run ID", "Query", "Geolevel", "Avg L1 Ratio", "Number of Geounits", "Number of Geounits with Correct Sign", "Quantiles", "Binned Proportion of Geounits with L1Relative error <= " + str(THRESHOLD)])

        schema = "PL94"
        analysis, spark = setup()

        for query in queries:
            for run_id, path in zip(run_ids, paths):
                for geolevel in all_geolevels:
                    new_row = [run_id, query, geolevel] + analyzeQuery(query, analysis, spark, geolevel, schema, path)
                    writer.writerow(new_row)

if __name__ == "__main__":
    main()
