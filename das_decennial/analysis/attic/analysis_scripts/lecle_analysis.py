import analysis.tools.sdftools as sdftools
import analysis.tools.treetools as treetools
import analysis.tools.metric_functions as mf

import analysis.constants as AC
import constants as C

from pyspark.sql import functions as sf

import analysis.tools.setuptools as setuptools
import programs.datadict as dd

import datetime

import numpy as np

def calc_index(query, schema):
    tb = dd.getTableBuilder(schema if isinstance(schema, str) else schema.name)
    print(f"{datetime.datetime.now()} --- calc_index retrieved tb {tb} w/ schema {schema} on query {query}")
    table = tb.getCustomTable(query)
    print(f"{datetime.datetime.now()} --- calc_index built table:\n{table}")
    levels = np.array(table['Level'])
    print(f"{datetime.datetime.now()} --- calc_index got levels:\n{levels}")
    print(f"{datetime.datetime.now()} --- # levels: {len(levels)}")
    levelList = list(range(int(len(levels)/2)))
    level_dict = dict(zip(levels, levelList+levelList)) # BRITTLE: this WILL NOT WORK if we change query
    print(f"{datetime.datetime.now()} --- calc_index created level_dict:\n{level_dict}")
    def age_to_index(age_str):
        return level_dict.get(age_str, -1)
    return age_to_index

def L1_expected_age_manual_addCustom(sdf, geolevels, groupby=[]):
    results = {}
    query = 'age * sex'
    age_udf = sf.udf(calc_index(query, sdf.schema))
    
    for geolevel in geolevels:
        geosdf = sdf.clone().getGeolevels(geolevel).answerQueries(query).show(n=1000)
        geosdf.df = geosdf.df.withColumn("age_index", age_udf(sf.col(AC.LEVEL))).persist()
        geosdf.df = geosdf.df.withColumn(f"ev_part_{AC.ORIG}", sf.col("age_index") * sf.col(AC.ORIG)).persist()
        # AC.PRIV means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
        geosdf.df = geosdf.df.withColumn(f"ev_part_{AC.PRIV}", sf.col("age_index") * sf.col(AC.PRIV)).persist()
        geosdf = geosdf.sum(groupby=groupby)
        geosdf.df = geosdf.df.withColumn(f"ev_{AC.ORIG}", sf.col(f"ev_part_{AC.ORIG}") / sf.col(AC.ORIG)).persist()
        geosdf.df = geosdf.df.withColumn(f"ev_{AC.PRIV}", sf.col(f"ev_part_{AC.PRIV}") / sf.col(AC.PRIV)).persist()
        geosdf = geosdf.L1(col1=f"ev_{AC.PRIV}", col2=f"ev_{AC.ORIG}")
        groupby = [AC.RUN_ID, AC.PLB, AC.GEOLEVEL] # Averaging over geounits, so we drop them from groupBy
        geosdf.df = geosdf.df.groupBy(groupby).avg('L1') # Will this handle geounits with priv=orig=0 correctly? Don't think so..
        
        results[f"{geolevel}_Avg_L1_E(age)"] = geosdf
    return results

def makeSexAgeHistogram(geocode_data):
    import numpy
    #print(f"makeSexAgeHistogram received geocode_data: {geocode_data}")
    geocode_runid_plb, data = geocode_data[0], list(geocode_data[1])
    print(f"makeSexAgeHistogram received:")
    print(f"{geocode_runid_plb}")
    print(f"Second looks like:")
    print(f"{data[:5]}")
    #print(f"Second expands like:")
    #print(f"{data[0]}")
    #print(f"{data[1]}")
    privHistogram = numpy.zeros(shape=(2,116)) # Sex by Age shape hard-coded
    origHistogram = numpy.zeros(shape=(2,116)) # Sex by Age shape hard-coded
    for row in data:
        age = int(row[-3])
        assert ('Male' in row[-1] or 'Female' in row[-1]), "Neither Male nor Female str found in row " + str(row)
        sex = 0 if 'Male' in row[-1] else 1
        origHistogram[sex, age] = int(row[3])
        privHistogram[sex, age] = int(row[4])
    print(f"makeSexAgeHistogram is returning:")
    print(geocode_runid_plb)
    print(privHistogram)
    print(origHistogram)
    print("******")
    return (geocode_runid_plb, (privHistogram, origHistogram))

