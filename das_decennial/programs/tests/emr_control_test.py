#!/usr/bin/env python

import py.test
import sys
import os
import os.path
import warnings
import programs.emr_control as emr_control

def test_user_in_group():
    assert emr_control.user_in_group('yarn',       'hadoop') == True
    assert emr_control.user_in_group('mapred',     'hadoop') == True
    assert emr_control.user_in_group('hdfs',       'hadoop') == True
    assert emr_control.user_in_group('kms',        'hadoop') == True
    assert emr_control.user_in_group('yarn',       'dcdlsg_su') == True
    assert emr_control.user_in_group('nosuchuser', 'hadoop') == False
    assert emr_control.user_in_group('yarn',       'nosuchgroup') == False

if __name__=="__main__":
    test_user_in_group()
