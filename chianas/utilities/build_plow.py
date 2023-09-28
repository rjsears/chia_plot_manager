#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-09-28)"

"""
build_plow.py

So, I built this script due to a screwup on my part. I manually
built the DESTS for Plow just taking a look at my mount and going
from there. Unfortunately, I included a "drive" that was not actually
a mount point, and you guessed it, it filled my root drive to capacity
and the harvester crashed.  

If you are running this integrated with the rest of my chia software,
simply set "integrated" to True and run the script, otherwise set the
appropriate glob and hostname. 

The output is shown below. It crawls your directory blob and creates
the necessary DEST entry for Plow. It will also show you the directories
that are NOT mount points (Non-Mount Point DESTS), which, of course, you
do NOT want to put into Plow lest you crash your server like I did.

When you run it, it will ask how many drives you want per set. For
For example, if you have 9 drives and say you want 3 per set, it will output
three unique DESTS lists for you. Useful if you are using multiple plows
from multiple plotters and want to keep drive saturation down to a 
minium and not cross drives between plotters. 

It also still outputs the non-mount points, which you would never want
to include in plow.py as it would fill your root filesystem.

root@chianas08:~/plot_manager# ./build_plow.py
Enter the number of drives per set: 3


DESTS = [
    'chianas08:/mnt/enclosure2/front/column0/drive213',
    'chianas08:/mnt/enclosure2/front/column0/drive214',
    'chianas08:/mnt/enclosure2/front/column0/drive215'
]
DESTS = [
    'chianas08:/mnt/enclosure2/front/column0/drive216',
    'chianas08:/mnt/enclosure2/front/column0/drive217',
    'chianas08:/mnt/enclosure2/front/column0/drive218'
]
DESTS = [
    'chianas08:/mnt/enclosure2/front/column0/drive219',
    'chianas08:/mnt/enclosure2/front/column0/drive220',
    'chianas08:/mnt/enclosure2/front/column0/drive221'
]
    
Non-Mount Point DESTS = [
    'chianas03:/mnt/enclosure1/rear/column3/drive74',
    'chianas03:/mnt/enclosure1/rear/column3/drive75',
    'chianas03:/mnt/enclosure1/rear/column2/drive77'
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

    drives_per_set = int(input("Enter the number of drives per set: "))
    
    if drives_per_set < 1:
        print("Number of drives per set should be 1 or more.")
        return

    # Sort the mount_dests in numerical order
    mount_dests.sort(key=lambda x: int(x.split("drive")[-1]))

    num_sets = len(mount_dests) // drives_per_set
    remaining_drives = len(mount_dests) % drives_per_set

    start_idx = 0

    for i in range(num_sets):
        end_idx = start_idx + drives_per_set
        if remaining_drives > 0:
            remaining_drives -= 1

        set_mount_dests = mount_dests[start_idx:end_idx]

        print("DESTS = [")
        for i, mount_dest in enumerate(set_mount_dests):
            if i == len(set_mount_dests) - 1:
                print(f"    '{hostname}:{mount_dest}'")
            else:
                print(f"    '{hostname}:{mount_dest}',")
        print("]")

        start_idx = end_idx

    if remaining_drives > 0:
        set_mount_dests = mount_dests[-remaining_drives:]
        
        print("DESTS = [")
        for i, mount_dest in enumerate(set_mount_dests):
            if i == len(set_mount_dests) - 1:
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
