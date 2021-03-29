import os
import pytest
import tempfile
import shutil
import sys
import warnings
import json
from os.path import abspath,dirname

DAS_DECENNIAL_DIR = dirname(dirname(dirname(abspath(__file__))))
if DAS_DECENNIAL_DIR not in sys.path:
    sys.path.append(DAS_DECENNIAL_DIR)

from programs.dvs_register import *
import programs.python_dvs.dvs as dvs

LOGFILE = os.path.join( dirname(abspath(__file__)), "demo-log.log")

def test_extract_paths():
    tu = extract_paths( LOGFILE )
    print(json.dumps(tu,indent=4,default=str))
    print(tu[dvs.COMMIT_METHOD])
    assert isinstance(tu,dict)

    P1 = 's3://uscb-decennial-ite-das/title13_input_data/table8/ri44.txt'
    assert dvs.COMMIT_BEFORE in tu
    assert P1 in tu[dvs.COMMIT_BEFORE]

    P2 = 's3://uscb-decennial-ite-das/runs/test/heine008/topdown_RI/noisy_measurements/application_1608047018101_1395-BlockOptimized.pickle/'
    assert dvs.COMMIT_AFTER in tu
    assert P2 in tu[dvs.COMMIT_AFTER]

    P3 = 'das_decennial commit a68488b617e09c9e9e67000f958a83dc7f782d08\n'
    assert P3 in tu[dvs.COMMIT_METHOD]

def test_dvs_dc():
    dc = dvs.DVS()

def test_dvs_dc_create():
    dc = dvs.DVS()
    dvs_dc_populate( dc, LOGFILE, ephemeral=True)

def test_helpers():
    assert s3prefix_exists("s3://uscb-decennial-ite-das/title13_input_data/table1a_20190709/")
    assert s3path_exists("s3://uscb-decennial-ite-das/title13_input_data/table1a_20190709/wy56.txt")
    assert s3path_exists("s3://uscb-decennial-ite-das/production-runs/2020-dpst-mdf-rerun-2/20200717/2020-dpst-mdf-rerun-2/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-BlockNodeDicts/part-00000")
    assert not s3path_exists("s3://uscb-decennial-ite-das/title13_input_data/table1a_20190709")
    assert not s3path_exists("s3://uscb-decennial-ite-das/title13_input_data/table1a_20190709/.txt")
    assert (characterize_line("2020-04-06 12:46:31,994 s3cat.py:128 (verbprint) s3cat(s3://uscb-decennial-ite-das/production-runs/2020-dpst-mdf-rerun-2/20200717/2020-dpst-mdf-rerun-2/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-DHCP2020_MDF/part-00000-1e618826-76ff-4fb7-abf7-8fe682a5f276-c000, demand_success=True, suffix=.csv) DOWNLOAD")
            ==(dvs.COMMIT_AFTER,"s3://uscb-decennial-ite-das/production-runs/2020-dpst-mdf-rerun-2/20200717/2020-dpst-mdf-rerun-2/mdf/us/per/MDF10_PER_US.txt/MDF10_PER_US-DHCP2020_MDF/part-00000-1e618826-76ff-4fb7-abf7-8fe682a5f276-c000.csv"))
