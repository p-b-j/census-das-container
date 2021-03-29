# This script implements plots for table 2, 6 races, in Exec Tab #3
#A separate plot is generated for each race - all plots are printed in one pdf 
# Note: NEED TO DEFINE NEW FUNCTION CENRACE_ALLRACES in cenrace.py to change race query for 6 major races, otherwise won't work
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
            "allraces * hispanic * sex * age"
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
        u=u.withColumn('diff',sf.col('priv')-sf.col('orig'))
        u=u.withColumn('abs diff', sf.abs(sf.col('diff')))
        return u
    
        # Get the geolevels (faster to do this before looping if the queries
    # are to be answered over the same geolevels; otherwise, can perform this
    # step in the loop)
    geolevels = [C.STATE]
    df_geolevel = sdftools.aggregateGeolevels(spark, df, geolevels)
    races_names=['white','black','aian','asian','nhopi','sor']
    path = du.addslash(save_location)
    plt.figure(figsize=(11,8.5))
    sns.set(style="whitegrid")
    #f, axes=plt.subplots(2,3)

    # loop over each table, calculating the queries for each one
    for table_name, queries in tabledict.items():
        sdftools.show(queries, f"The queries associated with table '{table_name}'")
        
        # answer the queries within the table
        df_table = sdftools.answerQueries(df_geolevel, schema, queries, labels=True).persist()
        pdf=df_table.toPandas()
        path=save_location_linux+"kull.csv"
        du.makePath(du.getdir(path))
        pdf.to_csv(path,index=False)
        
        sdftools.show(df_table, f"The DF with answers for the table '{table_name}'")
        av=ABSD(df_table)
        #df=df.groupby(['geocode','geolevel','level','Bin0','Bin1','Bin2','Bin3','Bin4','Bin5']).avg()
        df=av.groupby(['geocode','geolevel','level','query']).avg()
        df=df.toPandas()
        print(df.head(100))
        #make the plots , for each race, plotting L1 data vs geolevel
        
        plotnum=1
        for k in races_names:
            
            ax=plt.subplot(2,3, plotnum)
            
            bel=df[df['level'].str.contains(k)]
            print(bel.head(100))
            sns.violinplot(x=bel['geolevel'],y=bel['avg(abs diff)']).set_title(f"For race {k}")
            plotnum=plotnum+1
        plt.tight_layout()
        #Save all plots in a single PDF
        query_saveloc = save_location_linux+"Violin2.pdf"
        print(query_saveloc)
        plt.savefig(query_saveloc)
        plt.clf()
        print("done")
