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

# queries = ["total"] # ["voting"]
all_geolevels =  ["AIANState", "County"]
queries = ["total", "voting"]
denom_query="total"
denom_total="total"
# This script allows statistics to be aggregated over multiple simulation iterations. To do so, simulation_paths can be formatted as [[simulation_iteration_path_1, simulation_iteration_path_2, ...]].
# Note that this also allows for statistics to be computed independently on separate runs using the alternative format: [[das_run_path_1], [das_run_path_2], ...].
simulation_paths = [
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0412-1117-TRIAL1/DAS-PPMF-EPS10-0412-1117-TRIAL1/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0412-1604-TRIAL2/DAS-PPMF-EPS10-0412-1604-TRIAL2/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0412-1606-TRIAL3-2/DAS-PPMF-EPS10-0412-1606-TRIAL3-2/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0412-1607-TRIAL4/DAS-PPMF-EPS10-0412-1607-TRIAL4/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0412-1712-TRIAL5-2/DAS-PPMF-EPS10-0412-1712-TRIAL5-2/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0412-2011-TRIAL6/DAS-PPMF-EPS10-0412-2011-TRIAL6/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0412-2012-TRIAL7/DAS-PPMF-EPS10-0412-2012-TRIAL7/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0412-2013-TRIAL8/DAS-PPMF-EPS10-0412-2013-TRIAL8/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0413-0838-TRIAL9/DAS-PPMF-EPS10-0413-0838-TRIAL9/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0413-0840-TRIAL10/DAS-PPMF-EPS10-0413-0840-TRIAL10/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0413-0841-TRIAL11/DAS-PPMF-EPS10-0413-0841-TRIAL11/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0413-0842-TRIAL12/DAS-PPMF-EPS10-0413-0842-TRIAL12/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0413-0843-TRIAL13/DAS-PPMF-EPS10-0413-0843-TRIAL13/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-DAS-PPMF-EPS10-0413-1635-TRIAL14/DAS-DAS-PPMF-EPS10-0413-1635-TRIAL14/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-DAS-PPMF-EPS10-0413-1636-TRIAL15/DAS-DAS-PPMF-EPS10-0413-1636-TRIAL15/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-DAS-PPMF-EPS10-0413-1637-TRIAL16/DAS-DAS-PPMF-EPS10-0413-1637-TRIAL16/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-DAS-PPMF-EPS10-0413-1638-TRIAL17/DAS-DAS-PPMF-EPS10-0413-1638-TRIAL17/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-DAS-PPMF-EPS10-0413-1639-TRIAL18/DAS-DAS-PPMF-EPS10-0413-1639-TRIAL18/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0414-1019-TRIAL19-3/DAS-PPMF-EPS10-0414-1019-TRIAL19-3/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0414-0603-TRIAL20/DAS-PPMF-EPS10-0414-0603-TRIAL20/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0414-0604-TRIAL21-2/DAS-PPMF-EPS10-0414-0604-TRIAL21-2/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0414-1626-TRIAL22/DAS-PPMF-EPS10-0414-1626-TRIAL22/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0414-0605-TRIAL22/DAS-PPMF-EPS10-0414-0605-TRIAL22/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0415-0009-TRIAL24/DAS-PPMF-EPS10-0415-0009-TRIAL24/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"],
    ["s3://uscb-decennial-ite-das/runs/tests/DAS-PPMF-EPS10-0415-0010-TRIAL25/DAS-PPMF-EPS10-0415-0010-TRIAL25/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/"]
]

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

def make_run_ids_from_paths(paths):
    run_ids = []
    for path in paths:
        start_str = "/runs/"
        stop_str = "/mdf/"
        start = path.find(start_str) + len(start_str)
        # if start_str not in path str, set start to 0
        if start == -1 + len(start_str):
            start = 0
        stop = path.find(stop_str)
        # if stop_str not in path str, set stop to end of string
        if stop == -1:
            stop = len(path)
        run_ids.append(path[start:stop])
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
    spark_df = sdftools.remove_not_in_area(spark_df, [geolevel])
    spark_df = sdftools.answerQueries(spark_df, schema, [query])
    spark_df = sdftools.getL1(spark_df, colname="L1", col1=AC.PRIV, col2=AC.ORIG)
    rdd = spark_df.rdd.map(lambda row: row["L1"])
    l1_errors = np.array(rdd.collect())
    return l1_errors

def compute_metrics(query, analysis, spark, geolevel, schema_name, paths):
    l1_errors = np.array([])
    for path in paths:
        l1_errors = np.concatenate((l1_errors, analyzeQuery(query, analysis, spark, geolevel, schema_name, path)))
    mae = np.mean(l1_errors)
    cdf_vals = [(k * DOMAIN_ELEM_MULT, np.round(np.mean(l1_errors <= k * DOMAIN_ELEM_MULT), 2)) for k in range(MAX_L1_ERROR // DOMAIN_ELEM_MULT)]
    prop_lt_thresh = np.round(np.mean(l1_errors < THRESHOLD_FOR_PROP), 2)
    count = len(l1_errors) // len(paths)
    res = [prop_lt_thresh, count, cdf_vals, mae]
    print(res)
    return res

def main():
    run_ids = make_simulation_run_ids_from_paths(simulation_paths)
    with open('l1_cdf.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Run ID", "Query", "Geolevel", f"Proportion of Geounits with L1 error <= {THRESHOLD_FOR_PROP}", "Number of Geounits", "Values of CDF", "MAE"])
        schema = "PL94"
        analysis, spark = setup()
        for query in queries:
            for run_id, paths in zip(run_ids, simulation_paths):
                for geolevel in all_geolevels:
                    new_row = [run_id, query, geolevel] + compute_metrics(query, analysis, spark, geolevel, schema, paths)
                    writer.writerow(new_row)

if __name__ == "__main__":
    main()
