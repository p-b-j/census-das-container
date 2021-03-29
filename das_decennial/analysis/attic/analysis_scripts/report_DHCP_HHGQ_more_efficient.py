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

#import analysis.plotting.report_plots as rp

import operator

def generateReport(sdf, geolevels, queries, age_queries, product, state, plot=False):
    geolevel_sdf = sdf.getGeolevels(geolevels)
    
    results = {}
    
    # for getSignedError, getGeolevelTVD, and getGeolevelSparsity
    queries_sdf = geolevel_sdf.answerQueries(queries)

    # signed error calculations
    res = getSignedErrorFast(queries_sdf.clone())
    results.update(res)
    sdftools.print_item(results, "Results after Signed Error Calculations")
    
    # geolevel 1-tvd calculations
    res = getGeolevelTVDFast(queries_sdf.clone(), product, state, plot)
    results.update(res)
    sdftools.print_item(results, "Results after Signed Error and Geolevel 1-TVD Calculations")
    
    # geolevel sparsity calculations
    res = getGeolevelSparsityFast(queries_sdf.clone())
    results.update(res)
    sdftools.print_item(results, "Results after Signed Error, Geolevel 1-TVD, and Sparsity Calculations")
    
    # age quantile calculations
    res = getCategoryByAgeQuantilesFast(geolevel_sdf.clone(), age_queries, product, state, plot)
    results.update(res)
    sdftools.print_item(results, "Results after Signed Error, Geolevel 1-TVD, Sparsity, and Age Quantile Calculations")

    return results
    

    
def getSignedErrorFast(sdf):
    sdf.df = sdftools.getSignedErrorByTrueCountRuns(sdf.df)

    groupby = ['orig_count_bin', AC.GEOLEVEL, AC.QUERY, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP]
    results = {}
    # quantiles within groups
    SEQBG = "signed_error_quantiles_by_group"
    REQBG = "re_quantiles_by_group"
    quantiles = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    results[SEQBG] = sdftools.getGroupQuantiles2(sdf.df, columns=['signed_error'], groupby=groupby, quantiles=quantiles).persist()
    results[REQBG] = sdftools.getGroupQuantiles2(sdf.df, columns=['re'], groupby=groupby, quantiles=quantiles).persist()
    
    # average within groups
    SEABR = "signed_error_average_by_run" # formerly "avg(avg(signed_error))_by_run"
    REABR = "re_average_by_run"           # formerly "avg(avg(re))_by_run"
    results[SEABR] = sdf.df.groupBy(groupby).agg(sf.avg("signed_error")).persist()
    results[REABR] = sdf.df.groupBy(groupby).agg(sf.avg("re")).persist()

    return results
    

def getGeolevelTVDFast(sdf, product, state, plot=False):
    sdf = sdf.geolevel_tvd(groupby=[AC.GEOLEVEL, AC.RUN_ID, AC.QUERY, AC.PLB])
    
    if plot:
        saveloc = du.getdir(sdf.metric_save_location)
        sdftools.print_item(sdf.df.count(), "Number of rows in the Spark DF before transforming to Pandas DF")
        geolevel_tvd_pandas_df = sdf.toPandas()
        rp.geolevel_tvd_lineplot(geolevel_tvd_pandas_df, saveloc, product, state)
        rp.geolevel_tvd_heatmap(geolevel_tvd_pandas_df, saveloc, product, state)
    
    results = { 'geolevel_tvd': sdf }
        
    return results


def getCategoryByAgeQuantilesFast(sdf, queries, product, state, plot=False):
    df = sdf.df
    results = {}
    for query in queries:
        res = sdftools.categoryByAgeQuantiles(df, sdf.schema, query, labels=True)
        results.update(res)
    
    if plot:
        for key, df in results.items():
            queryname, category, datatype = parseAgeQuantileKey(key, fsname=False)
            sdftools.print_item(df.count(), "Number of rows in the Spark DF before transforming to Pandas DF")
            if datatype == "quantile_df":
                age_quantile_pandas_df = df.toPandas()
                saveloc = du.getdir(sdf.metric_save_location)
                rp.age_quantile_lineplot(age_quantile_pandas_df, saveloc, product, state)
            else: # datatype == "survival_props"
                pass
    
    return results


def parseAgeQuantileKey(key, fsname=False):
    """
    fsname: bool
        True: maintains the filesystem-safe naming conventions (e.g. sex.age instead of sex * age)
        False: converts back to the user-friendly naming conventions (e.g. 1_Race * Female instead of 1_Race.Female)
    """
    items = key.split("--")
    query, category, data = items
    if not fsname:
        query = " * ".join(query.split("."))
        category = " * ".join(category.split("."))
    return query, category, data


def checkAgeQuantileKeyParsing():
    key = 'sex.age--Female--quantile_df'
    query, category, data = parseAgeQuantileKey(key)
    assert query == 'sex * age'
    assert category == 'Female'
    assert data == 'quantile_df'

    key = 'numraces.sex.age--1_Race.Female--survival_props'
    query, category, data = parseAgeQuantileKey(key)
    assert query == 'numraces * sex * age'
    assert category == '1_Race * Female'
    assert data == 'survival_props'



    
def getGeolevelSparsityFast(sdf):
    df = sdf.df
    schema = sdf.schema
    groupby = [AC.GEOCODE, AC.GEOLEVEL, AC.PLB, AC.RUN_ID, AC.BUDGET_GROUP, AC.QUERY]
    group_sparsity_df = sdftools.getCellSparsityByGroup(df, schema, groupby)
    groupby = [AC.GEOLEVEL, AC.PLB, AC.BUDGET_GROUP, AC.QUERY, AC.RUN_ID]
    geolevel_sparsity = sdftools.getCellSparsityAcrossGeolevelSuperHistogram(group_sparsity_df, groupby)
    return { 'geolevel_sparsity': geolevel_sparsity }



