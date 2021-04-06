# Census DAS Container Execution
## Overview
The goal of this repo is to provide a means of running the Census' DAS project in a container on any machine.
This will hopefully enable researchers to run experiments on their own clusters without having to rely on AWS.

## Setup
### Gurobi License
You'll need to install a Gurobi license in order to run the DAS. See the [Gurobi website](https://www.gurobi.com/downloads/) for more information about how to obtain a free Gurobi license.

Download your license and save it to the file `~/gurobi.lic`.

If you are on the UW network, there is currently a license server up and running that you can use to dynamically retrieve a license file. This may be easier than downloading a single license as recommended above. If you wish to use this option, create a file `~/gurobi.lic` with the following contents:
```
TOKENSERVER=gurobiserver.cs.washington.edu
``` 

### Retrieving the 1940s IPUMS Dataset
Download the IPUMS 1940 full-count dataset [here](https://usa.ipums.org/usa/1940CensusDASTestData.shtml).
Store the file in the directory `~/das_files`, then decompress it with the following command:
```bash
$ gunzip ~/das_files/EXT1940USCB.dat.gz 
```

### Retrieving or Building a Singularity Image
Below are two ways to obtain a Singularity image for running the DAS.
#### **Option 1: Using a prebuilt image**
Because the current build process requires docker, there is an initial pre-built Singularity image available for download. At the time of writing this, the pre-built image worked, but we haven't rigorously tested it. Download into the top level of your repo using wget:
```bash
# Make sure we are at the top of the repo
$ basename $PWD
census-das-container
# Download image, takes roughly 5-10 minutes
$ wget https://homes.cs.washington.edu/~pbjones/census_das.img
```

You can also verify the `sha256sum` and/or `md5sum` of the downloaded image:
```bash
# Expected sha256sum output:
# 9bc14a6817eedf3ed4ffef6dd833d5efc2f218ecfc7e711bc3c004f0e048b849  census_das.img
$ sha256sum census_das.img
```
```bash
# Expected md5sum output:
# aa9d5b9131f50bb55c6f3438930b0694  census_das.img
$ md5sum census_das.img
```

#### **Option 2: Rebuilding from Docker and Singularity**
Singularity uses `/tmp` for temproary storage by default. Depending on how much space you have available in `/tmp`, you may run out of space when building the DAS. We recommend setting up a local temporary directory for Singularity to use by running the following commands from the top-level of the repo:

```bash
# Make sure we are at the top of the repo
$ basename $PWD
census-das-container
# Create temporary directory
$ mkdir singularity_tmp
# Point singularity tmp storage to new directory
# This will need to be run each bash session, or alternatively add it to your .bashrc
$ export SINGULARITY_TMPDIR=/path/to/census-das-container/singularity_tmp
```

Then you can build the image using Docker and Singularity:
```bash
# You may or may not need --network host depending on your docker setup
$ docker build --network host -t census:latest .
# Build a Singularity image from the local docker image
$ singularity build census_das.img docker-daemon:census:latest
```

## Configuration
There are a few ways to specify changes to where input/output/temporary files are located. These are specified using the `das_container.conf` file.

### DAS files location
By default, the code is meant to run under a subdirectory of your home directory,
and many of the input/output files are based on your home directory (`~/das_files`, `~/gurobi.lic`, `~/das-log`).

If you wish to run this code elsewhere on your system, you can define a new home directory
for the singularity container to use. Note that this new home directory cannot be a subdirectory
of your home directory due to the way that singularity mounts/binds directories.

For example, if I wanted my location for the DAS to be under `/scratch/pbj/`, I would do the following:
* Clone this repository (`census-das-container`) into a subdirectory of `/scratch/pbj/`.
* Setup your input files in the directory `/scratch/pbj/das_files`
* Setup your gurobi license file to have the path `/scratch/pbj/gurobi.lic`
* Specify your new DAS home location updating the `das_home` variable in `das_container.conf` (e.g. `das_home="/scratch/pbj"`)

Now you can run the DAS using the same commands specified in `standalone/README.md` and `cluster/README.md`. Your output files will now appear in `/scratch/pbj/das_files` and your logs should be in `/scratch/pbj/das-logs`.

### DAS Temporary Storage
The container scripts allow you to specify what directory in your system you want to bind to `/tmp` in the container. This is because we have often experienced permissions and space issues. This can be configured using the `container_tmp` variable in `das_container.conf`. By default, it is set to a local directory `singularity_tmp`, which you will have to create if you want to use it.

## Execution
Scripts/instructions for running the DAS in standalone (single-machine) mode are in the `standalone` directory. 
Scripts/instructions for running the DAS in cluster mode are in the `cluster` directory.
All scripts should be run from the top-level of the repository.

The DAS will assume your input IPUMS file is in `${das_home}/das_files` (see configuration section above for how to configure `${das_home}`) and will output logging info to `${das_home}/das-log`.
When the system finishes, your output files will be in `${das_home}/das_files/output`.

## Notes
This code currently relies on the Census' [census2020-das-e2e repo](https://github.com/uscensusbureau/census2020-das-e2e) which does not include the most updated code from the DAS framework. Syncing this repo with the latest Census code will be explored soon.
* Container setup done by Porter Jones (pbjones@uw.edu) with help from and to support the research of Abraham Flaxman (abie@uw.edu).
