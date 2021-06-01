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
from pyspark.sql import Row

import analysis.tools.setuptools as setuptools
import programs.datadict as dd

import operator


if __name__ == "__main__":
    # Recommended location: "/mnt/users/[your_jbid]/analysis_results/"
    save_location = "/mnt/users/moran331/analysis_results/"
    loglevel = "ERROR"
    analysis = setuptools.setup(save_location=save_location, spark_loglevel=loglevel)
    

    experiment_paths = [
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td10_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td1_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td3_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td025_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td05_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td001_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td01_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td2_1/"
    ]
    schema_name = "PL94_P12"
    
   
    geolevels = [C.STATE, C.COUNTY, C.SLDU, C.SLDL]
    queries = ['P1', 'P2', 'P3', 'P4', 'P42']
    
    # a metric builder object is needed for analysis, as experiments are built using it
    mb = sdftools.MetricBuilder()
    mb.add(
        desc = "Query Answers with zero-rows added",
        metric_function = lambda sdf: sdf.getGeolevels(geolevels).answerQueries(queries).fill(queries)
    )
    mb.add(
        desc = "L1 Sum Quantiles Across Runs, Grouped by Geolevel/Geocode",
        metric_function = lambda sdf: (
            sdf.getGeolevels(geolevels).answerQueries(queries).fill(queries)
               .L1("L1 Sum Quantiles Across Runs").show()
               .sum(groupby=[AC.RUN_ID, AC.GEOCODE, AC.GEOLEVEL, AC.PLB, AC.BUDGET_GROUP]).show()
               .group_quantiles("L1 Sum Quantiles Across Runs", groupby=[AC.GEOCODE, AC.GEOLEVEL, AC.PLB, AC.BUDGET_GROUP]).show()
            )
    )

    # create experiments and add them to analysis
    for i,path in enumerate(experiment_paths):
        runs = treetools.getDASRuns(path)
        analysis.add_experiment(
            name = f"PL94_P12/Redistricting_Analysis2/PLB={runs[0].plb}/",
            runs = runs,
            schema = schema_name,
            metric_builder = mb,
            mtype = AC.SPARSE
        )

    # run analysis
    analysis.run_analysis(save_results=True)

    
