# Accuracy metrics for demographers - MAE and MAPE metrics

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
import glob


analysis_results_save_location = f"/mnt/users/rao00316/analysis_reports/"
spark_loglevel = "ERROR"
analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
spark = analysis.spark
S3_BASE="s3://uscb-decennial-ite-das/users"
save_location_linux = f"/mnt/users/rao00316/amaz/"


path = [
    "s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td16/"
]

runs = datatools.getDASRuns(path)

schema_name = "DHCP_HHGQ"

schema = SchemaMaker.fromName(name=schema_name)

experiment = analysis.make_experiment("DHCP", path)
df = experiment.getDF()
schema = experiment.schema

geolevels = [C.COUNTY] #, C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD]

queries = ['total']
y=sdftools.getAnswers(spark,df,geolevels,schema,queries)

path2=save_location_linux+"RAW.csv"
pdf2=y.toPandas()
du.makePath(du.getdir(path2))
pdf2.to_csv(path2,index=False)



def MAE(spark,df,geolevels,queries,schema):
    u=sdftools.getAnswers(spark,df,geolevels,schema,queries)
    u=u.withColumn('diff',sf.col('priv')-sf.col('orig'))
    u=u.withColumn('abs diff', sf.abs(sf.col('diff')))
    y=u.groupby(['geocode','geolevel','level']).avg()
    z=u.groupby(['geolevel']).avg()
    return u,y,z

#def MAE_avg1(u):
  #  z=u.groupby(['geocode','geolevel','level']).avg()
  #  return u


#def MAE_avg2(u):
 #   u=u.groupby(['geolevel']).avg()
  #  return u

def MAPE(u):
    
    u=u.withColumn('MAPE', sf.col('abs diff')/sf.col('orig'))
    z=u.groupby(['geolevel']).avg()
    return u,z    

#def MAPE_avg(u):
 #   u=u.groupby(['geolevel']).avg()    
  #  return u

#quantile=[0.9]
#zef=sdftools.getGroupQuantiles(get5, 'MAPE','geolevel',0.9)
#sdftool.show(zef)

get,get2,get3=MAE(spark,df,geolevels,queries,schema)
path=save_location_linux+"MAE.csv"
pdf=get.toPandas()
du.makePath(du.getdir(path))
pdf.to_csv(path,index=False)

#get2=MAE_avg1(get)
path3=save_location_linux+"MAE_avg1.csv"
pdf3=get2.toPandas()
du.makePath(du.getdir(path3))
pdf3.to_csv(path3,index=False)

#get4=MAE_avg2(get)
path4=save_location_linux+"MAE_avg2.csv"
pdf4=get3.toPandas()
du.makePath(du.getdir(path4))
pdf4.to_csv(path4,index=False)

get5,get6=MAPE(get)
path5=save_location_linux+"MAPE.csv"
pdf5=get5.toPandas()
du.makePath(du.getdir(path5))
pdf5.to_csv(path5,index=False)

#get6=MAPE_avg(get5)
path6=save_location_linux+"MAPE_avg.csv"
pdf6=get6.toPandas()
du.makePath(du.getdir(path6))
pdf6.to_csv(path6,index=False)

quantile=[0.9]
zef=sdftools.getGroupQuantiles(get5, 'MAPE','geolevel',quantile)
sdftools.show(zef)


path = f"/mnt/users/rao00316/amaz/"

all_files = glob.glob(os.path.join(path, "*.csv"))

writer = pandas.ExcelWriter('out.xls', engine='xlswriter')

for f in all_files:
    df = pandas.read_csv(f)
    df.to_excel(writer, sheet_name=os.path.splitext(os.path.basename(f))[0], index=False)

writer.save()
