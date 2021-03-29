"""
    This file is a stand-alone script for computing the per-attribute epsilon (in an epsilon, delta sense) achieved by a given run of the DAS. Use of this script should rapidly be deprecated in favor of automatic calculation and printing of these values within each DAS run.
"""

import numpy as np
from fractions import Fraction
import scipy.optimize
import sys
#sys.path.append(".")
sys.path.append("..")
#from ..programs.engine.curve import zCDPEpsDeltaCurve as zCDPCurve
import programs.engine.curve as curve

queries = {}
queries["s3_1a"] = ["total", "cenrace", "hispanic", "votingage", "hhinstlevels", "hhgq", "hispanic * cenrace", "votingage * cenrace", "votingage * hispanic", "votingage * hispanic * cenrace", "detailed"]
queries["s3_1b"] = queries["s3_1a"]
queries["s3_2a"] = ["total", "hispanic * cenrace11cats", "votingage", "hhinstlevels", "hhgq", "hispanic * cenrace11cats * votingage", "detailed"]
queries["s3_2b"] = queries["s3_2a"]

query_props = {}
query_props["s3_1a"] = [1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11]
query_props["s3_1b"] = [1/1024, 1/512, 1/1024, 1/1024, 1/1024, 1/1024, 5/1024, 5/1024, 1/1024, 17/1024, 989/1024]
query_props["s3_2a"] = [1/7, 1/7, 1/7, 1/7, 1/7, 1/7, 1/7]
query_props["s3_2b"] = [1/1024, 1/1024, 1/1024, 1/1024, 1/1024, 1/1024, 1018/1024]

attrs_to_queries = {}
attrs_to_queries["cenrace"] = ["cenrace", "hispanic * cenrace", "votingage * cenrace", "votingage * hispanic * cenrace", "detailed"]
attrs_to_queries["cenrace"] += ["hispanic * cenrace11cats", "hispanic * cenrace11cats * votingage"]
attrs_to_queries["hispanic"] = ["hispanic", "hispanic * cenrace", "votingage * hispanic", "votingage * hispanic * cenrace"]
attrs_to_queries["hispanic"] += ["detailed", "hispanic * cenrace11cats", "hispanic * cenrace11cats"]
attrs_to_queries["votingage"] = ["votingage", "votingage * cenrace", "votingage * hispanic", "votingage * hispanic * cenrace"]
attrs_to_queries["votingage"] += ["detailed", "hispanic * cenrace11cats * votingage"]
attrs_to_queries["hhgq"] = ["hhinstlevels", "hhgq", "detailed"]

def get_q_props_for_attr(strat_name, attr):
    this_attr_q_props = []
    if attr != "*":
        for qname, q_prop in zip(queries[strat_name], query_props[strat_name]):
            if qname in attrs_to_queries[attr]:
                this_attr_q_props.append(q_prop)
    else:
        this_attr_q_props = query_props[strat_name]
    return this_attr_q_props

if __name__ == "__main__":
    strat_name = "s" + "3_1a"
    delta = 1e-10
    MODE = "geolevels" # Calculate semantics for geolevels or for demographic attrs?

    # Fill in manually based on fitted runs (or desired semantics, if not protecting some geolevels)
    # By convention, let -1 denote excluding a level from the semantics
    geolevels = ["US", "State", "County", "Tract", "Block_Group", "Block"]
    geolevel_props = [37/1024,37/1024,37/1024,37/1024,172/1024,704/1024]
    #geolevel_props = [-1, -1, -1, -1, -1, 721/1024] # aian 3_1a example, semantics only protect Block-in-BG
    #geolevel_props = [44/1024, 44/1024, 44/1024, 44/1024, 127/1024, 721/1024] # aian 3_1a example
    #geolevel_props = [106/1024, 106/1024, 106/1024, 106/1024, 122/1024, 478/1024] # aian 3_2b example
    #geolevel_props = [g for g in geolevel_props if g != -1]

    # Fill in manually based on fitted runs
    global_scale = 3883/4096
    #global_scale = 343/256 # aian 3_1a example
    #global_scale = 1117/1024 # aian 3_2b example

    if MODE == "attrs":
        list_of_attrs = list(attrs_to_queries.keys())
        list_of_geolevels = ["*"] # Asterisk is treated as wildcard geolevel; all geolevels match it
    elif MODE == "geolevels":
        list_of_attrs = ["*"] # Asterisk is treated as wildcard attr; all queries (within a geolevel) match it
        list_of_geolevels = geolevels
    else:
        raise ValueError(f"MODE {MODE} not recognized.")

    print(f"------\nComputing epsilon implied by global_scale, delta\n------")
    for i in range(len(list_of_geolevels)):
        cur_list_of_geolevels = list_of_geolevels[-1 * (i+1):] # Grab last i geolevels: [B], then [BG, B], then [TR, BG, B]...
        for attr in list_of_attrs:
            q_props = get_q_props_for_attr(strat_name, attr)
            print(f"\nFor {attr}, relevant query proportions: {q_props}")
            geolevel_props_tmp = [p if gn in cur_list_of_geolevels else -1 for gn, p in zip(geolevels, geolevel_props)]
            geolevel_props_tmp = [p for p in geolevel_props_tmp if p != -1] # Retains geolevel proportions for the current subset
            print(f"For {cur_list_of_geolevels}, relevant geolevel proportions: {geolevel_props_tmp}")
            gaussian_mechanism_curve = curve.zCDPEpsDeltaCurve(geo_prop=geolevel_props_tmp, query_prop=q_props, verbose=False)
            computed_epsilon = gaussian_mechanism_curve.get_epsilon(delta, global_scale, bounded=True,
                                                                                    tol=1e-7, zcdp=True)
            eps_msg = f"strat: {strat_name}, delta: {delta}, global_scale: {global_scale}"
            eps_msg += f"\ngeolevel props: {geolevel_props_tmp}"
            eps_msg += f"\nquery props: {q_props}"
            eps_msg += f"\nattribute: {attr}"
            eps_msg += f"\ncomputed epsilon: {computed_epsilon}"
            print(eps_msg)
