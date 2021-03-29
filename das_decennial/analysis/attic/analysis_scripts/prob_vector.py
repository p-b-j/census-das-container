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
import analysis.tools.crosswalk as crosswalk

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf
from pyspark.sql import Row

import analysis.tools.setuptools as setuptools
import programs.datadict as dd

from programs.schema.schemas.schemamaker import SchemaMaker

import scipy.sparse as ss
import programs.sparse as sp

import analysis.tools.mappers as mappers
from pyspark.sql import Row
from pyspark.sql.window import Window

# import recoder
import programs.writer.dhcp_to_mdf2020 as dhcp_to_mdf2020

import analysis.plotting.report_plots as rp

import operator

def testdata_random_geounit_generator(geocode, schema, density=0.01, scale=10):
    raw_mat = np.round(ss.random(1, schema.size, format='csr', density=density) * scale)
    syn_mat = np.round(ss.random(1, schema.size, format='csr', density=density) * scale)
    raw_sparse = sp.multiSparse(raw_mat, schema.shape)
    syn_sparse = sp.multiSparse(syn_mat, schema.shape)
    return { 'geocode': geocode, 'raw': raw_sparse, 'syn': syn_sparse }
    

def row_group_total(rows, columns=['orig','priv']):
    total_dict = {}
    for column in columns:
        total_dict[f"{column}_total"] = sum([x[column] for x in rows])
    for row in rows:
        row.update(total_dict)
    return rows

def prob_vector_mapper(rows):
    orig_total = sum([x['orig'] for x in rows])
    priv_total = sum([x['priv'] for x in rows])
    for row in rows:
        row['orig_prob'] = row['orig'] / orig_total
        row['priv_prob'] = row['priv'] / priv_total
    return rows


if __name__ == "__main__":
    ################################
    # define experiments to analyze
    ################################
    S3_BASE = "s3://uscb-decennial-ite-das/users"
    
    #################
    # setup analysis
    #################
    analysis_results_save_location = f"/mnt/users/moran331/analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
    spark = analysis.spark

    schema = SchemaMaker.fromName("DHCP_SCHEMA")
    num_geocodes = 2
    geocodes = [str(x).zfill(16) for x in range(num_geocodes)]
    geounits = [testdata_random_geounit_generator(x, schema, density=0.00001, scale=10) for x in geocodes]
    sdftools.print_item(geounits, "Random Geounit Data")
    
    rdd = spark.sparkContext.parallelize(geounits).persist()
    sdftools.print_item(rdd, "Parallelized RDD data")
    
    df = rdd.flatMap(lambda node: mappers.getSparseDF_mapper(node, schema)).map(lambda row: Row(**row)).toDF().persist()
    sdftools.print_item(df, "DF of Random Geounit Data")
    
    df = df.withColumn("STATE", sf.col("geocode")[0:2]).persist()
    sdftools.print_item(df, "DF with STATE code")
    
    df = sdftools.aggregateGeolevels(spark, df, 'STATE')
    sdftools.print_item(df, "Aggregated to the STATE geolevel")

    query = 'sex * age'
    df = sdftools.answerQuery(df, schema, query, labels=False)
    sdftools.print_item(df, "Answering the sex query")
    
    groupby = ['geocode', 'geolevel']
    rdd = sdftools.getRowGroupsAsRDD(df, groupby)
    df = rdd.flatMapValues(prob_vector_mapper).map(lambda row: Row(**row[1])).toDF()
    df = df.withColumn('age', sf.col('age').cast("int")).persist()
    df = df.sort(['geocode', 'age', 'sex']).persist()
    sdftools.print_item(df, f"Prob vector for {query} query", show=1000)
    

    
