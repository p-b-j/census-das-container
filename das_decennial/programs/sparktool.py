#!/usr/bin/env python3
"""Census Bureau's sparktool---a command-line interface to the Spark API.

This is the same interface that the GUI uses, but we don't have easy access to the GUI at Census."""

import os
import os.path
import sys
import json

sys.path.append( os.path.join( os.path.dirname(__file__), ".."))

import das_framework.ctools.cspark as cspark

def spark_ls(sparkinfo):
    for si in sparkinfo['spark']:
        print("Application name:{name} id:{id}".format(
            name=si['application']['name'],
            id=si['application']['id']))
        for attempt in si['application']['attempts']:
            print("  Attempt: ")
            for(k,v) in attempt.items():
                print("    {:15} {}".format(k,v))
            print("")
        print("Jobs:")
        for job in si['jobs']:
            print("")
            print("  Job:")
            for(k,v) in job.items():
                print("    {:15} {}".format(k,v))
        print("")
        print("Executors:")
        for executor in si['allexecutors']:
            for (k,v) in executor.items():
                print("    {:15} {}".format(k,v))
            print("")

if __name__=="__main__":
    from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
    parser = ArgumentParser( formatter_class = ArgumentDefaultsHelpFormatter,
                             description="Access to the Apache SPARK API" )
    parser.add_argument("--ls",help="List what we can",action='store_true')
    parser.add_argument("--write", help="Write spark json file to file")
    parser.add_argument("--read", help="Read spark json file from file")
    parser.add_argument("--port", help="Specify a specific spark port to use",type=int)
    parser.add_argument("--host", help="Specify a specific spark host to use")
    args = parser.parse_args()

    if args.read:
        sparkinfo = json.loads(open(args.read,"r").read())
    else:
        sparkinfo = cspark.get_spark_info(host=args.host,port=args.port)
        

    if args.write:
        open(args.write,"w").write(json.dumps(sparkinfo, indent=4, sort_keys=True))

    if args.ls:
        spark_ls(sparkinfo)
    
    

