# setup tests
# William Sexton

"""
   Run pytest inside programs dir.
"""

import sys
import os
import warnings

from os.path import dirname,abspath

DIR_DAS_DECENNIAL = dirname(dirname(dirname(abspath(__file__))))
DIR_FRAMEWORK = os.path.join(DIR_DAS_DECENNIAL, "das_framework")
DIR_CTOOLS = os.path.join(DIR_DAS_DECENNIAL, "das_framework/ctools")

for d in [DIR_FRAMEWORK, DIR_CTOOLS]:
    if d not in sys.path:
        sys.path.append(d)

warnings.filterwarnings("ignore", message="DeprecationWarning")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")





# from ctools import cspark # census spark tools
from configparser import ConfigParser
import programs.das_setup

def get_configs():
    configs = ConfigParser()
    configs.add_section("default")
    configs.set("default", "name", "DAS")
    configs.add_section("setup")
    configs.set("setup", "spark.name", "DAS")
    #configs.set("setup", "spark.master", "local[4]")
    configs.set("setup", "spark.loglevel", "ERROR")
    configs.add_section("budget")
    configs.set("budget", "queriesfile", "foo")
    configs.set("budget", "geolevel_budget_prop", "0.5,0.5")
    configs.add_section("schema")
    configs.set("schema", "schema", "PL94")
    configs.add_section("geodict")
    configs.set('geodict','geolevel_names', "Block,Block_Group,Tract,County")
    configs.set('geodict','geolevel_leng', "16,12,11,1")
    configs.add_section("writer")
    return configs

def test_setup(dd_das_stub):
    """
        Tests setup modules' __init__ method and setup_func
        __init__:
            check config and name are stored/accessible
        setup_func:
            check SparkSession is returned and configured as expected
    """
    # This only runs under spark
    # if not cspark.spark_running():
    #     return


    configs = get_configs()
    setup_obj = programs.das_setup.DASDecennialSetup(config=configs, name="setup", das=dd_das_stub)
    assert setup_obj.config == configs
    assert setup_obj.name == "setup"

    #setup_data = setup_obj.setup_func()
