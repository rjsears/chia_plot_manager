#!/usr/bin/python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.96 (2021-09-05)"

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
from system_logging import setup_logging
import shutil
from timeit import default_timer as timer
from drive_manager import notify, check_space_available, get_all_available_system_space, get_internal_plot_drive_to_use, get_drive_info
import subprocess
import pathlib
from drivemanager_classes import DriveManager, config_file, PlotManager
chianas = DriveManager.read_configs()
chiaplots = PlotManager.get_plot_info()



# Some Housekeeping
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

def are_we_configured(): #Check to see if we are configured and if there are any existing "move" errors:
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
        log.debug(f'This is the next plot to process: {plot_to_process[0].name}')
        return (plot_to_process[0].name)
    except IndexError:
        log.debug(f'{plot_dir} is Empty: No Plots to Process. Will check again soon!')
        return False


def update_move_local_plot():
    """
    This function just keeps our local plot moves off the same drive as our remote plot moves so
    we don't saturate a single drive with multiple inbound plots. Updated in 0.93.1 to support
    old style plot replacement as well as filling_local_drives_first.
    """
    log.debug("update_move_local_plot() Started")
    if not chianas.replace_non_pool_plots:  # If we are not replacing old plots with new portable plots, run the following code
        log.debug('Replace Plots has NOT been set in config, will build update_move_local_plot script for normal operation.')
        try:
            if chianas.current_internal_drive == get_internal_plot_drive_to_use()[0]:
                log.debug(f'Currently Configured Internal Plot Drive: {chianas.current_internal_drive}')
                log.debug(f'System Selected Internal Plot Drive:      {get_internal_plot_drive_to_use()[0]}')
                log.debug('Configured and Selected Drives Match!')
                log.debug(f'No changes necessary to Internal Plotting Drive')
                log.debug(
                    f'Plots left available on configured Internal plotting drive: {get_drive_info("space_free_plots_by_mountpoint", chianas.current_internal_drive)}')
            else:
                notify('Internal Plot Drive Updated', f'Internal Plot Drive Updated: Was: {chianas.current_internal_drive},  Now: {get_internal_plot_drive_to_use()[0]}')
                chianas.update_current_internal_drive(get_internal_plot_drive_to_use()[0])
                log.info(f'Updated Internal Plot Drive, Was: {chianas.current_internal_drive},  Now: {get_internal_plot_drive_to_use()[0]}')
        except TypeError:
            log.debug ('No Additional Drives found to be used as internal plot drives!')
            log.debug('Please add additional drive manually or via auto_drive.py and try again!')
    else:
        log.debug('Replace Plots Set, will build update_move_local_plot script for plot replacement!')
        log.debug('Checking to see if we need to fill empty drives first......')
        if chianas.fill_empty_drives_first:
            log.debug('fill_empty_drives_first flag is set. Checking for empty drive space.....')
            if (get_all_available_system_space("free")[1]) > chianas.empty_drives_low_water_mark:
                log.debug('Found Empty Drive Space!')
                log.debug(f'Low Water Mark: {chianas.empty_drives_low_water_mark} and we have {get_all_available_system_space("free")[1]} available')
                drive = get_internal_plot_drive_to_use()[0]
                try:
                    if chianas.current_internal_drive == drive:
                        log.debug(f'Currently Configured Internal Plot Drive: {chianas.current_internal_drive}')
                        log.debug(f'System Selected Internal Plot Drive:      {drive}')
                        log.debug('Configured and Selected Drives Match!')
                        log.debug(f'No changes necessary to Internal Plotting Drive')
                        log.debug(f'Plots left available on configured Internal plotting drive: {get_drive_info("space_free_plots_by_mountpoint", chianas.current_internal_drive)}')
                    else:
                        notify('Internal Plot Drive Updated', f'Internal Plot Drive Updated: Was: {chianas.current_internal_drive},  Now: {drive}')
                        chianas.update_current_internal_drive(drive)
                        log.info(f'Updated Internal Plot Drive, Was: {chianas.current_internal_drive},  Now: {drive}')
                except TypeError:
                    log.debug('No Additional Drives found to be used as internal plot drives!')
                    log.debug('We will now default to replacing old style plots!')
                    log.debug('Checking to see if we have any old plots to replace.....')
                    try:
                        if chiaplots.plots_to_replace:
                            log.debug(f'We found [{chiaplots.number_of_old_plots}] to replace. Continuing....')
                            drive = chiaplots.local_plot_drive  # Get the drive where we want to store local plots. This is reverse sorted from external plots coming in.
                            if chianas.current_internal_drive == drive:
                                log.debug(f'Currently Configured Internal Plot Drive: {chianas.current_internal_drive}')
                                log.debug(f'System Selected Internal Plot Drive:      {drive}')
                                log.debug('Configured and Selected Drives Match!')
                                log.debug(f'No changes necessary to Internal Plotting Drive')
                            else:
                                notify('Internal Plot Drive Updated',
                                       f'Internal Plot Drive Updated: Was: {chianas.current_internal_drive},  Now: {drive}')
                                chianas.update_current_internal_drive(drive)
                                log.info(
                                    f'Updated Internal Plot Drive, Was: {chianas.current_internal_drive},  Now: {drive}')
                        else:
                            log.debug('No old plots found, nothing left to do!')
                    except TypeError:
                        log.debug('No Additional Drives found that have old plots!')
            else:
                log.debug('fill_empty_drives_first flag is set, but we have no available free drive space....Defaulting to REPLACE PLOTS!')
                log.debug(f'Low Water Mark: {chianas.empty_drives_low_water_mark} and we have {get_all_available_system_space("free")[1]} available')
                log.debug('Checking to see if we have any old plots to replace.....')
                if chiaplots.plots_to_replace:
                    log.debug(f'We found [{chiaplots.number_of_old_plots}] to replace. Continuing....')
                    drive = chiaplots.local_plot_drive  # Get the drive where we want to store local plots. This is reverse sorted from external plots coming in.
                    try:
                        if chianas.current_internal_drive == drive:
                            log.debug(f'Currently Configured Internal Plot Drive: {chianas.current_internal_drive}')
                            log.debug(f'System Selected Internal Plot Drive:      {drive}')
                            log.debug('Configured and Selected Drives Match!')
                            log.debug(f'No changes necessary to Internal Plotting Drive')
                        else:
                            notify('Internal Plot Drive Updated', f'Internal Plot Drive Updated: Was: {chianas.current_internal_drive},  Now: {drive}')
                            chianas.update_current_internal_drive(drive)
                            log.info(f'Updated Internal Plot Drive, Was: {chianas.current_internal_drive},  Now: {drive}')
                    except TypeError:
                        log.debug('No Additional Drives found that have old plots!')
                else:
                    log.debug('No old plots found, nothing left to do!')
        else:
            log.debug('fill_empty_drives_first flag NOT set, continuing....')
            log.debug('Checking to see if we have any old plots to replace.....')
            try:
                if chiaplots.plots_to_replace:
                    log.debug(f'We found [{chiaplots.number_of_old_plots}] to replace. Continuing....')
                    drive = chiaplots.local_plot_drive # Get the drive where we want to store local plots. This is reverse sorted from external plots coming in.
                    if chianas.current_internal_drive == drive:
                        log.debug(f'Currently Configured Internal Plot Drive: {chianas.current_internal_drive}')
                        log.debug(f'System Selected Internal Plot Drive:      {drive}')
                        log.debug('Configured and Selected Drives Match!')
                        log.debug(f'No changes necessary to Internal Plotting Drive')
                    else:
                        notify('Internal Plot Drive Updated', f'Internal Plot Drive Updated: Was: {chianas.current_internal_drive},  Now: {drive}')
                        chianas.update_current_internal_drive(drive)
                        log.info(f'Updated Internal Plot Drive, Was: {chianas.current_internal_drive},  Now: {drive}')
                else:
                    log.debug('No old plots found, nothing left to do!')
            except TypeError:
                log.debug('No Additional Drives found that have old plots!')


