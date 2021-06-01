#!/usr/bin/env python3

""""
Test the s3cat program.
"""


import os
import time
import sys
import pytest
import boto3
import io
import logging

HOME_DIR=os.path.dirname(os.path.dirname( os.path.dirname( os.path.abspath(__file__))))
if HOME_DIR not in sys.path:
    sys.path.append( HOME_DIR)

import das_framework.ctools.s3 as ctools_s3
import programs.s3cat as s3cat


def test_s3cat():
    # Create some test files
    to_delete = []
    S3PREFIX = os.environ['DAS_S3ROOT'] + f'/tmp/s3test-{int(time.time())}'

    (bucket,prefix) = ctools_s3.get_bucket_key(S3PREFIX)
    # Write out three files ---
    s3 = boto3.client('s3')
    object_exists_waiter = s3.get_waiter('object_exists')

    alldata = b''
    for part in range(5):
        key = prefix+f"/part-{part:05}"
        data = b"".join([b"This is line {line}\n" for line in range(part*100,(part+1)*100)])
        alldata += data
        with io.BytesIO(data) as f:
            s3.upload_fileobj(f, bucket, key)
        object_exists_waiter.wait(Bucket=bucket, Key=key)
        to_delete.append(key)

    logging.info("Make sure that s3cat without a _SUCCESS throws an exception")
    SUFFIX = '.txt'
    try:
        s3cat.s3cat(S3PREFIX, demand_success=True, suffix=SUFFIX, verbose=False)
    except FileNotFoundError as e:
        logging.info("Exception: %s",str(e))
    else:
        raise RuntimeError("s3cat did not generate exception when no _SUCCESS file was present")

    with io.BytesIO(b"") as f:
        key = prefix+"/_SUCCESS"
        s3.upload_fileobj(f, bucket, key)
    object_exists_waiter.wait(Bucket=bucket, Key=key)
    to_delete.append(key)

    logging.info("Make sure s3cat works")
    s3cat.s3cat(S3PREFIX, demand_success=True, suffix=SUFFIX, verbose=False)

    # validate the data
    response = s3.get_object(Bucket=bucket, Key=prefix+SUFFIX)
    assert response['Body'].read() == alldata
    to_delete.append(prefix+SUFFIX)

    # Clean up
    for key in to_delete:
        s3.delete_object(Bucket=bucket, Key=key)

if __name__=="__main__":
    test_s3cat()