def unwrapHist(hist):
    unwrappedHist = [[i]*int(val) for i, val in enumerate(hist)]
    flatUnwrappedHist = []
    for sublist in unwrappedHist:
        flatUnwrappedHist += sublist
    assert len(flatUnwrappedHist) > 0, "flatUnwrappedHist with len <= 0 detected."
    flatUnwrappedHist = [-100] if len(flatUnwrappedHist) == 0 else flatUnwrappedHist # If no people, assume 1 dummy -100 y/o person
    return flatUnwrappedHist

def getQuantilesError(geocode_hists, quantiles=list(range(0,11,1)), sex="male"):
    import numpy
    sexMap = {"male":0, "female":1}
    print(f"getQuantilesError received geocode_hists: {geocode_hists}")
    quantiles = [float(q)/10. for q in quantiles]
    geocode_runid_plb, origHist, privHist = geocode_hists[0], geocode_hists[1][0], geocode_hists[1][1]
    quantileErrors = []
    for s in (sexMap[sex],): # Male, Female
        unwrappedOrig = unwrapHist(origHist[s,])
        unwrappedPriv = unwrapHist(privHist[s,])
        print(f"For sex {s}, unwrappedOrig:\n{unwrappedOrig}")
        print(f"For sex {s}, unwrappedPriv:\n{unwrappedPriv}")
        quantileErrorNp = numpy.abs(numpy.quantile(unwrappedOrig, quantiles) - numpy.quantile(unwrappedPriv, quantiles))
        quantileErrors.append(quantileErrorNp)
    #print(f"quantileErrors returning: {geocode_runid_plb}, {quantileErrors}")
    #return (geocode_runid_plb, quantileErrors)
    flattened_return = [x for x in geocode_runid_plb] + [float(x) for x in quantileErrors[0]]
    print(f"getQuantileErrors is returning: {flattened_return}")
    return flattened_return

def largeGeounitsOnly(geocode_hists, k=0, sex="male"):
    import numpy
    sexMap = {"male":0, "female":1}
    print(f"largeGeounitsOnly received geocode_hists: {geocode_hists}; & k param {k}")
    geocode_runid_plb, origHist, privHist = geocode_hists[0], geocode_hists[1][0], geocode_hists[1][1]
    if numpy.sum(origHist[sexMap[sex],]) >= k and numpy.sum(privHist[sexMap[sex],]) >= k:
        return True
    else:
        return False

def inspectRddHead(rdd, geolevel):
    rddHead = list(rdd.take(5))
    print(f"{datetime.datetime.now()} --- rdd head looks like:")
    for i, elem in enumerate(rddHead):
        elem0 = [x for x in elem[0]]
        print(f"{datetime.datetime.now()} --- For geolevel {geolevel}, element # {i} looks like: {elem0}, list of len {len(list(elem[1]))}")
        print(f"{datetime.datetime.now()} --- First few elements of elem 1 look like:")
        for item in list(elem[1])[:5]:
            print(item)
    numElements = rdd.count()
    print(f"Inspected rdd ^^^ had length {numElements}")

