# This script file implements Matt Spence's metrics, including MAE, MAPE, MALPE, CoV, RMS, for Executive Priority Tabulations #1, US+PR Run
# AnalyzeQuery function has been edited to include these metrics
 # Uses dict


######################################################
# To Run this script:
#
# cd into das_decennial/analysis/
# analysis=[path to analysis script] bash run_analysis.sh
#
# More info on analysis can be found here:
# https://github.ti.census.gov/CB-DAS/das_decennial/blob/master/analysis/readme.md
######################################################

import analysis.tools.sdftools as sdftools
import analysis.tools.datatools as datatools
import analysis.tools.setuptools as setuptools
import analysis.constants as AC
from pyspark.sql import functions as sf
from pyspark.sql import Row
import math as mathy

import constants as C
from constants import CC

import das_utils as du
import programs.datadict as dd
from programs.schema.schemas.schemamaker import SchemaMaker

import numpy as np
import matplotlib
print(f"matplotlib has methods: {dir(matplotlib)}")
print(f"matplotlib version: {matplotlib.__version__}")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas

import os, math
from collections import defaultdict

"""
Example target location:

abdat-ITE-MASTER:hadoop@ip-10-252-44-211$ aws s3 ls s3://uscb-decennial-ite-das/users/heiss002/cnstatDdpSchema_SinglePassRegular_va_cnstatDpqueries_cnstatGeolevels_version2/data-run | grep .*BlockNodeDicts.*\/
                           PRE data-run1.0-epsilon4.0-BlockNodeDicts/
                           PRE data-run10.0-epsilon4.0-BlockNodeDicts/
"""

