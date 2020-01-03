# CQNET-Alice
Code for monitoring Alice

## Overview
1. `AliceScanFunc.py` (Python3, Documented, INQNET4) -- Contains functions for remotely controlling Alice's power supply.
2. `plotExtRatio.py` (Python3, Documented, INQNET1) -- Plots the extinction ratio vs time for Alice's intensity modulator (IM) using data stored in the mysql database.
3. `runAliceIM.py` (Python3, Documented, INQNET4) -- Runs tuning voltage/optical power optimization code for Alice's intensity modulator.
4. `runAliceIMmanual.py` (Python3, Documented, INQNET4) -- Runs tuning voltage/optical power optimization code for Alice's intensity modulator, using the current voltage setting of the power supply. First find the optimal tuning voltage manually and set the power supply to that value.
5. `runAliceIMSocket.py` (Python3, Not Documented, INQNET4) -- Starter code for running the tuning voltage/optical power optimization code for Alice, using the "socket" software package to remotely control the power supply.


## Requirements
### Mysql
The scripts here store and collect data from mysql tables from local mysql databases. If you don't have
mysql installed, you first need to install it (see https://www.mysql.com/downloads/) and create databases, tables, and users. Unless you set up the exact same databases and tables, you will probably have to change the database, table, and column names/specs in the scripts.


### Python packages
Below are listed all the packages that are used in this repo. Many may already be installed on your computer, but otherwise you should install them.
#### Python3:
* pymysql
* ast
* datetime
* time
* numpy
* getpass
* os
* subprocess
* socket
* sys
* glob
* pipes
* argparse
* pyvisa
* matplotlib
* math
* ThorlabsPM100
* requests


### Installation command
To install python packages, use:
* `python3 -m pip install --user <package1> <package2> ...`

##### For tips and other useful commands for getting started, see the CQNET repo's README.

---
This code was written by Sam Davis at Caltech. Contact me at s1dav1s@alumni.stanford.edu if you have any questions.
