# Census DAS Container Standalone Execution
These are instructions for setting up and running the Census DAS in standalone mode.
All scripts/commands should be run from the top-level of the repository.

## Temp storage setup
These scripts rely on a local directory `singularity_tmp` for temporary storage in the Singularity container. Before running the scripts, create this directory if you haven't already:

```bash
$ mkdir singularity_tmp
```

## Run the DAS in standalone mode
Run the following command:
```bash
$ ./standalone/das_start.sh
```
