#!/bin/bash

# Outputing stdout and stderr to specific output files to ensure the output
# doesn't propagate back up to Jenkins (which displays stdout)
bash run_garfi303 fast 1> fast_output.out 2>&1
config=configs/PL94/topdown_RI.ini bash run_cluster.sh --fg 1>topdown_ri_output.out 2>&1

#config=configs/full_person/topdown_RI.ini bash run_cluster.sh --fg
#config=configs/full_household/topdown_RI.ini bash run_cluster.sh --fg
#onfig=configs/DHCP2020/MPD_FWF_RI.ini bash run_cluster.sh --fg
#config=configs/DHCH2020/MUD_FWF_RI.ini bash run_cluster.sh --fg

