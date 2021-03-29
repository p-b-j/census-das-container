# To run on AWS cluster locally on head node (e.g. for degugger to stop to local console)
PYTHONPATH=/usr/lib/spark/python/lib/pyspark.zip:/usr/lib/spark/python/lib/py4j-src.zip SPARK_HOME=/usr/lib/spark python das2020_driver.py $1
