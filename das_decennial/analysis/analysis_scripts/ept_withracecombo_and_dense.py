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

import programs.cenrace as cenrace
from programs.schema.attributes.cenrace import CenraceAttr as CENRACE
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas

import os, math
from collections import defaultdict

TEST = False    # Are we in small-scale testing mode?
TEST_NUM = 500   # How many records should we use when testing?

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
}
tabledict_EPT_no3 = {
        "EPT3_ROW2_TOMR"    :   ["tomr * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_WHITECOMBO": ["whitecombo * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_BLACKCOMBO": ["blackcombo * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_AIANCOMBO":  ["aiancombo * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_ASIANCOMBO": ["asiancombo * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_NHOPICOMBO": ["nhopi * hispanic * sex * agecat100plus"],
        "EPT3_ROW2_SORCOMBO":   ["sorcombo * hispanic * sex * agecat100plus"],


        "EPT3_ROW2_6RACES"  :   ["allraces * hispanic * sex * agecat100plus"],
        "EPT3_ROW8_TOMR"    :   ["tomr * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_WHITECOMBO": ["whitecombo * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_BLACKCOMBO": ["blackcombo * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_AIANCOMBO":  ["aiancombo * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_ASIANCOMBO": ["asiancombo * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_NHOPICOMBO": ["nhopicombo * hispanic * sex * agecat85plus"],
        "EPT3_ROW8_SORCOMBO":   ["sorcombo * hispanic * sex * agecat85plus"],



        "EPT3_ROW8_6RACES"  :   ["allraces * hispanic * sex * agecat85plus"],
        "EPT3_ROW12_TOMR"   :   ["tomr * sex * agecat85plus"],
        "EPT3_ROW12_6RACES" :   ["allraces * sex * agecat85plus"],
        "EPT3_ROW14_TOMR"   :   ["tomr * sex * hispanic * agePopEst18groups"],
        "EPT3_ROW14_6RACES" :   ["allraces * sex * hispanic * agePopEst18groups"],
        "EPT3_ROW15"        :   ["sex * agePopEst18groups"],
}
tabledict_H1 = {"H1":["h1"],}

all_geolevels = [C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD, C.STATE]
def listDefault():
    return all_geolevels
geolevels_dict = defaultdict(listDefault)
geolevels_dict["EPT3_ROW2_TOMR"]        = [C.STATE]     # Only needed for US, but current runs State-only
geolevels_dict["EPT3_ROW2_6RACES"]      = [C.STATE]     # Only needed for US, but current runs State-only
geolevels_dict["EPT3_ROW2_WHITECOMBO"]  = [C.STATE]
geolevels_dict["EPT3_ROW2_BLACKCOMBO"]  = [C.STATE]
geolevels_dict["EPT3_ROW2_AIANCOMBO"]   = [C.STATE]
geolevels_dict["EPT3_ROW2_ASIANCOMBO"]  = [C.STATE]
geolevels_dict["EPT3_ROW2_NHOPICOMBO"]  = [C.STATE]
geolevels_dict["EPT3_ROW2_SORCOMBO"]    = [C.STATE]
geolevels_dict["EPT3_ROW8_TOMR"]        = [C.STATE]
geolevels_dict["EPT3_ROW8_6RACES"]      = [C.STATE]
geolevels_dict["EPT3_ROW8_WHITECOMBO"]  = [C.STATE]
geolevels_dict["EPT3_ROW8_BLACKCOMBO"]  = [C.STATE]
geolevels_dict["EPT3_ROW8_AIANCOMBO"]   = [C.STATE]
geolevels_dict["EPT3_ROW8_ASIANCOMBO"]  = [C.STATE]
geolevels_dict["EPT3_ROW8_NHOPICOMBO"]  = [C.STATE]
geolevels_dict["EPT3_ROW8_SORCOMBO"]    = [C.STATE]

geolevels_dict["EPT3_ROW12_TOMR"]       = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW12_6RACES"]     = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW14_TOMR"]       = [C.COUNTY]
geolevels_dict["EPT3_ROW14_6RACES"]     = [C.COUNTY]
geolevels_dict["EPT3_ROW15"]            = [C.COUNTY]    # Also for PR Municipios, but PR not in current runs
#geolevels_dict["H1"]                    = all_geolevels + [C.US]
geolevels_dict["H1"]                    = [C.STATE, C.US]

default_buckets         = [(0,0), (1,10), (11,100), (100,1000), (1000,10000), (10000,float('inf'))]
major_omb_race_names    = ['white','black','aian','asian','nhopi','sor']
major_combination_race_names=['White','Black or African American','American Indian and Alaskan Native','Asian','Native Hawaiian and Other Pacific Islander','Some Other Race']
def schemaDefault():
    return "DHCP_HHGQ"
schema_dict = defaultdict(schemaDefault)
schema_dict["H1"] = "H1_SCHEMA"         # For H1-only internal runs as of 4/2/2020
#schema_dict["H1"] = "Household2010"    # For CNSTAT DDP Run

def getRddWithAbsDiff(spark, df, geolevels, queries, schema):
    rddWithAnswers = sdftools.getAnswers(spark, df, geolevels, schema, queries)
    rddWithDiff = rddWithAnswers.withColumn('diff',sf.col('priv')-sf.col('orig'))
    rddWithAbsDiff = rddWithDiff.withColumn('abs diff', sf.abs(sf.col('diff')))
    return rddWithAbsDiff

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

def setup():
    jbid = os.environ.get('JBID', 'temp_jbid')
    analysis_results_save_location = f"{jbid}/analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
    spark = analysis.spark
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
    return analysis, spark

def getPathsAndName(schema_name):
    """
        Copy and re-name to switch input locations.
    """
    print(f"Get paths received schema {schema_name}")

    S3_BASE="s3://uscb-decennial-ite-das/users"
    abbrev = {
        "SinglePassRegular"                 : "1PassReg",
        "DataIndUserSpecifiedQueriesNPass"  : "basicNpass",
        "TwoPassBigSmall"                   : "wigglesum",
        "nodetail"                          : "nodetail",
        "ndoetailsmall"                     : "nodetailsmall",
        "cnstatDpqueries"                   : "cnstatDpq",
        "dpQueries1"                        : "dpq1",
        "dpQueries2"                        : "dpq2",
        "dpQueries3"                        : "dpq3",
        "_cnstatGeolevels"                  : "_cnstatGeolevs",
        ""                                  : "",
    }

    if schema_name == "DHCP_HHGQ":
        algorithm = "SinglePassRegular"  # Basic TopDown
        #algorithm = "DataIndUserSpecifiedQueriesNPass" # User-specified DPQueries data-independent multi-pass
        #algorithm = "TwoPassBigSmall"  # Multi-pass w/ 2 phases that uses DPQuery estimates to partition into big, small estimates
        #algorithm = "nodetail"         # Relaxing asymptotic consistency
        #algorithm = "nodetailsmall"    # Relaxing asymptotic consistency (what is 'small'?)

        #dpqueries = "cnstatDpqueries"
        dpqueries = "dpQueries3"       # 1-3, depending

        #geolevelsStr = "_cnstatGeolevels"  # For original CNSTAT DDP run
        geolevelsStr = ""                 # For all other runs

        #wsmult = "-wsmult2.0"    # For wigglesum/TwoPassBigSmall
        wsmult = ""             # For all other runs

        suffix = "version2"     # Several naming conventions were used: version2, attempt3, etc
        #suffix = "attempt3"
        #suffix = ""            # Original runs had no suffix

        experiment_name = f"cnstatDdpSchema_{algorithm}_va_{dpqueries}{geolevelsStr}"

        if TEST:
            partial_paths = [f"data-run1.0-epsilon4.0{wsmult}-BlockNodeDicts/"]
        else:
            partial_paths = [
                                   f"data-run1.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run2.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run3.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run4.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run5.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run6.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run7.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run8.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run9.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   f"data-run10.0-epsilon4.0{wsmult}-BlockNodeDicts/"
            ]
        path_prefix = f"{S3_BASE}/heiss002/{experiment_name}_{suffix}/"
        paths = [path_prefix + partial_path for partial_path in partial_paths]
        if TEST:
            remainder_partial_paths = []
        else:
            remainder_partial_paths = [
                                   #f"data-run1.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   #f"data-run2.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   #f"data-run3.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   #f"data-run4.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   #f"data-run5.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   #f"data-run6.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   #f"data-run7.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   #f"data-run8.0-epsilon4.0{wsmult}-BlockNodeDicts/"#,
                                   #f"data-run9.0-epsilon4.0{wsmult}-BlockNodeDicts/",
                                   #f"data-run10.0-epsilon4.0{wsmult}-BlockNodeDicts/"
            ]
        path_prefix = f"{S3_BASE}/heiss002/{experiment_name}_{suffix}Remainder/"
        remainder_paths = [path_prefix + partial_path for partial_path in remainder_partial_paths]
    elif schema_name == "Household2010":
        raise NotImplementedError(f"Schema {schema_name} input locations not yet implemented.")
    elif schema_name == "H1_SCHEMA":
        experiment_name = "H1Schema_H1_national_H1Queries_allRuns"
        partial_paths = [f"MDF_UNIT-run{RUN}.0-epsilon{EPS}-BlockNodeDicts/" for RUN in range(1,6) for EPS in ("0.1","0.5","1.0","4.0")]
        path_prefix = f"{S3_BASE}/heiss002/{experiment_name}/"
        paths = [path_prefix + partial_path for partial_path in partial_paths]
        remainder_paths = []
    else:
        raise ValueError(f"Schema {schema_name} not recognized when getting s3 ingest paths.")

    paths = paths + remainder_paths
    return paths, experiment_name

def makePlots(experiment, experiment_name, table_name, queries, x_axis_variable_name,
                                           metric_name, geolevels, pandas_df, buckets,
                                           schema_name):
    EPT = table_name[:4]+"_"+schema_name
    for query in queries:
        for geolevel in geolevels:
            subsetted_df = pandas_df[pandas_df['geolevel'] == geolevel]
            race_iterates = major_omb_race_names if ("EPT3" in table_name and "allraces *" in query) else [""]
            race_iterates = ["2+ Races"] if (race_iterates == [""] and "tomr *" in query) else [""]
            race_iterates = major_combination_race_names if ("EPT3" in table_name and query.str.contains("combo")) else race_iterates
            print(f"table {table_name}, query {query}, geolevel {geolevel}, race_iterates {race_iterates})")

            # TODO: graph titling/subsetting for distinct queries is getting convoluted. Re-factor?
            for race in race_iterates:
                plotting_df = subsetted_df
                if race in major_omb_race_names:
                    plotting_df = subsetted_df[subsetted_df['level'].str.contains(race)]
                if race in major_combination_race_names:
                    plotting_df = subsetted_df[subsetted_df['level'].str.contains(race)]
                bucket_counts = {}
                for bindex, bucket in enumerate(buckets):
                    trueRows = plotting_df[plotting_df[f"Bin{bindex}"] == True]
                    bucket_counts[bucket] = trueRows.shape[0]
                print(f"Geolevel {geolevel} has bucket_counts: {bucket_counts}")
                bucket_names = [str(bucket) for bucket in buckets if bucket_counts[bucket] != 0]
                if (np.array(list(bucket_counts.values())) > 0).any():
                    graph_title = f"Average L1 Error (over trials) for {query}\nGeolevel: {geolevel}"
                    if race in major_omb_race_names:
                        graph_title += f"Race Alone: {race.title()}"
                    if race == "2+ Races":
                        graph_title += f"2+ Races"
                    if race in major_combination_race_names:
                        graph_title += f"Race: {race}"

                    graph_title += f"\n(binned by CEF count)\nDisclosure Prohibited - Title 13 U.S.C."

                    # Scatterplot strips superimposed on violin plots
                    sns.set(style="whitegrid")
                    sns.violinplot(x=x_axis_variable_name, y=metric_name, data=plotting_df, order=bucket_names,
                                            inner = None, color="0.8") \
                                            .set_title(graph_title)
                    sns.stripplot(x=x_axis_variable_name, y=metric_name, data=plotting_df, order=bucket_names)  \
                                            .set_title(graph_title)
                    plot_savepath = f"{experiment.save_location_linux}plots/{EPT}/scatteredViolin/{experiment_name}_"
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
    paths, experiment_name = getPathsAndName(schema_name)
    experiment = analysis.make_experiment(experiment_name, paths, schema_name=schema_name, dasruntype=AC.EXPERIMENT_FRAMEWORK_FLAT)
    sdftools.print_item(experiment.__dict__, "Experiment Attributes")

    df = experiment.getDF()
    if TEST:
        df = df.limit(TEST_NUM)
    print("df looks like:")
    df.show()
    schema = experiment.schema
    sdftools.print_item(df, "Flat Experiment DF")

    queries = [query]
    #y=sdftools.getAnswers(spark,df,geolevels,schema,queries)
    rddWithAbsDiff = getRddWithAbsDiff(spark, df, geolevels, queries, schema)
    rddWithAbsDiff=sdftools.getFullWorkloadDF(rddWithAbsDiff, schema, queri,groupby=[AC.GEOCODE, AC.GEOLEVEL, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP])

    rdd = sdftools.getRowGroupsAsRDD(rddWithAbsDiff, groupby=[AC.GEOLEVEL, AC.QUERY])
    rdd = rdd.flatMapValues(lambda rows: sepBounds(rows, 'orig', buckets)).persist()
    rdd = rdd.map(lambda row: Row(**row[1]))
    df = rdd.toDF().persist()

    metric_name = "Avg( |q(MDF) - q(CEF)| )"
    x_axis_variable_name = 'CEF Count, Binned'

    df = df.groupby(['geocode','geolevel','level','Bin0','Bin1','Bin2','Bin3','Bin4','Bin5']).avg()
    pandas_df = df.toPandas()
    pandas_df = pandas_df.rename(columns={"avg(abs diff)":metric_name, "avg(orig)":"orig"})
    pandas_df[x_axis_variable_name] = pandas_df.apply(lambda row: binIndexToInteger(row, buckets), axis=1)
    plt.figure(1, figsize=(11,8.5))
    plt.rc('axes', labelsize=8)

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
    csv_savepath = experiment.save_location_linux + f"Executive_Priority_Tabulations_#1_{experiment_name}.csv"
    du.makePath(du.getdir(csv_savepath))
    pandas_df.to_csv(csv_savepath, index=False)

    makePlots(experiment, experiment_name, table_name, queries, x_axis_variable_name,
                                           metric_name, geolevels, pandas_df, buckets,
                                           schema_name)

def main():
    analysis, spark = setup()

    #table_dicts = [tabledict_EPT_no1_no2, tabledict_EPT_no3, tabledict_H1]
    table_dicts = [tabledict_H1]
    for table_dict in table_dicts:
        for table_name, queries in table_dict.items():
            geolevels = geolevels_dict[table_name]
            schema = schema_dict[table_name]
            print(f"For table {table_name}, using schema {schema}")
            for query in queries:
                analyzeQuery(query, table_name, analysis, spark, geolevels, schema=schema)

if __name__ == "__main__":
    main()
