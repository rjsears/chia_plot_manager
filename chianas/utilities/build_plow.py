#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-09-18)"

"""
build_plow.py

So I built this script due to a screwup on my part. I manually
built the DESTS for Plow just taking a look at my mount and going
from there. Unfortunately I included a "drive" that was not actually
a mount point and you guessed it, it filled my root drive to capacity
and the harvester crashed.  

If you are running this integrated with the rest of my chia software,
simply set "integrated" to True and run the script, otherwise set the
appropriate glob and hostname. 

The output is shown below. It crawls your directory blob and creates
the necessary DEST entry for Plow. It will also show you the directories
that are NOT mount points (Non-Mount Point DESTS) which, of course, you
do NOT want to put into Plow lest you crash your server like I did.


Sample Output:

DESTS = [
    'chianas03:/mnt/enclosure1/front/column3/drive58',
    'chianas03:/mnt/enclosure1/front/column3/drive59',
    'chianas03:/mnt/enclosure1/front/column3/drive57',
    'chianas03:/mnt/enclosure1/front/column3/drive55'
    ]
    
Non-Mount Point DESTS = [
    'chianas03:/mnt/enclosure1/rear/column3/drive75',
    'chianas03:/mnt/enclosure1/rear/column3/drive77',
    'chianas03:/mnt/enclosure1/rear/column2/drive74'
]
"""



import os
import glob

# Read from main config files and classes?
integrated = False

def check_integrated():
    if integrated:
        from drivemanager_classes import DriveManager
        chianas = DriveManager.read_configs()
        directory_glob = chianas.directory_glob
        hostname = chianas.hostname
        return directory_glob, hostname
    else:
        # Set these variables if you are NOT using the integrated configuration
        # of plot and drive manager.
        # Define the directory glob pattern
        directory_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/'
        # Who are we?
        hostname = 'chianas01'
        return directory_glob, hostname




def is_actual_mount(directory):
    try:
        # Here we check if the directory is a mount point by comparing device numbers
        return os.path.ismount(directory) and os.stat(directory).st_dev != os.stat('/').st_dev
    except FileNotFoundError:
        return False

# Create and populate our lists: 
def generate_dest_lists(hostname, directory_blob):
    mount_dests = []
    non_mount_dests = []
    directories = glob.glob(directory_blob)

    for directory in directories:
        if (
            directory.startswith('/mnt/') and
            os.path.isdir(directory)
        ):
            if is_actual_mount(directory):
                mount_dests.append(directory.rstrip('/'))
            else:
                non_mount_dests.append(directory.rstrip('/'))

    return mount_dests, non_mount_dests


# Here we put it all together:
def main():
    server_info = check_integrated()
    hostname = server_info[1]
    directory_blob = server_info[0]
    mount_dests, non_mount_dests = generate_dest_lists(hostname, directory_blob)

    # Extract the drive numbers from the mount paths and sort by drive number
    sorted_mount_dests = sorted(mount_dests, key=lambda x: int(x.split("drive")[-1]))

    print("DESTS = [")
    for i, mount_dest in enumerate(sorted_mount_dests):
        if i == len(sorted_mount_dests) - 1:
            print(f"    '{hostname}:{mount_dest}'")
        else:
            print(f"    '{hostname}:{mount_dest}',")
    print("]")

    print("Non-Mount Point DESTS = [")
    for i, non_mount_dest in enumerate(non_mount_dests):
        if i == len(non_mount_dests) - 1:
            print(f"    '{hostname}:{non_mount_dest}'")
        else:
            print(f"    '{hostname}:{non_mount_dest}',")
    print("]")

if __name__ == "__main__":
    main()
