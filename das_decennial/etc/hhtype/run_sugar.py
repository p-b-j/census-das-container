#!/usr/bin/python
#
"""run_sugar.py:

Run sugar and with the specified input file and optionally print all possible results.

Decode the output either with SUGAR or with our PYTHON implementation
or with both (used to validate the python implementation, which is
much faster.)

If variables are defined with a $PRINT comment, we nicely format that.
"""
import os
import sys
import re
from subprocess import Popen,PIPE,call
from collections import defaultdict,OrderedDict
from zipfile import ZipFile
import time
import logging
import string
import json

#SUGAR_PERL = '/usr/local/sugar-v2-3-3/bin/sugar'
#SUGAR_JAR  = '/usr/local/sugar-v2-3-3/bin/sugar-v2-3-3.jar'
SUGAR_MAIN = 'jp.kobe_u.sugar.SugarMain'
PICOSAT_SOLVER = 'picosat'
GLUCOSE_SOLVER = './glucose_static'
DEFAULT_SOLVER = PICOSAT_SOLVER

DECODE_SUGAR  = False
DECODE_PYTHON = True
WARN_SEEN_TWICE = False


# Our encodings
SEXMAP = {"1":"M", "0":"F"}
RACEMAP = {"1":"W", "0":"B"}
MARRIAGEMAP = {"0":"S", "1":"M"}
VARMAP = {"S":SEXMAP,
          "R":RACEMAP,
          "M":MARRIAGEMAP}
DEFAULT_ALL_VARS = 'all_solutions.tex'

class Hashabledict(dict):
    def __hash__(self):
        return hash(frozenset(self))
    def __lt__(self,a):
        for key in sorted(self.keys()):
            if key not in a:
                return True
            if self[key] < a[key]:
                return True
            if self[key] > a[key]:
                return False
        return False
        
        
def setup_sugar(path_to_sugar):
    if not path_to_sugar.endswith("/"):
        path_to_sugar = path_to_sugar + "/"
    SUGAR_PERL = path_to_sugar + "sugar-v2-3-3/bin/sugar"
    SUGAR_JAR = SUGAR_PERL + "-v2-3-3.jar"
    unzipped = os.path.exists(SUGAR_PERL) and os.path.exists(SUGAR_JAR)
    if not unzipped:
        with ZipFile(path_to_sugar + "sugar-v2-3-3.zip", "r") as zipObj:
            zipObj.extractall(path=path_to_sugar)
    return [SUGAR_PERL, SUGAR_JAR]


def validate_installation(path_to_sugar):
    [SUGAR_PERL, SUGAR_JAR] = setup_sugar(path_to_sugar)
    """Check files"""
    for fn in [SUGAR_PERL,SUGAR_JAR]:
        if not os.path.exists(fn):
            raise FileNotFoundError(f"Cannot find sugar {fn}; download it from http://bach.istc.kobe-u.ac.jp/sugar/")

    import distutils.spawn
    if not distutils.spawn.find_executable(PICOSAT_SOLVER):
        raise FileNotFoundError(f"{PICOSAT_SOLVER} not in PATH {os.getenv('PATH')}")


################################################################
###
### SAT SOLVER SUPPORT
###
################################################################


def is_cnf_file(fname):
    """CNF (conjunctive normal form) output files are produced by DIMACS
    solvers.  Validate that this is this a CNF file.
    """
    with open(fname,"r") as f:
        return f.read(6)=="p cnf "

def is_satisfied_cnf(fname):
    with open(fname,"r") as f:
        for line in f:
            if "s SATISFIABLE" in line:
                return True
        return False

################################################################
###
### SUGAR SUPPORT
###
################################################################

