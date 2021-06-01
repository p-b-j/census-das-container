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
import operator
import os

import analysis.tools.setuptools as setuptools
import analysis.tools.datatools as datatools
import analysis.tools.sdftools as sdftools
import analysis.tools.graphtools as graphtools
import analysis.tools.crosswalk as crosswalk

import matplotlib.pyplot as plt

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
    # Looping over the P1-P4 + P42 tables in PL94
    ######################################################
    path = f"{AC.S3_BASE}lecle301/withRawForBrett_topdown_ri44/"
    experiment = analysis.make_experiment("pl94_tables", path)
    pandas.options.display.max_columns = None
    pandas.options.display.max_rows = None

    #per=f"/mnt/users/rao00316/goos/"
    per=os.path.abspath("/mnt/users/rao00316/goos/")
# P1-P4, P42 table definitions
    tabledict = {
        "P1": [
            "total",
            "numraces",
            "cenrace"
        ],

   #     "P2": [
    #        "total",
     #       "hispanic",
      #      "numraces",
       #     "cenrace",
        #    "hispanic * numraces",
         #   "hispanic * cenrace"
      #  ],

      #  "P3": [
      #      "votingage",
      #      "votingage * numraces",
      #      "votingage * cenrace"
      #  ],

      #  "P4": [
      #      "votingage",
      #      "votingage * hispanic",
      #      "votingage * numraces",
      #      "votingage * cenrace",
      #      "votingage * hispanic * numraces",
      #      "votingage * hispanic * cenrace"
      #  ],

      #  "P42": [
       #     "household",
       #     "institutionalized",
       #     "gqlevels"
       # ],
    }

    # Get the DF and schema
    schema = experiment.schema
    df = experiment.getDF()
    def AVG(u):
        # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
        u=u.withColumn('diff',sf.col('priv')-sf.col('orig'))
        u=u.withColumn('abs diff', sf.abs(sf.col('diff')))
        return u

    def sepBounds(rows, column, buckets):
        pandas_df=pandas.DataFrame(rows)
        for i in range(0,len(buckets)):
            k=str(i)
            pandas_df['Bin'+k]=(buckets[i][0]<=pandas_df[column])&(pandas_df[column]<=buckets[i][1])
        rows = pandas_df.to_dict('records')
        return rows
        # Get the geolevels (faster to do this before looping if the queries
    # are to be answered over the same geolevels; otherwise, can perform this
    # step in the loop)
    geolevels = [C.US, C.STATE, C.COUNTY, C.TRACT_GROUP, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU]
    df_geolevel = sdftools.aggregateGeolevels(spark, df, geolevels)
    buckets=[(0,0),(1,10),(11,100),(100,1000),(1000,10000),(10000,float('inf'))]
    path = du.addslash(save_location)

    # loop over each table, calculating the queries for each one
    for table_name, queries in tabledict.items():
        sdftools.show(queries, f"The queries associated with table '{table_name}'")

        # answer the queries within the table
        df_table = sdftools.answerQueries(df_geolevel, schema, queries, labels=True).persist()
        sdftools.show(df_table, f"The DF with answers for the table '{table_name}'")
        av=AVG(df_table)
        rdd = sdftools.getRowGroupsAsRDD(av, groupby=[AC.GEOLEVEL, AC.QUERY])
        rdd = rdd.flatMapValues(lambda rows: sepBounds(rows, 'orig', buckets)).persist()
        rdd = rdd.map(lambda row: Row(**row[1]))
        df = rdd.toDF().persist()
        #df=df.groupby(['geocode','geolevel','level','Bin0','Bin1','Bin2','Bin3','Bin4','Bin5']).avg()
        df=df.groupby(['geocode','geolevel','level','query','Bin0','Bin1','Bin2','Bin3','Bin4','Bin5']).avg()
        df=df.toPandas()
        print(df.head(30))# further computations...
        for g in geolevels:
            for qu in queries:
                for k in range(len(buckets)):
                    print("This is geolevels", g)
                    print("queries is", qu)
                    print("k is", k)
                    #print("this is orig data")
                    #print(df.head(30))
                    qf=df.loc[df['geolevel']==g]
        #create plots and save as pdf


                    qf=qf.loc[qf['query']==qu]
                    #print("This is the cut data")
                    #print(qf.head(30))
                    name='df'+str(k)
                    bind='Bin'+str(k)
                    name1=qf[bind]
                    temp=qf['avg(abs diff)']
                    #creates new dataframe with L1 and Bin data
                    new=pandas.concat([name1,temp],axis=1)
                    # Drop values that are False, that means the L1 does not pertain to that Bin
                    index=new[new[bind]==False].index
                    new.drop(index,inplace=True)
                    if (new.empty==False): # If there is L1 data present in that bin, then plot it
                        sns.set(style="whitegrid")

                        sns.violinplot(x=new[bind],y=new['avg(abs diff)'])
                        query_saveloc = f"{path}{g}{qu}{k}.pdf"
                        print(query_saveloc)
                        plt.savefig(query_saveloc)
                        plt.clf()
                        print("done")
                    else: # If the Bin is completely empty, there is no data to plot!
                        print(bind+"is empty")
