#!/bin/bash
#
# This script is used to manipulate the git properties for the das_decennial repo and its submodules.
# The whole script needs to be redone using 'git submodule foreach'
#
# If you are outside of Census, use this to clone the subrepos with:
# $ bash git_fixup.sh --clone
# For example:
# - accessing github.com from within census --- use https
# - accessing github.com from outside centus --- use ssh
#
# The script can be used to synchronize the internal repo with the external repo, and vice-versa.
# This should probably be rewritten in Python
#
# To kill a submodule:
# git submodule deinit -f das_framework/
# Simson Garfinkel, 2018-2019
#

set -u          # treat unset variables and parameters as an error
set -e          # exit if a command returns a non-zero return code not in a test
set -o pipefail # pass errors in a pipeline to the end

# Figure out if we are running INSIDE or OUTSIDE
if host github.ti.census.gov >/dev/null 2>&1 ; then
    INSIDE=Y
    echo Operating inside the Census firewall
else
    INSIDE=N
    echo Operating outside the census firewall
fi


help() {
  cat <<EOF
usage: $0 [options]   

Uses 'remote set-url' to set the all repos to pull from
the TI github repo using https.

options:
  --help         -- Print this
  --test         -- Test the repo after it is created
EOF

  if [ INSIDE == 'Y' ]; then
      cat <<EOF
specify your repo -- INSIDE CENSUS:
  --ti-ssh       -- Target github.ti.census.gov from within Census via ssh
  --ti-https     -- Target github.ti.census.gov from within Census via https (default)
EOF
  else
      cat <<EOF
specify your repo -- OUTSIDE CENSUS:
  --github-https -- Target github.com via HTTPS
  --github-ssh   -- Target github.com via SSH
EOF
  fi

  cat <<EOF
Actions for managing the remotes:
  --clone       -- clone 
  --show        -- just show the remotes
  --diff        -- Show differences with target, but do not do anything else
  --pull        -- Just pull the changes from the named repo
  --merge       -- Merge in changes from remote with a branch and merge
  --push        -- Push changes to remote
  --commit      -- Make sure every repo is on head and commit.
  --status      -- Show the status of every repo
  --showbranch  -- Just print the current branch of each repo
  --deinit      -- throw away all of the submodules
  --head        -- fix any detached heads


So to send to the outside, you might do this:
./git_fixup_census.sh --pull --ti            # run inside Census to pull from TI github
./git_fixup_census.sh --head                 # run inside Census to fix any detached heads
./git_fixup_census.sh --fetch --merge        # fetch from TI github and integrate changes to the head
./git_fixup_census.sh --fetch --merge  # pull from external repo
./git_fixup_census.sh --push           # and push all back to the external repos
EOF
    exit 0
}

# Operate on the repos from the bottom up in this order.
REPOS="das_framework/ctools das_framework/dfxml das_framework hdmm etl_2020/census_etl etl_2020 ."

GITHUB_SSH_SERVERBASE=ssh://git@github.com/dpcomp-org
GITHUB_HTTPS_SERVERBASE=https://github.com/dpcomp-org
TI_SSH_SERVERBASE=ssh://git@github.ti.census.gov/CB-DAS
TI_HTTPS_SERVERBASE=https://github.ti.census.gov/CB-DAS

# Defaults
SERVERBASE=$TI_SSH_SERVERBASE
branch=master

# This magic gets the directory of the script
# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

PUSH=N
COMMIT=N
STATUS=N
MERGE=N
SHOWBRANCH=N
EXT=N
DIFF=N
SHOW=N
REMOTE=ti
TEST=N
PULL=N
HEAD=N
CLONE=N