if __name__ == "__main__":

    ################################
    # define experiments to analyze
    ################################
    S3_BASE = "s3://uscb-decennial-ite-das/users"
    
    experiments = {
        'defaultManualStrategy': [
            # <--- Input locations for VA data from runs using historically default manual strategy --->
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP/td001/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP/td01/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td1/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td2/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td4/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td8/",
            f"{S3_BASE}/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td16/"
        ],
        
        "danVariant1-2": [
            # <--- Input Locations for VA data from runs with Dan's new post-processing (not sure how this works) --->
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td001/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td01/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td1/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td2/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td4/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td8/",
            f"{S3_BASE}/kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td16/"
        ],
        
        "danVariant1": [
            # <--- Input Locations for VA data with simple HB tree branchFactor4 age-range queries added to workload --->
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td001/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td01/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td1/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td2/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td4/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td8/",
            f"{S3_BASE}/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/td16/"
        ],
        
        "scqSimpleAgeSexQ": [
            # <--- Input Locations for VA data with small-cell-query at both State & County levels --->
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps0.1/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ/full_person/", # 1.0
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps2/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps4/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps8.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps16.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqSimpleAgeSexQ_eps20.0/full_person/"
        ],
        
        "scqCOnly_SimpleAgeSexQ": [
            # <--- Input Locations for VA data with small-cell-query at County level only --->
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps0.1/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps1.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps2.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps4.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps8.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps16.0/full_person/",
            f"{S3_BASE}/lecle301/smallCellQuery/VA_allCountiesTest_scqCOnly_SimpleAgeSexQ_eps20.0/full_person/"
        ]
    }

    trialsPerExperiment = {}
    trialsPerExperiment["defaultManualStrategy"] = 3
    trialsPerExperiment["danVariant1"] = 3
    trialsPerExperiment["danVariant1-2"] = 3
    trialsPerExperiment["scqSimpleAgeSexQ"] = 1
    trialsPerExperiment["scqCOnly_SimpleAgeSexQ"] = 1

    #################
    # setup analysis
    #################
    analysis_results_save_location = f"/mnt/users/moran331/VA_analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)

    # list of experiments to analyze
    experimentDesignators = ['danVariant1', 'danVariant1-2'] #list(experiments.keys())
    
    ##############################
    # add experiments to analysis
    #############################
    for d in experimentDesignators:
        numTrials = trialsPerExperiment[d]
        experiment_name = f"{d}_{numTrials}Trial_allPLBs"
        experiment_paths = experiments[d]

        schema_name = "DHCP_HHGQ"

        #######################
        # setup metric builder
        #######################
        geolevels = [
            C.STATE, 
            C.COUNTY,
            C.TRACT_GROUP, 
            C.TRACT, 
            C.BLOCK_GROUP, 
            C.BLOCK,
            C.SLDL,
            C.SLDU
        ]
        
        queries = [
            'total', 
            'hhgq', 
            'votingage * citizen', 
            'numraces * hispanic', 
            'cenrace * hispanic', 
            'sex * age', 
            'detailed'
        ]
        
        age_queries = [
            'sex * age', 
            'majorRaces * age', 
            'numraces * age', 
            'hhgq * age', 
            'hispanic * age',
        ]
        
        product = "DHC-P HHGQ"
        state = "VA"
        plot = False
        
        # a metric builder object is needed for analysis, as experiments are built using it
        mb = sdftools.MetricBuilder()
        mb.add(
            desc = f"generating a report with 'signed error', 'geolevel 1-tvd', 'geolevel sparsity', and 'category-by-age quantile' calculations",
            filename = "report_DHCP_HHGQ",
            metric_function = lambda sdf: generateReport(sdf, geolevels, queries, age_queries, product, state, plot)
        )
        # mb.add(
        #     desc = f"bias by true counts for queries: {queries} and geolevels: {geolevels}",
        #     filename = "bias_metric",
        #     metric_function = lambda sdf: getSignedError(sdf, geolevels, queries)
        # )
        # mb.add(
        #     desc = f"geolevel 1-TVD for queries: {queries} and geolevels: {geolevels}",
        #     filename = "geolevel_tvd_metric",
        #     metric_function = lambda sdf: getGeolevelTVD(sdf, geolevels, queries, product="DHC-P HHGQ", state="VA", plot=True)
        # )
        # mb.add(
        #     desc = f"avg L1 between quantiles of CEF and DAS across geounits for category-by-age queries",
        #     filename = "age_quantiles",
        #     metric_function = lambda sdf: getCategoryByAgeQuantiles(sdf, geolevels, age_queries)
        # )
        # mb.add(
        #     desc = f"Sparsity across super histogram of all geounits in a geolevel",
        #     filename = "geolevel_sparsity",
        #     metric_function = lambda sdf: getGeolevelSparsity(sdf, geolevels, queries)
        # )
        
        #############################################
        # build an experiment and add it to analysis
        #############################################
        analysis.add_experiment(
            name = experiment_name,     # need a unique name for each experiment
            runs = experiment_paths,    # can be either the string paths, or the DASRun objects themselves
            schema = schema_name,       # the name of the schema for the runs provided (must all be data from the same schema)
            metric_builder = mb,        # the metric builder object constructed above
            mtype = AC.SPARSE           # mapper type: we almost always will want to use AC.SPARSE
        )
        
    ###############
    # run analysis
    ###############
    analysis.run_analysis(save_results=True)
    #spark.stop()