# If we have plots and we are NOT currently transferring another plot and
# we are NOT testing the script, then process the next plot if there is
# one to process.
def process_plot():
    if plot_dir == 'not_set':
        log.debug('You need to set the Directory where your local plots are located!')
        log.debug('Please set "plot_dir" to the correct mount point and try again!')
        log.debug(f'Edit {config_file} to update this setting.')
        exit() # Nothing left to do, we're outta here!
    else:
        log.debug('process_plot() Started')
        if not process_control('check_status', 0):
            plot_to_process = get_list_of_plots()
            if plot_to_process and not testing:
                plot_source = plot_dir + '/' + plot_to_process
                if chianas.pools:
                    plot_destination = chianas.current_internal_drive + '/' + 'portable.' + plot_to_process
                else:
                    plot_destination = chianas.current_internal_drive + '/' + plot_to_process
                process_control('set_status', 'start')
                log.info(f'Processing Plot: {plot_source}')
                log.debug(f'Current Internal Plotting Drive is: {chianas.current_internal_drive}')
                if check_space_available(chianas.current_internal_drive):
                    log.debug(f'Starting Copy of {plot_source} to {plot_destination}')
                    start_time = timer()
                    try:
                        shutil.copy2(plot_source, plot_destination)
                    except:
                        log.debug(f'ERROR: There was a problem copying: {plot_dir}!')
                        chianas.set_local_move_error()
                        if not chianas.local_move_error_alert_sent:
                            notify('LOCAL MOVE ERROR', 'Local Move Error Encountered, You MUST manually reset error or no more local plots will get moved! Also reset Alert Sent to rearm this alert!')
                            log.debug('Local Move Error Alert Sent')
                            chianas.toggle_alert_sent('local_move_error_alert_sent')
                        else:
                            log.debug('Local Move Error Alert Already Sent - Not Resending')
                        exit()
                    end_time = timer()
                    if verify_plot_move(plot_source, plot_destination):
                        log.info('Plot Sizes Match, we have a good plot move!')
                        log.info(f'Total Elapsed Time: {end_time - start_time:.2f} seconds or {(end_time - start_time)/60:.2f} Minutes')
                    else:
                        log.debug('FAILURE - Plot sizes DO NOT Match')
                        process_control('set_status', 'stop')  #Set to stop so it will attempt to run again in the event we want to retry....
                        main() # Try Again - no need to do anything with the file, shutil.copy2 will overwrite an existing file.
                    process_control('set_status', 'stop')
                    os.remove(plot_source)
                    log.info(f'Removing: {plot_source}')
                else:
                    if chianas.replace_non_pool_plots: # Double verify we want to remove non-pool plots before doing anything.....
                        if chiaplots.plots_to_replace:
                            log.debug('No available plot space left, we need to remove an old plot...')
                            log.debug(f'Replace non-pool plots has been set....')
                            log.debug(f'We have {chiaplots.number_of_old_plots} plots to replace.')
                            log.debug(f'We will remove this plot first: {chiaplots.next_local_plot_to_replace}')
                            log.debug(f'The next inbound plot will be saved here: {chiaplots.local_plot_drive}')
                            log.debug(f'We currently have {chiaplots.number_of_portable_plots} portable plots on the system.')
                            os.remove(chiaplots.next_local_plot_to_replace)
                            if not os.path.isfile(chiaplots.next_local_plot_to_replace):
                                print('Old Plot has been removed, making room for new Portable Plot! Continuing..... ')
                                log.debug(f'Starting Copy of {plot_source} to {plot_destination}')
                                start_time = timer()
                                try:
                                    shutil.copy2(plot_source, plot_destination)
                                except:
                                    log.debug(f'ERROR: There was a problem copying: {plot_dir}!')
                                    chianas.set_local_move_error()
                                    if not chianas.local_move_error_alert_sent:
                                        notify('LOCAL MOVE ERROR',
                                               'Local Move Error Encountered, You MUST manually reset error or no more local plots will get moved! Also reset Alert Sent to rearm this alert!')
                                        log.debug('Local Move Error Alert Sent')
                                        chianas.toggle_alert_sent('local_move_error_alert_sent')
                                    else:
                                        log.debug('Local Move Error Alert Already Sent - Not Resending')
                                    exit()
                                end_time = timer()
                                if verify_plot_move(plot_source, plot_destination):
                                    log.info('Plot Sizes Match, we have a good plot move!')
                                    log.info(
                                        f'Total Elapsed Time: {end_time - start_time:.2f} seconds or {(end_time - start_time) / 60:.2f} Minutes')
                                else:
                                    log.debug('FAILURE - Plot sizes DO NOT Match')
                                    process_control('set_status',
                                                    'stop')  # Set to stop so it will attempt to run again in the event we want to retry....
                                    main()  # Try Again - no need to do anything with the file, shutil.copy2 will overwrite an existing file.
                                process_control('set_status', 'stop')
                                os.remove(plot_source)
                                log.info(f'Removing: {plot_source}')
                            else:
                                log.debug('ERROR: Plot Still Exists!! EXITING')
                                raise Exception
                        else:
                            log.debug('No more old plots to replace. Quitting!')
                            exit()
                    else:
                        log.debug('We are out of space and replace_non_pool_plots is NOT set, I cannot do anything more.....')
                        exit()
            elif testing:
                log.debug('Testing Only - Nothing will be Done!')
            else:
                return
        else:
            return


