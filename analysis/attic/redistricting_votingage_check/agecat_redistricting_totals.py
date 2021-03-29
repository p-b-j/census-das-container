import numpy as np
import pandas as pd
import gc
from programs.schema.schemas.schemamaker import SchemaMaker
import das_utils as du
import analysis.sdftools as sdftools
import analysis.treetools as treetools
import programs.workload.census_workloads as cw
import time
import re
from constants import *
import analysis.aggtools as aggtools
from pyspark.sql import Row, SparkSession
from pyspark.sql import functions as sf


def main():
    spark = SparkSession.builder.appName('RI Redistricting Data - PL94_P12 - Extracting agecat totals').getOrCreate()
    experiments = [
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td10_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td1_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td3_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td025_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td05_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td001_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td01_1/",
        "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td2_1/"
    ]


    # add das_decennial zip file to the spark context (to be sent to the core nodes)
    spark.sparkContext.addPyFile("/mnt/users/moran331/das_decennial.zip")
    schema_name = "PL94_P12"
    schema = SchemaMaker.fromName(name=schema_name)
    for path in experiments:
        tree = treetools.RunTree(path)
        runs = tree.runs
        for r, run in enumerate(runs):
            if r == 0:
                df = sdftools.getSparseDF(spark, run, schema, run_columns=True).persist()
            else:
                df = df.union(sdftools.getSparseDF(spark, run, schema, run_columns=True)).persist()
        df = df.persist()
        plb = str(du.algset2plb(du.findallSciNotationNumbers(tree.algsets[0])[0]))
        df = df.withColumn("plb", sf.lit(plb))
        df.show()
        geodict = aggtools.getGeodict()
        geolevel = "State"
        mapping = geodict[geolevel]
        group = ["plb", "run_id", geolevel] + schema.dimnames
        geodf = df.withColumn(geolevel, df.geocode[0:mapping]).groupBy(group).sum().persist()
        geodf = sdftools.stripSQLFromColumns(geodf)
        geodf.show()
        queryname = "votingage"
        querydf = sdftools.getQueryDF(geodf, queryname, schema, basegroup=["run_id", geolevel, "plb"]).persist()
        querydf.show()
        savepath = f"/mnt/users/moran331/redistricting/agecat_redistricting_state_totals_2019_06_27/{tree.algsets[0]}/"
        du.makePath(savepath)
        pd = querydf.toPandas().to_csv(savepath + "votingage_all_25_runs.csv", index=False)
        print(f"---Agecat--- | \n{querydf.toPandas().to_string()}")
            




if __name__ == "__main__":
    main()










