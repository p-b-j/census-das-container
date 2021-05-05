# Bias metrics for demographers

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

analysis_results_save_location = f"/mnt/users/rao00316/analysis_reports/"
spark_loglevel = "ERROR"
analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
spark = analysis.spark
S3_BASE="s3://uscb-decennial-ite-das/users"
save_location_linux = f"/mnt/users/rao00316/bias/"


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


def NEbias(spark,df,geolevels,queries,schema):
    u=sdftools.getAnswers(spark,df,geolevels,schema,queries)
    # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
    u=u.withColumn('diff',sf.col('priv')-sf.col('orig'))
    z=u.groupby(['geolevel']).avg()
    return u,z
def MMbias(u):
    u=u.withColumn('MMPE', sf.col('diff')/sf.col('orig'))
    z=u.groupby(['geolevel']).avg()
    return u,z

def TAES(spark,df,geolevels,queries,schema,u):
    z=sdftools.getAnswers(spark,df,geolevels,schema,queries)
    z=z.groupby(['geolevel','run_id']).sum()
    u.show(10)
    print("this is z")
    z.show(10)
    q=u.join(z, on=['geolevel','run_id'])
    columnstodrop=['plb','budget_group']
    q=q.drop(*columnstodrop)
    # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
    q=q.withColumn('MDF/sum',sf.col('priv')/sf.col('sum(priv)'))
    q=q.withColumn('CEF/sum',sf.col('orig')/sf.col('sum(orig)'))
    q=q.withColumn('difference',sf.col('MDF/sum')-sf.col('CEF/sum'))
    q=q.withColumn('abs',sf.abs(sf.col('difference')))
    print("This is q")
    q.show(10)
    q=q.groupby(['geolevel','run_id']).sum()
    columnstodrop=['sum(diff)','sum(sum(orig))','sum(sum(priv))','sum(MDF/sum)','sum(CEF/sum)','sum(difference)']
    print("this is q2")
    q=q.drop(*columnstodrop)
    q.show(10)
    z=q.groupby(['geolevel']).avg()
    print("this is z")
    z.show(10)
    return q,z

get,get2=NEbias(spark,df,geolevels,queries,schema)
path=save_location_linux+"NEbias.csv"
pdf=get.toPandas()
du.makePath(du.getdir(path))
pdf.to_csv(path,index=False)

path2=save_location_linux+"NEbias_av.csv"
pdf2=get2.toPandas()
du.makePath(du.getdir(path2))
pdf2.to_csv(path2,index=False)

get3,get4=MMbias(get)
path3=save_location_linux+"MMbias.csv"
pdf3=get3.toPandas()
du.makePath(du.getdir(path3))
pdf3.to_csv(path3,index=False)

path4=save_location_linux+"MMbias_av.csv"
pdf4=get4.toPandas()
du.makePath(du.getdir(path4))
pdf4.to_csv(path4,index=False)

zed,zed2=TAES(spark,df,geolevels,queries,schema,get)
path5=save_location_linux+"TAES.csv"
pdf5=zed.toPandas()
du.makePath(du.getdir(path5))
pdf5.to_csv(path5,index=False)

path6=save_location_linux+"TAESavg.csv"
pdf6=zed2.toPandas()
du.makePath(du.getdir(path6))
pdf6.to_csv(path6,index=False)


