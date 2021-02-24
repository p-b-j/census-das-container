# Census DAS Container Cluster Execution
These are instructions for setting up and running the Census DAS on a cluster of nodes.
This is very much a WIP; we do not know how Singularity will play w/Spark at the moment.

## Terminology Acknowledgement
`Spark`, like many computing areas, unfortunately made use of the terms "master" and "slave" to describe their system. These words reinforce computing as a space has been unwelcome and hostile for Black people and others who have faced systemic oppression. In our documentation, we will opt for the terms "coordinator" and "worker", but there are some `Spark` commands that unfortunately still make use of the prior terminology and it may appear in some commands cited in our documentation.

## Setting up Spark
If you don't have `Spark` downloaded on your cluster, start by downloading it.
Currently we recommend downloading the same version used in the Census code, though
it is likely possible to use a more up to date version.

```bash
# Feel free to put the spark directory wherever seems most convenient for you
$ cd /usr/local
$ wget -O spark.tgz https://apache.osuosl.org/spark/spark-2.4.7/spark-2.4.7-bin-hadoop2.7.tgz
$ tar xzvf spark.tgz
```

Then go ahead and add the following lines to your `.bashrc` or preferred profile file,
setting `SPARK_HOME` based on your installation directory in the above steps. 
The `PYSPARK_PYTHON` may need to be updated with a valid path to a `Python` binary on your system.
We recommend using a path to `python3.6`, again for consistency w/the Census' code,
but any version of `python3` should be ok. 
```bash
# Use the correct path based on where you installed spark
export SPARK_HOME="/usr/local/spark"
export PATH="${PATH}:${SPARK_HOME}/bin:${SPARK_HOME}/sbin"
# This may need to be updated to match your system
# Ideally python3.6, but any version of python3 should be ok
export PYSPARK_PYTHON="/usr/bin/python3.6"
```

And a friendly reminder to refresh your current session :)
```bash
$ source .bashrc
```

## Spinning up a cluster
Ok now we can try to actually spin a cluster up!

### Setting up the coordinator
Pick a node to be the coordinator. We'll need to be able to reference this node later
when spinning up workers and submitting our application,
so let's start by getting the hostname of this node.
```bash
$ hostname
```
Alternatively you can use the explicit ip address to reference this node
```bash
$ hostname -i
```
You'll need to reference this hostname or ip address in future commands.

Then you can startup the coordinator using `Spark`'s tools.
```bash
$ start-master.sh
```
The program should exit and run in the background.

### Setting up the workers
Now let's get some workers connected to your coordinator!
Run the following command for each worker that you want to setup
(replace `<hostname>` with either the hostname or ip address of your coordinator from above):
```bash
$ spark-class org.apache.spark.deploy.worker.Worker <hostname>:7077
```

You can also set the number of cores and memory you want the worker to use
using the `-m` and `-c` arguments:
```bash
$ spark-class org.apache.spark.deploy.worker.Worker -m 4G -c 4 <hostname>:7077
```

Your workers should now be idling waiting for a task!

## Running an applcation
Back on your coordinator node, you can now submit an application to your cluster!
When running `spark-submit`, just specify the coordinator node using the `--master` argument, e.g. `--master spark://<hostname>:7077`).

As a test, you can use one of `Spark`'s examples:
```bash
$ spark-submit --master spark://<hostname>:7077 --class org.apache.spark.examples.SparkPi --num-executors 1 --executor-cores 1 ${SPARK_HOME}/examples/jars/spark-examples_2.11-2.4.7.jar 10000
```

If you want to try it with the Census' code, change the following line in `start_das.sh`:
```bash
./run_1940_standalone.sh
```
Update it to the following:
```bash
./run_1940_cluster.sh spark://<hostname>:7077
```