# https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
# Process arguments
while [[ "$#" > 0 ]];
do case $1 in
       ## General
       --help) help;;
       --test) TEST=Y;;

   ## Targets:

   --ti)           SERVERBASE=ssh://git@github.ti.census.gov/CB-DAS;  REMOTE=ti-ssh; EXT=N; ;;
   --github-ssh)   SERVERBASE=ssh://git@github.com/simsong;           REMOTE=github-com-ssh; EXT=Y; ;;
   --github-https) SERVERBASE=https://github.com/simsong;             REMOTE=github-com-https; EXT=Y; ;;

   ## Actions:
   --show)   SHOW=Y;;
   --head)   HEAD=Y;;
   --diff)   DIFF=Y;;
   --push)   PUSH=Y;;
   --commit) COMMIT=Y;;
   --status) STATUS=Y;;
   --pull)   PULL=Y;;
   --merge)  MERGE=Y;;
   --showbranch) SHOWBRANCH=Y;;
   *) echo "Unknown parameter: $1";exit 1;;
esac; shift; done
			     
if [ -z ${SERVERBASE+x} ]; then
    echo SERVERBASE is unset.
    if [ $PUSH = Y ]; then
	please specify --ti, --ext or --github for --push
	exit 1
    fi
fi
       --ti-ssh)       SERVERBASE=$TI_SSH_SERVERBASE;       REMOTE=ti-ssh;           EXT=N; ;;
       --ti-https)     SERVERBASE=$TI_HTTPS_SERVERBASE;     REMOTE=ti-https;         EXT=N; ;;
       --github-ssh)   SERVERBASE=$GITHUB_SSH_SERVERBASE;   REMOTE=github-com-ssh;   EXT=Y; ;;
       --github-https) SERVERBASE=$GITHUB_HTTPS_SERVERBASE; REMOTE=github-com-https; EXT=Y; ;;
       
       ## Actions:
       --clone)  CLONE=Y;;
       --show)   SHOW=Y;;
       --clone)  CLONE=Y;;
       --head)   HEAD=Y;;
       --diff)   DIFF=Y;;
       --push)   PUSH=Y;;
       --commit) COMMIT=Y;;
       --status) STATUS=Y;;
       --pull)   PULL=Y;;
       --merge)  MERGE=Y;;
       --showbranch) SHOWBRANCH=Y;;
       *) echo "Unknown parameter: $1";exit 1;;
   esac; shift; done

################################################################
### Useful functions
################################################################
die() {
    echo $*
    exit 1
}

cmd() {
    echo '>>>' `pwd`: $*
    $* || die command failed
}

check_git() {
    cmd git $*
}


## Set up git
export GIT_SSL_NO_VERIFY=true
check_git config --global credential.helper store

# Make sure we are on master
current_branch=`git status --porcelain -b | grep '##' | sed 's/[.][.][.].*//'`
if [ "$current_branch" != '## master' ]; then
    echo not on master branch
    exit 1

################################################################
## Make sure vars are set 
################################################################
if [ -z ${SERVERBASE+x} ]; then
    echo SERVERBASE is unset.
    if [ $PUSH = Y ]; then
	please specify --ti-ssh, --ti-https, --ext or --github for --push
	exit 1
    fi
fi

# Make sure we have a sync remote added if we have a serverbase
if [ -z ${REMOTE+x} ]; then
    echo No Remote
    exit 1
fi

## Set up git
export GIT_SSL_NO_VERIFY=true
check_git config --global credential.helper store
check_git checkout master

if [ -r $ROOT/das_framework/.git ]; then
    echo submodules have been cloned
    CLONED=Y
else
    echo submodules have not been cloned
    CLONED=N
fi

if [ $CLONE == "Y" ]; then
    echo Hit return to start cloning of sub-repos...
    readline

    if [ $CLONED == 'Y'  ]; then
        echo das_framework is already cloned. Stopping > /dev/stderr
        exit 1
    fi
    if [ $INSIDE == N ]; then
        # external operation -- change the URL for das_framework
        cd $ROOT
        check_git config --file=.gitmodules submodule.das_framework.url $GITHUB_SSH_SERVERBASE/das_framework
        check_git submodule sync das_framework
        check_git submodule init das_framework
        check_git submodule update das_framework
        cd das_framework
        for sm in ctools dfxml ; do
            # check out submodule sm
            check_git config --file=.gitmodules submodule.$sm.url $GITHUB_SSH_SERVERBASE/$sm
            check_git submodule sync $sm
            check_git submodule init $sm
            check_git submodule update $sm

            # And put the submodule URLs back
            check_git config --file=.gitmodules submodule.$sm.url $TI_HTTPS_SERVERBASE/$sm
            check_git submodule sync $sm
        done

        cd ..
        check_git config --file=.gitmodules submodule.das_framework.url $TI_HTTPS_SERVERBASES/das_framework
        check_git submodule sync
        cd ..
        echo clone complete
        exit 0
    else
        check_git submodule init --recursive
        check_git submodule update --recursive
    fi
