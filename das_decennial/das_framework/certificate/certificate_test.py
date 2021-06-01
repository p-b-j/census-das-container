#!/usr/bin/env python3
#

import datetime
import sys
import os
import warnings
from os.path import dirname,abspath

sys.path.append( dirname(dirname( abspath( __file__ ))))
import certificate

def test_make_certificate():
    """Generate a certificate"""
    warnings.filterwarnings("ignore")
    c = certificate.CertificatePrinter(title="Test Certificate")
    c.add_params({"NAME"   : "A very precise data set",
                  "DATE"   : datetime.datetime.now().isoformat()[0:19],
                  "PERSON1": "Ben Bitdiddle",
                  "TITLE1" : "Novice Programmer",
                  "PERSON2": "Alyssa P. Hacker",
                  "TITLE2" : "Supervisor"})
    c.typeset("certificate_demo.pdf")


def test_get_bom():
    """test get_bom function"""
    for (name, path, ver, bytecount) in certificate.get_bom(content=False):
        assert isinstance(name, str), "Invalid name " + str(name)
        assert isinstance(path, str), "Invalid path " + str(path)
        assert isinstance(ver, str) or ver is None or isinstance(ver, bytes), "Invalid ver " + str(ver)
        assert isinstance(bytecount, int) or bytecount is None, "Invalid bytecount " + str(bytecount)
    for (name, path, ver, stat1, stat2, stat3) in certificate.get_bom(content=True):
        assert isinstance(name, str), "Invalid name " + str(name)
        assert isinstance(path, str), "Invalid path " + str(path)
        assert isinstance(stat1, int) or stat1 is None, "Invalid name len " + str(stat1)
        assert isinstance(stat2, int) or stat2 is None, "Invalid count " + str(stat2)
        assert isinstance(stat3, str) or stat3 is None, "Invalid hex " + str(stat3)


if __name__=="__main__":
    test_make_certificate()
    test_get_bom()