tabledict_EPT_no1 = {
#        "Table 1a"           :   (["total"], "A", '0', '0', '0'),
#        "Table 1b"           :   (["total"], "B", '0', '0', '1'),
#        "Table 2a"           :   ["total"], "A", '0', '0', '0'),
#        "Table 2b"           :   (["total"], "B", '0', '0', '1')
#         "Table 3"               :   (["total"], "A", '0', '0', '0')
#         "Table 10"               :   (["hispanic"],"C", '0', '0', '0'),
#         "Table 11"                : (["hispanic"], "B", '0', '0','2'),
#         "Table 12"              : (["hispanic"], "B", '0', '0','2'),
#          "Table 13"              :(["hispanic"], "A", '0', '0', '0'),
#           "Table 14a"            :(["hispanic * whiteAlone"],"C", '0', '0', '0'),
#           "Table 14b"            :(["hispanic * blackAlone"],"C", '0', '0', '0')
#            "Table 14c"            :(["hispanic * aianAlone"],"C", '0', '0', '0')
#             "Table 14d"            :(["hispanic * asianAlone"],"C", '0', '0', '0')
#            "Table 14e"            :(["hispanic * nhopiAlone"],"C", '0', '0', '0')
#             "Table 14f"            :(["hispanic * sorAlone"],"C", '0', '0', '0')
#             "Table 14g"            :(["hispanic * tomr"],"C", '0', '0', '0')
#              "Table 15a"            :(["hispanic * whiteAlone"], "B", '0', '0','2'),
 #             "Table 15b"            :(["hispanic * blackAlone"], "B", '0', '0','2')
  #            "Table 15c"            :(["hispanic * aianAlone"], "B", '0', '0','2')
#              "Table 15d"            :(["hispanic * asianAlone"], "B", '0', '0','2')
#              "Table 15e"            :(["hispanic * nhopiAlone"], "B", '0', '0','2')
#              "Table 15f"            :(["hispanic * sorAlone"], "B", '0', '0','2')
#              "Table 15g"            :(["hispanic * tomr"], "B", '0', '0','2')
#              "Table 16a"            :(["hispanic * whiteAlone"], "B", '0', '0','2')
#              "Table 16b"            :(["hispanic * blackAlone"], "B", '0', '0','2')
#              "Table 16c"            :(["hispanic * aianAlone"], "B", '0', '0','2')
#              "Table 16d"            :(["hispanic * asianAlone"], "B", '0', '0','2')
#              "Table 16e"            :(["hispanic * nhopiAlone"], "B", '0', '0','2')
#              "Table 16f"            :(["hispanic * sorAlone"], "B", '0', '0','2')
#              "Table 16g"            :(["hispanic * tomr"], "B", '0', '0','2')
#               "Table 17a"            :(["hispanic * whiteAlone"], "A", '0', '0', '0')
#               "Table 17b"            :(["hispanic * blackAlone"],"A", '0', '0', '0')
#               "Table 17c"            :(["hispanic * aianAlone"],"A", '0', '0', '0')
#               "Table 17d"            :(["hispanic * asianAlone"],"A", '0', '0', '0')
#               "Table 17e"            :(["hispanic * nhopiAlone"],"A", '0', '0', '0')
#               "Table 17f"            :(["hispanic * sorAlone"],"A", '0', '0', '0')
#               "Table 17g"            :(["hispanic * tomr"],"A", '0', '0', '0')
 #               "Table 18a"            :(["hispanic * whitecombo"],"C", '0', '0', '0')
 #               "Table 18b"            :(["hispanic * blackcombo"],"C", '0', '0', '0')
 #               "Table 18c"            :(["hispanic * aiancombo"],"C", '0', '0', '0')
 #               "Table 18d"            :(["hispanic * asiancombo"],"C", '0', '0', '0')
 #               "Table 18e"            :(["hispanic * nhopicombo"],"C", '0', '0', '0')
 #               "Table 18f"            :(["hispanic * sorcombo"],"C", '0', '0', '0')
#                 "Table 19a"            :(["hispanic * whitecombo"], "B", '0', '0','2')
#                 "Table 19b"            :(["hispanic * blackcombo"], "B", '0', '0','2')
#                 "Table 19c"            :(["hispanic * aiancombo"], "B", '0', '0','2')
#                 "Table 19d"            :(["hispanic * asiancombo"], "B", '0', '0','2')
#                 "Table 19e"            :(["hispanic * nhopicombo"], "B", '0', '0','2')
#                 "Table 19f"            :(["hispanic * sorcombo"], "B", '0', '0','2')
#                 "Table 20a"            :(["hispanic * whitecombo"], "B", '0', '0','2')
#                 "Table 20b"            :(["hispanic * blackcombo"], "B", '0', '0','2')
#                 "Table 20c"            :(["hispanic * aiancombo"], "B", '0', '0','2')
#                 "Table 20d"            :(["hispanic * asiancombo"], "B", '0', '0','2')
#                 "Table 20e"            :(["hispanic * nhopicombo"], "B", '0', '0','2')
#                 "Table 20f"            :(["hispanic * sorcombo"], "B", '0', '0','2')
#                  "Table 21a"            :(["hispanic * whitecombo"], "A", '0', '0', '0')
#                  "Table 21b"            :(["hispanic * blackcombo"],"A", '0', '0', '0')
#                  "Table 21c"            :(["hispanic * aiancombo"],"A", '0', '0', '0')
#                  "Table 21d"            :(["hispanic * asiancombo"],"A", '0', '0', '0')
#                  "Table 21e"            :(["hispanic * nhopicombo"],"A", '0', '0', '0')
#                  "Table 21f"            :(["hispanic * sorcombo"],"A", '0', '0', '0')
#                  "Table 22a"            :(["onerace"],"C", '0', '0', '0')
#                  "Table 22b"            :(["tworaces"], "C", '0', '0', '0')
#                  "Table 22c"            :(["threeraces"],"C", '0', '0', '0')
#                   "Table 22d"            :(["fourraces"],"C", '0', '0', '0')
#                   "Table 22e"            :(["fiveraces"],"C", '0', '0', '0')
#                   "Table 22f"            :(["sixraces"],"C", '0', '0', '0')
#                    "Table 23a"            :(["onerace"],"B", '0', '0','2')
#                    "Table 23b"            :(["tworaces"],"B", '0', '0','2')
#                    "Table 23c"            :(["threeraces"],"B", '0', '0','2')
#                    "Table 23d"            :(["fourraces"],"B", '0', '0','2')
#                    "Table 23e"            :(["fiveraces"],"B", '0', '0','2')
#                    "Table 23f"            :(["sixraces"]"B", '0', '0','2')
#                     "Table 24a"            :(["onerace"],"B", '0', '0','2')
#                     "Table 24b"            :(["tworaces"],"B", '0', '0','2')
#                     "Table 24c"            :(["threeraces"],"B", '0', '0','2')
#                     "Table 24d"            :(["fourraces"],"B", '0', '0','2')
#                     "Table 24e"            :(["fiveraces"],"B", '0', '0','2')
#                     "Table 24f"            :(["sixraces"],"B", '0', '0','2')
#                      "Table 25a"            :(["onerace"],"A", '0', '0', '0')
#                      "Table 25b"            :(["tworaces"],"A", '0', '0', '0')
#                      "Table 25c"            :(["threeraces"],"A", '0', '0', '0')
#                      "Table 25d"            :(["fourraces"],"A", '0', '0', '0')
#                      "Table 25e"            :(["fiveraces"],"A", '0', '0', '0')
#                      "Table 25f"            :(["sixraces"],"A", '0', '0', '0')

#                       "Table 26a"            :(["hispanic*whiteAlone*age18plus"],"A", '0', '0', '0')
#                       "Table 26b"            :(["hispanic*blackAlone*age18plus"],"A", '0', '0', '0')
#                      "Table 26c"            :(["hispanic*aianAlone*age18plus"],"A", '0', '0', '0')
#                       "Table 26d"            :(["hispanic*asianAlone*age18plus"],"A", '0', '0', '0')
#                       "Table 26e"            :(["hispanic*nhopiAlone*age18plus"],"A", '0', '0', '0')
#                          "Table 26f"            :(["hispanic*sorAlone*age18plus"],"A", '0', '0', '0')
#                          "Table 26g"            :(["hispanic*tomr*age18plus"],"A", '0', '0', '0')
#                       "Table 27a"            :(["hispanic*whiteAlone*age18plus"],"A", '0', '0', '0')
#                       "Table 27b"            :(["hispanic*blackAlone*age18plus"],"A", '0', '0', '0')
#                       "Table 27c"            :(["hispanic*aianAlone*age18plus"],"A", '0', '0', '0')
#                       "Table 27d"            :(["hispanic*asianAlone*age18plus"],"A", '0', '0', '0')
#                       "Table 27e"            :(["hispanic*nhopiAlone*age18plus"],"A", '0', '0', '0')
#                       "Table 27f"            :(["hispanic*sorAlone*age18plus"],"A", '0', '0', '0')
#                        "Table 27g"            :(["hispanic*tomr*age18plus"],"A", '0', '0', '0')

#                         "Table 28a"            :(["hispanic*whitecombo*age18plus"],"A", '0', '0', '0')
#                         "Table 28b"            :(["hispanic*blackcombo*age18plus"],"A", '0', '0', '0')
#                         "Table 28c"            :(["hispanic*aiancombo*age18plus"],"A", '0', '0', '0')
#                         "Table 28d"            :(["hispanic*asiancombo*age18plus"], "A", '0', '0', '0')
#                         "Table 28e"            :(["hispanic*nhopicombo*age18plus"],"A", '0', '0', '0')
#                         "Table 28f"            :(["hispanic*sorcombo*age18plus"],"A", '0', '0', '0')
#                         "Table 29a"            :(["hispanic*whitecombo*age18plus"],"A", '0', '0', '0')
#                         "Table 29b"            :(["hispanic*blackcombo*age18plus"],"A", '0', '0', '0')
#                         "Table 29c"            :(["hispanic*aiancombo*age18plus"],"A", '0', '0', '0')
#                         "Table 29d"            :(["hispanic*asiancombo*age18plus"],"A", '0', '0', '0')
#                         "Table 29e"            :(["hispanic*nhopicombo*age18plus"],"A", '0', '0', '0')
#                         "Table 29f"            :(["hispanic*sorcombo*age18plus"],"A", '0', '0', '0')


                       "Table 30a"            :(["hispanic*onerace*age18plus"], "A", '0', '0', '0'),
#                       "Table 30b"            :(["hispanic*tworaces*age18plus"],"A", '0', '0', '0')
#                       "Table 30c"            :(["hispanic*threeraces*age18plus"],"A", '0', '0', '0')
#                       "Table 30d"            :(["hispanic*fourraces*age18plus"],"A", '0', '0', '0')
#                      "Table 30e"            :(["hispanic*fiveraces*age18plus"],"A", '0', '0', '0')
#                       "Table 30f"            :(["hispanic*sixraces*age18plus"],"A", '0', '0', '0')
#                       "Table 31a"            :(["hispanic*onerace*age18plus"],"A", '0', '0', '0')
#                       "Table 31b"            :(["hispanic*tworaces*age18plus"],"A", '0', '0', '0')
#                       "Table 31c"            :(["hispanic*threeraces*age18plus"],"A", '0', '0', '0')
#                       "Table 31d"            :(["hispanic*fourraces*age18plus"],"A", '0', '0', '0')
#                       "Table 31e"            :(["hispanic*fiveraces*age18plus"],"A", '0', '0', '0')
#                       "Table 31f"            :(["hispanic*sixraces*age18plus"],"A", '0', '0', '0')
#                        "Table 32a"            :(["agecat43"], "D", '1', '0', '0')
                        "Table 32b"            :(["sex*agecat43"],"E", '1', '1', '0'),
                         "Table 33a"            :(["agecat43"], "D", '1', '0', '0')
#                         "Table 33b"            :(["sex*agecat43"],"E", '1', '1', '0')
#                          "Table 34a"            :(["5yeargroups"],"D", '2','0','0')
#                          "Table 35a"            :(["5yeargroups"], "D", '2','0','0')

#                           "Table 34b"            :(["sex*5yeargroups"], "E", '2','1','0')
#                           "Table 35b"            :(["sex*5yeargroups"], "E", '2','1','0')


}
tabledict_EPT_no2 = {
#        "EPT2_P1"           :   ["numraces","cenrace"],
 #       "EPT2_P2"           :   ["hispanic","hispanic * numraces","hispanic * cenrace"],
  #      "EPT2_P3"           :   ["votingage","votingage * numraces","votingage * cenrace"],
   #     "EPT2_P4"           :   ["votingage * hispanic","votingage * hispanic * numraces","votingage * hispanic * cenrace"],
    #    "EPT2_P5"           :   ["instlevels","gqlevels"],
}
tabledict_EPT_no3 = {
    #    "EPT3_ROW2_TOMR"    :   ["tomr * hispanic * sex * agecat100plus"],
     #   "EPT3_ROW2_6RACES"  :   ["allraces * hispanic * sex * agecat100plus"],
      #  "EPT3_ROW8_TOMR"    :   ["tomr * hispanic * sex * agecat85plus"],
   #     "EPT3_ROW8_6RACES"  :   ["allraces * hispanic * sex * agecat85plus"],
    #    "EPT3_ROW12_TOMR"   :   ["tomr * sex * agecat85plus"],
     #   "EPT3_ROW12_6RACES" :   ["allraces * sex * agecat85plus"],
     #   "EPT3_ROW14_TOMR"   :   ["tomr * sex * hispanic * agePopEst18groups"],
    #    "EPT3_ROW14_6RACES" :   ["allraces * sex * hispanic * agePopEst18groups"],
      #  "EPT3_ROW15"        :   ["sex * agePopEst18groups"],
}
tabledict_H1 = {"H1":["h1"],}