def L1_quantile_rdd(sdf, geolevels, sex="male"):
    results = {}
    query = 'sex * age'
    age_udf = sf.udf(calc_index(query, sdf.schema))
    print(f"{datetime.datetime.now()} --- Full list of l1 quantile rdd geolevels is: {geolevels}")
    for geolevel in geolevels:
        print(f"{datetime.datetime.now()} --- Starting geolevel {geolevel}")
        geosdf = sdf.clone().getGeolevels(geolevel).answerQueries(query)
        geosdf.show(n=1000)
        print(f"^^^ {datetime.datetime.now()} --- geosdf after cloning (but lazy, so..) ^^^")
        df = geosdf.df.withColumn("age_index", age_udf(sf.col(AC.LEVEL)))
        # AC.PRIV means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
        df = df.select([AC.GEOCODE, AC.RUN_ID, AC.PLB, AC.ORIG, AC.PRIV, AC.LEVEL, "age_index", "age", "sex"])
        df.show(1000)
        print(f"^^^ {datetime.datetime.now()} --- Showing RDD after we drop back to just the 7 variables we need for geolevel {geolevel} ^^^")
        rdd = df.rdd.map(lambda x: ((x[0],x[1],x[2]), list(x))).groupByKey() # Group by geocode/run_id/plb
        inspectRddHead(rdd, geolevel)
        rdd = rdd.map(makeSexAgeHistogram)
        inspectRddHead(rdd, geolevel)
        rdd = rdd.filter(lambda x: largeGeounitsOnly(x, k=1, sex=sex)) # Restrict to geounits where both orig & priv have size >= k
        inspectRddHead(rdd, geolevel)
        rdd = rdd.map(lambda x: getQuantilesError(x, sex=sex))
        inspectRddHead(rdd, geolevel)
        quantileVars = [f"{sex}Quantile0.{i}" for i in range(10)] + [f"{sex}Quantile1.0"]
        cols = ["geocode", "run_id", "plb"] + quantileVars
        df = rdd.toDF(cols)
        df.show()
        print(f"^^^ rdd converted back to dataframe")
        quantileVars = [f"`{sex}Quantile0.{i}`" for i in range(10)] + [f"`{sex}Quantile1.0`"]
        df = df.groupBy(["run_id", "plb"]).avg(*quantileVars)
        df.show()
        print(f"^^^ rdd converted back to dataframe, L1 error averaged over geocode")
        geosdf.df = df
        results[f"{geolevel}_L1_age_quantiles"] = geosdf
    return results

