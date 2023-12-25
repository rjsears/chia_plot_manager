#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-12-25)"


'''
Simple script that looks at your config.yaml (update your path in main())
and matches the list of plot directories listed there against the 
directory glob (also set in main()) on your harvester. Outputs a list of 
directories that are in your yaml that are not mounted and a list of 
directories that are mounted but not in your yaml file. 
'''

import yaml
import glob
import os

def normalize_path(path):
    return os.path.normpath(path)

def get_directories_from_config(config_path):
    with open(config_path, 'r') as file:
        config_data = yaml.safe_load(file)
        return config_data.get('harvester', {}).get('plot_directories', [])

def get_directories_from_glob(glob_pattern):
    return [normalize_path(path) for path in glob.glob(glob_pattern)]

def find_unmounted_directories(config_directories, mounted_directories):
    unmounted_directories = set(config_directories) - set(mounted_directories)
    return list(unmounted_directories)

def find_unlisted_directories(config_directories, mounted_directories):
    unlisted_directories = set(mounted_directories) - set(config_directories)
    return sorted(list(unlisted_directories))

def main():
    config_path = "/home/chia/.chia/mainnet/config/config.yaml"
    glob_pattern = "/mnt/enclosure[0-9]/*/column[0-9]/*/"

    config_directories = get_directories_from_config(config_path)
    mounted_directories = get_directories_from_glob(glob_pattern)

    unmounted_directories = find_unmounted_directories(config_directories, mounted_directories)
    unlisted_directories = find_unlisted_directories(config_directories, mounted_directories)

    print("Directories listed in config.yaml but not mounted:")
    for directory in unmounted_directories:
        print(directory)

    print("\nDirectories mounted but not listed in config.yaml:")
    for directory in unlisted_directories:
        print(directory)

if __name__ == "__main__":
    main()