#all_geolevels = [C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD, C.STATE, C.PLACE] # For 1-state runs
#all_geolevels = [C.COUNTY, C.TRACT, C.BLOCK_GROUP, C.BLOCK, C.SLDL, C.SLDU, C.CD, C.STATE, C.US, C.PLACE] # For US runs
# For patching 'missing' geolevels in already saved analyses:
all_geolevels = [C.COUNTY]
#all_geolevels = [C.PLACE]
#all_geolevels = [C.STATE]   # Just for quick tests
def listDefault():
    return all_geolevels
geolevels_dict = defaultdict(listDefault)

geolevels_dict["Table 1a"]        = [C.COUNTY]
geolevels_dict["Table 1b"]        = [C.COUNTY]
geolevels_dict["Table 2a"]         = [C.PLACE]
geolevels_dict["Table 2b"]         = [C.PLACE]


geolevels_dict["Table 3"]             = [C.TRACT]
geolevels_dict["Table 10"]             = [C.STATE, C.COUNTY, C.PLACE]
geolevels_dict["Table 11"]             = [C.COUNTY]
geolevels_dict["Table 12"]            = [C.PLACE]
geolevels_dict["Table 13"]            = [C.TRACT]
geolevels_dict["Table 13"]            = [C.TRACT]
geolevels_dict["Table 14a"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14b"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14c"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14d"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14e"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14f"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14g"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 14a"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 15a"]          = [C.COUNTY]
geolevels_dict["Table 15b"]          = [C.COUNTY]
geolevels_dict["Table 15c"]          = [C.COUNTY]
geolevels_dict["Table 15d"]          = [C.COUNTY]
geolevels_dict["Table 15e"]          = [C.COUNTY]
geolevels_dict["Table 15f"]          = [C.COUNTY]
geolevels_dict["Table 15g"]          = [C.COUNTY]
geolevels_dict["Table 16a"]          = [C.PLACE]
geolevels_dict["Table 16b"]          = [C.PLACE]
geolevels_dict["Table 16c"]          = [C.PLACE]
geolevels_dict["Table 16d"]          = [C.PLACE]
geolevels_dict["Table 16e"]          = [C.PLACE]
geolevels_dict["Table 16f"]          = [C.PLACE]
geolevels_dict["Table 16g"]          = [C.PLACE]
geolevels_dict["Table 17a"]          = [C.TRACT]
geolevels_dict["Table 17b"]          = [C.TRACT]
geolevels_dict["Table 17c"]          = [C.TRACT]
geolevels_dict["Table 17d"]          = [C.TRACT]
geolevels_dict["Table 17e"]          = [C.TRACT]
geolevels_dict["Table 17f"]          = [C.TRACT]
geolevels_dict["Table 17g"]          = [C.TRACT]
geolevels_dict["Table 18a"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 18b"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 18c"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 18d"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 18e"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 18f"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 19a"]          = [C.COUNTY]
geolevels_dict["Table 19b"]          = [C.COUNTY]
geolevels_dict["Table 19c"]          = [C.COUNTY]
geolevels_dict["Table 19d"]          = [C.COUNTY]
geolevels_dict["Table 19e"]          = [C.COUNTY]
geolevels_dict["Table 19f"]          = [C.COUNTY]
geolevels_dict["Table 20a"]          = [C.PLACE]
geolevels_dict["Table 20b"]          = [C.PLACE]
geolevels_dict["Table 20c"]          = [C.PLACE]
geolevels_dict["Table 20d"]          = [C.PLACE]
geolevels_dict["Table 20e"]          = [C.PLACE]
geolevels_dict["Table 20f"]          = [C.PLACE]
geolevels_dict["Table 21a"]          = [C.TRACT]
geolevels_dict["Table 21b"]          = [C.TRACT]
geolevels_dict["Table 21c"]          = [C.TRACT]
geolevels_dict["Table 21d"]          = [C.TRACT]
geolevels_dict["Table 21e"]          = [C.TRACT]
geolevels_dict["Table 21f"]          = [C.TRACT]
geolevels_dict["Table 22a"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 22b"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 22c"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 22d"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 22e"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 22f"]          = [C.STATE,C.COUNTY, C.PLACE]
geolevels_dict["Table 23a"]          = [C.COUNTY]
geolevels_dict["Table 23b"]          = [C.COUNTY]
geolevels_dict["Table 23c"]          = [C.COUNTY]
geolevels_dict["Table 23d"]          = [C.COUNTY]
geolevels_dict["Table 23e"]          = [C.COUNTY]
geolevels_dict["Table 23f"]          = [C.COUNTY]

geolevels_dict["Table 24a"]          = [C.PLACE]
geolevels_dict["Table 24b"]          = [C.PLACE]
geolevels_dict["Table 24c"]          = [C.PLACE]
geolevels_dict["Table 24d"]          = [C.PLACE]
geolevels_dict["Table 24e"]          = [C.PLACE]
geolevels_dict["Table 24f"]          = [C.PLACE]


geolevels_dict["Table 25a"]          = [C.TRACT]
geolevels_dict["Table 25b"]          = [C.TRACT]
geolevels_dict["Table 25c"]          = [C.TRACT]
geolevels_dict["Table 25d"]          = [C.TRACT]
geolevels_dict["Table 25e"]          = [C.TRACT]
geolevels_dict["Table 25f"]          = [C.TRACT]

geolevels_dict["Table 26a"]          = [C.TRACT]
geolevels_dict["Table 26b"]          = [C.TRACT]
geolevels_dict["Table 26c"]          = [C.TRACT]
geolevels_dict["Table 26d"]          = [C.TRACT]
geolevels_dict["Table 26e"]          = [C.TRACT]
geolevels_dict["Table 26f"]          = [C.TRACT]
geolevels_dict["Table 26g"]          = [C.TRACT]

geolevels_dict["Table 27a"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 27b"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 27c"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 27d"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 27e"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 27f"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 27g"]          = [C.BLOCK_GROUP]

geolevels_dict["Table 28a"]          = [C.TRACT]
geolevels_dict["Table 28b"]          = [C.TRACT]
geolevels_dict["Table 28c"]          = [C.TRACT]
geolevels_dict["Table 28d"]          = [C.TRACT]
geolevels_dict["Table 28e"]          = [C.TRACT]
geolevels_dict["Table 28f"]          = [C.TRACT]

geolevels_dict["Table 29a"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 29b"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 29c"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 29d"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 29e"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 29f"]          = [C.BLOCK_GROUP]



geolevels_dict["Table 30a"]          = [C.TRACT]
geolevels_dict["Table 30b"]          = [C.TRACT]
geolevels_dict["Table 30c"]          = [C.TRACT]
geolevels_dict["Table 30d"]          = [C.TRACT]
geolevels_dict["Table 30e"]          = [C.TRACT]
geolevels_dict["Table 30f"]          = [C.TRACT]

geolevels_dict["Table 31a"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 31b"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 31c"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 31d"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 31e"]          = [C.BLOCK_GROUP]
geolevels_dict["Table 31f"]          = [C.BLOCK_GROUP]

geolevels_dict["Table 32a"]          = [C.COUNTY]

geolevels_dict["Table 32b"]          = [C.COUNTY]

geolevels_dict["Table 33a"]          = [C.PLACE]

geolevels_dict["Table 33b"]          = [C.PLACE]

geolevels_dict["Table 34a"]          = [C.COUNTY]
geolevels_dict["Table 34b"]          = [C.COUNTY]
geolevels_dict["Table 35a"]          = [C.PLACE]
geolevels_dict["Table 35b"]          = [C.PLACE]
# Only needed for US (but most current runs State-only)
#geolevels_dict["EPT3_ROW2_6RACES"]      = [C.STATE]
#geolevels_dict["EPT3_ROW8_TOMR"]        = [C.STATE]
#geolevels_dict["EPT3_ROW8_6RACES"]      = [C.STATE]

geolevels_dict["EPT3_ROW2_TOMR"]        = [C.STATE, C.US] # For US runs
geolevels_dict["EPT3_ROW2_6RACES"]      = [C.STATE, C.US]
geolevels_dict["EPT3_ROW8_TOMR"]        = [C.STATE, C.US]
geolevels_dict["EPT3_ROW8_6RACES"]      = [C.STATE, C.US]

geolevels_dict["EPT3_ROW12_TOMR"]       = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW12_6RACES"]     = [C.STATE]     # Only for PR, but PR not in current runs
geolevels_dict["EPT3_ROW14_TOMR"]       = [C.COUNTY]
geolevels_dict["EPT3_ROW14_6RACES"]     = [C.COUNTY]
geolevels_dict["EPT3_ROW15"]            = [C.COUNTY]    # Also for PR Municipios
geolevels_dict["H1"]                    = all_geolevels + [C.US]
#geolevels_dict["H1"]                    = [C.STATE, C.US]  # Only for quick tests
#geolevels_dict["H1"]                    = [C.US]           # Only for very quick tests


table_bucket_list1 = ['Table 1b', 'Table 2b']

table_bucket_list2 = ['Table 11', 'Table 12', 'Table 15a', 'Table 15b', 'Table 15c', 'Table 15d', 'Table 15e', 'Table 15f', 'Table 15g','Table 16a', 'Table 16b', 'Table 16c', 'Table 16d', 'Table 16e', 'Table 16f', 'Table 16g','Table 19a','Table 19b','Table 19c','Table 19d','Table 19e','Table 19f','Table 20a','Table 20b','Table 20c','Table 20d','Table 20e','Table 20f','Table 23a','Table 23b','Table 23c','Table 23d','Table 23e','Table 23f','Table 24a','Table 24b','Table 24c','Table 24d','Table 24e','Table 24f']

def schemaDefault():
    return "DHCP_HHGQ"
schema_dict = defaultdict(schemaDefault)
schema_dict["H1"] = "H1_SCHEMA"         # For H1-only internal runs as of 4/2/2020
#schema_dict["H1"] = "Household2010"    # For CNSTAT DDP Run

def getSparkDFWithAbsDiff(spark, df, geolevels, queries, schema):
    sparkDFWithAnswers = sdftools.getAnswers(spark, df, geolevels, schema, queries)
    # 'priv' means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
    sparkDFWithDiff = sparkDFWithAnswers.withColumn('diff',sf.col('priv')-sf.col('orig'))
    sparkDFWithAbsDiff = sparkDFWithDiff.withColumn('abs diff', sf.abs(sf.col('diff')))
    return sparkDFWithAbsDiff


def largestIntInStr(bucket_name):
    if '[' in bucket_name:
        integerStr = bucket_name[1:-1].split('-')[1]
    else:
        integerStr = bucket_name[:-1].strip()
    return int(integerStr)

def setup():
    jbid = os.environ.get('JBID', 'temp_jbid')
    analysis_results_save_location = f"{jbid}/analysis_reports/"
    spark_loglevel = "ERROR"
    analysis = setuptools.setup(save_location=analysis_results_save_location, spark_loglevel=spark_loglevel)
    analysis.save_log(to_linux=False, to_s3=True)
    spark = analysis.spark
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
    return analysis, spark

def getPathsAndName(schema_name):
    """
        Copy and re-name to switch input locations.
    """
    print(f"Get paths received schema {schema_name}")

    S3_BASE="s3://uscb-decennial-ite-das/users"
    eps = 4.0
    num_trials = 1
    JBID = "lecle301"   # JBID used in s3 paths for saved runs (not necessarily your JBID)
    if schema_name == "DHCP_HHGQ":
        # Example:
        # s3://uscb-decennial-ite-das/users/lecle301/cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries4_version7/
        # cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_National_dpQueries1_officialCNSTATrun
        experiment_name = "cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_National_dpQueries1_officialCNSTATrun"
        #experiment_name = "cnstatDdpSchema_SinglePassRegular_va_dpQueries1_version2"
        #experiment_name = "cnstatDdpSchema_TwoPassBigSmall_va_dpQueries2_AllChildFilter"
        #experiment_name = "cnstatDdpSchema_InfinityNorm_va_dpQueries2_AllChildFilter"
        #experiment_name = "cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries13_version7"
        #experiment_name = "cnstatDdpSchema_DataIndUserSpecifiedQueriesNPass_va_dpQueries1_version2"
        partial_paths = [f"data-run{RUN}.0-epsilon{eps:.1f}-BlockNodeDicts/" for RUN in range(1,num_trials+1)]
        path_prefix = f"{S3_BASE}/{JBID}/{experiment_name}/"
        paths = [path_prefix + partial_path for partial_path in partial_paths]
        remainder_paths = []
    elif schema_name == "Household2010":
        raise NotImplementedError(f"Schema {schema_name} input locations not yet implemented.")
    elif schema_name == "H1_SCHEMA":
        # Example:
        # s3://uscb-decennial-ite-das/users/lecle301/cnstatDdpSchema_SinglePassRegular_natH1_Only_withMeasurements_v8/
        experiment_name = "cnstatDdpSchema_SinglePassRegular_nat_H1_Only_withMeasurements_v8"
        partial_paths = [f"MDF_UNIT-run{RUN}.0-epsilon{eps:.1f}-BlockNodeDicts/" for RUN in range(1,num_trials+1)]
        path_prefix = f"{S3_BASE}/{JBID}/{experiment_name}/"
        paths = [path_prefix + partial_path for partial_path in partial_paths]
        remainder_paths = []
    else:
        raise ValueError(f"Schema {schema_name} not recognized when getting s3 ingest paths.")
    paths = paths + remainder_paths
    return paths, experiment_name, f"{eps:.1f}" # Change this for eps<0.1

def MattsMetrics(query, table_name, analysis, spark, geolevels, key, agekey, sexkey, bucketkey, schema="DHCP_HHGQ"):
    """
    This function computes metrics for MAE, MALPE, CoV, RMS, MAPE, and percent thresholds"

    """
    print(f"For table {table_name}, analyzing query {query} at geolevels {geolevels} with schema {schema}")
    schema_name = schema
    paths, experiment_name, eps_str = getPathsAndName(schema_name)
    experiment = analysis.make_experiment(experiment_name, paths, schema_name=schema_name, dasruntype=AC.EXPERIMENT_FRAMEWORK_FLAT)
    sdftools.print_item(experiment.__dict__, "Experiment Attributes")

    spark_df = experiment.getDF()
    print("df looks like:")
    spark_df.show()
    schema = experiment.schema
    sdftools.print_item(spark_df, "Flat Experiment DF")

    queries = [query]
    spark_df = sdftools.aggregateGeolevels(spark, spark_df, geolevels)
    spark_df = sdftools.answerQueries(spark_df, schema, queries)
    spark_df = sdftools.getFullWorkloadDF(spark_df, schema, queries,groupby=[AC.GEOCODE, AC.GEOLEVEL, AC.RUN_ID, AC.PLB, AC.BUDGET_GROUP])

    #spark_df.show(spark_df.count(), False)
    # AC.PRIV means "protected via the differential privacy routines in this code base" variable to be renamed after P.L.94-171 production
    spark_df = sdftools.getL1(spark_df, colname = "L1", col1=AC.PRIV, col2=AC.ORIG)
    spark_df = sdftools.getL2(spark_df, colname = "L2", col1=AC.PRIV, col2=AC.ORIG)
    # apply bin functions for particular tables
    if (table_name in table_bucket_list1):
        spark_df = sdftools.getCountBins(spark_df, column=AC.ORIG, bins=[0,1000,5000,10000,50000,100000]).persist()
    if (table_name in table_bucket_list2):
        spark_df = sdftools.getCountBins(spark_df, column=AC.ORIG, bins=[0,10,100]).persist()
    # This finds overall metrics
    spark_df.show(100, False)

    metrics_result = sdftools.combined_metrics(spark_df, spark, geolevels, agekey, sexkey, bucketkey, key)
    file_name = f"{table_name}.csv"
    pandas_df =metrics_result.toPandas()
    csv_savepath = experiment.save_location_linux + file_name
    du.makePath(du.getdir(csv_savepath))
    pandas_df.to_csv(csv_savepath, index=False)


def main():
    analysis, spark = setup()
    #table_dicts = [tabledict_EPT_no3]
    #table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2]
    table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2, tabledict_EPT_no3]
    #table_dicts = [tabledict_H1]
    #table_dicts = [tabledict_EPT_no1, tabledict_EPT_no2]
    for table_dict in table_dicts:
        for table_name, (queries, key, agekey, sexkey, bucketkey) in table_dict.items():
            geolevels = geolevels_dict[table_name]
            schema = schema_dict[table_name]
            print(f"For table {table_name}, using schema {schema}")
            print("queries are:", queries)
            print("key is:", key)
            print("agekey is:", agekey)
            print("sexkey is:", sexkey)
            print("bucketkey is:", bucketkey)
            for query in queries:
                MattsMetrics(query, table_name, analysis, spark, geolevels, key, agekey, sexkey, bucketkey, schema=schema)

if __name__ == "__main__":
    main()
