# This script file implements violin plots for total population entities, satisfying Executive Priority tabulations # 1
# Original Author: Vikram Rao [<=3/24/2020]
# Amended By: Philip Leclerc [3/25/2020]
# Using Supporting Code From: Brett Moran [<= 3/24/2020]

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

import constants as C
from constants import CC

import das_utils as du
import programs.datadict as dd
import programs.dashboard
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
        "EPT2_P1"           :   ["numraces","cenrace"],
        "EPT2_P2"           :   ["hispanic","hispanic * numraces","hispanic * cenrace"],
        "EPT2_P3"           :   ["votingage","votingage * numraces","votingage * cenrace"],
        "EPT2_P4"           :   ["votingage * hispanic","votingage * hispanic * numraces","votingage * hispanic * cenrace"],
        "EPT2_P5"           :   ["instlevels","gqlevels"],
}
tabledict_EPT_no3 = {
        "EPT3_ROW2_TOMR"    :   ["tomr * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_6RACES"  :   ["allraces * hispanic * sex * agecat100plus"],
        "EPT3_ROW8_TOMR"    :   ["tomr * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_6RACES"  :   ["allraces * hispanic * sex * agecat85plus"],
        "EPT3_ROW12_TOMR"   :   ["tomr * sex * agecat85plus"],
        "EPT3_ROW12_6RACES" :   ["allraces * sex * agecat85plus"],
        "EPT3_ROW14_TOMR"   :   ["tomr * sex * hispanic * agePopEst18groups"],
        "EPT3_ROW14_6RACES" :   ["allraces * sex * hispanic * agePopEst18groups"],
        "EPT3_ROW15"        :   ["sex * agePopEst18groups"],
}
tabledict_H1 = {"H1":["h1"],}

all_geolevels = [C.COUNTY] # For very quick turnaround
#all_geolevels = [C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD, C.STATE, C.PLACE] # For 1-state runs
#all_geolevels = [C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD, C.STATE, C.US, C.PLACE] # For US runs
# For patching 'missing' geolevels in already saved analyses:
#all_geolevels = [C.US, C.PLACE]
#all_geolevels = [C.PLACE]
#all_geolevels = [C.STATE]   # Just for quick tests
#all_geolevels = [C.COUNTY]
def listDefault():
    return all_geolevels
geolevels_dict = defaultdict(listDefault)

#geolevels_dict["EPT3_ROW2_TOMR"]        = [C.STATE]     # Only needed for US (but most current runs State-only)
#geolevels_dict["EPT3_ROW2_6RACES"]      = [C.STATE]
#geolevels_dict["EPT3_ROW8_TOMR"]        = [C.STATE]
#geolevels_dict["EPT3_ROW8_6RACES"]      = [C.STATE]

#geolevels_dict["EPT3_ROW2_TOMR"]        = [C.STATE, C.US] # For US runs
#geolevels_dict["EPT3_ROW2_6RACES"]      = [C.STATE, C.US]
#geolevels_dict["EPT3_ROW8_TOMR"]        = [C.STATE, C.US]
#geolevels_dict["EPT3_ROW8_6RACES"]      = [C.STATE, C.US]

geolevels_dict["EPT3_ROW12_TOMR"]       = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW12_6RACES"]     = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW14_TOMR"]       = [C.COUNTY]
geolevels_dict["EPT3_ROW14_6RACES"]     = [C.COUNTY]
geolevels_dict["EPT3_ROW15"]            = [C.COUNTY]    # Also for PR Municipios
geolevels_dict["H1"]                    = all_geolevels + [C.US]
#geolevels_dict["H1"]                    = [C.STATE, C.US]  # Only for quick tests
#geolevels_dict["H1"]                    = [C.US]           # Only for very quick tests

default_buckets         = [(0,0), (1,10), (11,100), (100,1000), (1000,10000), (10000,float('inf'))]
major_omb_race_names    = ['white','black','aian','asian','nhopi','sor']

def schemaDefault():
    #return "DHCP_HHGQ"
    return "PL94"
schema_dict = defaultdict(schemaDefault)
schema_dict["H1"] = "H1_SCHEMA"         # For H1-only internal runs as of 4/2/2020
#schema_dict["H1"] = "Household2010"    # For CNSTAT DDP Run

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
    JBID = "lecle301"   # JBID used in s3 paths for saved runs (not necessarily your JBID)
    #if schema_name == "DHCP_HHGQ":
    if schema_name == "PL94":
        # Example:
        # s3://uscb-decennial-ite-das/users/lecle301/cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries4_version7/
        # cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_National_dpQueries1_officialCNSTATrun
        #experiment_name = "cnstatDdpSchema_multiL2_cellWiseRounder_nested_accuracyTest_RI"
        #experiment_name = "cnstatDdpSchema_multiL2_singlePassRounder_nested_accuracyTest"
        #s3://uscb-decennial-ite-das/users/lecle301/2010PL94_multipass_optTol_L1Rounder_GeometricMechanism_RI_4DPQs
        #experiment_name = "2010PL94_multipass_optTol_L1Rounder_GeometricMechanism_RI_4DPQs"
        #experiment_name = "2010PL94_multipass_optTol_L1Rounder_GaussianMechanism_VA_6DPQs_v2"
        #experiment_name = "2010PL94_multipass_optTol_L1Rounder_GeometricMechanism_VA_6DPQs_v2"
        experiment_name = "Sept2020_PPMF_AIAN_discGauss_12DPQs_MultiL2_MultiRoundVar1"
        #partial_paths = [f"data-run{RUN}.0-epsilon{eps:.1f}-BlockNodeDicts/" for RUN in range(1,num_trials+1)]
        partial_paths = [f"data-run{RUN}.0-epsilon{eps:.1f}/" for RUN in range(1,num_trials+1)]
        #partial_paths = [f"data-epsilon{eps:.1f}/" for RUN in range(1,num_trials+1)]
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
    experiment_name += "_" + query + "_" + table_name
    return num_trials, paths, experiment_name, f"{eps:.1f}" # Change this for eps<0.1

def saveFigs(plot_savepath, filetypes, filename, plt):
    for filetype in filetypes:
        filetype_savepath = plot_savepath + filetype + "/"
        full_path = filetype_savepath + filename + "." + filetype
        print(f"Making dir-path to {filetype_savepath}\nAnd saving to {full_path}")
        du.makePath(filetype_savepath)
        if filetype != "pdf":
            plt.savefig(full_path)
        else:
            plt.savefig(full_path, dpi=300)

def makePlots(experiment, experiment_name, table_name, queries, x_axis_variable_name,
                                           metric_name, geolevels, pandas_df, buckets,
                                           schema_name, eps_str, missing_rows_dict, num_trials):
    EPT = table_name[:4]+"_"+schema_name
    for query in queries:
        for geolevel in geolevels:
            subsetted_df = pandas_df[pandas_df['geolevel'] == geolevel]
            print("subsetted pandas df:")
            print(subsetted_df)
            if geolevel == C.PLACE: # If PLACE, drop the 'non-place' remainder geocode ST+99999
                subsetted_df = subsetted_df[~subsetted_df['geocode'].str.endswith('99999')]
                print("subsetted pandas df after dropping 99999 from PLACE geocodes:")
                print(subsetted_df)
            race_iterates = major_omb_race_names if ("EPT3" in table_name and "allraces *" in query) else [""]
            race_iterates = ["2+ Races"] if (race_iterates == [""] and "tomr *" in query) else race_iterates
            print(f"table {table_name}, query {query}, geolevel {geolevel}, race_iterates {race_iterates})")

            # TODO: graph titling/subsetting for distinct queries is getting convoluted. Re-factor?
            for race in race_iterates:
                plotting_df = subsetted_df
                if race in major_omb_race_names:
                    plotting_df = subsetted_df[subsetted_df['level'].str.contains(race)]

                bucket_counts = {}
                for bucket in buckets:
                    trueRows = plotting_df[plotting_df[x_axis_variable_name] == bucket]
                    bucket_counts[str(bucket)] = trueRows.shape[0]
                print(f"Geolevel {geolevel} has bucket_counts: {bucket_counts}")
                bucket_names = [str(bucket) for bucket in buckets if bucket_counts[bucket] != 0]

                pandas.set_option('display.max_columns', None)
                #pandas.set_option('display.max_rows', None)
                print(f"pandas df before re-naming has cols: {plotting_df.columns.values}")
                print(f"Before re-naming, first 25 rows: {plotting_df.head(25)}")
                for i in range(len(bucket_names)): # Adding newline + bucket count to x-axis labels
                    bucket_name = bucket_names[i]
                    bucket_count = bucket_counts[bucket_name]
                    new_bucket_name = bucket_name+"\n"+str(bucket_count)
                    #plotting_df = plotting_df.rename(columns={bucket_name:new_bucket_name})
                    plotting_df[x_axis_variable_name] = plotting_df[x_axis_variable_name].replace(bucket_name, new_bucket_name)
                    bucket_names[i] = new_bucket_name
                    print(f"bucket_name was {bucket_name}. Became {bucket_names[i]}")
                print(f"pandas df before plotting has cols: {plotting_df.columns.values}")
                print(f"After re-naming, first 25 rows: {plotting_df.head(25)}")

                if (np.array(list(bucket_counts.values())) > 0).any():
                    graph_title = f"Average L1 Error (over {num_trials} trials) for {query}, eps={eps_str}"
                    graph_title += f" Geolevel: {geolevel}"
                    if race in major_omb_race_names:
                        graph_title += f"Race Alone: {race.title()}"
                    if race == "2+ Races":
                        graph_title += f"2+ Races"
                    graph_title += f"\n{experiment_name}"
                    graph_title += f"\nExcluding {missing_rows_dict[geolevel]} CEF=MDF=0 Observations"
                    graph_title += f" (binned by CEF count)\nDisclosure Prohibited - Title 13 U.S.C."

                    #pandas.set_option('display.max_columns', None)
                    #pandas.set_option('display.max_rows', None)
                    # Scatterplot strips superimposed on violin plots
                    sns.set(style="whitegrid")

                    filename = f"{table_name}_{query.replace(' ', '_')}_{geolevel}_{race.replace(' ','_')}"
                    plot_savebase = f"{experiment.save_location_linux}plots/{EPT}/epsilon{eps_str}/"
                    for plot_type in ("violin", "scatterViolin"):
                        plot_savepath = plot_savebase + plot_type + "/"
                        if plot_type == "violin":
                            ax = sns.violinplot(x=x_axis_variable_name, y=metric_name, data=plotting_df, order=bucket_names,
                                                    inner = None, color="0.8") \
                                                    .set_title(graph_title)
                        elif plot_type == "scatterViolin":
                            ax = sns.stripplot(x=x_axis_variable_name, y=metric_name, data=plotting_df, order=bucket_names)  \
                                                    .set_title(graph_title)
                        else:
                            raise ValueError(f"plot_type {plot_type} not recognized.")
                        maxVal = plotting_df[metric_name].max()
                        minVal = plotting_df[metric_name].min()
                        print(f"maxVal type, val: {type(maxVal)}, {maxVal}")
                        print(f"minVal type, val: {type(minVal)}, {minVal}")
                        if abs(maxVal - minVal) < 0.1:
                            ax.axes.set(ylim=(minVal-10, maxVal+10))
                        #saveFigs(plot_savepath, ["jpg","pdf","png"], filename, plt)
                        saveFigs(plot_savepath, ["png"], filename, plt)
                    plt.clf()
                else:
                    print(f"No observations for {table_name}, {query}, {geolevel}, {race}. Plot not generated.")

def analyzeQuery(query, table_name, analysis, spark, geolevels, eps, buckets=default_buckets, schema="DHCP_HHGQ"):
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
    print(f"For table {table_name}, analyzing query {query} at geolevels {geolevels} with schema {schema}")
    schema_name = schema
    num_trials, paths, experiment_name, eps_str = getPathsAndName(schema_name, query, table_name, eps)
    print(f"Passing paths to Analysis experiment maker: {paths}")
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
    spark_df = sdftools.getAvgAbsErrorByTrueCountRuns(spark_df, bins=[0,1,10,100,1000,10000]).persist()
    missing_rows_pandas_df = sdftools.getMissingRowCounts(spark_df, schema, queries, groupby=[AC.GEOCODE, AC.GEOLEVEL, AC.PLB, AC.BUDGET_GROUP])
    missing_rows_dict = defaultdict(int)
    for index, row in missing_rows_pandas_df.iterrows():
        #print(f"missing df row # {index} geolevel, sum(missing) = {row['geolevel']},{row['sum(missing)']}")
        missing_rows_dict[row['geolevel']] = row['sum(missing)']
    spark_df.show()
    print("^^^^ with abs error, DF looks like ^^^^")

    metric_name = "Avg( |q(MDF) - q(CEF)| )"
    x_axis_variable_name = 'CEF Count, Binned'

    pandas_df = spark_df.toPandas()
    pandas_df = pandas_df.rename(columns={"abs_error":metric_name, "orig_count_bin":x_axis_variable_name})
    plt.figure(1, figsize=(11,8.5))
    plt.rc('axes', labelsize=8)
    print(f"pandas df before plotting has cols: {pandas_df.columns.values}")
    print(f"{x_axis_variable_name} column has distinct levels: {pandas_df[x_axis_variable_name].unique()}")
    buckets = pandas_df[x_axis_variable_name].unique()
    buckets = sorted(buckets, key=lambda bucket_name: largestIntInStr(bucket_name))
    print(f"Sorted bucket names: {buckets}")

    # Saving data frame
    csv_savepath = experiment.save_location_linux + f"{experiment_name}.csv"
    du.makePath(du.getdir(csv_savepath))
    pandas_df.to_csv(csv_savepath, index=False)

    makePlots(experiment, experiment_name, table_name, queries, x_axis_variable_name,
                                           metric_name, geolevels, pandas_df, buckets,
                                           schema_name, eps_str, missing_rows_dict, num_trials)

def main():
    analysis, spark = setup()
    #table_dicts = [tabledict_EPT_no1]
    #table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2]
    #table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2, tabledict_EPT_no3]
    #table_dicts = [tabledict_H1]
    table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2]
    #table_dicts = [tabledict_EPT_no2]
    #table_dicts = [tabledict_EPT_no3]
    for table_dict in table_dicts:
        for table_name, queries in table_dict.items():
            #if table_name in ("EPT1_P1", "EPT2_P1"):
            #if table_name in ["EPT2_P2"]:
            #if table_name in ["EPT2_P3"]:
            #if table_name in ["EPT2_P4"]:
            #if table_name in ["EPT2_P5"]:
            if True:
                geolevels = geolevels_dict[table_name]
                schema = schema_dict[table_name]
                for query in queries:
                    #for eps in [1., 4., 15., 25., 40., 50., 75., 100., 500.]:
                    for eps in [4., 15.]:
                        #for eps in [1., 4., 8., 10., 15., 20., 40., 100., 1000.]:
                        #for eps in [40., 50., 75., 100., 500.]:
                        print(f"For table {table_name}, using schema {schema}. Processing query {query}...")
                        #if query == "hispanic * cenrace":
                        #if query == "votingage * hispanic * cenrace" or query == "gqlevels":
                        if True:
                        #if query not in ("cenrace", "numraces"):
                        #if query not in ("total", "numraces","cenrace","hispanic","hispanic * numraces"):
                            analyzeQuery(query, table_name, analysis, spark, geolevels, eps, schema=schema)

if __name__ == "__main__":
    main()