def sugar_encode_csp(*,cspfile,cnffile,mapfile, path_to_sugar):
    """Run sugar to make an output file"""
    [SUGAR_PERL, SUGAR_JAR] = setup_sugar(path_to_sugar)
    assert os.path.exists(cspfile)
    assert not os.path.exists(cnffile)
    assert not os.path.exists(mapfile)
    cmd = ['java','-cp',SUGAR_JAR,SUGAR_MAIN,'-v', '-encode', cspfile, cnffile, mapfile]
    logging.info("%s"," ".join(cmd))
    p = Popen(cmd,stdout=PIPE,stderr=PIPE)
    (out,err) = p.communicate()
    sugar_out = out.decode('utf-8'); del out
    sugar_err = err.decode('utf-8'); del err
    if p.returncode!=0:
        raise RuntimeError("sugar returned {}. out='{}' err='{}'".format(p.returncode,sugar_out,sugar_err))
        exit(1)
    assert os.path.exists(cnffile)
    assert os.path.exists(mapfile)
    
def sugar_decode_picosat_out(outdata,mapfile, path_to_sugar):
    [SUGAR_PERL, SUGAR_JAR] = setup_sugar(path_to_sugar)
    cmd = ['java','-cp',SUGAR_JAR,'jp.kobe_u.sugar.SugarMain','-decode','/dev/stdin',mapfile]
    logging.info("%s"," ".join(cmd))
    (out,err) = Popen(cmd,stdin=PIPE,stdout=PIPE,stderr=PIPE).communicate(outdata.encode('utf-8'))
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    if err:
        raise RuntimeError("sugar decode error: "+err)
    return out

def extract_vars_from_sugar_decode(outdata):
    """Extract the variables from the sugar output. Returns a dictionary
    with the key the variable name and the value being the variable
    value"""
    # vars[] is the mapping of the sugar variable to the solution
    vars = Hashabledict()
    for line in outdata.split("\n"):
        line = line.strip()
        if len(line)==0: continue
        if line[0]=='s' and line!='s SATISFIABLE':
            logging.error(outdata)
            raise RuntimeError("Constraints not satisfied; line={}".format(line))
        if line[0]=='a' and "\t" in line:
            (var,val) = line[2:].split("\t")
            vars[var] = int(val)
    return vars

### Same as above, but use Python.
### This should be much faster than running a Java subprocess

def python_get_mapvars(mapfile):
    """Read the sugar .map file and return a dictionary
    where the key is the variable name and the value is the (type,start,r0,r1)
    kind = 'bool' for boolean coding, 'int' for integer coding
    start = boolean of first value
    r0 = first ordinal for integer coding
    r1 = last ordinal for integer coding. Sugar uses uniary encoding."""
    mapvars = {}
    with open(mapfile,"r") as f:
        for line in f:
            line = line.strip()
            if len(line)==0:
                continue
            fields = line.split(" ")
            try:
                (kind,name,start) = fields[0:3]
            except ValueError as e:
                logging.error("line: %s",line)
                logging.error("fields: %s",fields)
                raise e
            start = int(start)
            if kind=="int":
                if ".." in fields[3]:
                    (r0,r1) = fields[3].split("..")
                else:
                    (r0,r1) = int(fields[3]),int(fields[3])
                r0 = int(r0)
                r1 = int(r1)
                mapvars[name] = ('int',start,r0,r1)
            elif kind=='bool':
                mapvars[name] = ('bool',start,0,0)
            else:
                raise RuntimeError(f"Variables of type '{kind}' are not supported")
    return mapvars

def python_decode_picosat_and_extract_satvars(*,solver_output_lines,mapvars=None):
    """Read the output from a SAT solver and a map file and return the variable assignments 
    and a set of coeficients to add the dimacs file to prevent this solution."""

    satvars    = Hashabledict()
    # Compute the highest variable in use. The rest are internal CNF Booleans used by Sugar which we don't need
    highest = max(v[1]+v[3]-v[2] for v in mapvars.values())
    # Now read the boolean variables and learn what each one's value is
    coefs = dict()               # each variable is positive or negative
    for line in solver_output_lines:
        # For each line in the DIMACS output file
        # read the numbers and add each to the coefficients set. 
        # stop when the first line is higher than the higest variable that we care about
        line = line.strip()
        if line[0:1]!='v':
            continue
        try:
            vals = [int(v) for v in line[2:].split(" ")]
        except ValueError as e:
            logging.error("invalid line: %s",line)
            raise e
        for val in vals:
            coefs[abs(val)] = val
        if abs(vals[0]) > highest:
            break               # no need to read any more

    # Now for each variable, check all of the booleans that make it up
    # to find the value of the variable. 
    for var in mapvars:
        (kind,start,r0,r1) = mapvars[var]
        if kind=='int':
            for i in range(r1-r0):
                x = start+i
                if coefs[x] > 0:    # positive value indicates the value
                    satvars[var] = r0+i
                    break
            # If they were all negative, then it's the highest value
            if var not in satvars:
                satvars[var] = r1
        else:
            raise RuntimeError(f'variables of type {kind} are not yet supported.')
    return satvars

