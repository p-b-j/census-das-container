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

import analysis.tools.sdftools as sdftools
import analysis.tools.treetools as treetools
import analysis.tools.metric_functions as mf
import analysis.tools.crosswalk as crosswalk

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf
from pyspark.sql import Row

import analysis.tools.setuptools as setuptools
import programs.datadict as dd

from programs.schema.schemas.schemamaker import SchemaMaker

import scipy.sparse as ss
import programs.sparse as sp

import analysis.tools.mappers as mappers
from pyspark.sql import Row
from pyspark.sql.window import Window

# import recoder
import programs.writer.dhcp_to_mdf2020 as dhcp_to_mdf2020

#import analysis.plotting.report_plots as rp

import operator

def testdata_random_geounit_generator(geocode, schema, density=0.01, scale=10):
    raw_mat = np.round(ss.random(1, schema.size, format='csr', density=density) * scale)
    syn_mat = np.round(ss.random(1, schema.size, format='csr', density=density) * scale)
    raw_sparse = sp.multiSparse(raw_mat, schema.shape)
    syn_sparse = sp.multiSparse(syn_mat, schema.shape)
    return { 'geocode': geocode, 'raw': raw_sparse, 'syn': syn_sparse }
    

def addIndexToRow(row_ind):
    row, index = row_ind
    row['EPNUM'] = index
    return row


if __name__ == "__main__":
    ################################
    # define experiments to analyze
    ################################
    S3_BASE = "s3://uscb-decennial-ite-das/users"
    
    #################
    # setup analysis
    #################
    analysis_results_save_location = f"/mnt/users/moran331/analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
    spark = analysis.spark

    schema = SchemaMaker.fromName("DHCP_SCHEMA")
    num_geocodes = 5
    geocodes = [str(x).zfill(16) for x in range(num_geocodes)]
    geounits = [testdata_random_geounit_generator(x, schema, density=0.00001, scale=10) for x in geocodes]
    sdftools.print_item(geounits, "Random Geounit Data")
    
    rdd = spark.sparkContext.parallelize(geounits).persist()
    sdftools.print_item(rdd, "Parallelized RDD data")
    
    df = rdd.flatMap(lambda node: mappers.getSparseDF_mapper(node, schema)).map(lambda row: Row(**row)).toDF().persist()
    sdftools.print_item(df, "DF of Random Geounit Data")
    
    recoder = dhcp_to_mdf2020.DHCPToMDF2020Recoder().recode
    mdf = (
        rdd.flatMap(lambda node: mappers.getMicrodataDF_mapper(node, schema, privatized=True, mangled_names=True, recoders=recoder))
           .zipWithIndex()
           .map(addIndexToRow)
           .map(lambda row: Row(**row))
           .toDF()
           .persist()
    )
    sdftools.print_item(mdf, "DF of Microdata (privatized)")
    
    #mdf = mdf.withColumn("EPNUM", sf.monotonically_increasing_id()).persist()
    #mdf = mdf.withColumn("EPNUM", sf.row_number().over(Window.orderBy(sf.monotonically_increasing_id())) - 1)
    mdf = mdf.drop('data_type').persist()
    
    sdftools.print_item(mdf, "DF of Microdata (privatized)", show=1000)

    ###################################################################
    # Converting back to histogram form
    ###################################################################
    def age_recoder(rowdict, schema):
        age = rowdict.pop('QAGE', None)
        rowdict['age'] = int(age)
        return rowdict
    
    def sex_recoder(rowdict, schema):
        qsex = rowdict.pop('QSEX', None)
        if qsex == "1":
            sex = 0 # male
        elif qsex == "2":
            sex = 1 # female
        else:
            raise ValueError("invalid QSEX value")
        rowdict['sex'] = sex
        return rowdict
        
    def hispanic_recoder(rowdict, schema):
        cenhisp = rowdict.pop('CENHISP', None)
        if cenhisp == "1":
            hispanic = 0 # not hispanic
        elif cenhisp == "2":
            hispanic = 1 # hispanic
        else:
            raise ValueError("invalid CENHISP value")
        rowdict['hispanic'] = hispanic
        return rowdict
    
    def cenrace_recoder(rowdict, schema):
        cenrace = rowdict.pop('CENRACE', None)
        rowdict['cenrace'] = int(cenrace) - 1
        return rowdict
    

    gqtype_dict = {
        '101': 18,
        '102': 19,
        '103': 20,
        '104': 21,
        '105': 22,
        '106': 23,
        '201': 24,
        '202': 25,
        '203': 26,
        '301': 27,
        '401': 28,
        '402': 29,
        '403': 30,
        '404': 31,
        '405': 32,
        '501': 33,
        '601': 34,
        '602': 35,
        '701': 36,
        '801': 37,
        '802': 38,
        '900': 39,
        '901': 40,
        '997': 41
    }

    relship_dict = {
        '21': 2,
        '22': 3,
        '23': 4,
        '24': 5,
        '25': 6,
        '26': 7,
        '27': 8,
        '28': 9,
        '29': 10,
        '30': 11,
        '31': 12,
        '32': 13,
        '33': 14,
        '34': 15,
        '35': 16,
        '36': 17
    }

    def relgq_recoder(rowdict, schema):
        rtype = rowdict.pop('RTYPE', None)
        relship = rowdict.pop('RELSHIP', None)
        live_alone = rowdict.pop('LIVE_ALONE', None)
        gqtype = rowdict.pop('GQTYPE', None)
        
        if rtype == "3": # housing unit
            if relship == '20' and live_alone == "1": # household and lives alone
                relgq = 0
            elif relship == '20' and live_alone == "2": # household and doesn't live alone
                relgq = 1
            else:
                relgq = relship_dict.get(relship, None)
                if relgq is None:
                    raise ValueError("invalid relship for rtype == '3'")
        
        elif rtype == "5": # gq type
            relgq = gqtype_dict.get(gqtype, None)
            if relgq is None:
                raise ValueError("invalid gqtype for rtype == '5'")
        
        else:
            raise ValueError("invalid RTYPE value")
        
        rowdict['relgq'] = relgq
        return rowdict
        
        
    
    def reader_recoder(rowdict, schema):
        rowdict = relgq_recoder(rowdict, schema)
        rowdict = sex_recoder(rowdict, schema)
        rowdict = age_recoder(rowdict, schema)
        rowdict = hispanic_recoder(rowdict, schema)
        rowdict = cenrace_recoder(rowdict, schema)
        return rowdict
    
    mdf = mdf.withColumn('geocode', sf.concat(sf.col("TABBLKST"), sf.col("TABBLKCOU"), sf.col("TABTRACTCE"), sf.col("TABBLK")[0:1], sf.col("TABBLK"))).persist()
    mdf = mdf.withColumn('geolevel', sf.lit('BLOCK')).persist()
    mdf = (
        mdf.rdd
           .map(lambda row: row.asDict())
           .map(lambda rowdict: reader_recoder(rowdict, schema))
           .map(lambda rowdict: Row(**rowdict))
           .toDF()
           .persist()
    )
    mdf = mdf.select("*").groupBy(schema.dimnames + ['geocode', 'geolevel']).count()
    sdftools.print_item(mdf, "Priv Counts", show=10000)

    
    # try repartition and/or coalesce to get smaller numbers of part files
    #popdf.repartition(1).write.format('csv').option('header', 'true').save(f"{S3_BASE}/moran331/population_densities/DHCP_HHGQ/danVariant1-2_td4_run_0000_VA_pop_densities2")
        
