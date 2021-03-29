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

import analysis.tools.datatools as datatools
import analysis.tools.setuptools as setuptools
import analysis.plotting.report_plots as rp
import analysis.tools.sdftools as sdftools

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf
from pyspark.sql import Row

from programs.schema.schemas.schemamaker import SchemaMaker


if __name__ == "__main__":
    ################################
    # define experiments to analyze
    ################################
    S3_BASE = "s3://uscb-decennial-ite-das/users"
    
    #################
    # setup analysis
    #################
    save_location       = f"moran331/analysis_reports/"
    save_location_s3    = f"{S3_BASE}/moran331/analysis_reports/"
    save_location_linux = f"/mnt/users/moran331/analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=save_location, spark_loglevel=spark_loglevel)

    ####################################
    # Accessing Noisy Measurements
    ####################################
    noisy_measurements_state_path = f"{S3_BASE}/lecle301/dhcp_eps4/run36_of_25/full_person/noisy_measurements/application_1574779932308_0073-State.pickle/"
    noisy_measurements_state = analysis.spark.sparkContext.pickleFile(noisy_measurements_state_path)
    nm_state = noisy_measurements_state
    print(nm_state)
    
    geounit = nm_state.take(1).pop()
    
    print(geounit)
    geocode = geounit.geocode
    print(geocode)
    dp_queries = geounit.dp_queries
    
    experiment_name = "dhcp_eps4_run36"
    experiment_path = f"{S3_BASE}/lecle301/dhcp_eps4/run36_of_25/full_person/"
    experiment = analysis.make_experiment(experiment_name, experiment_path)
    
    df = experiment.getDF()
    sdftools.print_item(df, "Experiment DF", show=100)
    
    geolevel_df = sdftools.aggregateGeolevels(experiment.spark, df, ['STATE'])
    sdftools.print_item(geolevel_df, "Geolevel DF")
    
    filtered_df = df.filter(df.geocode == geocode).persist()
    sdftools.print_item(filtered_df, "Experiment DF", show=1000)
    
    
    
        
    
    
    
    
    
    
    
    
    
    
