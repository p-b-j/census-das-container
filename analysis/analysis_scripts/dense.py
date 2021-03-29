# This script does dense vs sparse analysis 

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
            "allraces * hispanic * sex * agecat85plus"
        ],
        
        
}        
        
    # Get the DF and schema
    schema = experiment.schema
    df = experiment.getDF()
    def ABSD(u):
        u=u.withColumn('diff',sf.col('priv')-sf.col('orig'))
        u=u.withColumn('abs diff', sf.abs(sf.col('diff')))
        return u
    
    def ReturnZeroCounts(df, geolevels): #This function returns the number of rows in a dataframe where 'orig'=0, and 'priv'=0
        zerocounts=pandas.DataFrame(columns=geolevels)
        counter=0
        df=df.toPandas()
        print(df.head(50))
        for k in geolevels:
            l=df.loc[df['geolevel']==k]
            if (df['orig']==0 & df['priv']==0):
                counter=counter+1
            zerocounts=zerocounts.append({k:counter})    
        return zerocounts            
       # Get the geolevels (faster to do this before looping if the queries
    # are to be answered over the same geolevels; otherwise, can perform this
    # step in the loop)
    geolevels = [C.COUNTY, C.TRACT]
    queri = ["allraces"]
    
    
    df_geolevel = sdftools.aggregateGeolevels(spark, df, geolevels)
    df_table = sdftools.answerQueries(df_geolevel, schema, queri, labels=True).persist()
    df_withmissingrows=sdftools.getFullWorkloadDF(df_table, schema, queri,groupby=[AC.GEOCODE, AC.GEOLEVEL, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP])
    #print(df_withmissingrows.head(200))
    sparse = sdftools.getCellSparsityByGroup(df_withmissingrows,schema,groupby=[AC.GEOCODE, AC.GEOLEVEL, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP,AC.QUERY])
    zero=ReturnZeroCounts(df_withmissingrows, geolevels)
    print("This is sparse:")
    print(sparse.head(20))
    print("This is zero")
    print(zero.head(20))
    csv_savepath = save_location_linux + f"origtable.csv"
    csv_savepath2 = save_location_linux + f"missingrows.csv"
    du.makePath(du.getdir(csv_savepath))
    du.makePath(du.getdir(csv_savepath2))
    pandas_df_table=df_table.toPandas()
    
    pandas_df_table.to_csv(csv_savepath, index=False)
    pandas_dfmissing=df_withmissingrows.toPandas()
    pandas_dfmissing.to_csv(csv_savepath2, index=False)


