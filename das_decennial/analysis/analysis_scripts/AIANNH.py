
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

import analysis.constants as AC
import constants as C

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

    spark = analysis.spark


    #######################################################
    # Create an experiment using one or more DAS Run paths
    #######################################################
    paths = [
        f"{AC.S3_BASE}kifer001/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1-2/td4/run_0000/"
    ]

    experiment = analysis.make_experiment("danVariant1-2", paths)
    sdftools.print_item(experiment.__dict__, "Experiment Attributes")
    
    ##############################
    # Work with the Experiment DF
    ##############################
    df = experiment.getDF()
    schema = experiment.schema
    sdftools.print_item(df, "Experiment DF")

    # Read grf file and select relevant columns
    grf=spark.read.csv("s3://uscb-decennial-ite-das/2010/cefv2/pp10_grf_tab_ikeda_100219.csv")
    grf=grf.select("_c0","_c1","_c2","_c3","_c26","_c27","_c28","_c29","_c70")
    
    #rename columns with appropriate titles
    grf=grf.withColumnRenamed("_c26","AIANNHFP").withColumnRenamed("_c27","AIANNHCE").withColumnRenamed("_c28","AIANNHNS").withColumnRenamed("_c29","AIHHTLI").withColumnRenamed("_c70","OIDTABBLK")
    grf=grf.withColumnRenamed("_c0","TABBLKST").withColumnRenamed("_c1","TABBLKCOU").withColumnRenamed("_c2","TABTRACTCE").withColumnRenamed("_c3","TABBLK")
    
    
    # concatenate levels to get geocode
    grf=grf.withColumn("geocode", sf.concat(sf.col("TABBLKST"), sf.col("TABBLKCOU"),sf.col("TABTRACTCE"),sf.col("TABBLK")[0:1],sf.col("TABBLK")))
    
    
    grf=grf.filter((grf.OIDTABBLK != "OIDTABBLK"))
    grf.show(50)
    print("Count of OIDTABBLK is")
    print(grf.select(['OIDTABBLK']).distinct().count())

    df.show(100)
    print("geocode count is")
    print(df.select(['geocode']).distinct().count())
    
    #Perform join of experiment df with AIANNH columns, linking via geocode
    df = df.join(grf, on=['geocode'], how='inner')
    df.show(50)
    print("geocode count is")
    print(df.select(['geocode']).distinct().count())
    
