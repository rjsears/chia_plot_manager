#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-10-08)"

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
Enter 'True' for debug mode (shows available space), or 'False': F

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



If you choose to show drive space, this is a quick test to verify 
that build_plow.py is correcting detecting what compression you 
have set, it will output the drive space. You CANNOT use this
output for plow, if course.


root@chianas08:~/plot_manager# ./build_plow.py                                                                                   
Enter the number of drives per set: 3                        
Enter 'True' for debug mode (shows available space), or 'False': t
DESTS = [                                                    
'chianas08:/mnt/enclosure2/front/column0/drive219', 173.47GB,
'chianas08:/mnt/enclosure2/front/column0/drive220', 113.70GB,
'chianas08:/mnt/enclosure2/front/column0/drive221', 154.19GB 
]                                                            
DESTS = [                                                    
'chianas08:/mnt/enclosure2/front/column0/drive222', 174.96GB,
'chianas08:/mnt/enclosure2/front/column0/drive223', 94.43GB,
'chianas08:/mnt/enclosure2/front/column0/drive224', 114.97GB 
]                                                            
DESTS = [                                                    
'chianas08:/mnt/enclosure2/front/column0/drive225', 101.83GB,
'chianas08:/mnt/enclosure2/front/column0/drive226', 141.83GB,
'chianas08:/mnt/enclosure2/front/column0/drive227', 121.95GB 
]  


Regardless, at the end it also output any non-mounted paths in 
your directory glob. These paths, if written to, would fill your
root file system, so you would want to make sure NONE of these
are in your plow.py


