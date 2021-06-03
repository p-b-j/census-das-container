#
# fake DAS class for testing
#

import sys
import os
from os.path import basename,abspath,dirname
import logging
import time

from dfxml_writer import DFXMLWriter

class StubDelegate:
    def log_testpoint(self, testpoint=None):
        pass

class DASStub:
    def __init__(self):
        if 'MISSION_NAME' in os.environ:
            raise RuntimeError("DASStub() should not be called within Missions.")
        self.dfxml_writer = DFXMLWriter()
        self.t0 = time.time()
        self.output_paths = []
        self.delegate     = StubDelegate()

    def log_warning_and_print(self, message, cui=False):
        pass

    def make_bom_only(self, *args, **kwargs):
        pass

    def log_and_print(self, message, cui=False):
        print(f"ANNOTATE: {message}")
        #logging.info("ANNOTATE: " + message)

    def make_bom_only(self, *args, **kwargs):
        pass

    def annotate(self, message, verbose=True):
        #if verbose:
        print(f"ANNOTATE: {message}")
        #logging.info("ANNOTATE: " + message)
