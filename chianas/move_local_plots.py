#!/usr/bin/python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.92 (2021-06-07)"

# This script is part of my plot management set of tools. This
# script is used to move plots from one location to another on
# the same physical machine.
#
# If you are using a drive as a temp drive that falls within your
# scope of drives used for drive_manager.py, it is recommended that
# you offline that drive `./drive_manager -off drive43` to prevent
# drive_manager.py from placing plots on that drive.



import os
import logging
import configparser
from system_logging import setup_logging
import shutil
from timeit import default_timer as timer
from drive_manager import get_device_by_mountpoint
import subprocess
import pathlib
import psutil
from drivemanager_classes import DriveManager, config_file
chianas = DriveManager.read_configs()

script_path = pathlib.Path(__file__).parent.resolve()



# Are we testing?
testing = False
if testing:
    plot_dir = script_path.joinpath('test_plots/')
    plot_size = 10000000
    status_file = script_path.joinpath('local_transfer_job_running_testing')
    drive_check = script_path.joinpath('drive_stats.sh')
    drive_check_output = script_path.joinpath('drive_stats.io')
else:
    plot_dir = chianas.dst_dirs[0] # Where do you hold your plots before they are moved?
    plot_size = 108644374730  # Based on K32 plot size
    status_file = script_path.joinpath('local_transfer_job_running')
    drive_check = script_path.joinpath('drive_stats.sh')
    drive_check_output = script_path.joinpath('drive_stats.io')

def are_we_configured():
    if not chianas.configured:
        log.debug('We have not been configured! Please edit the main config file')
        log.debug(f'{config_file} and try again!')
        exit()
    else:
        pass


# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
level = logging._checkLevel(chianas.log_level)
log = logging.getLogger('move_local_plots.py')
log.setLevel(level)

# Let's Get Started

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
    if plot_dir == 'not_set':
        log.debug('You need to set the Directory where your local plots are located!')
        log.debug('Please set "plot_dir" to the correct mount point and try again!')
        log.debug(f'Edit {config_file} to update this setting.')
        exit()
    else:
        log.debug('process_plot() Started')
        if not process_control('check_status', 0):
            plot_to_process = get_list_of_plots()
            if plot_to_process and not testing:
                process_control('set_status', 'start')
                plot_path = plot_dir + '/' + plot_to_process
                log.info(f'Processing Plot: {plot_path}')
                log.debug(f'Current Internal Plotting Drive is: {chianas.current_internal_drive}')
                log.debug(f'Starting Copy of {plot_path} to {chianas.current_internal_drive}')
                start_time = timer()
                try:
                    shutil.copy2(plot_path, chianas.current_internal_drive)
                except:
                    log.debug(f'ERROR: There was a problem copying: {plot_dir}!')
                    exit()
                end_time = timer()
                if verify_plot_move(chianas.current_internal_drive, plot_path, plot_to_process):
                    log.info('Plot Sizes Match, we have a good plot move!')
                    log.info(f'Total Elapsed Time: {end_time - start_time:.2f} seconds or {(end_time - start_time)/60:.2f} Minutes')
                else:
                    log.debug('FAILURE - Plot sizes DO NOT Match')
                    process_control('set_status', 'stop')  #Set to stop so it will attempt to run again in the event we want to retry....
                    main() # Try Again - no need to do anything with the file, shutil.copy2 will overwrite an existing file.
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
        if os.path.isfile(status_file) and check_drive_activity():
            log.debug(f'Checkfile Exists and Disk I/O is present, We are currently Copying a Plot, Exiting')
            return True
        elif os.path.isfile(status_file) and not check_drive_activity():
            log.debug('WARNING! - Checkfile exists but there is no Disk I/O! Forcing Reset')
            os.remove(status_file)
            return False
        else:
            log.debug(f'Checkfile Does Not Exist!')
            return False
    else:
        return


def check_drive_activity():
    """
    Here we are checking drive activity on the drive we are moving plots to internally. If there is
    drive activity, then we are most likely moving a plot to that drive and do not want to 'double
    up' on moves.
    """
    log.debug('check_drive_activity() called')
    try:
        subprocess.call([drive_check])
    except subprocess.CalledProcessError as e:
        log.warning(e.output)
    with open(drive_check_output, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()
        log.debug(last_line)
    if (str.split(last_line)[1]) == 'Time':
        log.debug('No Drive Activity detected')
        return False
    else:
        return True

def main():
    are_we_configured()
    process_plot()

if __name__ == '__main__':
    main()
