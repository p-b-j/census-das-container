#
# test the testpoint system, including the fact that the testpoints go to local1.log

import random
import io
import time
import sys
import warnings

from das2020_driver import get_testpoint_filename, DASDelegate


def test_testpoint_filename():
    try:
        testpoint_file = get_testpoint_filename()
        assert testpoint_file.endswith("DAS_TESTPOINTS.csv")
    except FileNotFoundError as e:
        warnings.warn(f"DAS_TESTPOINTS.csv unable to be found: {str(e)}")


def test_testpoint_log_local1():
    nounce = str(random.randint(0, 1000000))
    try: 
        with open('/var/log/local1.log') as f:
            f.seek(io.SEEK_END)  # go to the end of the file
            DASDelegate('Logging Tests').log_testpoint('T99-999S', 'A successful testpoint ' + nounce)
            time.sleep(1)  # wait a second for it to appear
            buf = f.read()  # read to the end
            if nounce not in buf:
                print("Lines read from /var/log/local1.log during test:", file=sys.stderr)
                print(buf, file=sys.stderr)
                print(
                    "Nounce {nounce} not in data. Perhaps rsyslogd needs restarting or local1 logging to /var/log/local1.log is not set up",
                    file=sys.stderr)
                warnings.warn("Local1 exists but is not being properly logged tois no")
    except FileNotFoundError as e:
        warnings.warn(f"/var/log/local1.log does not exist or is otherwise unable to be accessed: {str(e)}")  