Non-Mount Point DESTS = [                                    
    'chianas08:/mnt/enclosure3/front/column0/drive315',      
    'chianas08:/mnt/enclosure3/front/column0/drive347',      
    'chianas08:/mnt/enclosure3/front/column0/drive357',      
    'chianas08:/mnt/enclosure3/front/column0/drive330',      
    'chianas08:/mnt/enclosure3/front/column0/drive338'
    [


Finally, if you call it with '--next-mountpoint' it will simply output
the next available moutpoint that has available space. Good for calling
from another script.


"""

import os
import glob
import argparse
import subprocess

# Read from main config files and classes?
integrated = True

# Set this as a buffer ABOVE your compression value for how
# much space must be available on a drive. This is designed
# to be a little buffer. Adjust as needed.
plot_size_buffer = 2

# Define the compression sizes (bladebit_plots)
compression_sizes = {
    'c01': 87.5,
    'c02': 86,
    'c03': 84.5,
    'c04': 82.9,
    'c05': 81.3,
    'c06': 79.6,
    'c07': 78
}

def check_integrated():
    if integrated:
        from drivemanager_classes import DriveManager
        chianas = DriveManager.read_configs()
        directory_glob = chianas.directory_glob
        hostname = chianas.hostname
        compression_size = chianas.compression_in_use
        return directory_glob, hostname, compression_size
    else:
        # Set these variables if you are NOT using the integrated configuration
        # of plot and drive manager.
        # Define the directory glob pattern
        directory_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/'
        # Who are we?
        hostname = 'chianas01'
        compression_size = 'c05'
        return directory_glob, hostname, compression_size

def is_actual_mount(directory):
    try:
        # Here we check if the directory is a mount point by comparing device numbers - prevents filling root file system
        return os.path.ismount(directory) and os.stat(directory).st_dev != os.stat('/').st_dev
    except FileNotFoundError:
        return False


def generate_dest_lists(hostname, directory_blob):
    rsync_mountpoints = get_rsync_mountpoints()
    mount_dests = []
    non_mount_dests = []
    directories = glob.glob(directory_blob)

    for directory in directories:
        if (
                directory.startswith('/mnt/') and
                os.path.isdir(directory)
        ):
            if is_actual_mount(directory):
                # Exclude mountpoints used by rsync
                if directory not in rsync_mountpoints:
                    mount_dests.append(directory.rstrip('/'))
            else:
                non_mount_dests.append(directory.rstrip('/'))
    return mount_dests, non_mount_dests



def get_rsync_mountpoints():
    rsync_mountpoints = set()
    try:
        # Run the ps command to get rsync processes
        ps_output = subprocess.check_output(["ps", "aux"])
        ps_lines = ps_output.decode("utf-8").split("\n")

        # Extract mountpoints from rsync processes
        for line in ps_lines:
            if "rsync --server" in line:
                parts = line.split("--server")
                if len(parts) > 1:
                    mountpoint = parts[1].strip()  # Extract the mountpoint after "--server"
                    rsync_mountpoints.add(mountpoint)
    except Exception as e:
        print(f"Error getting rsync mountpoints: {e}")

    return rsync_mountpoints


def parse_arguments():
    parser = argparse.ArgumentParser(description="Build PLOW mountpoints")
    parser.add_argument("--next-mountpoint", action="store_true", help="Output the next available mountpoint")
    return parser.parse_args()

def main():
    args = parse_arguments()
    if args.next_mountpoint:
        server_info = check_integrated()
        hostname = server_info[1]
        directory_blob = server_info[0]
        mount_dests, _ = generate_dest_lists(hostname, directory_blob)

        mount_dests.sort(key=lambda x: int(x.split("drive")[-1]))

        for mount_dest in mount_dests:
            free_space_gb = get_free_space_gb(mount_dest)
            required_space_gb = (compression_sizes[server_info[2]] + plot_size_buffer)

            if free_space_gb >= required_space_gb:
                print(f"{hostname}:{mount_dest}")
                break
        return


    server_info = check_integrated()
    hostname = server_info[1]
    directory_blob = server_info[0]
    mount_dests, non_mount_dests = generate_dest_lists(hostname, directory_blob)

    drives_per_set = int(input("Enter the number of drives per set: "))

    if drives_per_set < 1:
        print("Number of drives per set should be 1 or more.")
        return

    mount_dests.sort(key=lambda x: int(x.split("drive")[-1]))

    compression_size = server_info[2]

    debug_input = input("Enter 'True' for debug mode (shows available space), or 'False': ").strip().lower()
    if debug_input in ['true', 't', '1']:
        debug = True
    else:
        debug = False

    required_space_gb = (compression_sizes[compression_size] + plot_size_buffer)

    sets = [mount_dests[i:i + drives_per_set] for i in range(0, len(mount_dests), drives_per_set)]

    selected_drives = []
    suitable_drives_found = False  # Flag to track if any suitable drives are found

    for set_idx, set_mount_dests in enumerate(sets):
        filtered_dests = []

        for i, mount_dest in enumerate(set_mount_dests):
            free_space_gb = get_free_space_gb(mount_dest)
            if free_space_gb >= required_space_gb:
                if debug:
                    filtered_dests.append(f"'{hostname}:{mount_dest}', {free_space_gb:.2f}GB")
                else:
                    filtered_dests.append(f"'{hostname}:{mount_dest}'")

        if len(filtered_dests) > 0:
            selected_drives.extend(filtered_dests)
            suitable_drives_found = True

    if suitable_drives_found:
        while selected_drives:
            print("DESTS = [")
            print(',\n'.join(selected_drives[:drives_per_set]))
            print("]")
            selected_drives = selected_drives[drives_per_set:]
    else:
        print("No suitable drives found.")


    print("Non-Mount Point DESTS = [")
    for i, non_mount_dest in enumerate(non_mount_dests):
        if i == len(non_mount_dests) - 1:
            print(f"    '{hostname}:{non_mount_dest}'")
        else:
            print(f"    '{hostname}:{non_mount_dest}',")
    print("]")

def get_free_space_gb(directory):
    statvfs = os.statvfs(directory)
    free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024 ** 3)
    return free_space_gb

if __name__ == "__main__":
    main()
