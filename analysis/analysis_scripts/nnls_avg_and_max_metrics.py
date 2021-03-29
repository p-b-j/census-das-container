# This script computes the Average squared error and Max Squared error for each query type, for each geolevel, and each geounit, at each level. It returns a .csv file that shows the average and max of averaged squared errors, and the average and max of max squared errors, over the geolevels/geounits. It does not return the average and max values that are computed at levels, however you can choose to save those values if you wish

import das_utils as du
import pandas
import numpy as np

import analysis.tools.sdftools as sdftools
import analysis.tools.datatools as datatools

import analysis.constants as AC
import constants as C
from constants import CC
from pyspark.sql import functions as sf
from pyspark.sql import Row

import analysis.tools.setuptools as setuptools
from programs.schema.schemas.schemamaker import SchemaMaker
import operator
import programs.datadict as dd
import sys
import os
sys.path.append("/mnt/users/{os.environ['JBID']}/das_decennial/")
analysis_results_save_location = f"/mnt/users/rao00316/analysis_reports/"
spark_loglevel = "ERROR"
analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
spark = analysis.spark
S3_BASE="s3://uscb-decennial-ite-das/users"
save_location_linux = f"/mnt/users/rao00316/ref/"

du.ship_files2spark(spark, subdirs=('programs','das_framework','analysis'), tempdir='/mnt/tmp/')
path = [
    "s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td16/"
]

runs = datatools.getDASRuns(path)

schema_name = "DHCP_HHGQ"

schema = SchemaMaker.fromName(name=schema_name)

experiment = analysis.make_experiment("DHCP", path)
df = experiment.getDF()
schema = experiment.schema

geolevels = [C.COUNTY,C.TRACT] #, C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD]

queries = ['cenrace']


def AvgSqError(spark,df,geolevels,queries,schema):
    # This function calculates the average squared error for levels at each geounit and geolevel
    u=sdftools.getAnswers(spark,df,geolevels,schema,queries)
    print("u is")
    u.show()
    u=u.withColumn('diff',sf.col('priv')-sf.col('orig'))
    u=u.withColumn('sq',sf.lit(2))
    u=u.withColumn('sq diff', sf.pow(sf.col('diff'),sf.col('sq')))
    u=u.groupBy(['geocode','geolevel','level']).avg()
    return u


def MaxSqError(spark,df,geolevels,queries,schema):
    # This function calculates the max squared error for levels at each geounit and geolevel
    u=sdftools.getAnswers(spark,df,geolevels,schema,queries)
    print("u is")
    u.show()
    u=u.withColumn('diff',sf.col('priv')-sf.col('orig'))
    u=u.withColumn('sq',sf.lit(2))
    u=u.withColumn('sq diff', sf.pow(sf.col('diff'),sf.col('sq')))
    u=u.groupBy(['geocode','geolevel','level']).max()

    return u

def AvgofSqError(get):
    # This function takes the average over levels for each geounit in the input
    u=get.groupBy(['geocode','geolevel']).avg()
    columnstodrop=['avg(avg(orig))','avg(avg(priv))','avg(avg(diff))','avg(avg(sq))','avg(max(orig))','avg(max(priv))','avg(max(diff))','avg(max(sq))']
    u=u.drop(*columnstodrop)
    return u
def MaxofSqError(get,get2):
    # This function takes the max over levels for each geounit of the input
    groupz=['geocode', 'geolevel']
    u=get.groupBy(['geocode','geolevel']).max()
    columnstodrop2=['max(avg(orig))','max(avg(priv))','max(avg(diff))','max(avg(sq))','max(max(orig))','max(max(priv))','max(max(diff))','max(max(sq))']
    u=u.drop(*columnstodrop2)
    u=u.join(get2,on=groupz)
    return u

# The following finds the avg and max of averages
get=AvgSqError(spark,df,geolevels,queries,schema)
get2=AvgofSqError(get)
get3=MaxofSqError(get,get2)

path3=save_location_linux + "NNLS_A.csv"
pdf3=get3.toPandas()
du.makePath(du.getdir(path3))
pdf3.to_csv(path3,index=False)

#the following finds the avg and max of maxes
pet=MaxSqError(spark,df,geolevels,queries,schema)
pet2=AvgofSqError(pet)
pet3=MaxofSqError(pet,pet2)


path2 = save_location_linux + "NNLS_B.csv"
pdf2 = pet3.toPandas()
du.makePath(du.getdir(path2))
pdf2.to_csv(path2, index=False)

def AvgofSqErrorGeo(get):
    # This function takes the average over geolevels (overall average) based on the input
    u=get.groupBy(['geolevel']).avg()
    columnstodrop=['avg(avg(orig))','avg(avg(priv))','avg(avg(diff))','avg(avg(sq))','avg(max(orig))','avg(max(priv))','avg(m\
ax(diff))','avg(max(sq))']
    u=u.drop(*columnstodrop)
    return u

def MaxofSqErrorGeo(let,qet):
    # This function takes the max over geolevels (overall max) based on the input
    groupz=['geolevel']
    u=let.groupBy(['geolevel']).max()
    columnstodrop2=['max(avg(orig))','max(avg(priv))','max(avg(diff))','max(avg(sq))','max(max(orig))','max(max(priv))','max(max(diff))','max(max(sq))']
    u=u.drop(*columnstodrop2)
    u=u.join(qet, on=groupz)
    return u


let=AvgofSqErrorGeo(get)
qet=MaxofSqErrorGeo(get,let)


path4 = save_location_linux + "NNLS_C.csv"
pdf4 = qet.toPandas()
du.makePath(du.getdir(path4))
pdf4.to_csv(path4, index=False)

wet=AvgofSqErrorGeo(pet)
zet=MaxofSqErrorGeo(pet,wet)
path5 = save_location_linux + "NNLS_D.csv"
pdf5 = zet.toPandas()
du.makePath(du.getdir(path5))
pdf5.to_csv(path5, index=False)