def verify_plot_move(plot_source, plot_destination):
    log.debug('verify_plot_move() Started')
    log.debug (f'Verifing: {plot_source}')
    original_plot_size = os.path.getsize(plot_source)
    copied_plot_size = os.path.getsize(plot_destination)
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
        drive_io = check_drive_activity()
        if os.path.isfile(status_file) and drive_io:
            log.debug(f'Checkfile Exists and Disk I/O is present, We are currently Copying a Plot, Exiting')
            return True
        elif os.path.isfile(status_file) and not drive_io:
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
    log.debug(f'Welcome to move_local_plots.py: Version {VERSION}')
    if chianas.local_move_error:
        log.debug('LOCAL MOVE ERROR Flag has been set, unable to continue!')
        log.debug('Determine nature of error and set local_move_error to false. Also')
        log.debug('reset Alert Sent notification to reenable this alert. These settings')
        log.debug(f'are located in your config file: {config_file}')
        if not chianas.local_move_error_alert_sent: #Verify that alert has been sent and send it if it has not
            notify('LOCAL MOVE ERROR',
                   'Local Move Error Encountered, You MUST manually reset error or no more local plots will get moved! Also reset Alert Sent to rearm this alert!')
            log.debug('Local Move Error Alert Sent')
            chianas.toggle_alert_sent('local_move_error_alert_sent')
        else:
            log.debug('Local Move Error Alert Already Sent - Not Resending')
        exit() # Nothing left to do, we're outta here!
    if chianas.local_plotter:
        are_we_configured()
        update_move_local_plot()
        process_plot()
    else:
        log.debug(f'Whoops! Local Plotting has not been configured in {config_file}. Quitting')
        exit()

if __name__ == '__main__':
    main()
