export PYTHONPATH=$PYTHONPATH:/mnt/users/moran331/das_decennial/


nohup 2>&1 spark-submit --py-files /mnt/users/moran331/das_decennial.zip --driver-memory 200g --num-executors 20 --executor-memory 10g --executor-cores 60 --driver-cores 50  --conf spark.driver.maxResultSize=0g --conf spark.executor.memoryOverhead=10g --conf spark.local.dir="/mnt/tmp/" --conf spark.eventLog.enabled=true --conf spark.eventLog.dir="/mnt/tmp/logs/" --master yarn --conf spark.submit.deployMode=client --conf spark.network.timeout=100000000 agecat_redistricting_totals.py &> agecat_redistricting_totals.out & 
