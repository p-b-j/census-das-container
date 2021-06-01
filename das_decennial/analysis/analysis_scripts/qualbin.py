# This function computes quantile bins for a given number of bins, returns a csv file with Bin # and TRUE if the value is in the particular Bin and FALSE if it is not
import das_utils as du
import pandas
import numpy as np
import operator
import os

import analysis.tools.datatools as datatools
import analysis.tools.setuptools as setuptools
import analysis.tools.sdftools as sdftools

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf
from pyspark.sql import Row

from programs.schema.schemas.schemamaker import SchemaMaker

from programs.nodes.nodes import GeounitNode
from programs.sparse import multiSparse
from programs.schema.schema import Schema

import analysis.vignettes.toytools as toytools


if __name__ == "__main__":
    """
    It's entirely possible to take advantage of Analysis's Spark DataFrame-based functionality within the DAS.
    The error_metrics module is the spot that makes the most sense for accessing Analysis.
    
    The steps to prepare the data for use is:
    1. Use analysis.tools.datatools.rdd2df to transform the RDD of GeounitNode objects into the histogram form
       required by Analysis
    2. Use the tools to analyze the data
        - analysis.tools.crosswalk is used to access and join the GRFC to the data for geolevel aggregation support
        - analysis.tools.sdftools is the location of most of the Spark DataFrame operations for answering queries
          and calculating a wide variety of metrics
    """
    # Note that this script is not running the DAS; it's only used to demostrate that it's possible to
    # take an RDD of GeounitNodes (as is typically found in the DAS) and use Analysis to calculate metrics
    
    # since we're not in the DAS in this script, we will use setuptools to extract the SparkSession object
    ################################################################
    # Set the save_location to your own JBID (and other folder(s))
    # it will automatically find your JBID
    # if something different is desired, just pass what is needed 
    # into the setuptools.setup function.
    ################################################################
jbid = os.environ.get('JBID', 'temp_jbid')
save_folder = "analysis_results/"
save_location = du.addslash(f"{jbid}/{save_folder}")
    
spark_loglevel = "ERROR"
analysis = setuptools.setup(save_location=save_location, spark_loglevel=spark_loglevel)

    # save the analysis script?
    # toggle to_linux=True|False to save|not save this analysis script locally
    # toggle to_s3=True|False to save|not save this analysis script to s3
analysis.save_analysis_script(to_linux=False, to_s3=False)
    
    # save/copy the log file?
analysis.save_log(to_linux=False, to_s3=False)
    
    # zip the local results to s3?
analysis.zip_results_to_s3(flag=False)
save_location_linux = f"/mnt/users/rao00316/brief/"
spark = analysis.spark
paths = [
        f"{AC.S3_BASE}kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td4/run_0000/"]

experiment = analysis.make_experiment("danVariant1-2", paths)
sdftools.print_item(experiment.__dict__, "Experiment Attributes")
    
    ##############################
    # Work with the Experiment DF
    ##############################
df = experiment.getDF()
schema = experiment.schema
sdftools.print_item(df, "Experiment DF")
    
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
        #'total',
        #'hhgq',
        #'votingage * citizen',
        #'numraces * hispanic',
        #'cenrace * hispanic',
        #'sex * age',
        #'detailed'
        'cenrace'
]

sdftools.show(df, "df with geolevel crosswalk columns")
sdftools.show(df, "df with geolevel crosswalk columns")
df = sdftools.aggregateGeolevels(spark, df, geolevels)
sdftools.show(df, "df after geolevel aggregation", 1000)
qdf = sdftools.answerQuery(df, schema, "total", labels=False, merge_dims=False)
sdftools.show(qdf, "Query df with the query 'total'", 1000)
rdd = sdftools.getRowGroupsAsRDD(qdf, groupby=[AC.GEOLEVEL, AC.QUERY])
#sdftools.show(rdd.collect(), "Row groups")

path = save_location_linux + "Gel.csv"
q = qdf.toPandas()
du.makePath(du.getdir(path))
q.to_csv(path, index=False)
def Qualbins(rows, column, bins):
    #only works if bins > 2
    pandas_df = pandas.DataFrame(rows)
    q = 1/bins
    
    p = bins+1
    for i in range (1, p):
        k=str(i)
        pandas_df['Bin'+k]=(np.quantile(pandas_df[column],q)>=pandas_df[column])&(pandas_df[column]>=np.quantile(pandas_df[column],q-1/bins))
            
        q=q+1/bins    
         
   
    rows = pandas_df.to_dict('records')
    return rows
        

# Call function here and specify number of bins,
# 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
rdd = rdd.flatMapValues(lambda rows: Qualbins(rows, AC.PRIV, 5)).persist()
rdd = rdd.map(lambda row: Row(**row[1]))
df = rdd.toDF().persist()

# Save to csv
path2 = save_location_linux + "Kel.csv"
z = df.toPandas()
du.makePath(du.getdir(path2))
z.to_csv(path2, index=False)
