# This script implements plots for Row 2, 6 races, in Exec Tab #3
#A separate plot is generated for each race. 

import das_utils as du
import pandas
import numpy as np
import operator
import os

import analysis.tools.setuptools as setuptools
import analysis.tools.datatools as datatools
import analysis.tools.sdftools as sdftools
import analysis.tools.graphtools as graphtools
import analysis.tools.crosswalk as crosswalk

import matplotlib.pyplot as plt
import programs.cenrace as cenrace
from programs.schema.attributes.cenrace import CenraceAttr as CENRACE
import analysis.constants as AC
import constants as C
import seaborn as sns
from pyspark.sql import functions as sf
from pyspark.sql import Row

from programs.schema.schemas.schemamaker import SchemaMaker

import programs.sparse as sp
import scipy.sparse as ss


if __name__ == "__main__":
    ################################################################
    # Set the save_location to your own JBID (and other folder(s))
    # it will automatically find your JBID
    # if something different is desired, just pass what is needed 
    # into the setuptools.setup function.
    ################################################################
    jbid = os.environ.get('JBID', 'temp_jbid')
    save_folder = "plots/"

    save_location = f"/mnt/users/rao00316/"
    
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

    spark = analysis.spark
    
    #save_folder = "plots2/"
    #save_location = du.addslash(f"/mnt/users/rao00316//{save_folder}")
    
    save_location_linux = f"/mnt/users/rao00316/amaz/"
    ######################################################
    # This script is for Exec Priority Tabulations #3
    ######################################################
    path = f"{AC.S3_BASE}lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td16/"
    experiment = analysis.make_experiment("pl94_tables", path)
    pandas.options.display.max_columns = None
    pandas.options.display.max_rows = None
            
    #per=f"/mnt/users/rao00316/goos/"
    per=os.path.abspath("/mnt/users/rao00316/goos/")
# Tables 1&2 for row 2 tabulations 
    tabledict = {
        "P1": [
           # "total",
            #"C.CENRACE_TOMR * hispanic * sex * age"
            "allraces * hispanic * sex * agecat100plus"
        ],
        
   #     "P2": [
    #        "total",
     #       "hispanic",
      #      "numraces",
       #     "cenrace",
        #    "hispanic * numraces",
         #   "hispanic * cenrace"
      #  ],
}        
        
    # Get the DF and schema
    schema = experiment.schema
    df = experiment.getDF()
    def ABSD(u):
        # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
        u=u.withColumn('diff',sf.col('priv')-sf.col('orig'))
        u=u.withColumn('abs diff', sf.abs(sf.col('diff')))
        return u
    
        # Get the geolevels (faster to do this before looping if the queries
    # are to be answered over the same geolevels; otherwise, can perform this
    # step in the loop)
    geolevels = [C.STATE]
    df_geolevel = sdftools.aggregateGeolevels(spark, df, geolevels)
    races_names=['white','black','aian','asian','nhopi','sor']
    buckets=[(0,0),(1,10),(11,100),(100,1000),(1000,10000),(10000,float('inf'))]
    path = du.addslash(save_location)
    plt.figure(figsize=(11,8.5))
    sns.set(style="whitegrid")
    #f, axes=plt.subplots(2,3)
    
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

    # loop over each table, calculating the queries for each one
    for table_name, queries in tabledict.items():
        sdftools.show(queries, f"The queries associated with table '{table_name}'")
        
        # answer the queries within the table
        df_table = sdftools.answerQueries(df_geolevel, schema, queries, labels=True).persist()
        df_table = ABSD(df_table)
        rdd = sdftools.getRowGroupsAsRDD(df_table, groupby=[AC.GEOLEVEL, AC.QUERY])
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
        print(pandas_df.head(30))
        bucketCounts = {}
        for bindex, bucket in enumerate(buckets):
            trueRows = pandas_df[pandas_df[f"Bin{bindex}"] == True]
            bucketCounts[bucket] = trueRows.shape[0]
        print(f"bucketCounts: {bucketCounts}")
        
        print(f"pandas_df headers: {list(pandas_df.columns.values)}")
        tmpDf = pandas_df[[x_axis_variable_name, 'orig', metric_name]]
        print("tmpDf looks like:")
        with pandas.option_context('display.max_rows', None, 'display.max_columns', None):
            print(tmpDf)
        
        csv_savepath = save_location_linux + "zoom2.csv"
        du.makePath(du.getdir(csv_savepath))
        pandas_df.to_csv(csv_savepath, index=False)
        bucketNames = [str(bucket) for bucket in buckets if bucketCounts[bucket] != 0]
        plotnum=1
        for k in races_names:
             bel=pandas_df[pandas_df['level'].str.contains(k)]
             print(bel.head(100))
             
             sns.violinplot(x=x_axis_variable_name, y=metric_name, data=bel, order=bucketNames,
                                    inner = None, color="0.8") \
                                    .set_title(f"Average L1 Error (over trials) for race {k} at state geolevel\n(binned by CEF count)")
             sns.stripplot(x=x_axis_variable_name, y=metric_name, data=bel, order=bucketNames)  \
                                    .set_title(f"Average L1 Error (over trials) for race {k} at state geolevel\n(binned by CEF count)")
             plot_savepath = f"{save_location_linux}plots/scatteredViolin{plotnum}.pdf"
             du.makePath(du.getdir(plot_savepath))
             print(f"Saving scatterplot strips for query {queries} & geolevel {geolevels} to: {plot_savepath}")
             plt.savefig(plot_savepath)
             plt.clf()
             plotnum=plotnum+1

        