################################################################
def latex_def(name,value):
    return "\\newcommand\\{}{{\\xspace{:,d}\\xspace}}\n".format(name,value)

def lines_iter(data):
    """Returns the lines without a newline"""
    return (x.group(0) for x in re.finditer(".*", data) if x.group(0))

def linecount(fname,filter_func):
    return len(list(filter(filter_func,open(fname,"r").read().split("\n"))))

def unmap(satvars,var):
    # Given a variable that is to be unmapped (e.g. A2)
    # transform it to text
    try:
        rvar = satvars[var]        # rvar is what we are returning
    except KeyError:
        return var
    try:
        return VARMAP[var[0]][rvar]
    except KeyError:
        return rvar

def sugar_decode_picostat_and_extract_satvars(lines,mapfile,path_to_sugar):
    return extract_vars_from_sugar_decode( sugar_decode_picosat_out( "\n".join(lines), mapfile, path_to_sugar))

def picosat_get_next_solution(path):
    """Read the picosat solution file and return each solution"""
    lines = []
    with open(path,"r") as f:
        for line in f:
            if line.startswith('c'):
                continue
            if line=="s SATISFIABLE\n":
                if lines:
                    yield lines
                    lines = []
            if line.startswith('s SOLUTIONS'):
                continue
            lines.append(line)
        if lines:
            yield(lines)
            
def sparse(line):
    """A tiny little and possibly broken s-expression parser"""
    stack = []                  # current stack
    ret   = []                  # what we are returning
    atom  = None                # current atom being built
    
    for ch in line:
        if ch==';':
            break
        if ch=='(':
            stack.append([])
            atom = None
            continue
        if ch==')':
            ret.append(stack.pop())
            atom = None
            if len(stack)==0:
                return ret[0]
            continue
        if ch in string.whitespace:
            atom = None
            continue
        if atom is None:
            atom = ch
            stack[-1].append(ch)
        else:
            stack[-1].append( stack[-1].pop() + ch)
    return ret[0] if len(ret)>0 else None
    
            
