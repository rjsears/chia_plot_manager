#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-09-18)"

"""
check_mountpoints.py

Like some of my other scripts, this script was created after I blew
up one of my harvesters by "plowing" to a non-mount point directory
on the harvester. I have sense wrote a script to create the DESTS
entry for plow (build_plow.py), but this script is designed for the
person who has hundreds of devices and is trying to figure out where
the offending files(s) might be parked. It looks at all directories
you set below  and returns a list of all NON mount points and 
the file size. If you are plowing to one of these, you can fill your
entire '/' in no time. 

Sample Output:

Non-Mount Drives and Their Sizes:
Drive: /mnt/enclosure1/front/column1/drive46, Size: 0 bytes
Drive: /mnt/enclosure3/front/column0/drive312, Size: 0 bytes
Drive: /mnt/enclosure3/front/column0/drive343, Size: 87220359168 bytes

In this case you can see that '/mnt/enclosure3/front/column0/drive343' is 
actually a directory with a file in it as opposed to a mount point that
is a drive.

As a side note, all of my drives end with drivexxx where xxx is a number.
If you configuration is different you may need to adjust the following
lines below:

directory.startswith('drive') and
directory[5:].isdigit()

Non of the paths that are returned should be included in the DESTS in 
plow.py, this should go without saying, that is how I screwed up in 
the first place.


"""


import os

# Set this to the start of the path you want your search to start from
base_directory = '/mnt/'

# Within the base_directory from above, what do your harvester mount points
# start with? As you can see from the sample output above, all of my mount
# points are under '/mnt' and start with '/mnt/enclosure'
starts_with = '/mnt/enclosure'

# Check if the directory is a mount point by comparing device numbers
def is_actual_mount(directory):
    try:
        return os.path.ismount(directory) and os.stat(directory).st_dev != os.stat('/').st_dev
    except FileNotFoundError:
        return False

# If it is NOT a mount point but a directory, what is the size?
def calculate_directory_size(directory):
    total_size = 0
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
    return total_size

# Look at the directories and see which ones are not actual
# mount points.
def find_non_mount_drives(base_directory):
    for root, dirs, _ in os.walk(base_directory):
        for directory in dirs:
            directory_path = os.path.join(root, directory)
            if (
                directory_path.startswith(starts_with) and
                not is_actual_mount(directory_path) and
                directory.startswith('drive') and
                directory[5:].isdigit()
            ):
                yield directory_path, calculate_directory_size(directory_path)

def main():
    print("Non-Mount Drives and Their Sizes:")
    for non_mount_drive, size in find_non_mount_drives(base_directory):
        print(f"Drive: {non_mount_drive}, Size: {size} bytes")

if __name__ == "__main__":
    main()
