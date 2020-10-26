#!/usr/bin/env python
"""Script for creating a blacklist.

Will flag stations with unacceptably high or low mean innovations 
(observation-minus-background values).  Will also flag stations with
too few reports, and stations that have more than one reported network.

NOTE:  Satellite observations are ignored.

Eric Kemp, SSAI/NASA GSFC
"""

# Standard modules
import configparser
import glob
import os
import sys

#------------------------------------------------------------------------------
def usage():
    """Print usage statement to standard out"""
    print("Usage: %s config.cfg" %(sys.argv[0]))

#------------------------------------------------------------------------------
def is_sat(platform):
    """Check if platform is satellite-based"""
    if platform in ["SSMI", "GEOPRECIP", "CMORPH", "IMERG"]:
        return True
    else:
        return False

#------------------------------------------------------------------------------

# Check command line
if len(sys.argv) != 2:
    print("[ERR] Bad command line arguments!")
    usage()
    sys.exit(1)

# Read config file
cfgfile = sys.argv[1]
if not os.path.exists(cfgfile):
    print("[ERR] Config file %s does not exist!" %(cfgfile))
    sys.exit(1)
config = configparser.ConfigParser()
config.read(cfgfile)
          
# Process the threshold settings
network_thresh = config.get('Input', 'network_thresh')
count_thresh = config.get('Input', 'count_thresh')
omb_thresh = config.get('Input', 'omb_thresh')

# Process the filename information.
data_directory = config.get('Input', 'data_directory')
if not os.path.exists(data_directory):
    print("[ERR] Directory %s does not exist!" %(data_directory))
data_frequency = config.get('Input', 'data_frequency')
data_hours = config.get('Input', 'data_hours')
data_hour_list = data_hours.split(",")

data = {}

# Build list of files
files = glob.glob("%s/oba_*_%s.txt" %(data_directory,
                                      data_frequency))
files.sort()

# Loop through each file, and store the O and B for each platform
for file in files:
    chunk = file.split("/")[1][12:14]
    if chunk not in data_hour_list:
        continue
    lines = open(file, "r").readlines()
    for line in lines[1:]:
        network = line.split()[0]
        platform = line.split()[1]
        if is_sat(platform):
            continue
        if platform not in data:
            data[platform] = []
        ob = line.split()[4]
        back = line.split()[5]
        data[platform].append("%s:%s:%s" %(network, ob, back))

# Now, loop through each station and calculate the mean OMB.  Create
# a blacklist
print("# Creating blacklist")
print("# Rejecting stations with more than %s network" %(network_thresh))
print("# Rejecting stations with less than %s observations" %(count_thresh))
print("# Rejecting stations with absolute mean OMB beyond %s" %(omb_thresh))

platforms = list(data.keys())
platforms.sort()
for platform in platforms:
    n = {}
    OMB = {}
    entries = data[platform]
    for entry in entries:
        network = entry.split(":")[0]
        ob = float(entry.split(":")[1])
        back = float(entry.split(":")[2])
        if network not in n:
            n[network] = 1
        else:
            n[network] += 1
        if network not in OMB:
            OMB[network] = 0.
        OMB[network] += (ob - back)
    length = len(OMB.keys())
    if length > int(network_thresh):
        print("%s # Found in %s networks" %(platform, length))
        continue
    for network in OMB:
        if n[network] < int(count_thresh):
            print("%s # Only have %s observation(s)" %(platform, n[network]))
            continue
        OMB[network] = OMB[network] / float(n[network])
        if abs(OMB[network]) > float(omb_thresh):
            print("%s # Mean OMB is %s" %(platform, OMB[network]))
            continue