SORT_ORDER_RE=re.compile(r"\$SORT-ORDER: (\S+)")
class PicosatPrinter:
    """Use picosat to find all of the solutions"""

    def __init__(self):
        self.printvars  = set()
        self.sort_order = []
        pass

    def orderedVars(self,vars):
        """Given a dictionary of variables, order them in sort_order if possible"""
        varskeys = set(vars.keys())
        ret  = OrderedDict()
        for var in self.sort_order:
            if var in varskeys:
                ret[var] = vars[var]
                varskeys.remove(var)
        for remaining_key in varskeys:
            ret[remaining_key] = vars[remaining_key]
        return ret

    def sortfun(self,vars):
        return tuple(self.orderedVars(vars).values())

    def extractPrintVars(self,vars):
        """Extract the print variables from a dictionary."""
        return {key:vars.get(key,None) for key in self.printvars}

    def get_printvars_from_csp(self,path):
        for line in open(path):
            if "$PRINT" in line:
                s = sparse(line)
                if (s is not None) and (s[0] in ['int','bool']):
                    self.printvars.add(s[1])
            m = SORT_ORDER_RE.search(line)
            if m:
                if self.sort_order:
                    raise ValueError("$SORT-ORDER appears twice in comments")
                self.sort_order = m.group(1).split(",")

    def parse_picosat_all_solutions(self,path,mapfile):
        logging.info("parsing all picosat solutions in %s",path)
        total_solutions = 0
        distinct_solutions = 0
        seen = dict()
        ctr = 0
        psatvars_seen  = set()  # variables seen with python implementation
        ssatvars_seen  = set()  # variables seen with sugar implementation
        mapvars = python_get_mapvars(mapfile)
        for lines in picosat_get_next_solution(path):
            # We can use either the python decoder or the sugar decoder.
            # If we use both, we can compare them.
            if DECODE_PYTHON:
                psatvars = python_decode_picosat_and_extract_satvars(solver_output_lines=lines,mapvars=mapvars)
                if (psatvars in psatvars_seen) and WARN_SEEN_TWICE:
                    logging.warning("Seen twice: %s",psatvars)
                psatvars_seen.add(psatvars)
                if len(psatvars_seen) % 100==0:
                    logging.warning("Total solutions so far: %s",len(psatvars_seen))

            if DECODE_SUGAR:
                ssatvars = sugar_decode_picostat_and_extract_satvars(lines,mapfile)
                if DECODE_PYTHON:
                    if ssatvars!=psatvars:
                        print("lines:")
                        print("".join(lines))
                        print("mapfile:")
                        print(open(mapfile).read())
                        raise RuntimeError("Error in python decoder. ssatvars: %s  satvars: %s",ssatvars,satvars)
                else:
                    assert ssatvars not in ssatvars_seen
                    ssatvars_seen.add(ssatvars)


        # If we ran sugar, use its solutiosn, otherwise use Python's solutions
        satvars = ssatvars_seen if DECODE_SUGAR else psatvars_seen

        # Create a sorted list using sortvars if present
        self.solutions = list(sorted(satvars,key=self.sortfun))

        if len(self.solutions)==0:
            raise RuntimeError("NO SOLUTIONS FOUND")

    def print_all_solutions(self, path: str = ''):
        if not self.printvars:
            print("No $PRINT variables specified. Printing all solutions.")
            for (ct,satvars) in enumerate(solutions):
                print(f"picosat solution #{ct}: {satvars}")
                return

        if path:
            folder, file_name = os.path.split(path)
            if folder and not os.path.exists(folder):
                raise ValueError(f'Directory {folder} does not exist')
            with open(file=path, mode='w') as file:
                # Print header indicating when and how the file was generated
                file.write("# This file was automatically generated by {} on {}\n".format(sys.argv[0], time.asctime()))
                file.write("# Command line: {}\n".format(" ".join(sys.argv)))

                start = '{'
                end = '}'
                file.write(f'mapping = {start}\n')
                for (ct, satvars) in enumerate(self.solutions):
                    extracted = self.orderedVars(self.extractPrintVars(satvars))
                    extracted_json = json.dumps(extracted)
                    file.write(f'    {ct}: {extracted_json},\n')
                file.write(f'    {end}\n')

        print("#Printing just these variable: ",self.printvars)
        print("#Printing in sort order: ",self.sort_order)
        print("#")
        # Get just the list of variables we want to print
        eseen = defaultdict(list)
        for (ct,satvars) in enumerate(self.solutions):
            # extract the printing vars from this solution
            extracted = self.orderedVars(self.extractPrintVars(satvars))
            extracted_json = json.dumps(extracted)
            # If we have seen this before, indicate that two solutions have the same variables
            print(f"# {ct}")
            print(extracted_json)
            if extracted_json in eseen:
                print(f"  DEGENERATE PRINTED VARIABLES")
                for deg in eseen[extracted_json]:
                    print(f"   #{deg:03}: {solutions[deg]}")
                print(f"   #{ct:03}: {solutions[ct]}")
                exit(0)
            eseen[extracted_json].append(ct)
            print("")


