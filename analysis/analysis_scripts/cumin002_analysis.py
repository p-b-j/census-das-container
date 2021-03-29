# This script file implements violin plots for total population entities, satisfying Executive Priority tabulations # 1
# Original Author: Vikram Rao [<=3/24/2020]
# Amended By: Philip Leclerc [3/25/2020]
# Using Supporting Code From: Brett Moran [<= 3/24/2020]


######################################################
# To Run this script:
#
# cd into das_decennial/analysis/
# analysis=analysis_scripts/cumin002_analysis.py bash run_analysis.sh
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
        "EPT1_P1"           :   ["cenrace_7_lev_two_comb * hispanic", "total"] # ["cenrace_7lev_two_comb * hispanic", "total"]
}

tabledict_EPT_no2 = {
         "EPT2_P1"           :   ["numraces","cenrace"],
         "EPT2_P2"           :   ["hispanic"],#,"hispanic * numraces","hispanic * cenrace"],
         "EPT2_P3"           :   ["votingage"],#"votingage * numraces","votingage * cenrace"],
       # "EPT2_P4"           :   ["votingage * hispanic","votingage * hispanic * numraces","votingage * hispanic * cenrace"],
       # "EPT2_P5"           :   ["instlevels","gqlevels"],
}

tabledict_H1 = {"H1":["h1"],}

all_geolevels =  ['STATE', 'AIAN_AREAS', 'OSE', 'AIANTract', 'AIANState', 'AIANBlock', C.TRACT, C.STATE, C.BLOCK]
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

def getPathsAndName(schema_name, query, table_name, eps):
    """
        Copy and re-name to switch input locations.
    """
    print(f"Get paths received schema {schema_name}")

    S3_BASE="s3://uscb-decennial-ite-das/users"
    num_trials = 1
    JBID = "cumin002"   # JBID used in s3 paths for saved runs (not necessarily your JBID)
    if schema_name == "DHCP_HHGQ":
        print("k")
    elif schema_name == "Household2010":
        raise NotImplementedError(f"Schema {schema_name} input locations not yet implemented.")
    elif schema_name == "H1_SCHEMA":
        # Example:
        # s3://uscb-decennial-ite-das/users/lecle301/cnstatDdpSchema_SinglePassRegular_natH1_Only_withMeasurements_v8/
        experiment_name = "Sept2020_Housing_Persons_PPMF_nonAIAN_discGauss_12DPQs_MultiL2_MultiRound"
        partial_paths = [f"data-run{RUN}.0-epsilon{eps:.1f}-BlockNodeDicts/" for RUN in range(1,num_trials+1)]
        path_prefix = f"{S3_BASE}/{JBID}/{experiment_name}/"
        paths = [path_prefix + partial_path for partial_path in partial_paths]
        remainder_paths = []
    elif schema_name == "PL94":
        spines = ["Opt", "AIAN", "nonAIAN"] * 2
        mechanisms = ["DGaus"] * 3 + ["Geom"] * 3
        experiment_names = ["cumin002/Sept2020_US_Persons_PPMF_opt_spine_v4_discGauss_12DPQs_MultiL2_MultiRound",
                            "lecle301/Sept2020_US_Persons_PPMF_AIAN_discGaussFixed_12DPQs_MultiL2_MultiRound",  # lecle301/Sept2020_US_Persons_PPMF_AIAN_discGaussFixed_12DPQs_MultiL2_MultiRound
                            "lecle301/Sept2020_US_Persons_PPMF_nonAIAN_discGauss_12DPQs_MultiL2_MultiRound",
                            "cumin002/Sept2020_US_Persons_PPMF_opt_spine_geometric_12DPQs_MultiL2_MultiRound",
                            "lecle301/Sept2020_US_Persons_PPMF_AIAN_geoMech_12DPQs_MultiL2_MultiRound",
                            "lecle301/Sept2020_US_Persons_PPMF_nonAIAN_geoMech_12DPQs_MultiL2_MultiRound"]
        paths = [f"{S3_BASE}/" + x + f"/data-run1.0-epsilon{eps:.1f}-BlockNodeDicts/" for x in experiment_names]
        # path_prefix = f"{S3_BASE}/"
        # paths = [path_prefix + partial_path for partial_path in partial_paths]
        remainder_paths = []
        experiment_name = 'AIAN_areas_from_Geo'
    else:
        raise ValueError(f"Schema {schema_name} not recognized when getting s3 ingest paths.")
    paths = paths + remainder_paths
    experiment_name += "_" + query + "_" + table_name
    return num_trials, paths, experiment_name, f"{eps:.1f}", spines, mechanisms # Change this for eps<0.1


