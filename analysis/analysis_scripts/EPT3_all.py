# This script implements plots for all rows for Exec. Tabulations #3. Plots are generated for 2 or more races, and 6 races 
 

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

schema = SchemaMaker.fromName("DHCP_SCHEMA")

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
    
    save_location_linux = f"/mnt/users/rao00316/bland/"
    ######################################################
    # This script is for Exec Priority Tabulations #3
    ######################################################
    path = f"{AC.S3_BASE}lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td16/"
    experiment = analysis.make_experiment("pl94_tables", path)
    pandas.options.display.max_columns = None
    pandas.options.display.max_rows = None
            
    #per=f"/mnt/users/rao00316/goos/"
   # per=os.path.abspath("/mnt/users/rao00316/goos/")
# Tables for row tabulations
  
    tabledict = {
        "ROW2_TOMR": [
           
            "tomr * hispanic * sex * agecat100plus"
        ],
        
        "ROW2_6RACES": [
            "allraces * hispanic * sex * agecat100plus"
           
        ],
        "ROW8_TOMR": [
            "tomr * hispanic * sex * agecat85plus"
        ],
        "ROW8_6RACES": [
            "allraces * hispanic * sex * agecat85plus"
        ],
        "ROW12_TOMR": [ 
            "tomr * sex * agecat85plus"
        ],
        "ROW12_6RACES":[
            "allraces * sex * agecat85plus"
        ],
        "ROW14_TOMR":[
            "tomr * sex * hispanic * agecat17plus"
        ],
        "ROW14_6RACES":[
            "allraces * sex * hispanic * agecat17plus"
        ],
        "ROW15_TOMR":[
            "tomr * sex * agecat25plus"
        ],
        "ROW15_6RACES":[
             "allraces * sex * agecat25plus"
        ],    
}        

    # This is a dictionary of plot titles corresponding to row names. It will be used later to place the correct titles for plots

    PlotNames = {
        "ROW2_TOMR": "Average L1 Error (over trials) for 2 or more races, ages 0..99, 100+, hispanic, sex" ,
        "ROW2_6RACES":"Average L1 Error (over trials) for ages 0..99,100+, hispanic, sex",
        "ROW8_TOMR": "Average L1 Error (over trials) for 2 or more races, ages 0..84, 85+, hispanic, sex",
        "ROW8_6RACES":"Average L1 error (over trials) for ages 0..84,85+, hispanic, sex",
        "ROW12_TOMR":"Average L1 Error (over trials) for 2 or more races, ages 0..84, 85+, sex",
        "ROW12_6RACES":"Average L1 Error (over trials) for ages 0..84,85+, sex",
        "ROW14_TOMR":"Average L1 Error (over trials) for 2 or more races, ages 0..17, 18+, sex, hispanic",
        "ROW14_6RACES":"Average L1 Error (over trials) for ages 0..17,18+, sex, hispanic",
        "ROW15_TOMR":"Average L1 Error (over trials) for 2 or more races, ages 0..24, 25+, sex",
        "ROW15_6RACES":"Average L1 Error (over trials) for ages 0..24,25+, sex"



    }
    
    # Get the DF and schema
    schema = experiment.schema
    df = experiment.getDF()
    def ABSD(u):
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
    X_name="at state geolevel\n(binned by CEF count)"
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
        
        csv_savepath = save_location_linux + f"zoom{table_name}.csv"
        du.makePath(du.getdir(csv_savepath))
        pandas_df.to_csv(csv_savepath, index=False)
        bucketNames = [str(bucket) for bucket in buckets if bucketCounts[bucket] != 0]
        plotnum=1
        print("Here are the queries", queries)
        #min="allraces" in queries
        #print("Is this allraces", min)
        #Print plots for all races if that is the query
        if any("allraces" in s for s in queries):
            print("Printing plots for allraces")
        
            for k in races_names:
                bel=pandas_df[pandas_df['level'].str.contains(k)]
                print(bel.head(100))
             
                sns.violinplot(x=x_axis_variable_name, y=metric_name, data=bel, order=bucketNames,
                                    inner = None, color="0.8") \
                                    .set_title(PlotNames[table_name]+f" race {k} "+X_name) #verage L1 Error (over trials) for race {k} at state geolevel\n(binned by CEF count)")
                sns.stripplot(x=x_axis_variable_name, y=metric_name, data=bel, order=bucketNames)  \
                                    .set_title(PlotNames[table_name]+f" race {k} "+X_name) #f"Average L1 Error (over trials) for race {k} at state geolevel\n(binned by CEF count)")
                plot_savepath = f"{save_location_linux}plots/{table_name}_{k}.pdf"
                du.makePath(du.getdir(plot_savepath))
                print(f"Saving scatterplot strips for query {queries} & geolevel {geolevels} to: {plot_savepath}")
                plt.savefig(plot_savepath)
                plt.clf()
                plotnum=plotnum+1
        else:
            # Print plots for 2 or more races, since that is the other query
            print("Printing plots for 2 or more races")
            sns.set(style="whitegrid")
            sns.violinplot(x=x_axis_variable_name, y=metric_name, data=pandas_df, order=bucketNames,
                                    inner = None, color="0.8") \
                                    .set_title(f"Average L1 Error (over trials) for 2 or more races at state geolevel")
            sns.stripplot(x=x_axis_variable_name, y=metric_name, data=pandas_df, order=bucketNames)  \
                                    .set_title(f"Average L1 Error (over trials) for 2 or more races at state geolevel")
            plot_savepath = f"{save_location_linux}plots/{table_name}.pdf"
            du.makePath(du.getdir(plot_savepath))
            print(f"Saving scatterplot strips for query {queries} & geolevel {geolevels} to: {plot_savepath}")
            plt.savefig(plot_savepath)
            plt.clf()
