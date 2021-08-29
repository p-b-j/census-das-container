FROM centos:7

# install yum dependencies
RUN yum update -y
RUN yum install -y epel-release passwd initscripts cronie wget bzip2 zip unzip
RUN yum makecache
RUN yum update -y

# download gurobi and get gurobi license key
WORKDIR /usr/local
RUN wget https://packages.gurobi.com/9.1/gurobi9.1.1_linux64.tar.gz
RUN tar xfz gurobi9.1.1_linux64.tar.gz
# Hash specific to a particular user's license
# If you are running the script for the first time, you will have to update
# with a hash for your own license. Free academic licenses should be available at gurobi.com
RUN /usr/local/gurobi911/linux64/bin/grbgetkey --path ~ 12f740fc-588c-11eb-be23-020d093b5256

# copy in directories
COPY census2020-das-e2e/etc ~/das_centennial/etc

# start the setup scripts
WORKDIR ~/das_centennial/etc
RUN mkdir -p /etc/rsyslog.d/
# Remove sudo from the scripts since we are already sudo
RUN for f in *.sh; do mv ${f} sudo${f} && sed 's/sudo //g' sudo${f} > ${f} && rm sudo${f}; done
RUN chmod +x *.sh
RUN bash -c "source ./standalone_prep.sh"
RUN bash -c "/usr/local/anaconda3/bin/python3.6 -m pip install msgpack"
RUN bash -c "/usr/local/anaconda3/bin/python3.6 -m pip install --upgrade pip"
RUN bash -c "/usr/local/anaconda3/bin/python3.6 -m pip install numpy --upgrade"
RUN bash -c "/usr/local/anaconda3/bin/python3.6 -m pip install randomgen"

ENTRYPOINT ./start_das.sh
