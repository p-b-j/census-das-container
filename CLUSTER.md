# Census DAS Container Cluster Execution
These are instructions for setting up and running the Census DAS on a cluster of nodes.
This is very much a WIP; we do not know how Singularity will play w/Spark at the moment.

## Terminology Acknowledgement
`Spark`, like many computing areas, unfortunately made use of the terms "master" and "slave" to describe their system. These words reinforce computing as a space has been unwelcome and hostile for Black people and others who have faced systemic oppression. In our documentation, we will opt for the terms "coordinator" and "worker", but there are some `Spark` commands that unfortunately still make use of the prior terminology and it may appear in some commands and scripts cited in our documentation.

## Spinning up a cluster
We've provided a few wrapper scripts in `cluster_scripts` that are meant to be executed inside of `census_das.img`. All of these should be run from the top-level of the repository.

Note that for the following commands, we've omitted the `--home $HOME` and `--bind singularity_tmp:/tmp` options that we've used in the instructions for running the DAS. If you run into permissions issues with `/tmp`, you may have to use `--bind singularity_tmp:/tmp` for all of your cluster setup scripts (see README.md for more info). Singularity options can be added after the `exec` portion of the following commands, for example:
```bash
$ singularity exec --bind singularity_tmp:/tmp census_das.img ...
```

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

Then you can startup the coordinator:
```bash
$ singularity exec census_das.img ./cluster_scripts/start_coord.sh
```
The program should exit and run in the background.

### Setting up the workers
Now let's get some workers connected to your coordinator!
Run the following command for each worker that you want to setup
(replace `<hostname>` with either the hostname or ip address of your coordinator from above):
```bash
$ singularity exec census_das.img ./cluster_scripts/start_worker.sh <hostname>:7077
```

You can also set the number of cores and memory you want the worker to use using the `-m` and `-c` arguments.
For example, if you want to run a worker using 4GB of memory and 2 cores:
```bash
$ singularity exec census_das.img ./cluster_scripts/start_worker.sh -m 4G -c 2 <hostname>:7077
```

Your workers should now be idling waiting for a task!

## Running an applcation
Back on your coordinator node, you can now submit the DAS application to your cluster!

You should be able to run the following:
```bash
$ singularity exec --home $HOME census_das.img ./cluster_scripts/start_cluster.sh spark://<hostname>:7077
```
or if you're using a specific temp directory:
```bash
$ singularity exec --home $HOME --bind singularity_tmp:/tmp census_das.img ./cluster_scripts/start_cluster.sh spark://<hostname>:7077
```

## Teardown
The worker nodes will run forever waiting for more jobs, so you'll need to explicitly kill each of those (using ^C or another way of killing the process).
You'll then need to run the following command on the coordinator node to stop it's spark process:
```bash
$ singularity exec census_das.img ./cluster_scripts/stop_coord.sh
```
