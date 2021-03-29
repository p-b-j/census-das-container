import das_utils as du
import pandas
import numpy as np
import operator
import os

import analysis.tools.setuptools as setuptools
import analysis.tools.datatools as datatools
import analysis.tools.sdftools as sdftools
import analysis.tools.graphtools as graphtools

import analysis.constants as AC
import constants as C
from constants import CC

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

    schema = SchemaMaker.fromName(CC.SCHEMA_REDUCED_DHCP_HHGQ)

    pp10_gq_edited = spark.read.csv("s3://uscb-decennial-ite-das/2010/cef/pp10_gq_edited.csv")

    pp10_hu_edited = spark.read.csv("s3://uscb-decennial-ite-das/2010/cef/pp10_hu_edited.csv")


    pp10_grf = spark.read.csv("s3://uscb-decennial-ite-das/2010/cef/pp10_grf_tab.csv")

    # Clean up gq file by removing extra characters like b and ' from data, renaming columns, and dropping un-needed columns
    gq_revised = pp10_gq_edited.withColumn("final_pop",sf.regexp_replace(sf.col("_c9"), "[b']", "")).withColumn("FGQ",sf.regexp_replace(sf.col("_c6"), "[b']", "")).withColumn("PEG",sf.regexp_replace(sf.col("_c4"), "[b']", "")).withColumn("LC",sf.regexp_replace(sf.col("_c2"), "[b']", "")).withColumn("GQ",sf.regexp_replace(sf.col("_c5"), "[b']", "")).withColumn("COLB",sf.regexp_replace(sf.col("_c1"), "[b']", ""))

    gq_revised=gq_revised.drop("_c0","_c1","_c2","_c4","_c5","_c6","_c9") 

    gq_revised=gq_revised.withColumnRenamed("_c3","MAFID").withColumnRenamed("_c7","PP_GQ_MEDIAN_AGE").withColumnRenamed("_c8","EDIT_SEQ").withColumnRenamed("final_pop","FINAL_POP").withColumnRenamed("FGQ","FGQTYPE").withColumnRenamed("GQ","GQTYPE").withColumnRenamed("PEG","PEGQTYPE").withColumnRenamed("LC","LCO").withColumnRenamed("COLB","COLBLKST")

    # Remove first row, which contains column names and no data
    gq_revised=gq_revised.filter((gq_revised.MAFID != "MAFID"))

    # Clean hu data
    hu_revised = pp10_hu_edited.select("_c0", "_c1", "_c2", "_c21", "_c22")


    hu_revised = hu_revised.withColumnRenamed("_c0","COLBLKST").withColumnRenamed("_c1","LCO").withColumnRenamed("_c2","MAFID").withColumnRenamed("_c21","EDIT_SEQ").withColumnRenamed("_c22","FINAL_POP")

    hu_revised=hu_revised.filter((hu_revised.MAFID != "MAFID"))
    
    # Clean gq file by removing extra digits not needed
    gq_revised=gq_revised.withColumn("mafid_temp",sf.expr("substring(MAFID, 1, length(MAFID)-2)"))
    gq_revised=gq_revised.withColumn("edit_seq2",sf.expr("substring(EDIT_SEQ, 1, length(EDIT_SEQ)-2)"))
    gq_revised=gq_revised.drop("MAFID", "GQTYPE", "PEGQTYPE", "FGQTYPE", "PP_GQ_MEDIAN_AGE","EDIT_SEQ")
    gq_revised=gq_revised.withColumnRenamed("mafid_temp","MAFID").withColumnRenamed("edit_seq2","EDIT_SEQ")

    # Perform Union of gq and hu 
    gq_hu_union = hu_revised.union(gq_revised)

    # Read and clean ops file
    op_revised= spark.read.csv("s3://uscb-decennial-ite-das/2010/cef/pp10_op.csv")
    op_revised=op_revised.select("_c0", "_c16","_c17","_c55","_c68")
    op_revised=op_revised.withColumnRenamed("_c0","MAFID").withColumnRenamed("_c16", "LCO").withColumnRenamed("_c17", "COLBLKST").withColumnRenamed("_c55", "FINAL_POP").withColumnRenamed("_c68", "OIDTB")
    op_revised=op_revised.filter((op_revised.MAFID != "MAFID"))

    # This join produces duplicate columns
    #inner_gq_hu_op = gq_hu_union.join(op_revised, gq_hu_union.MAFID==op_revised.MAFID)

    # This is the proper join that eliminates duplicate columns
    inner_gq_hu_op = gq_hu_union.join(op_revised, ["MAFID"]+["COLBLKST"]+["LCO"]+["FINAL_POP"])


    # Read and clean GRF file
    pp10_grf = spark.read.csv("s3://uscb-decennial-ite-das/2010/cef/pp10_grf_tab.csv")
    grf_revised=pp10_grf.drop("_c4","_c5","_c6","_c7","_c8","_c9","_c10","_c11","_c12","_c13","_c14","_c15","_c16","_c17","_c18","_c19","_c20","_c21","_c22","_c24","_c25","_c27","_c28","_c29","_c30","_c31","_c32","_c33","_c34","_c35","_c36","_c37","_c38","_c39","_c40","_c41","_c42","_c45","_c46","_c47","_c48","_c49","_c50","_c51","_c52","_c53","_c54","_c55","_c56","_c57","_c58","_c59","_c60","_c61","_c62","_c63","_c64","_c65","_c66","_c67","_c68","_c69")
    grf_revised=grf_revised.withColumnRenamed("_c0","TABBLKST").withColumnRenamed("_c1","TABBLKCOU").withColumnRenamed("_c2","TABTRACTCE").withColumnRenamed("_c3","TABBLK").withColumnRenamed("_c23","PLACEFP").    withColumnRenamed("_c26","AIANNHFP").withColumnRenamed("_c43","SLDUST").withColumnRenamed("_c44","SLDLST").withColumnRenamed("_c70","OIDTABBLK")
    grf_revised=grf_revised.filter((grf_revised.TABBLKST != "TABBLKST"))

    # Perform join of ops file and grf file, linking via OIDTB
    inner_op_grf = op_revised.join(grf_revised, op_revised.OIDTB==grf_revised.OIDTABBLK)
    

    # Perform final join of Union of (gq+hu) Joined with ops and join of ops and grf

    total_join=inner_gq_hu_op.join(inner_op_grf, ["OIDTB"]+["FINAL_POP"]+["LCO"]+["COLBLKST"]+["MAFID"])

    total_join.show()
    print(total_join.count())

    # Compute counts of desired geolevels
    no_state=total_join.select(['TABBLKST']).distinct().count()

    block=total_join.withColumn("Block", sf.concat(sf.col("TABBLKST"), sf.col("TABBLKCOU"),sf.col("TABTRACTCE"),sf.col("TABBLK")))

    no_block = block.select(['Block']).distinct().count()
    place=total_join.withColumn("Place", sf.concat(sf.col("TABBLKST"), sf.col("PLACEFP")))
    no_place = place.select(['Place']).distinct().count()
    group=block.withColumn("group", sf.expr("substring(Block, 1, length(Block)-3)"))
    no_group = group.select(['group']).distinct().count()
    county=total_join.withColumn("county", sf.concat(sf.col("TABBLKST"), sf.col("TABBLKCOU")))
    no_county = county.select(['county']).distinct().count()
    no_tract = total_join.select(['TABTRACTCE']).distinct().count()
    sldl=total_join.withColumn("sldl", sf.concat(sf.col("TABBLKST"), sf.col("sldlst")))
    no_sldl=sldl.select(['sldl']).distinct().count()
    sldu=total_join.withColumn("sldu", sf.concat(sf.col("TABBLKST"), sf.col("sldust")))
    no_sldu=sldu.select(['sldu']).distinct().count()
    data=[{"Area":'State','Value': no_state},
          {"Area":'County','Value':no_county},
          {"Area":'Tract','Value':no_tract},
          {"Area":'Place', 'Value':no_place},
          {"Area":'Block Group','Value':no_group},
          {"Area":'Block','Value': no_block},
          {"Area":'SLDL','Value': no_sldl},
          {"Area":'SLDU','Value': no_sldu}
    ]
    df = spark.createDataFrame(data)
    pandas_df=df.toPandas()
    csv_savepath = "s3://uscb-decennial-ite-das/rao001/Geolevel_counts.csv"
    du.makePath(du.getdir(csv_savepath))
    pandas_df.to_csv(csv_savepath, index=False)