else
    if [ $CLONED == 'N' ]; then
        echo das_framework is not cloned. Please run $0 --clone
        exit 1
    fi
fi


echo REMOTE: $REMOTE
echo URL: $SERVERBASE/$repo
echo MERGE: $MERGE  PULL: $PULL
echo 
echo Hit return to continue
read


for dir in $REPOS
do
    if [ $dir != . ]; then
	repo=`basename $dir`
    else
	repo=das_decennial
    fi
    d=$ROOT/$dir
    echo 
    echo
    echo === $repo ===

    if [ ! -d $d ]; then
        echo $d does not yet exist. Skipping. Be sure to re-run.
        continue
    fi
    echo cd $d
    cd $d

    if [ $EXT == "Y" ] && [ -e .NO_EXTERNAL_SYNC ] ; then
	echo WILL NOT EXTERNALLY SYNC $repo
        continue
    fi
    
    if [ $DIFF = 'Y' ]; then
	check_git diff
	continue
    fi

    if [ $SHOW = 'Y' ]; then
	check_git remote -v
	continue
    fi

    if [ $SHOWBRANCH = 'Y' ]; then
	check_git remote show $REMOTE
        check_git branch -v
    fi

    # Make sure REMOTE Is present
    /bin/rm -f /tmp/remote$$
    check_git remote -v > /tmp/remote$$
    if ! grep $REMOTE /tmp/remote$$ >/dev/null 2>&1 ; then
	check_git remote add $REMOTE $SERVERBASE/$repo
    fi

    if [ $PULL = 'Y' ]; then
	check_git pull $REMOTE master
    fi

    if [ $STATUS == "Y" ]; then
	check_git status
    fi

    ## These things cause changes

    if [ $HEAD = 'Y' ]; then
	/bin/rm -f /tmp/status$$
	check_git status | tee /tmp/status$$
	if grep 'HEAD detached' /tmp/status$$ >/dev/null 2>&1 ; then
	    echo Fixing detached head
	    tmp=tmp$$
	    check_git checkout -b $tmp
	    check_git checkout master
	    check_git merge $tmp
	    check_git branch -d $tmp
	else
	    echo head is fine
	fi
    fi

    if [ $MERGE = 'Y' ]; then 
	tmp=tmp$$
	if [ $repo == 'hdmm' ]; then
	    echo will only pull hdmm
	    check_git pull $REMOTE/master
	else
	    echo FIXME so that we do not merge if there are no changes
            check_git checkout -b $tmp  
	    check_git checkout master 
	    check_git merge $tmp 
	    check_git merge $REMOTE/master 
	    check_git branch -d $tmp
	fi
    fi
    
    if [ $COMMIT == "Y" ]; then
	tmp=tmp$$
	check_git commit -m sync -a --allow-empty
        check_git checkout -b $tmp  ; check_git checkout master ; check_git merge $tmp ; check_git branch -d $tmp 
    fi

    if [ $PUSH == "Y" ]; then
	if [ $EXT == 'Y' ] && [ -e .NO_EXTERNAL_PUSH ]; then
	    echo will not externally push

	elif [ $repo == 'hdmm' ]; then
	    echo special push code for hdmm
	    echo REMOTE: $REMOTE
	    if [ $REMOTE == github-com-https ]; then
		echo pushing to simsong instead
		check_git pull https://github.com/simsong/hdmm $branch
		check_git push https://github.com/simsong/hdmm $branch
	    else
		check_git push $REMOTE branch
	    fi
	else
	    check_git push $REMOTE $branch
	fi
    fi
done