if __name__=="__main__":
    from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
    parser = ArgumentParser( formatter_class = ArgumentDefaultsHelpFormatter,
                             description="Runs sugar with picosat and parse the results into LaTeX")
    parser.add_argument("--cnf",default="constraints.cnf",help="specify cnf file")
    parser.add_argument("--parseout",
                        help="Parse the variables out of an .out file. A map file must be specified")
    parser.add_argument("--solver",default="picosat")
    parser.add_argument("--picosat_out",help='picosat output file',default='constraints.out')
    parser.add_argument("--mapfile",help="Specify map file",default='constraints.map')
    parser.add_argument("--all",help="Compute all possible solutions; store results in ALL")
    parser.add_argument("--parseall",help='Just Evaluate output file of the picosat --all (you also need a --mapfile)')
    parser.add_argument("--decode",help="test the decode function")
    parser.add_argument("--define",help="specify a #define to CPP")
    parser.add_argument("--sugar_output",help="specify sugar output",default='constraints.sugar.out')
    parser.add_argument("--tmpcsp", help="Temp CSP File (after running cpp)")
    parser.add_argument("--outname", help="Output file name")
    parser.add_argument("problem",default="hhtype.csp",help="specify the problem CSP")
    args = parser.parse_args()

    path_to_sugar = "/mnt/gits/das-vm-config/dist/zip"
    validate_installation(path_to_sugar)
    [SUGAR_PERL, SUGAR_JAR] = setup_sugar(path_to_sugar)

    if not args.tmpcsp:
        args.tmpcsp = args.problem+".tmp"

    if args.parseout:
        out = open(args.parseout,"r").read()
        mapvars = python_get_mapvars(args.mapfile)
        satvars = python_decode_picosat_and_extract_satvars( solver_output_lines=out.split("\n"), mapvars=mapvars)
        print(parse_vars_to_printable(satvars))
        exit(1)

    if args.decode:
        decode(open(args.decode,"r").read())
        exit(0)

    if not args.parseall:
        # Run the pre-processor and remove the files that begin with a '#'
        cmd = ['cpp',args.problem]
        (out,err) = Popen(cmd,stdout=PIPE).communicate()
        with open( args.tmpcsp, "w") as f:
            for line in out.decode('utf-8').split("\n"):
                if line.startswith('#'):
                    continue
                f.write(line)
                f.write("\n")

        # Run sugar, which runs the solver
        if args.all:
            args.solver += " --all"
        tmp = args.cnf.replace(".cnf","")

        # Here is what the Java looks like
        # java  -cp './sugar-v2-3-3/bin/sugar-v2-3-3.jar' jp.kobe_u.sugar.SugarMain -vv  -encode 'constraints.csp' 'constraints.cnf' 'constraints.map'

        cmd = ['perl',SUGAR_PERL,
               '-jar',SUGAR_JAR,
               '-vv',
               '-solver',args.solver,'-keep','-tmp','constraints',
               '-output',args.picosat_out,
               args.tmpcsp]

        print(" ".join(cmd))
        t0 = time.time()
        p = Popen(cmd,stdout=PIPE,stderr=PIPE,encoding='utf-8')
        (sugar_out,sugar_err) = p.communicate()
        t1 = time.time()
        if p.returncode!=0:
            raise RuntimeError("sugar returned {}. out='{}' err='{}'".
                               format(p.returncode,sugar_out,sugar_err))
            exit(1)
        print("sugar run time: {:.4} sec".format(t1-t0))
        for line in sugar_out.split("\n"):
            if ("ERROR" in line) and ("SOLUTIONS" not in line):
                print("Error in running sugar:")
                print(line)
                exit(1)
    
    if args.all or args.parseall:
        pp = PicosatPrinter()
        pp.get_printvars_from_csp(args.problem)
        if args.parseall:
            pp.parse_picosat_all_solutions(args.parseall,args.mapfile)
        else:
            pp.parse_picosat_all_solutions(args.picosat_out,args.mapfile)
        pp.print_all_solutions(args.outname)
        exit(0)

    # keep a copy of the sugar output
    # Not strictly necessary, but useful for debugging
    with open(args.sugar_output,'w') as f:
        f.write(sugar_out)

    # Now constraints.out has the output from picosat

    satvars = extract_vars_from_sugar_decode(sugar_out)
    results = satvars_to_codes(satvars)

    # Print information about reconstruction, sorted
    for (age,desc) in sorted(results):
        print(desc)
        
