import numpy as np
import pandas as pd
import gc
from programs.schema.schemas.schemamaker import SchemaMaker
import das_utils
import analysis.sdftools as sdftools
import analysis.treetools as treetools
import programs.workload.census_workloads as cw
import time
import re
from constants import *
import analysis.aggtools as aggtools
from pyspark.sql import Row, SparkSession
from pyspark.sql import functions as sf
import programs.writer.rowtools as rowtools


#spark = SparkSession.builder.appName('US PL94 CVAP Data - Saving Records as CSVs').getOrCreate()
experiments = [
    "s3://uscb-decennial-ite-das/experiments/PL94_CVAP/ManualTopdown_National_PLB_Time/td01/",
    "s3://uscb-decennial-ite-das/experiments/PL94_CVAP/ManualTopdown_National_PLB_Time/td025/",
    "s3://uscb-decennial-ite-das/experiments/PL94_CVAP/ManualTopdown_National_PLB_Time/td05/",
    "s3://uscb-decennial-ite-das/experiments/PL94_CVAP/ManualTopdown_National_PLB_Time/td1/",
    "s3://uscb-decennial-ite-das/experiments/PL94_CVAP/ManualTopdown_National_PLB_Time/td2/",
    "s3://uscb-decennial-ite-das/experiments/PL94_CVAP/ManualTopdown_National_PLB_Time/td4/"
]
# add das_decennial zip file to the spark context (to be sent to the core nodes)
spark.sparkContext.addPyFile("/mnt/users/moran331/das_decennial.zip")
schema_name = "PL94_CVAP"
schema = SchemaMaker.fromName(name=schema_name)
runs = np.array([treetools.RunTree(path).getDataPaths().tolist() for path in experiments]).flatten()
blocks = []
geocode = None
for r,run in enumerate(runs):
    print(run)
    rdd = spark.sparkContext.pickleFile(run)
    if r == 0:
        block = rdd.take(1).pop()
        geocode = block['geocode']
    else:
        block = rdd.filter(lambda node: node['geocode'] == geocode).take(1).pop()
    block['run_id'] = ".".join(run.split("/")[-3:-1])
    blocks.append(block)

blocks2 = []
for blk in blocks:
    blk['raw'] = blk['raw'].toDense()
    blk['syn'] = blk['syn'].toDense()
    blocks2.append(blk)

blockrdd = spark.sparkContext.parallelize(blocks)
#blockrdd = aggtools.getGeolevelRDD(blockrdd, "Block")
mapper = sdftools.makeHistRows
# node, runid, schema, sparse=False
blockdf = blockrdd.flatMap(lambda node: mapper(node, node['run_id'], schema=schema, sparse=False)).toDF()

sparse = blockdf.filter((sf.col('orig') != 0) | (sf.col('priv') != 0))
sparse = sparse.sort(schema.dimnames + ['run_id']).persist()

# Checked on 2019-06-05
# There seems to be sufficient variation across runs (even in a single block) to suggest that
# the reload_noisy option being turned on did NOT reuse noisy measurements in-between runs.

# The clearPath function in savePickledRDD within the das_utils module seems to have deleted
# noisy measurements from previous runs before saving (and subsequently loading) the current
# run's noisy measurements.

# The most likely reason that the experiment crashed is because the subprocess within clearPath
# probably did not finish deleting the previous run's noisy measurements before spark tried to
# write the current run's noisy measurements to s3.
# This should be addressed, as subprocess probably has callback/waiting capabilities.

# The odd thing of having over 150 runs of the experiment finish successfully without crashing
# from this error is consistent with the subtleties of the process interactions; if the subprocess
# has finished deleting before the other process began to save, then there would be no reason for
# spark to crash, which it did over 150 times. On the other hand, if it didn't finish, then it
# would crash, which also happened, just at a much later run.

das_utils.freeMemRDD(blockrdd)
