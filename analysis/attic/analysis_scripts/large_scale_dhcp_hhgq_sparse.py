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

import analysis.tools.sdftools as sdftools
import analysis.tools.treetools as treetools
import analysis.tools.metric_functions as mf

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf

import analysis.tools.setuptools as setuptools
import programs.datadict as dd


def L1_avg_age(sdf, geolevels):
    results = {}
    queries = ['age']
    tb = dd.getTableBuilder(sdf.schema.name)
    age_table = tb.getCustomTable(queries)
    age_query_len = len(age_table)
    assert age_query_len != 0, "Age query is broken"
    
    for geolevel in geolevels:
        geosdf = (
            sdf
            .copy()
            .getGeolevels(geolevel)
            .getQueryAnswers(queries)
            .show(n=200)
            .sum(groupby=[AC.GEOCODE, AC.GEOLEVEL])
            .show(n=200)
        )
        geosdf.df = geosdf.df.withColumn(f"average_{AC.ORIG}", sf.col(AC.ORIG) / sf.lit(age_query_len)).persist()
        geosdf.df = geosdf.df.withColumn(f"average_{AC.PRIV}", sf.col(AC.PRIV) / sf.lit(age_query_len)).persist()
        geosdf = geosdf.L1(col1=f"average_{AC.PRIV}", col2=f"average_{AC.ORIG}")
        
        results[f"{geolevel}_L1_AverageAge"] = geosdf
    return results
        

def L1_avg_age_fillMissingRows(sdf, geolevels, queries):
    sdf = sdf.getGeolevels(geolevels).getQueryAnswers(queries).fill(queries).sum(groupby=[AC.GEOCODE, AC.GEOLEVEL])
    sdf.df = sdf.df.groupBy([AC.GEOCODE, AC.GEOLEVEL]).agg(sf.avg(AC.ORIG), sf.avg(AC.PRIV)).persist()
    sdf = sdf.L1(col1=f"avg({AC.PRIV})", col2=f"avg({AC.ORIG})")
    return sdf

def L1_expected_age(sdf, geolevels):
    results = {}
    query = 'age'
    age_udf = sf.udf(sdftools.calc_index(query, sdf.schema))
    
    for geolevel in geolevels:
        geosdf = sdf.clone().getGeolevels(geolevel).answerQueries(query).show(n=1000)
        geosdf.df = geosdf.df.withColumn("age_index", age_udf(sf.col(AC.LEVEL))).persist()
        geosdf.df = geosdf.df.withColumn(f"ev_part_{AC.ORIG}", sf.col("age_index") * sf.col(AC.ORIG)).persist()
        geosdf.df = geosdf.df.withColumn(f"ev_part_{AC.PRIV}", sf.col("age_index") * sf.col(AC.PRIV)).persist()
        geosdf = geosdf.sum(groupby=[AC.GEOCODE, AC.GEOLEVEL])
        geosdf.df = geosdf.df.withColumn(f"ev_{AC.ORIG}", sf.col(f"ev_part_{AC.ORIG}") / sf.col(AC.ORIG)).persist()
        geosdf.df = geosdf.df.withColumn(f"ev_{AC.PRIV}", sf.col(f"ev_part_{AC.PRIV}") / sf.col(AC.PRIV)).persist()
        geosdf = geosdf.L1(col1=f"ev_{AC.PRIV}", col2=f"ev_{AC.ORIG}")
        
        results[f"{geolevel}_L1_E(age)"] = geosdf
    return results


if __name__ == "__main__":
    # setup tools will return the analysis object
    # the analysis object contains the spark session and save location path for this run
    # NOTE: You will need to specify a location for the results to be saved
    #       It should be passed into setuptools.setup, where it will be altered to
    #       add a subdirectory matching the logfile's name

    # Recommended location: "/mnt/users/[your_jbid]/analysis_results/"
    save_location = "/mnt/users/moran331/large_scale_analysis/"

    # Most common options are "INFO" and "ERROR"
    # In addition to the analysis print statements...
    # "INFO" provides ALL spark statements, including stage and task info
    # "ERROR" provides only error statements from spark/python
    loglevel = "ERROR"

    analysis = setuptools.setup(save_location=save_location, spark_loglevel="ERROR")

    # Specify the experiment paths
    experiment_paths = [
        "s3://uscb-decennial-ite-das/users/lecle301/experiments/full_person/smallCellQuery/avgLE1/"
    ]
    schema_name = "DHCP_HHGQ"

    geolevels = [C.STATE, C.COUNTY]
    queries = ['detailed']
    
    mb = sdftools.MetricBuilder()
    mb.add(
        desc = "L1( E(DAS_age), E(CEF_age) ) per geounit",
        metric_function = lambda sdf: L1_expected_age(sdf, mb.geolevels)
    )
   
    # build an experiment and add it to analysis
    analysis.add_experiment(
        name = f"PL94_Large_Scale_Analysis",
        runs = experiment_paths,
        schema = schema_name,
        metric_builder = mb,
        mtype = AC.SPARSE
    )

    # run analysis
    analysis.run_analysis(save_results=True)
