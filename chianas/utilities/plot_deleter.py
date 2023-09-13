#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-09-13)"

"""
plot_deleter.py

Script to check drive space and keep only enough space required for a new, inbound, compressed
plot. Deletes old plots one at a time. Due to the advent of compressed plots and newer, faster
plotters, I am now using Plow.py (https://github.com/lmacken/plow/tree/main) to move my plots
from my plotter to my various harvesters. My network is 100G between all machines with ultra
fast WD Black Nvme drives so I can complete a plot and move it in about 2.7 to 3 minutes. 
I obviously didn't want to wholesale delete plots so I came up with this script. It will 
delete a single plot on each drive in your directories_glob and keep doing so in order to keep
space available for new, compressed plots. 

It is important to note that on my plow configuration, all drives listed in this directory_glob 
are listed as destinations in plow.py. Otherwise,what would be the use :-)

If you are using this script in conjunction with the rest of my tools, set "integrated" to 
True and it will read out of your plot_manager.yaml configuration file, otherwise set to false
and set the necessary variables.

This script is intended to be used with CAUTION. I run this script once per minute from my 
root cron, it takes in a directory glob and checks to see if the directory in question is
an actual mountpoint, then checks available drive space and if the drive space is below 100G,
it deletes a single plot file matching the file_glob. In my case, when I replotted to portable
plots I renamed them all "portable.plot" so it is easy for me to glob this. If you have standard
plot naming convention you might try:

file_glob = "portable.plot-k32-202"

This should find any plot that was created in 2021, 2022 or 2023 as it's glob. 

When run in Test mode it will tell you what it plans on doing without actually deleting any files. 
Debug mode outputs additional information so you can run tests before implementing the script. 

My suggestion, once you think you are ready to run it, is to adjust your directory_glob to a single
directory that you know needs to have a plot deleted, run it in test mode and it should only print
out that it will delete a single plot and the name of the plot it will delete. Then turn off test 
mode and try it again. It should tell you it deleted that plot. Run it again (not in test mode)
and it should tell you that there is enough disk space available so nothing needs to be done.

Once you are happy, adjust your directory_glob back to match your system.

"""

import os
import glob
import subprocess
import sys

# Read from main config files and classes?
integrated = True

# Test mode (set to True to avoid actual file deletion)
test_mode = True

# Debug mode (set to True to enable debug output)
debug = True


if integrated:
    from drivemanager_classes import DriveManager, PlotManager, config_file
    chianas = DriveManager.read_configs()
    chiaplots = PlotManager.get_plot_info()
    directory_glob = chianas.directory_glob
    compression_size = chianas.compression_in_use
    hostname = chianas.hostname
    if debug:
        print('Integrated Configuration')
else:
    # Set these variables if you are NOT using the integrated configuration
    # of plot and drive manager.
    # Define the directory glob pattern
    directory_glob = "/mnt/enclosure[0-9]/*/column[0-9]/*/"
    # Set the compression size (adjust as needed)
    compression_size = 'c05'
    # Where do we send notifications?
    email_address = 'your_email_address@gmail.com'
    # Who are we?
    hostname = 'chianas01'
    if debug:
        print('Stand Alone Configuration')



# Define our file glob. This MUST match the plots you want to DELETE!!
# BE VERY CAREFUL HERE!!!
file_glob = "portable.plot-k32-*"

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

# Check if the compression size is valid, exit if not.
if compression_size not in compression_sizes:
    print(f"Invalid compression size: {compression_size}")
    sys.exit(1)

# How much drive space do we want to have available?
min_drive_space_threshold = (compression_sizes[compression_size] + plot_size_buffer) * 1024  # Convert to MB

# Test output to make sure drive space is set correctly....
if test_mode:
    print(f"Test mode: Requires at least {min_drive_space_threshold:.2f} MB of available drive space.")

def send_email(recipient, subject, body) -> None:
    """
    Part of our notification system.
    Setup to send email via the builtin linux mail command.
    Your local system **must** be configured already to send mail or this will fail.
    """
    try:
        subprocess.run(['mail', '-s', subject, recipient], input=body, encoding='utf-8')
        if debug:
            print(f"Email Notification Sent: Subject: {subject}, Recipient: {recipient}, Message: {body}")
    except subprocess.CalledProcessError as e:
        print(f'send_email error: {e}')
    except Exception as e:
        print(f'send_email: Unknown Error! Email not sent.')

def notify(title, message) -> None:
    """ Notify system for email only """
    if debug:
        print(f'notify() called with Title: {title} and Message: {message}')
    if integrated:
        if chianas.notifications:
            if chianas.email:
                for emails in chianas.emails:
                    send_email(emails, title, message)
        else:
            pass
    else:
        send_email(email_address, title, message)

def delete_portable_plots(directory):
    # Check if the directory is a mount point, skip if not!
    if not os.path.ismount(directory):
        if debug:
            print(f"Skipping {directory}: Not a mount point")
        return

    # Get a list of portable plot files in the directory
    portable_plots = glob.glob(os.path.join(directory, file_glob))

    for plot_file in portable_plots:
        try:
            drive = os.path.abspath(directory)
            available_space = (os.statvfs(drive).f_frsize * os.statvfs(drive).f_bavail) / (1024 * 1024)

            if available_space < min_drive_space_threshold:
                if not test_mode:
                    os.remove(plot_file)
                    print(f"Deleted {plot_file}")
                else:
                    print(f"Test mode: Would delete {plot_file}")
                break  # Exit after deleting one file
            elif debug:
                print(f"Skipping {plot_file}: Sufficient drive space available ({available_space:.2f} MB)")
        except Exception as e:
            print(f"Error processing {plot_file}: {e}")


if __name__ == "__main__":
    if test_mode:
        notify(f'Test from {hostname}', f'Testing the notify system on {hostname}')

    portable_plots_exist = False

    directories = glob.glob(directory_glob)
    portable_plots_deleted = 0

    for directory in directories:
        if debug:
            print(f"Processing directory: {directory}")
        delete_portable_plots(directory)
        portable_plots_deleted += 1

        # Check if there are any portable plots left
        portable_plots_exist = any(glob.glob(os.path.join(directory, file_glob)) for directory in directories)

    if not portable_plots_exist:
        message = f'All portable plots have been deleted from {portable_plots_deleted} mountpoints on {hostname}.'
        notify('No more Portable Plots', message)