#    df_geolevel = sdftools.aggregateGeolevels(spark, df, geolevels)
#    races_names1=['White','Black or African American','American Indian and Alaskan Native']
#    races_names2=['Asian','Native Hawaiian and Other Pacific Islander','Some Other Race']
#    white1=['Aian']
#    buckets=[(0,0),(1,10),(11,100),(100,1000),(1000,10000),(10000,float('inf'))]
#    path = du.addslash(save_location)
#    plt.figure(figsize=(11,8.5))
#    sns.set(style="whitegrid")
    #f, axes=plt.subplots(2,3)
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

    # loop over each table, calculating the queries for each one
    count=1
    for table_name, queries in tabledict.items():
        sdftools.show(queries, f"The queries associated with table '{table_name}'")
        
        # answer the queries within the table
        

                sns.violinplot(x=x_axis_variable_name, y=metric_name, data=bel, order=bucketNames,
                                    inner = None, color="0.8") \
                                    .set_title(f"Average L1 Error (over trials) for race {m} and combination at state geolevel for ages 0 to 85 and 85+\n(binned by CEF count)")
                sns.stripplot(x=x_axis_variable_name, y=metric_name, data=bel, order=bucketNames)  \
                                    .set_title(f"Average L1 Error (over trials) for race {m} and combination at state geolevel for ages 0 to 85 and 85+\n(binned by CEF count)")

                counter2=counter2+1
                plot_savepath = f"{save_location_linux}plots/scatteredViolin{plotnum2}.pdf"
                du.makePath(du.getdir(plot_savepath))
                print(f"Saving scatterplot strips for query {queries} & geolevel {geolevels} to: {plot_savepath}")
                plt.savefig(plot_savepath)
                plt.clf()
             
  """           
                bel=pandas_df[pandas_df['level'].str.contains(m)]
                print("The split data for", m)
                print(bel.head(100))
        print(f"pandas_df headers: {list(pandas_df.columns.values)}")
                #ax=plt.subplot(3,1, counter)
                ax=plt.subplot(1,3, counter2)
            
                sns.violinplot(x=x_axis_variable_name, y=metric_name, data=bel, order=bucketNames,
                                    inner = None, color="0.8") \
                                    .set_title(f"Average L1 Error (over trials) for race {k} and combination at state geolevel for ages 0 to 85 and 85+\n(binned by CEF count)")

       for m in races_names2:
                sns.stripplot(x=x_axis_variable_name, y=metric_name, data=bel, order=bucketNames)  \
                                    .set_title(f"Average L1 Error (over trials) for race {k} and combination at state geolevel for ages 0 to 85 and 85+\n(binned by CEF count)")
                counter=counter+1
        #plt.tight_layout()
        plot_savepath = f"{save_location_linux}plots/scatteredViolin{plotnum}.pdf"
        du.makePath(du.getdir(plot_savepath))
        print(f"Saving scatterplot strips for query {queries} & geolevel {geolevels} to: {plot_savepath}")
        plt.savefig(plot_savepath)
        plt.clf()
                bel=pandas_df[pandas_df['level'].str.contains(k)]
                print("The split data for", k)
                print(bel.head(100))
        tmpDf = pandas_df[[x_axis_variable_name, 'orig', metric_name]]
        print("tmpDf looks like:")
        with pandas.option_context('display.max_rows', None, 'display.max_columns', None):
            print(tmpDf)
        
        for k in white1:
        csv_savepath = save_location_linux + f"zoom{count}.csv"
        du.makePath(du.getdir(csv_savepath))
        count=count+1
        pandas_df.to_csv(csv_savepath, index=False)
        bucketNames = [str(bucket) for bucket in buckets if bucketCounts[bucket] != 0]
        plotnum=1
        plotnum2=2
        counter=1
        counter2=1
        df_table = sdftools.answerQueries(df_geolevel, schema, queries, labels=True).persist()
        df_table = ABSD(df_table)
        print(f"bucketCounts: {bucketCounts}")
        rdd = sdftools.getRowGroupsAsRDD(df_table, groupby=[AC.GEOLEVEL, AC.QUERY])
        rdd = rdd.flatMapValues(lambda rows: sepBounds(rows, 'orig', buckets)).persist()
            bucketCounts[bucket] = trueRows.shape[0]
        rdd = rdd.map(lambda row: Row(**row[1]))
        for bindex, bucket in enumerate(buckets):
            trueRows = pandas_df[pandas_df[f"Bin{bindex}"] == True]
        df = rdd.toDF().persist()
        metric_name = "Avg( |q(MDF) - q(CEF)| )"
        bucketCounts = {}
        x_axis_variable_name = 'CEF Count, Binned'
        plt.rc('axes', labelsize=4)
        print(pandas_df.head(30))
        
        df = df.groupby(['geocode','geolevel','level','Bin0','Bin1','Bin2','Bin3','Bin4','Bin5']).avg()
        plt.figure(1, figsize=(8.5,11))
        pandas_df = df.toPandas()
        pandas_df = pandas_df.rename(columns={"avg(abs diff)":metric_name, "avg(orig)":"orig"})
        pandas_df[x_axis_variable_name] = pandas_df.apply(lambda row: binIndexToInteger(row, buckets), axis=1)
