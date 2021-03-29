from operator import add
import das_utils



# checking the nodes (need an older commit to run it since the nodes have changed since the experiments were conducted)
# use the following commit:
# git checkout 960ed599eb19d5a7e78aea43ce4f0c4856899a37
spark.sparkContext.addPyFile("/mnt/users/moran331/das_decennial_oldcommit.zip")

check_these = [
    "s3://uscb-decennial-ite-das/experiments/PL94_SF1_c1state/td10_1/",
    "s3://uscb-decennial-ite-das/experiments/PL94_SF1_c1state/td1_1/",
    "s3://uscb-decennial-ite-das/experiments/PL94_SF1_c1state/td3_1/",
    "s3://uscb-decennial-ite-das/experiments/PL94_SF1_c1state2/td025_1/",
    "s3://uscb-decennial-ite-das/experiments/PL94_SF1_c1state2/td05_1/",
    "s3://uscb-decennial-ite-das/experiments/PL94_SF1_c1state3/td001_1/",
    "s3://uscb-decennial-ite-das/experiments/PL94_SF1_c1state3/td01_1/",
    "s3://uscb-decennial-ite-das/experiments/PL94_SF1_c1state3/td2_1/"
]


va_results = {}                 

for exp in range(len(check_these)):
    experiment = check_these[exp]
    algset = experiment.split("/")[-2]
    if exp in [0,1,2,3,4]:
        raw18 = []
        syn18 = []
        for run in range(25):
            data = spark.sparkContext.pickleFile(f"{experiment}run_{run}/data/")
            raw18 += [data.map(lambda d: sum(d.raw.toDense().sum(axis=(0,1,3,4))[4:])).reduce(add)]
            syn18 += [data.map(lambda d: sum(d.syn.toDense().sum(axis=(0,1,3,4))[4:])).reduce(add)]
            va_results[algset] = { "raw18": raw18, "syn18": syn18 }
            print(f"{algset} | Run {run}")
    else:
        raw18 = []
        syn18 = []
        for run in range(25):
            data = spark.sparkContext.pickleFile(f"{experiment}run_{run}/data/")
            raw18 += [data.map(lambda d: sum(d['raw'].toDense().sum(axis=(0,1,3,4))[4:])).reduce(add)]
            syn18 += [data.map(lambda d: sum(d['syn'].toDense().sum(axis=(0,1,3,4))[4:])).reduce(add)]
            va_results[algset] = { "raw18": raw18, "syn18": syn18 }
            print(f"{algset} | Run {run}")

print(va_results)
das_utils.savePickleFile("/mnt/users/moran331/other/va_results_originalExperiments.p", va_results)


################################################################################################################
################################################################################################################

# checking the nodes converted to dicts
spark.sparkContext.addPyFile("/mnt/users/moran331/das_decennial.zip")

check_these_next = [
    "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td10_1/",
    "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td1_1/",
    "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state/td3_1/",
    "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td025_1/",
    "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state2/td05_1/",
    "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td001_1/",
    "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td01_1/",
    "s3://uscb-decennial-ite-das/experiments/convertedFromGeounitNodeToDict/PL94_SF1_c1state3/td2_1/"
]

va_results = {}

for exp in range(len(check_these_next)):
    experiment = check_these_next[exp]
    algset = experiment.split("/")[-2]
    raw18 = []
    syn18 = []
    for run in range(25):
        data = spark.sparkContext.pickleFile(f"{experiment}run_{run}/data/")
        raw18 += [data.map(lambda d: sum(d['raw'].toDense().sum(axis=(0,1,3,4))[4:])).reduce(add)]
        syn18 += [data.map(lambda d: sum(d['syn'].toDense().sum(axis=(0,1,3,4))[4:])).reduce(add)]
        va_results[algset] = { "raw18": raw18, "syn18": syn18 }
        print(f"{algset} | Run {run}")

print(va_results)
das_utils.savePickleFile("/mnt/users/moran331/other/va_results_node2dictExperiments.p", va_results)





import numpy
import pandas


keys = list(va_results.keys())

for key in keys:
    orig = va_results_orig[key]
    n2d = va_results[key]
    orig_raw = orig['raw18']
    n2d_raw = n2d['raw18']
    orig_syn = orig['syn18']
    n2d_syn = n2d['syn18']
    print(f"{key} | Raw matches?  {numpy.all(orig_raw == n2d_raw)}")
    print(f"{key} | Syn matches?  {numpy.all(orig_syn == n2d_syn)}")


