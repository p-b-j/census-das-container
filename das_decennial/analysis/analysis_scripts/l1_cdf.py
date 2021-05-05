######################################################
# To Run this script:
#
# cd into das_decennial/analysis/
# analysis=analysis_scripts/l1_cdf.py bash run_analysis.sh
#
# More info on analysis can be found here:
# https://github.ti.census.gov/CB-DAS/das_decennial/blob/master/analysis/readme.md
######################################################

import csv

import analysis.tools.sdftools as sdftools
import analysis.tools.datatools as datatools
import analysis.tools.setuptools as setuptools
import analysis.constants as AC
from pyspark.sql import functions as sf
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

queries = ["total"] # ["cenrace_7lev_two_comb * hispanic * voting"]
all_geolevels =  ["AIANState", "OSE"]
# This script provides the CDF of the L1 error, evaluated from 0 to MAX_L1_ERROR in intervals of DOMAIN_ELEM_MULT:
MAX_L1_ERROR = 25
DOMAIN_ELEM_MULT = 5
# As well as the CDF evaluate at THRESHOLD_FOR_PROP:
THRESHOLD_FOR_PROP = 5

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

simulation_paths = [['s3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy2c-MultipassRounder-aian_spine-eps2-dynamic_geolevel-20201231-110811/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/',
's3://uscb-decennial-ite-das/runs/production/dsep_experiments_dec_2020/DSEP-DEC2020-PL94-strategy1a-MultipassRounder-opt_spine-eps4-dynamic_geolevel-20201228-115337/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/']]





def make_run_ids_from_paths(paths):
    run_ids = []
    for path in paths:
        run_id_str = path.split("dsep_experiments_dec_2020/DSEP-DEC2020-")[1]
        run_id = ""
        while run_id_str[:4] != "/mdf":
            run_id += run_id_str[0]
            run_id_str = run_id_str[1:]
        run_ids.append(run_id)
    return run_ids

def make_simulation_run_ids_from_paths(simulation_paths):
    simulation_run_ids = []
    for simulation_path in simulation_paths:
        simulation_run_ids.extend(make_run_ids_from_paths([simulation_path[0]]))
    return simulation_run_ids

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
    experiment_name = "NA"
    experiment = analysis.make_experiment(experiment_name, [path], schema_name=schema_name, dasruntype=AC.EXPERIMENT_FRAMEWORK_FLAT, budget_group='1', run_id='run1.0')
    spark_df = experiment.getDF()
    sdftools.print_item(experiment.__dict__, "Experiment Attributes")

    schema = experiment.schema
    sdftools.print_item(spark_df, "Flat Experiment DF")

    spark_df = sdftools.aggregateGeolevels(spark, spark_df, geolevel)

    if geolevel == C.PLACE:
        spark_df = spark_df.filter(spark_df.geocode[2:7] != "99999")
    elif geolevel == 'AIAN_AREAS':
        spark_df = spark_df.filter(spark_df.geocode != "9999")
    elif geolevel == 'OSE':
        spark_df = spark_df.filter(sf.col(AC.GEOCODE).substr(sf.length(sf.col(AC.GEOCODE)) - 4, sf.length(sf.col(AC.GEOCODE))) != "99999")
    elif geolevel == 'AIANTract':
        spark_df = spark_df.filter(spark_df.geocode != "9" * 11)
    elif geolevel == 'AIANState':
        spark_df = spark_df.filter(spark_df.geocode != "99")
    elif geolevel == 'AIANBlock':
        spark_df = spark_df.filter(spark_df.geocode != "9" * 16)
    elif geolevel == 'COUNTY_NSMCD':
        spark_df = spark_df.filter(spark_df.geocode != "999")

    spark_df = sdftools.answerQueries(spark_df, schema, [query])
    # AC.PRIV means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
    spark_df = sdftools.getL1(spark_df, colname="L1", col1=AC.PRIV, col2=AC.ORIG)
    rdd = spark_df.rdd.map(lambda row: row["L1"])
    l1_errors = np.array(rdd.collect())
    return l1_errors

def compute_metrics(query, analysis, spark, geolevel, schema_name, paths):
    l1_errors = np.array([])
    for path in paths:
        l1_errors = np.concatenate((l1_errors, analyzeQuery(query, analysis, spark, geolevel, schema_name, path)))
    cdf_vals = [(k * DOMAIN_ELEM_MULT, np.round(np.mean(l1_errors <= k * DOMAIN_ELEM_MULT), 2)) for k in range(MAX_L1_ERROR // DOMAIN_ELEM_MULT)]
    prop_lt_thresh = np.round(np.mean(l1_errors < THRESHOLD_FOR_PROP), 2)
    count = len(l1_errors) // len(paths)
    res = [prop_lt_thresh, count, cdf_vals]
    print(res)
    return res

def main():
    run_ids = make_simulation_run_ids_from_paths(simulation_paths)
    with open('l1_cdf.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Run ID", "Query", "Geolevel", f"Proportion of Geounits with L1 error <= {THRESHOLD_FOR_PROP}", "Number of Geounits", "Values of CDF"])

        schema = "PL94"
        analysis, spark = setup()

        for query in queries:
            for run_id, paths in zip(run_ids, simulation_paths):
                for geolevel in all_geolevels:
                    new_row = [run_id, query, geolevel] + compute_metrics(query, analysis, spark, geolevel, schema, paths)
                    writer.writerow(new_row)

if __name__ == "__main__":
    main()
