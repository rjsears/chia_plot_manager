#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-12-25)"


'''
Simple python script to ask you what compression level you are using (gigahorse listed below,
please update the compression dictionary if you are using bladebit) and then outputs any
mountpoint included in the directory_glob listed in main() that is mounted abd has at least that much space
or more. Useful to determine if you have space left for a specific type of compression and to
maximize space available on your drives. 
'''

import os
import glob
import subprocess

compression_sizes = {
    'c01': 84.2,
    'c02': 82.6,
    'c03': 81.0,
    'c04': 79.4,
    'c05': 77.8,
    'c06': 76.2,
    'c07': 74.6,
    'c08': 71.3,
    'c09': 68.1,
    'c11': 85.7,
    'c12': 82.5,
    'c13': 78.9,
    'c14': 74.7,
    'c15': 71.6,
    'c16': 64.8,
    'c17': 63.0,
    'c18': 59.7,
    'c19': 56.4,
    'c20': 53.1
}

def get_available_space(directory):
    statvfs = os.statvfs(directory)
    block_size = statvfs.f_frsize
    available_blocks = statvfs.f_bavail
    available_space_gb = (block_size * available_blocks) / (1024 ** 3)
    return available_space_gb

def list_directories_with_space(compression_size, glob_pattern):
    required_space_gb = compression_sizes.get(compression_size, 0)

    if not required_space_gb:
        print(f"Compression size {compression_size} not found.")
        return

    matching_directories = sorted([dir_path for dir_path in glob.glob(glob_pattern) if os.path.ismount(dir_path) and get_available_space(dir_path) >= required_space_gb])

    return matching_directories

def run_df_command(directory):
    try:
        command = f"df -h {directory} | awk 'NR==2 {{printf \"%-15s %-8s %-8s %-8s %-5s %-s\\n\", $1, $2, $3, $4, $5, $6}}'"
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout, end='')  # end='' to eliminate extra line space
    except subprocess.CalledProcessError as e:
        print(f"Error running df command on {directory}: {e.stderr}")

def main():
    directory_structure_glob = "/mnt/enclosure[0-9]/*/column[0-9]/*/"

    compression_size = input("Compression Size? ").lower()

    matching_directories = list_directories_with_space(compression_size, directory_structure_glob)

    if matching_directories:
        print("\nMatching directories:")
        for directory in matching_directories:
            print(directory)

        print("\nRunning 'df' command on each directory:")
        print("Filesystem      Size     Used     Avail    Use%  Mounted on")
        for directory in matching_directories:
            run_df_command(directory)
    else:
        print(f"No matching directories found for compression size {compression_size}.")

if __name__ == "__main__":
    main()