def analyzeQuery(query, table_name, analysis, spark, geolevels, eps, schema_name="DHCP_HHGQ"):
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
    geolevel = geolevels[0]
    EPT = table_name[:4] + "_" + schema_name
    graph_title = f"Error for query: {table_name}-{query}, eps: {int(eps)}, geography: {geolevels}\nDisclosure Prohibited - Title 13 U.S.C."
    plt.figure(1, figsize=(20, 40))
    sns.set(style="ticks")
    fig, axes = plt.subplots(ncols=3, nrows=2, sharey=True, sharex=True)
    axes_flat = axes.ravel()
    sns.despine(fig=fig)
    #.set_title(graph_title)
    print(f"For table {table_name}, analyzing query {query} at geolevel {geolevel} with schema_name {schema_name} and eps: {eps}")
    num_trials, paths, experiment_name, eps_str, spines, mechanisms = getPathsAndName(schema_name, query, table_name, eps)
    plt.xscale('log')
    plt.yscale('symlog', linthreshy=100)
    for k, path in enumerate(paths):
        axes_flat[k].set_title(spines[k] + '_' + mechanisms[k])
        experiment = analysis.make_experiment(experiment_name, [path], schema_name=schema_name, dasruntype=AC.EXPERIMENT_FRAMEWORK_FLAT)
        spark_df = experiment.getDF()
        sdftools.print_item(experiment.__dict__, "Experiment Attributes")

        schema = experiment.schema
        sdftools.print_item(spark_df, "Flat Experiment DF")

        queries = [query]
        spark_df = sdftools.aggregateGeolevels(spark, spark_df, geolevels)
        # jitter points to make them visually distinct:
        spark_df = sdftools.answerQueries(spark_df, schema, queries) \
                           .withColumn("Error", sf.col("priv") - sf.col("orig") + sf.rand() - 1/2.) \
                           .withColumn("orig", sf.col("orig") + sf.rand() - 1/2.)
        if geolevel == "AIAN_AREAS":
            spark_df = spark_df.filter(spark_df.geocode != "9999")
        elif geolevel == 'OSE':
            spark_df = spark_df.filter(sf.col(AC.GEOCODE).substr(sf.length(sf.col(AC.GEOCODE)) - 4, sf.length(sf.col(AC.GEOCODE))) != "99999")
        elif geolevel == 'AIANTract':
            spark_df = spark_df.filter(spark_df.geocode != "9" * 11)
        elif geolevel == 'AIANState':
            spark_df = spark_df.filter(spark_df.geocode != "99")
        elif geolevel == 'AIANBlock':
            spark_df = spark_df.filter(spark_df.geocode != "9" * 16)
        # t = spark_df.filter(sf.abs(spark_df.Error) > 1000)
        spark_df = spark_df.select(["orig", "Error"])

        pandas_df = spark_df.toPandas()
        #if pandas_df.max()["Error"] == pandas_df.min()["Error"]:
        #    continue
        sns.scatterplot(x="orig", y="Error", data=pandas_df, alpha=.6, s=10, marker="+", ax=axes_flat[k])
        axes_flat[k].axhline(0., ls='--')

    filename = f"{table_name}_{query.replace(' ', '_')}_{geolevel}"
    plot_path = f"{experiment.save_location_linux}epsilon_{eps_str}/"
    du.makePath(plot_path)
    plt.savefig(plot_path + filename + ".png")
    plt.clf()


def main():
    analysis, spark = setup()
    table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2]
    for table_dict in table_dicts:
        for table_name, queries in table_dict.items():
            geolevels = geolevels_dict[table_name]
            schema = schema_dict[table_name]
            for query in queries:
                for eps in [4., 16.]:
                    for geolevel in geolevels:
                        print(f"For table {table_name}, using schema {schema}. Processing query {query}...")
                        analyzeQuery(query, table_name, analysis, spark, [geolevel], eps, schema_name=schema)


if __name__ == "__main__":
    main()
