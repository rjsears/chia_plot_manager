#!/usr/bin/python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.5 (2021-04-22)"

# This script is part of my plot management set of tools. This
# script is used to move plots from one location to another on
# the same physical machine.
#
# If you are using a drive as a temp drive that falls within your
# scope of drives used for drive_manager.py, it is recommended that
# you offline that drive `./drive_manager -off drive43` to prevent
# drive_manager.py from placing plots on that drive.



import os
import sys
sys.path.append('/root/plot_manager')
import logging
import configparser
from system_logging import setup_logging
from system_logging import read_logging_config
import pathlib
import shutil
from timeit import default_timer as timer


# Are we testing?
testing = False
if testing:
    plot_dir = '/root/plot_manager/test_plots/'
    plot_size = 10000000
    status_file = '/root/plot_manager/local_transfer_job_running_testing'
else:
    plot_dir = '/mnt/enclosure1/front/column1/drive43/'
    plot_size = 108644374730  # Based on K32 plot size
    status_file = '/root/plot_manager/local_transfer_job_running'


# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
level = read_logging_config('plot_manager_config', 'system_logging', 'log_level')
level = logging._checkLevel(level)
log = logging.getLogger('move_local_plots')
log.setLevel(level)


# Let's Get Started

# Setup to read and write to our config file.
# If we are expecting a boolean back pass True/1 for bool,
# otherwise False/0
config = configparser.ConfigParser()
def read_config_data(file, section, item, bool):
    pathname = '/root/plot_manager/' + file
    config.read(pathname)
    if bool:
        return config.getboolean(section, item)
    else:
        return config.get(section, item)

# Look in our plot directory and get a list of plots. Do a basic
# size check for sanity's sake.
def get_list_of_plots():
    log.debug('get_list_of_plots() Started')
    try:
        plot_to_process = [plot for plot in pathlib.Path(plot_dir).glob("*.plot") if plot.stat().st_size > plot_size]
        log.debug(f'{plot_to_process[0].name}')
        return (plot_to_process[0].name)
    except IndexError:
        log.debug(f'{plot_dir} is Empty: No Plots to Process. Will check again soon!')
        return False

# If we have plots and we are NOT currently transferring another plot and
# we are NOT testing the script, then process the next plot if there is
# one to process.
def process_plot():
    log.debug('process_plot() Started')
    if not process_control('check_status', 0):
        plot_to_process = get_list_of_plots()
        if plot_to_process and not testing:
            process_control('set_status', 'start')
            plot_path = plot_dir + plot_to_process
            log.info(f'Processing Plot: {plot_path}')
            current_plotting_drive = read_config_data('plot_manager_config', 'plotting_drives', 'current_plotting_drive', False)
            log.debug(f'Current Plotting Drive is: {current_plotting_drive}')
            log.debug(f'Starting Copy of {plot_path}')
            start_time = timer()
            shutil.copy2(plot_path, current_plotting_drive)
            end_time = timer()
            if verify_plot_move(current_plotting_drive, plot_path, plot_to_process):
                log.info('Plot Sizes Match, we have a good plot move!')
                log.info(f'Total Elapsed Time: {end_time - start_time:.2f} seconds or {(end_time - start_time)/60:.2f} Minutes')
            else:
                log.debug('FAILURE - Plot sizes DO NOT Match - Exiting') # ToDo Do some notification here and then...?
                process_control('set_status', 'stop') #Set to stop so it will attempt to run again in the event we want to retry....
                main() # Try Again
            process_control('set_status', 'stop')
            os.remove(plot_path)
            log.info(f'Removing: {plot_path}')
        elif testing:
            log.debug('Testing Only - Nothing will be Done!')
        else:
            return
    else:
        return


def verify_plot_move(current_plotting_drive, plot_path, plot_to_process):
    log.debug('verify_plot_move() Started')
    log.debug (f'Verifing: {current_plotting_drive}/{plot_to_process}')
    original_plot_size = os.path.getsize(plot_path)
    copied_plot_size = os.path.getsize(current_plotting_drive + '/' + plot_to_process)
    log.debug(f'Original Plot Size Reported as: {original_plot_size}')
    log.debug(f'Copied Plot Size Reported as: {copied_plot_size}')
    if original_plot_size == copied_plot_size:
        return True
    else:
        log.debug(f'Plot Size Mismatch!')
        return False


def process_control(command, action):
    log.debug(f'process_control() called with [{command}] and [{action}]')
    if command == 'set_status':
        if action == "start":
            if os.path.isfile(status_file):
                log.debug(f'Status File: [{status_file}] already exists!')
                return
            else:
                os.open(status_file, os.O_CREAT)
        if action == "stop":
            if os.path.isfile(status_file):
                os.remove(status_file)
            else:
                log.debug(f'Status File: [{status_file}] does not exist!')
                return
    elif command == 'check_status':
        if os.path.isfile(status_file):
            log.debug(f'Checkfile Exists, We are currently Copying a Plot, Exiting')
            return True
        else:
            log.debug(f'Checkfile Does Not Exist!')
            return False
    else:
        return


def main():
    process_plot()

if __name__ == '__main__':
    main()
