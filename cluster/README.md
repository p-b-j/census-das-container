# Census DAS Container Cluster Execution
These are instructions for setting up and running the Census DAS on a cluster of nodes.
All scripts/commands should be run from the top-level of the repository.
This is very much a WIP; we do not know how Singularity will play w/Spark at the moment.

## Terminology Acknowledgement
`Spark`, like many computing areas, unfortunately made use of the terms "master" and "slave" to describe their system. These words reinforce computing as a space has been unwelcome and hostile for Black people and others who have faced systemic oppression. In our documentation, we will opt for the terms "coordinator" and "worker", but there are some `Spark` commands that unfortunately still make use of the prior terminology and it may appear in some commands and scripts cited in our documentation.

## Spinning up a cluster

### Temp storage setup
These scripts rely on a local directory `singularity_tmp` for temporary storage in the Singularity container. Before running the scripts, create this directory if you haven't already:

```bash
$ mkdir singularity_tmp
```

### Picking a coordinator
Pick a node to be the coordinator. We'll need to be able to reference this node later
when spinning up workers and submitting our application,
so let's start by saving the hostname of this node to a file.
```bash
$ hostname > coord_hostname.txt
```
Alternatively you can use the explicit ip address to reference this node
```bash
$ hostname -i > coord_hostname.txt
```

Scripts for starting the workers and running the DAS rely on `coord_hostname.txt`
existing at the top-level of the repo.
If your cluster does not have a shared file system, then you'll have to create the
file `coord_hostname.txt` manually on nodes that start workers/run the DAS,
and then update its contents with the hostname of the coordinator.

### Starting the coordinator
After following the above steps, you should be able to start the coordinator:
```bash
$ ./cluster/coord_start.sh
```
The program should exit and run in the background.

### Setting up the workers
Now let's get some workers connected to your coordinator!
Run the following command for each worker that you want to setup:
```bash
$ ./cluster/worker_start.sh
```

You can also set the number of cores and memory you want the worker to use using the `-m` and `-c` arguments.
For example, if you want to run a worker using 4GB of memory and 2 cores:
```bash
$ ./cluster/worker_start.sh -m 4G -c 2
```

Your workers should now be idling waiting for a task!

## Running the DAS
You can now submit the DAS application to your cluster!
We recommend running this from the coordinator node, but any node that can
reach your coordinator should be fine.
```bash
$ ./cluster/das_start.sh
```

## Teardown
The worker nodes will run forever waiting for more jobs, so you'll need to explicitly kill each of those (using ^C or another way of killing the process).
You'll then need to run the following command on the coordinator node to stop it's spark process:
```bash
$ ./cluster/coord_stop.sh
```
