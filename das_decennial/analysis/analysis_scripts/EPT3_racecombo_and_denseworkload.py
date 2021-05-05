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

tabledict_EPT_no1_no2 = {
        "EPT1_P1"           :   ["total"],
        "EPT2_P1"           :   ["numraces","cenrace"],
        "EPT2_P2"           :   ["hispanic","hispanic * numraces","hispanic * cenrace"],
        "EPT2_P3"           :   ["votingage","votingage * numraces","votingage * cenrace"],
        "EPT2_P4"           :   ["votingage * hispanic","votingage * hispanic * numraces","votingage * hispanic * cenrace"],
        "EPT2_P5"           :   ["instlevels","gqlevels"],
}
tabledict_EPT_no3 = {
        "EPT3_ROW2_TOMR"    :   ["tomr * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_6RACES"  :   ["allraces * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_RACECOMBO":  ["racecombos * hispanic * sex * agecat100plus"],
        "EPT3_ROW8_TOMR"    :   ["tomr * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_6RACES"  :   ["allraces * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_RACECOMBO":  ["racecombos * hispanic * sex * agecat85plus"],
        "EPT3_ROW12_TOMR"   :   ["tomr * sex * agecat85plus"],
        "EPT3_ROW12_6RACES" :   ["allraces * sex * agecat85plus"],
        "EPT3_ROW14_TOMR"   :   ["tomr * sex * hispanic * agePopEst18groups"],
        "EPT3_ROW14_6RACES" :   ["allraces * sex * hispanic * agePopEst18groups"],
        "EPT3_ROW14_RACECOMBO": ["racecombos * sex * hispanic * agePopEst18groups"],
        "EPT3_ROW15"        :   ["sex * agePopEst18groups"],
}
tabledict_H1 = {"H1":["h1"],}

all_geolevels = [C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD, C.STATE]
#all_geolevels = [C.STATE]   # Just for quick tests
def listDefault():
    return all_geolevels
geolevels_dict = defaultdict(listDefault)
geolevels_dict["EPT3_ROW2_TOMR"]        = [C.STATE]     # Only needed for US (but most current runs State-only)
geolevels_dict["EPT3_ROW2_6RACES"]      = [C.STATE]     # Only needed for US (but most current runs State-only)
geolevels_dict["EPT3_ROW2_RACECOMBO"]   = [C.STATE]
geolevels_dict["EPT3_ROW8_TOMR"]        = [C.STATE]
geolevels_dict["EPT3_ROW8_6RACES"]      = [C.STATE]
geolevels_dict["EPT3_ROW8_RACECOMBO"]   = [C.STATE]
geolevels_dict["EPT3_ROW12_TOMR"]       = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW12_6RACES"]     = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW14_TOMR"]       = [C.COUNTY]
geolevels_dict["EPT3_ROW14_6RACES"]     = [C.COUNTY]
geolevels_dict["EPT3_ROW14_RACECOMBO"]  = [C.COUNTY]
geolevels_dict["EPT3_ROW15"]            = [C.COUNTY]    # Also for PR Municipios
geolevels_dict["H1"]                    = all_geolevels + [C.US]
#geolevels_dict["H1"]                    = [C.STATE, C.US]  # Only for quick tests
#geolevels_dict["H1"]                    = [C.US]           # Only for very quick tests

default_buckets         = [(0,0), (1,10), (11,100), (100,1000), (1000,10000), (10000,float('inf'))]
major_omb_race_names    = ['white','black','aian','asian','nhopi','sor']
race_combo_names        = ['White alone or in combination', 'Black alone or in combination', 'Aian alone or in combination', 'Asian alone or in combination', 'Nhopi alone or in combination', 'Some other race alone or in combination']

def schemaDefault():
    return "DHCP_HHGQ"
schema_dict = defaultdict(schemaDefault)
schema_dict["H1"] = "H1_SCHEMA"         # For H1-only internal runs as of 4/2/2020
#schema_dict["H1"] = "Household2010"    # For CNSTAT DDP Run

def getSparkDFWithAbsDiff(spark, df, geolevels, queries, schema):
    sparkDFWithAnswers = sdftools.getAnswers(spark, df, geolevels, schema, queries)
    # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
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

def makePlots(experiment, experiment_name, table_name, queries, x_axis_variable_name,
                                           metric_name, geolevels, pandas_df, buckets,
                                           schema_name, eps_str):
    EPT = table_name[:4]+"_"+schema_name
    for query in queries:
        for geolevel in geolevels:
            subsetted_df = pandas_df[pandas_df['geolevel'] == geolevel]
            race_iterates = major_omb_race_names if ("EPT3" in table_name and "allraces *" in query) else [""]
            race_iterates = race_combo_names if (race_iterates == [""] and "racecombos *" in query) else race_iterates
            race_iterates = ["2+ Races"] if (race_iterates == [""] and "tomr *" in query) else race_iterates
            print(f"table {table_name}, query {query}, geolevel {geolevel}, race_iterates {race_iterates})")

            # TODO: graph titling/subsetting for distinct queries is getting convoluted. Re-factor?
            for race in race_iterates:
                plotting_df = subsetted_df
                if race in major_omb_race_names:
                    plotting_df = subsetted_df[subsetted_df['level'].str.contains(race)]
                if race in race_combo_names:
                    plotting_df = subsetted_df[subsetted_df['level'].str.contains(race)]
                bucket_counts = {}
                for bucket in buckets:
                    trueRows = plotting_df[plotting_df[x_axis_variable_name] == bucket]
                    bucket_counts[bucket] = trueRows.shape[0]
                print(f"Geolevel {geolevel} has bucket_counts: {bucket_counts}")
                bucket_names = [str(bucket) for bucket in buckets if bucket_counts[bucket] != 0]
                if (np.array(list(bucket_counts.values())) > 0).any():
                    graph_title = f"Average L1 Error (over trials) for {query}\nGeolevel: {geolevel}"
                    if race in major_omb_race_names:
                        graph_title += f"\n Race Alone: {race.title()}"
                    if race in race_combo_names:
                        graph_title += f"\n Race Combination: {race.title()}"

                    if race == "2+ Races":
                        graph_title += f"\n 2+ Races"
                    graph_title += f"\n(binned by CEF count)\nDisclosure Prohibited - Title 13 U.S.C."

                    pandas.set_option('display.max_columns', None)
                    pandas.set_option('display.max_rows', None)
                    #print(f"Before plotting, plotting_df looks like:")
                    #print(plotting_df)
                    #print(f"Feeding plotting_df to seaborn with xvar {x_axis_variable_name} & yvar {metric_name}")
                    #print(f"And bucket_names are: {bucket_names}")

                    # Scatterplot strips superimposed on violin plots
                    sns.set(style="whitegrid")
                    ax = sns.violinplot(x=x_axis_variable_name, y=metric_name, data=plotting_df, order=bucket_names,
                                            inner = None, color="0.8") \
                                            .set_title(graph_title)

                    maxVal = plotting_df[metric_name].max()
                    minVal = plotting_df[metric_name].min()
                    print(f"maxVal type, val: {type(maxVal)}, {maxVal}")
                    print(f"minVal type, val: {type(minVal)}, {minVal}")
                    if abs(maxVal - minVal) < 0.1:
                        #print(f"violin ax has type {type(ax)} & methods: {dir(ax)}")
                        #print(f"violin ax.axes has type {type(ax.axes)} & methods: {dir(ax.axes)}")
                        ax.axes.set(ylim=(minVal-10, maxVal+10))
                    ax = sns.stripplot(x=x_axis_variable_name, y=metric_name, data=plotting_df, order=bucket_names)  \
                                            .set_title(graph_title)
                    #if geolevel == C.US:
                    #    #print(f"strip ax has type {type(ax)} & methods: {dir(ax)}")
                    #    ax.axes.set(ylim=(plotting_df[x_axis_variable_name].min - 10,plotting_df[x_axis_variable_name].max + 10))
                    plot_savepath = f"{experiment.save_location_linux}plots/{EPT}/epsilon{eps_str}/scatteredViolin/{experiment_name}_"
                    plot_savepath += f"{table_name}_{query.replace(' ', '_')}_{geolevel}_{race.replace(' ','_')}.pdf"
                    du.makePath(du.getdir(plot_savepath))
                    print(f"Saving scatterstrips w/ violins for query {query}, geolevel {geolevel}, & race {race} to: {plot_savepath}")
                    plt.savefig(plot_savepath)
                    plt.clf()
                else:
                    print(f"No observations for {table_name}, {query}, {geolevel}, {race}. Plot not generated.")

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
    #y=sdftools.getAnswers(spark,df,geolevels,schema,queries)

    # Old approach to computing df with abs diff, bucketed by true count:
    #sparkDFWithAbsDiff = getSparkDFWithAbsDiff(spark, spark_df, geolevels, queries, schema)
    #getSignedErrorByTrueCountRuns(spark_df, bins=[0,1,10,100,1000,10000]):
    #rdd = sdftools.getRowGroupsAsRDD(sparkDFWithAbsDiff, groupby=[AC.GEOLEVEL, AC.QUERY])
    #rdd = rdd.flatMapValues(lambda rows: sepBounds(rows, 'orig', buckets)).persist()
    #rdd = rdd.map(lambda row: Row(**row[1]))
    #spark_df = rdd.toDF().persist()

    # New (actually preexisting) approach to computing spark_df with abs diff, bucketed by true count:
    # (avoids pandas dfs inside mappers, which is RAM-hungry)
    spark_df = sdftools.aggregateGeolevels(spark, spark_df, geolevels)
    spark_df = sdftools.answerQueries(spark_df, schema, queries)
    spark_df = sdftools.getFullWorkloadDF(spark_df, schema, queries,groupby=[AC.GEOCODE, AC.GEOLEVEL, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP])
    spark_df = sdftools.getAvgAbsErrorByTrueCountRuns(spark_df, bins=[0,1,10,100,1000,10000]).persist()

    spark_df.show()
    print("^^^^ with abs error, DF looks like ^^^^")

    metric_name = "Avg( |q(MDF) - q(CEF)| )"
    x_axis_variable_name = 'CEF Count, Binned'

    # spark_df = spark_df.groupby(['geocode','geolevel','level','Bin0','Bin1','Bin2','Bin3','Bin4','Bin5']).avg()
    # Below spark_df has cols: geocode, geolevel, run_id, plb, budget_group, query, orig_count_bin, signed_error, re
    #spark_df = spark_df.groupby(['geocode', 'geolevel', 'plb', 'budget_group', 'query', 'orig_count_bin']).avg()
    #print("^^^^ after averaging, spark_df looks like ^^^^")
    pandas_df = spark_df.toPandas()
    #pandas_df = pandas_df.rename(columns={"avg(signed_error)":metric_name, "avg(orig)":"orig"})
    #pandas_df[x_axis_variable_name] = pandas_df.apply(lambda row: binIndexToInteger(row, buckets), axis=1)
    #pandas_df = pandas_df.rename(columns={"avg(signed_error)":metric_name, "avg(orig_count_bin)":"orig"})
    pandas_df = pandas_df.rename(columns={"abs_error":metric_name, "orig_count_bin":x_axis_variable_name})
    plt.figure(1, figsize=(11,8.5))
    plt.rc('axes', labelsize=8)
    print(f"pandas df before plotting has cols: {pandas_df.columns.values}")
    print(f"{x_axis_variable_name} column has distinct levels: {pandas_df[x_axis_variable_name].unique()}")
    buckets = pandas_df[x_axis_variable_name].unique()
    buckets = sorted(buckets, key=lambda bucket_name: largestIntInStr(bucket_name))
    print(f"Sorted bucket names: {buckets}")
    new_bucket_order = [0,1,2,3,5,4] # Apply ordering system to make 10000+ the last bucket
    buckets = [buckets[i] for i in new_bucket_order]
    print(f"Sorted bucket names: {buckets}")


    """
    print(pandas_df.head(30))
    print(f"pandas_df headers: {list(pandas_df.columns.values)}")
    tmpDf = pandas_df[[x_axis_variable_name, 'orig', metric_name]]
    print("tmpDf looks like:")
    with pandas.option_context('display.max_rows', None, 'display.max_columns', None):
        print(tmpDf)
    print("^^^^ pandas df looks like ^^^^")
    print("And first 3 rows:")
    print(pandas_df.iloc[:3])
    #print(df.dtypes)
    print("And first 100 rows, subset to Bins:")
    print(pandas_df.iloc[0:101,3:9])
    print(pandas_df.iloc[0:101,-1])
    """

    # Saving data frame
    csv_savepath = experiment.save_location_linux + f"Executive_Priority_Tabulations_#1_{experiment_name}_{table_name}_{query}.csv"
    du.makePath(du.getdir(csv_savepath))
    pandas_df.to_csv(csv_savepath, index=False)

    makePlots(experiment, experiment_name, table_name, queries, x_axis_variable_name,
                                           metric_name, geolevels, pandas_df, buckets,
                                           schema_name, eps_str)

def main():
    analysis, spark = setup()
    table_dicts = [tabledict_EPT_no1_no2, tabledict_EPT_no3]
    #table_dicts = [tabledict_H1]
    #table_dicts = [tabledict_EPT_no1_no2]
    for table_dict in table_dicts:
        for table_name, queries in table_dict.items():
            geolevels = geolevels_dict[table_name]
            schema = schema_dict[table_name]
            print(f"For table {table_name}, using schema {schema}")
            for query in queries:
                analyzeQuery(query, table_name, analysis, spark, geolevels, schema=schema)

if __name__ == "__main__":
    main()
