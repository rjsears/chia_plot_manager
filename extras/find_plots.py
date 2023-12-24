#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-12-24)"

'''
Simple script that looks for any plot (or file actually) that contains a specific 
word or phrase. For example entering 'k32-c05' would find all k32-c05 plots on your
system (based on the directory glob below) and return any directory that contains 
a file which includes that within it's name. It will also return the number of files
in each directory as well as the total number it has found. I use it to find specific
plots I want to replace, but you could use it for finding any file.

root@plotripper01:~# ./find_plots.py
Enter the file prefix to search for: k32-c05
Output file totals? (y/n): y

Matching Directories:
/mnt/enclosure2/front/column0/drive250/          150 Files
/mnt/enclosure2/front/column0/drive251/          150 Files
/mnt/enclosure2/front/column0/drive252/          150 Files

Total Files: 450 Files Found containing "k32-c05"
'''


import os
import glob

# Set you directory blob here that you want to use:
directory_structure_glob = "/mnt/enclosure[0-9]/*/column[0-9]/*/"

'''
This particular blob is designed around my harvester structure:

/mnt
     ├── enclosure1
     │   ├── front
     │   │   ├── column0
     │   │   │   ├── drive100
     │   │   │   ├── drive101
     │   │   │   ├── drive102
     │   │   │   └── drive103
     ├── enclosure2
     │   ├── front
     │   │   ├── column0
     │   │   │   ├── drive201
     │   │   │   ├── drive202
'''


file_prefix = input("Enter search pattern: ")
output_total_files = input('Output file totals? (y/n): ').lower() in {'y', 'yes'}


def find_matching_directories(directory_pattern, file_prefix):
    matching_directories = glob.glob(directory_pattern)

    result_directories = []

    for directory in matching_directories:
        matching_files = [file for file in os.listdir(directory) if file_prefix in file]

        if matching_files:
            if output_total_files:
                result_directories.append((directory, matching_files))
            else:
                result_directories.append((directory))

    result_directories.sort()

    return result_directories


def print_directories():
    # What do we want to look for? Ask when we start....

    matching_directories = find_matching_directories(directory_structure_glob, file_prefix)

    if output_total_files:
        if matching_directories:
            print("\nMatching Directories:")
            total_files = 0
            for directory, files in matching_directories:
                print(f"{directory} \t {len(files)} Files")
                total_files += len(files)

            print(f"\nTotal Files: {total_files} Files Found containing \"{file_prefix}\"")
        else:
            print("No matching directories found.")
    else:
        if matching_directories:
            print("\nMatching Directories:")
            for directory in matching_directories:
                print(directory)
        else:
            print("No matching directories found.")


def main():
    print_directories()


if __name__ == '__main__':
    main()