if __name__ == "__main__":
    # overwrite save_location with some other local space (not /mnt/users/ ...etc)
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_hierarchical_age_range/quantiles_pop_GEQ1/male/"
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_danvariant1/totalOnly/"
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_danVariant1/cenraceXhispanic/"
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_danVariant1/hhgq/"
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_danVariant1/detailed/"
    save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_danVariant1/ageBins4/"
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_manualTopDown/totalOnly/"
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_manualTopDown/cenraceXhispanic/"
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_manualTopDown/hhgq/"
    #save_location = "/mnt/users/lecle301/analysis/Aug29_DHCP_manualTopDown/detailed/"
    #save_location = "/mnt/users/lecle301/analysis/test/"
    # setup tools will return the spark session and save location path for this run
    spark, save_location = setuptools.setup(save_location=save_location)
    
    experiment_paths = [
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output/td001/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output/td01/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output/td025/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output/td05/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output/td1/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output/td2/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output/td4/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_rerun1/td8/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_rerun1/td16/"
        "s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/"
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP/td001/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP/td01/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP/td025/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td05/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td1/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td2/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td4/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td8/",
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_manualTopDown_output_DHCP_reRun1/td16/"
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output_danVariant1/"
        #"s3://uscb-decennial-ite-das/users/lecle301/Aug29_experiments_hierarchicalAgeRangeTopDown_branchFactor4_output/"
        #"s3://uscb-decennial-ite-das/users/lecle301/experiments/full_person/smallCellQuery/avgLE0.1_replication1/"
        #"s3://uscb-decennial-ite-das/users/lecle301/experiments/full_person/smallCellQuery/avgLE0.1/"
        #"s3://uscb-decennial-ite-das/users/lecle301/experiments/full_person/smallCellQuery/avgLE0.25/"
        #"s3://uscb-decennial-ite-das/users/lecle301/experiments/full_person/smallCellQuery/avgLE1/"
        #"s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td10_1/",
        # "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td1_1/",
        # "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td3_1/",
        # "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td025_1/",
        # "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td05_1/",
        # "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td001_1/",
        # "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td01_1/",
        # "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td2_1/"
    ]
    #schema_name = "PL94_P12"
    #schema_name = "Households2010"
    schema_name = "DHCP_HHGQ"
    strategy_name = "hierarchicalAgeRange_danVariant1"
    
    experiments = []
    runsList = []
    for path in experiment_paths:
        # only grabbing the first two runs for testing purposes
        runsList += treetools.getDASRuns(path)
    name = f"aug29DSEP_{strategy_name}_{schema_name}/"
    experiment = sdftools.Experiment(name, runsList, schema_name)
    experiments.append(experiment)

    """
    experiments = []
    for path in experiment_paths:
        # only grabbing the first two runs for testing purposes
        runs = treetools.getDASRuns(path)
        name = f"sexByAge_perGeolevelTVD/aug29DSEP_{strategy_name}_{schema_name}/PLB={runs[0].plb}/"
        experiment = sdftools.Experiment(name, runs, schema_name)
        experiments.append(experiment)
    """
   
    def getRangeQNames():
        names = []
        for rangeQLength in range(116):
            for start in range(rangeQLength):
                name = f"sex * rangeQueries({start}, {rangeQLength})"
                names.append(name)
        return names
 
    # These can each be a list of lists if desired
    geolevels = [C.STATE, C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK] # add tracts blockgroups etc
    #queries = ['total']
    #queries = ['cenrace * hispanic']
    #queries = ['hhgq']
    #queries = ['detailed']
    #queries = ['sex * age']
    queries = ['sex * agegroup4']
    #queries = ['sex * agegroup16']
    #queries = ['sex * agegroup64']
    #queries = getRangeQNames()
    groupby = [AC.RUN_ID, AC.PLB, AC.GEOLEVEL]#, AC.GEOCODE] # Retain these columns in final csv 
 
    # a metric builder object is needed for analysis, as experiments are built using it
    """
    mbCustom = sdftools.MetricBuilder(geolevels, queries)
    mbCustom.addCustom(
        desc = "L1 Error in Quantiles",
        metric_function = lambda sdf: L1_quantile_rdd(sdf, geolevels)
    )
    """
    mb = sdftools.MetricBuilder(geolevels, queries)
    mb.add(
        desc = "Per Geolevel 1-TVD",
        split_geolevels = False, # Only want one csv, not one per geolevel
        fill = None,    # Don't use (deeply inefficient) row-by-row filling in of sampling zeros
        metric_function = lambda sdf: (
            sdf.show()
            .geolevel_tvd("Geolevel TVD", groupby=groupby).show()
        )
    )
    """
    mb.add(
        desc = "Total L1 Error",
        split_geolevels = False, # Only want one csv, not one per geolevel
        fill = None,    # Don't use (deeply inefficient) row-by-row filling in of sampling zeros
        metric_function = lambda sdf: (
            sdf.show()
            .L1("L1").show()        # Compute L1 error for each range query
            .sum(groupby=groupby)   # Sum L1 error across range queries & geounits in geolevel
        )
    )
    """

    # Add metric builder to the experiments
    #for curMetric in [mbCustom]:
    for curMetric in [mb]:
        print(f"Loading MetricBuilder {curMetric} and computing its requested analyses...")
        for experiment in experiments:
            experiment = experiment.addMetricBuilder(curMetric)
        
            # Calculate and save results
            print(f"Analyzing experiment:\n{experiment}")
            experiment_save_location = f"{save_location}{experiment.name}{'/' if experiment.name[-1] != '/' else ''}"
            print(experiment_save_location)
            experiment = experiment.calculateMetrics(spark, save_results=True, save_location=experiment_save_location)
