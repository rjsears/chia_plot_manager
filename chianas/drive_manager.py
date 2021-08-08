#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.94 (2021-08-08)"

"""
NOTE NOTE NOTE NOTE NOTE NOTE NOTE
This script is designed to run with a particular directory structure:

/mnt
     ├── enclosure0
     │   ├── front
     │   │   ├── column0
     │   │   │   ├── drive2
     │   │   │   ├── drive3
     │   │   │   ├── drive4
     │   │   │   └── drive5
     ├── enclosure1
     │   ├── rear
     │   │   ├── column0
     │   │   │   ├── drive6
     │   │   │   ├── drive7
     
     
Because of this, if you have a different directory structure there are
changes that you will to make for this to work for you. For example
if you have mountpoints that start with `/mnt/server0` instead of 
`/mnt/enclosure0`, you will need to look for each instance of 
`/mnt/enclosure` in this script and replace it with `/mnt/server0`
in order for things to work properly. 

In addition, you would also need to modify get_path_info_by_mountpoint()
so that it returns the correct values as well. Eventually I will attempt
to figure this out on the fly, but for right now this needs to be done
to get the script working for you.



Simple python script that helps to move my chia plots from my plotter to
my nas. I wanted to use netcat as it was much faster on my 10GBe link than
rsync and the servers are secure so I wrote this script to manage that
move process. It will get better with time as I add in error checking and
other things like notifications and stuff.


 Updates
   v0.94 2021-08-08
   - Added ability to search for any UUID across any harvester and it will return 
     the harvester the UUID is located on as well as the mountpoint where it is
     assigned. Eventually will be used for automated moving of drives between
     systems.

   - Added ability to support pool plots. Now is you tell the system you are doing
     pool plots, it will prepend the name of every  plot with "portable." so that
     we can manage those plots.

   - Added ability both locally (if your harvester is a local plotter) or remotely
     (vi a remote plotter) to replace your old style plots on a one-by-one basis
     with new portable plots. Minimized number of plots that have to be deleted to
     convert to new plots. Has ability to fill empty drives first with new plots
     before deleting old plots based on a specific high water mark. When using your
     harvester as both a local plotter and harvester, will move locla plots to a
     different drive than where inbound external plots are being saved to help with
     drive bus contention.

   - Updated the harvester export functions to support old plot replacement and 
     reporting.
     
   - Updated local plot reports to report on plot replacement stats (old plots vs new
     plots during the plot replacement process. Still need to work on farm reports.
       
   V0.92 2021-05-31
   - Converted to a central YAML config file
 
   V0.9 2021-05-27
   - Major changes to code to auto detect installation path and try
     to make intelligent decisions as a result. Also updated the
     directory structures. 
    
   - Added host checking for multi-nas setup and configuration. If a 
     host is not available the farm report will still run after letting
     you know that one of your NASs is offline. 
     
   - Added additional error checking.
    
 
   V0.8 2021-05-24
   - Added Multi-Harvester Reporting. Once configured across all harvesters
     you can run a farm report from any of your harvesters. Outputs all of 
     your harvester data to a json file which is then grabbed when you run 
     the report. Utilizes Paramiko to manage the sftp connection between 
     the harvesters. If you want to utilize this, please be sure to read
     the instructions below.
     
   - Added additional command line utility to drive_manager.py:
        * -fr or --farm_report    Quick total Farm Report outputs to screen
   
 
   V0.7 2021-05-17
   - Minor Fixes

   V0.6 2021-04-22
   - Check Chia logs and report actual plots being farmed (per Chia) and
     total amount of drive space in use (also per Chia). It is not
     uncommon for the total number of plots on your system to be slightly
     different that what `drive_manager.py` reports due to plot moves, etc
     but if there is a large difference, you should check your logs for
     signs of other issues.

   V0.5 2021-04-22
   - Updated to support local plot management via `move_local_plots.py`

   V0.4 2021-04-13
   - Added ability to "offline" a drive for maintenance. Before, the script would
     select the very first available drive (based on drive number: drive0, drive1)
     for plot storage. I ran into a problem when one of my drives kicked out a
     smartctl error and I needed to move the plots off of it before it failed. As
     soon as I started to move them, drive_manager.py started to fill the drive
     back up. So now you can offline and drive_manager will not use it until
     you online it again. You still need to go into your chia harvester config
     and remove the drive from there.


   V0.3 2021-04-04
   - Added multiple command line utilities to drive_manager.py including:
        * -dr or --drive_report    Immediately runs the Daily Report and sends email (if configured)
        * -ct or --check_temps     Checks the temperatures of all configured plot drives
        * -pr or --plot_report     Quick plot report like email report but to the screen
        * -ud or --update_daily    Designed to be called from cron, updates daily plot stats (speed, etc)
                                   Be careful if using it from the command line, it resets your stats. This
                                   should be run once per day from a cronjob.

   - Added plot time information to the daily email report including:
        * Total Plots last 24 hours
        * Average Plots per Hour (last 24 hours)
        * Average Plotting Speed (last 24 hours)

   V0.2 2021-30-23
   - Moved system logging types to plot_manager_config and updated necessary functions.
   - Added per_plot system notification function (send_new_plot_notification())
   - Updated read_config_data() to support ConfigParser boolean returns
   - Updated necessary functions for read_config_data() change
"""

import os
import sys
import subprocess
import shutil
import psutil
from pySMART import Device, DeviceList  # CAUTION - DO NOT use PyPI version, use https://github.com/truenas/py-SMART
from psutil._common import bytes2human
import logging
from system_logging import setup_logging
from pushbullet import Pushbullet, errors as pb_errors
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from jinja2 import Environment, select_autoescape, FileSystemLoader
from datetime import datetime
import argparse
import textwrap
from natsort import natsorted
import mmap
import json
import paramiko
import pathlib
from drivemanager_classes import DriveManager, PlotManager, config_file, config_file_update
chianas = DriveManager.read_configs()
chiaplots = PlotManager.get_plot_info()

script_path = pathlib.Path(__file__).parent.resolve()


# Define some colors for our help message
red='\033[0;31m'
yellow='\033[0;33m'
green='\033[0;32m'
white='\033[0;37m'
blue='\033[0;34m'
nc='\033[0m'


# Let's do some housekeeping
plot_size_k = 108995911228
plot_size_g = 101.3623551
receive_script = script_path.joinpath('receive_plot.sh')
replace_plots_receive_script = script_path.joinpath('replace_plots_receive_plot.sh')

# Date and Time Stuff
current_military_time = datetime.now().strftime('%Y%m%d%H%M%S')

# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
level = logging._checkLevel(chianas.log_level)
log = logging.getLogger(__name__)
log.setLevel(level)


def are_we_configured():
    if not chianas.configured:
        log.debug('We have not been configured! Please edit the main config file')
        log.debug(f'{config_file} and try again!')
        exit()
    elif chianas.chia_log_file == 'net_set':
        log.debug('Your chia debug logfile path has not been set.')
        log.debug(f'Please edit {config_file} and put the correct path in for your chia log file.')
        exit()
    else:
        pass


"""
If you have multiple harvesters, load their host names in the config file. Make
sure each server can be reached by ssh via their hostname and make sure you have
configured passwordless ssh between them first. Do not include this harvester in
the list. This is only if you want to run the -hr or --harvester_report to report on
all of your harvesters.

It is important that this server can reach your remote harvesters by using the
exact names you use and that it can be reached vi ssh without a password.
Remote reporting won't work otherwise.

Finally if you want to run remote harvester reports, set to True in the YAML
config file.
"""
local_export_file = script_path.joinpath(f'export/{chianas.hostname}_export.json')
uuid_export_file = script_path.joinpath(f'export/{chianas.hostname}_uuid_export.json')
global_uuid_export_file = script_path.joinpath(f'export/{chianas.hostname}_global_uuid_export.json')



def remote_harvester_report():
    if not chianas.remote_harvester_reports:
        log.debug('Remote Harvester Reports are NOT Configured')
    else:
        remote_harvesters = check_remote_harvesters()
        if chianas.hostname in remote_harvesters:
            print(f'\n{red}CAUTION{nc}: Your local harvester {yellow}{chianas.hostname}{nc} is listed as one of your remote harvesters!')
            print(f'{red}CAUTION{nc}: Unable to Run Report. Please Correct!\n')
            exit()
        else:
            servers = []
            with open(local_export_file, 'r') as local_host:
                harvester = json.loads(local_host.read())
                servers.append(harvester)
            for harvester in remote_harvesters:
                remote_export_file = (script_path.joinpath(f'export/{harvester}_export.json').as_posix())
                get_remote_exports(harvester, remote_export_file)
                with open(remote_export_file, 'r') as remote_host:
                    harvester = json.loads(remote_host.read())
                    servers.append(harvester)
            totals = {'total_plots': 0, 'total_plots_farming': 0, 'total_tib_farming': 0, 'total_plot_drives': 0,
                      'total_plots_until_full': 0, 'max_plots_when_full': 0, 'plots_last_day': 0, 'avg_plots_per_hour': 0,
                      'avg_plotting_speed': 0, 'approx_days_to_fill_drives': 0}
            for e in servers:
                totals["total_plots"] += e["total_plots"]
                totals["total_plots_farming"] += e["total_plots_farming"]
                totals["total_tib_farming"] += e["total_tib_farming"]
                totals["total_plot_drives"] += e["total_plot_drives"]
                totals["total_plots_until_full"] += e["total_plots_until_full"]
                totals["max_plots_when_full"] += e["max_plots_when_full"]
                totals["plots_last_day"] += e["plots_last_day"]
                totals["avg_plots_per_hour"] += e["avg_plots_per_hour"]
                totals["avg_plotting_speed"] += e["avg_plotting_speed"]
                totals["approx_days_to_fill_drives"] += e["approx_days_to_fill_drives"]
            return totals, servers, remote_harvesters


def uuid_search(uuid):
    """
    Searched all available remote harvesters for a specific UUID and returns
    the server and mountpoint if found. Because of the code, remote harvester
    reports must be configured and working for this to work.
    """
    if not chianas.remote_harvester_reports:
        log.debug('Remote Harvester Reports are NOT Configured')
    else:
        remote_harvesters = check_remote_harvesters()
        if chianas.hostname in remote_harvesters:
            print(f'\n{red}CAUTION{nc}: Your local harvester {yellow}{chianas.hostname}{nc} is listed as one of your remote harvesters!')
            print(f'{red}CAUTION{nc}: Unable to Run UUID Search. Please Correct!\n')
            exit()
        else:
            servers = []
            master_uuid = dict()
            with open(uuid_export_file, 'r') as local_host:
                harvester = json.loads(local_host.read())
                servers.append(harvester)
            for harvester in remote_harvesters:
                remote_export_file = (script_path.joinpath(f'export/{harvester}_uuid_export.json').as_posix())
                get_remote_exports(harvester, remote_export_file)
                with open(remote_export_file, 'r') as remote_host:
                    harvester = json.loads(remote_host.read())
                    servers.append(harvester)
                    master_uuid.update(harvester)
            with open(global_uuid_export_file, 'w') as global_export_file:
                global_export_file.write(json.dumps(master_uuid))
            with open(global_uuid_export_file, "r") as f:
                uuid_search = json.loads(f.read())
            try:
                return uuid_search[uuid]
            except KeyError:
                return False

def check_remote_harvesters():
    """
    Make sure our harvesters are online!
    """
    harvesters_check = {}
    for harvester in chianas.remote_harvesters:
        harvesters_check[harvester] = host_check(harvester)
    dead_hosts = [host for host, alive in harvesters_check.items() if not alive]
    if dead_hosts != []:
        print(f'\n           {red}WARNING{nc}: {yellow}{dead_hosts}{nc} is OFFLINE!{nc}')
    alive_hosts = [host for host, alive in harvesters_check.items() if alive]
    return(alive_hosts)


def host_check(host):
    """
    Check to see if a specific host is alive
    """
    proc = subprocess.run(
        ['ping', '-W1', '-q', '-c', '2', host],
        stdout=subprocess.DEVNULL)
    return proc.returncode == 0


def get_remote_exports(host, remote_export_file):
    """
    Utilize Paramiko to grab our harvester exports
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host)
        sftp = ssh.open_sftp()
        sftp.get(remote_export_file, remote_export_file)
    finally:
        ssh.close()


def farm_wide_space_report():
    """
    This prints out our Farm Wide Report
    """
    if chianas.remote_harvester_reports:
        remote_harvester_reports = (remote_harvester_report())
        totals = remote_harvester_reports[0]
        days_until_full = (totals.get("total_plots_until_full") / totals.get("plots_last_day"))
        harvesters = [chianas.hostname, *remote_harvester_reports[2]]
        print('')
        print(f'{blue}############################################################{nc}')
        print(f'{blue}################### {green}Farm Wide Plot Report{blue} ##################{nc}' )
        print(f'{blue}############################################################{nc}')
        print(f'Harvesters: {yellow}{harvesters}{nc}')
        print (f'Total Number of Plots on {green}Farm{nc}:                          {yellow}{totals.get("total_plots")}{nc}')
        print (f'Total Number of Plots {green}Chia{nc} is Farming:                  {yellow}{totals.get("total_plots_farming")}{nc}')
        print (f'Total Amount of Drive Space (TiB) {green}Chia{nc} is Farming:       {yellow}{totals.get("total_tib_farming")}{nc}')
        print (f'Total Number of Systemwide Plots Drives:                 {yellow}{totals.get("total_plot_drives")}{nc}')
        print (f'Total Number of k32 Plots until full:                   {yellow}{totals.get("total_plots_until_full")}{nc}')
        print (f'Maximum # of plots when full:                          {yellow}{totals.get("max_plots_when_full")}{nc}')
        print (f'Plots completed in the last 24 Hours:                    {yellow}{totals.get("plots_last_day")}{nc}')
        print (f'Average Plots per Hour:                                  {yellow}{round(totals.get("avg_plots_per_hour"))}{nc}')
        print (f'Average Plotting Speed Last 24 Hours (TiB/Day):           {yellow}{round(totals.get("avg_plotting_speed"))}{nc}')
        print(f'Appx Number of Days to fill all current plot drives:     {yellow} {round(days_until_full)}{nc}')
        print(f'{blue}############################################################{nc}')
        individual_harvester_report(remote_harvester_reports[1], remote_harvester_reports[2])
        print()
    else:
        print(f'\n{red}ERROR{nc}: {yellow}Farm Wide Reports Have Not Been Configured. Please Configure and Try Again!{nc}\n')

def individual_harvester_report(servers, remote_harvesters):
    for server in servers:
        print(f'{blue}################ {green}{server["server"]} Harvester Report{blue} ################{nc}')
        print(f'{blue}############################################################{nc}')
        print(f'Total number of plots on {green}{server["server"]}{nc}:                    {yellow}{server["total_plots"]}{nc}')
        print(f'Plots completed in the last 24 hours:                  {yellow}{server["plots_last_day"]}{nc}')
        print(f'Average Plotting Speed Last 24 Hours (Tib/Day):        {yellow}{server["avg_plotting_speed"]}{nc}')
        print(f'Appx # of Days to fill all drives on this harvester:   {yellow}{server["approx_days_to_fill_drives"]}{nc}')
        print(f'{blue}############################################################{nc}')


def uuid_report(uuid):
    print()
    print(f'Please wait while we search all harvesters for {green}{uuid}{nc}')
    uuid_search_results = uuid_search(uuid)
    if not uuid_search_results:
        print()
        print(f'{blue}############################################################{nc}')
        print(f'{blue}################### {green}UUID Search Report{blue} #####################{nc}')
        print(f'{blue}############################################################{nc}')
        print(f'UUID:          {green}{uuid}{nc}')
        print(f'Status:        {red}NOT LOCATED{nc}')
        print(f'{blue}############################################################{nc}')
        print()
        print()
    else:
        server = uuid_search_results[0]
        mountpoint = uuid_search_results[1]
        print()
        print(f'{blue}############################################################{nc}')
        print(f'{blue}################### {green}UUID Search Report{blue} #####################{nc}')
        print(f'{blue}############################################################{nc}')
        print(f'UUID:          {green}{uuid}{nc}')
        print(f'Status:        {yellow}LOCATED{nc}')
        print(f'Harvester:     {yellow}{server}{nc}')
        print(f'Mount Point:   {yellow}{mountpoint}{nc}')
        print(f'{blue}############################################################{nc}')
        print()
        print()

# Define our help message
class RawFormatter(argparse.HelpFormatter):
    def _fill_text(self, text, width, indent):
        return "\n".join(
            [textwrap.fill(line, width) for line in textwrap.indent(textwrap.dedent(text), indent).splitlines()])

program_descripton = f'''
                {red}******** {green}ChiaNAS Drive Manager{nc} - {blue}{VERSION}{red} ********{nc}
    Running drive_manager.py with no arguments causes drive_manager to run in '{yellow}normal{nc}' mode.
    In this mode {green}drive_manager{nc} will check the drive utilization and update which drive your
    Chia plots will be sent to when they arrive from your plotter. This is generally called
    from a cronjob on a regular basis. Please read the full information about how it works
    on my github page.

    
    There are several commandline switches you can use to get immediate reports and feedback:
    

    {green}-dr {nc}or{green} --drive_report{nc}       {blue}Runs the Daily ChiaNAS Report (if configured), and emails
                                it to you. This can be called from a crontab job as well.{nc}
    
    {green}-ct {nc}or{green} --check_temps{blue}        This will query all of your hard drives using {yellow}smartctl{blue} and
                                return a list of drive temperatures to you.
                                
    {green}-pr {nc}or{green} --plot_report{blue}        This queries the NAS and returns a report letting you know 
                                how many plots are currently on the system and how many more
                                you can add based on the current drive configuration. It also
                                includes plotting speed information for the last 24 hours.{nc}
    
    {green}-fr {nc}or{green} --farm_report{blue}        This queries your farm and returns a report letting you know 
                                how many plots are currently in the farm and how many more
                                you can add based on the current drive configuration. It also
                                includes plotting speed information for the last 24 hours farm wide.
                                **{red}NOTE{nc}{blue}: Must be configured! {nc}
    
    {green}-ud {nc}or{green} --update_daily{blue}       This updates the total number of plots the system has created
                                over the past 24 hours. Use with {nc}CAUTION!{blue}. This {nc}should{blue} be ran
                                from crontab once every 24 hours only! It updates the total
                                from the last time is was run until now, hence why you should
                                only run this once per 24 hours.{nc}
    
    {green}-rp {nc}or{green} --replace_plot{blue}       This is {yellow}GENERALLY{blue} run remotely by your plotter when it detects
                                that you are configured for plot replacement, ie - you have a 
                                lot of old plots and you are replacing them with new portable 
                                style plots. Use {red}CAUTION{blue} running it manually! It will {nc}DELETE{blue}
                                an old plot every time it is run.{nc}
    
    {green}-uuid {nc}or{green} --check_uuid{blue}       This checks all remote harvesters to see if the requested UUID is 
                                present and mounted. Returns the server and mountpoint if found.{nc}
    
    {green}-off {nc}or{green} --offline_hdd{blue}       This takes a drive as it's input (for example {yellow} drive6{blue}) and
                                "{red}offlines{blue}" it so that no more plots will get written to it. 
                                You must {green}--on{blue} or {green}--online_hdd{blue} the drive for it to be used
                                again. Useful if the drive is failing and needs to be replaced.
                                You cannot "{red}offline{blue} a drive that is not mounted.
    
    {green}-on {nc}or{green} --online_hdd{blue}         This takes a drive as it's input (for example {yellow} drive6{blue}) and
                                "{green}onlines{blue}" it so that plots will get written to it. This option
                                will be {nc}UNAVAILABLE{blue} if there are no drives that have been 
                                offlined!{nc}
                                

    USAGE:
    '''

def init_argparser():
    parser = argparse.ArgumentParser(description=program_descripton, formatter_class=RawFormatter)
    parser.add_argument('-v', '--version', action='version', version=f'{parser.prog} {VERSION}')
    parser.add_argument('-dr', '--daily_report', action='store_true', help='Run the ChiaPlot Daily Email Report and exit')
    parser.add_argument('-ct', '--check_temps', action='store_true', help='Return a list of drives and their temperatures and exit')
    parser.add_argument('-pr', '--plot_report', action='store_true', help='Return the total # of plots on the system and total you can add and exit')
    parser.add_argument('-fr', '--farm_report', action='store_true',help='Return the total # of plots on your entire farm and total you can add and exit')
    parser.add_argument('-ud', '--update_daily', action='store_true', help=f'Updates 24 hour plot count. {red}USE WITH CAUTION, USE WITH CRONTAB{nc}')
    parser.add_argument('-rp', '--replace_plot', action='store_true',
                        help=f'Remove a single old Plot. {red}USE WITH CAUTION, READ DOCS FIRST{nc}. Generally called remotely by Plotter!')
    parser.add_argument('-uuid', '--check_uuid', action='store', help=f'Check to see is a specific {green}UUID{nc} is mounted on any harvester')
    parser.add_argument('-off', '--offline_hdd', action='store', help=f'Offline a specific drive. Use drive number: {green}drive6{nc}')
    if chianas.offlined_drives != []:
        parser.add_argument('-on', '--online_hdd', action='store', help=f'Online a specific drive.' , choices=chianas.offlined_drives)
    return parser


def get_offlined_drives():
    """
    Get a list of all of our offlined drives.
    """
    if chianas.offlined_drives != None:
        return chianas.offlined_drives
    else:
        return False


def get_drive_info(action, drive):
    """
    This allows us to query specific information about our drives including
    temperatures, smart assessments, and space available to use for plots.
    It allows us to simply hand it a drive number (drive0, drive22, etc)
    and will present us with the data back. This utilizes pySMART, but
    a word of caution, use the TrueNAS versions linked to above, the PiPy
    version has a bug!
    """
    if action == 'device':
        plot_drives = get_list_of_plot_drives()
        device = [hd for hd in plot_drives
                  if hd[0] == (get_mountpoint_by_drive_number(drive)[0])]
        if device != []:
            device = [hd for hd in plot_drives
                      if hd[0] == (get_mountpoint_by_drive_number(drive)[0])]
        return device[0][1]
    if action == 'temperature':
        return Device(get_device_info_by_drive_number(drive)[0][1]).temperature
    if action == 'capacity':
        return Device(get_device_info_by_drive_number(drive)[0][1]).capacity
    if action == 'health':
        return Device(get_device_info_by_drive_number(drive)[0][1]).assessment
    if action == 'name':
        return Device(get_device_info_by_drive_number(drive)[0][1]).name
    if action == 'serial':
        return Device(get_device_info_by_drive_number(drive)[0][1]).serial
    if action == 'space_total':
        return int(bytesto(shutil.disk_usage(get_device_info_by_drive_number(drive)[0][0])[0], 'g'))
    if action == 'space_used':
        return int(bytesto(shutil.disk_usage(get_device_info_by_drive_number(drive)[0][0])[1], 'g'))
    if action == 'space_free':
        return int(bytesto(shutil.disk_usage(get_device_info_by_drive_number(drive)[0][0])[2], 'g'))
    if action == 'space_free_plots':
        return int(bytesto(shutil.disk_usage(get_device_info_by_drive_number(drive)[0][0])[2], 'g') / plot_size_g)
    if action == 'space_free_plots_by_mountpoint':
        return int(bytesto(shutil.disk_usage(drive)[2], 'g') / plot_size_g)
    if action == 'total_current_plots':
        return int(bytesto(shutil.disk_usage(get_mountpoint_by_drive_number(drive)[0])[1], 'g') / plot_size_g)
    if action == 'total_current_plots_by_mountpoint':
        return int(bytesto(shutil.disk_usage(drive)[1], 'g') / plot_size_g)



def dev_test(drive):
    bytes_available = shutil.disk_usage(drive).free
    gb_available = bytes_available /  1024 / 1024 / 1024
    return gb_available / 102
    #return shutil.disk_usage(drive).free
    #return Device(drive)

def get_drive_by_mountpoint(mountpoint):
    """
    This accepts a mountpoint ('/mnt/enclosure0/rear/column2/drive32') and returns the drive:
    drive32
    """
    return (mountpoint.split("/")[5])

def get_mountpoint_by_drive_number(drive):
    """
    This accepts a drive number (drive0) and returns the device assignment: /dev/sda1 and mountpoint:
    /mnt/enclosure0/front/column0/drive0
    """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/enclosure') and p.mountpoint.endswith(drive):
            return [(p.mountpoint)]

def get_mountpoint_by_drive_number_enclosure(enclosure, drive):
    """
    This accepts an enclosure (enclosure0) and  drive number (drive0) and returns the device assignment: /dev/sda1 and mountpoint:
    /mnt/enclosure0/front/column0/drive0
    """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/' + enclosure) and p.mountpoint.endswith(drive):
            return [(p.mountpoint)]


def get_device_info_by_drive_number(drive):
    """
    This accepts a drive number (drive0) and returns the device assignment: /dev/sda1 and mountpoint
    """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/enclosure') and p.mountpoint.endswith(drive):
            return [(p.mountpoint, p.device)]


def get_device_info_by_drive_number_enclosure(enclosure, drive):
    """
    This accepts an enclosure (enclosure2) and drive number (drive0) and returns the device assignment: /dev/sda1 and mountpoint
    """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/'+ enclosure) and p.mountpoint.endswith(drive):
            return [(p.mountpoint, p.device)]


def get_device_by_mountpoint(mountpoint):
    """
        This accepts a mountpoint and returns the device assignment: /dev/sda1 and mountpoint
        """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith(mountpoint):
            return [(p.mountpoint, p.device)]
        else:
            if p.device.startswith('/dev/nv') and p.mountpoint.startswith(mountpoint):
                return [(p.mountpoint, p.device)]

def get_mountpoint_by_device(device):
    """
        This accepts a mountpoint and returns the device assignment: /dev/sda1 and mountpoint
        """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith(device):
            return [(p.mountpoint, p.device)]

def get_list_of_plot_drives():
    """
    Return list of tuples of all available plot drives on the system and the device assignment
    [('/mnt/enclosure0/front/column0/drive3', '/dev/sde1')]
    """
    partitions = psutil.disk_partitions(all=False)
    mountpoint = []
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/enclosure'):
            mountpoint.append((p.mountpoint, p.device, p.fstype))
    return mountpoint

def get_path_info_by_mountpoint(mountpoint, info):
    """
    This accepts a mountpoint ('/mnt/enclosure0/rear/column2/drive32') and returns the enclosure:
    enclosure1. This will need to be changed based on your current directory configuration. For
    example if your mount point looked like this: "/server01/top/row1/drive4" this would look like:

    if info == 'server':
        return (mountpoint.split("/")[2])
    elif info == 'topbottom':
        return (mountpoint.split("/")[3])
    elif info == 'row':
        return (mountpoint.split("/")[4])
    else:
        return (f'/{mountpoint.split("/")[1]}')
    """
    if info == 'enclosure':
        return (mountpoint.split("/")[2])
    elif info == 'frontrear':
        return (mountpoint.split("/")[3])
    elif info == 'column':
        return (mountpoint.split("/")[4])
    else:
        return (f'/{mountpoint.split("/")[1]}')


# Thank you: https://gist.github.com/shawnbutts/3906915
def bytesto(bytes, to, bsize=1024):
    a = {'k': 1, 'm': 2, 'g': 3, 't': 4, 'p': 5, 'e': 6}
    r = float(bytes)
    return bytes / (bsize ** a[to])


def get_all_available_system_space(type):
    """
    Return Systems drive space information (total, used and free) based on plot_size
    """
    partitions = psutil.disk_partitions(all=False)
    drive_space_available = []
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/enclosure'):
            if type == 'all':
                drive_space_available.append((p.mountpoint, shutil.disk_usage(p.mountpoint)))
            if type == 'total':
                drive_space_available.append(int(bytesto(shutil.disk_usage(p.mountpoint)[0], 'g') / plot_size_g))
            if type == 'used':
                drive_space_available.append(int(bytesto(shutil.disk_usage(p.mountpoint)[1], 'g') / plot_size_g))
            if type == 'free':
                drive_space_available.append(int(bytesto(shutil.disk_usage(p.mountpoint)[2], 'g') / plot_size_g))
    return len(drive_space_available), sum(drive_space_available)


def get_plot_drive_with_available_space():
    """
    This looks at all available plot drives that start with /dev/sd and include
    /mnt/enclosure in the mount path (this covers all of my plot drives), it then
    looks for any drive that has enough space for at least one plot (k32), sorts
    that list based on the /dev/sdx sorting and then returns the mountpoint and
    the device of each drive.
    ======> Currently Unused <======
    """
    available_drives = []
    for part in psutil.disk_partitions(all=False):
        if part.device.startswith('/dev/sd') and part.mountpoint.startswith('/mnt/enclosure') and get_drive_info(
                'space_free_plots_by_mountpoint', part.mountpoint) >= 1:
            available_drives.append((part.mountpoint, part.device))
    return (sorted(available_drives, key=lambda x: x[1]))


def get_plot_drive_to_use():
    """
        This looks at all available plot drives that start with /dev/sd and include
        /mnt/enclosure in the mount path (this covers all of my plot drives), it then
        looks for any drive that has enough space for at least one plot (k32), sorts
        that list based on the drive# sorting (drive0, drive10, etc) sorting and then
        returns the mountpoint of the device we want to use. Basically the same as above
        but simply returns the 'next' available drive we want to use. This also checks
         to make sure the drive selected has not been marked as "offline".
        When you run out of drives, these scripts will fail.
        """
    available_drives = []
    try:
        for part in psutil.disk_partitions(all=False):
            if part.device.startswith('/dev/sd') \
                    and part.mountpoint.startswith('/mnt/enclosure') \
                    and get_drive_info('space_free_plots_by_mountpoint', part.mountpoint) >= 1 \
                    and get_drive_by_mountpoint(part.mountpoint) not in chianas.offlined_drives:
                drive = get_drive_by_mountpoint(part.mountpoint)
                available_drives.append((part.mountpoint, part.device, drive))
        return (natsorted(available_drives)[0])
    except IndexError:
        log.debug("ERROR: No Drives Found, Please add drives, run auto_drive.py and try again!")
        exit()


def get_internal_plot_drive_to_use():
    """
        Same as above but returns the next drive. This is the drive we will use for internal plots. We do
        this to make sure we are not over saturating a single drive with multiple plot copies. When you run
        out of drives, these scripts will fail.
        """
    available_drives = []
    try:
        for part in psutil.disk_partitions(all=False):
            if part.device.startswith('/dev/sd') \
                    and part.mountpoint.startswith('/mnt/enclosure') \
                    and get_drive_info('space_free_plots_by_mountpoint', part.mountpoint) >= 1 \
                    and get_drive_by_mountpoint(part.mountpoint) not in chianas.offlined_drives:
                drive = get_drive_by_mountpoint(part.mountpoint)
                available_drives.append((part.mountpoint, part.device, drive))
        return (natsorted(available_drives)[1])
    except IndexError: # We will get an IndexError when we run out of drive space
        # If we have no more drive space available on a drive not already being use to store local plot AND we are using pools and have elected to
        # replace non-pool plots, fall back to returning pool plot internal replacement drive:
        if chianas.pools and chianas.replace_non_pool_plots: # Sanity check, must have pools and replace_non__pool_plots set to true in config file.
            log.debug('CAUTION: No additional internal drives are available for use! Since you have replace_non_pools_plots set,')
            log.debug('we are going to return the next available local plot drives with old plots to replace.')
            return chiaplots.local_plot_drive
        else:
            # If we have no more drives left, fall back to the only drive left on the system with space available
            log.debug('CAUTION: No additional internal drives are available for use! Defaulting to using the next available drive with space available.')
            log.debug('This can cause contention on the drive bus and slow down all transfers, internal and external. It is recommended that you resolve')
            log.debug('this issue is you are able.')
            notify('Drive Overlap!', 'Internal and External plotting drives now overlap! Suggest fixing to prevent drive bus contention and slow transfers. If you have selected plot replacement, we will attempt to convert to replacement now.')
            return get_plot_drive_to_use()
       # log.debug("ERROR: No Additional Internal Drives Found, Please add drives, run auto_drive.py and try again!")
       # exit()



def get_sorted_drive_list():
    """
    Returns sorted list of drives
    """
    available_drives = []
    for part in psutil.disk_partitions(all=False):
        if part.device.startswith('/dev/sd') and part.mountpoint.startswith('/mnt/enclosure'):
            drive=get_drive_by_mountpoint(part.mountpoint)
            available_drives.append((part.mountpoint, part.device, drive))
    return natsorted(available_drives)

def get_current_plot_drive_info():
    """
    Designed for debugging and logging purposes when we switch drives
    """
    return Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1])


def log_drive_report():
    """
    Logs a drive report of our newly selected plot drive
    """
    templ = "%-15s %6s %15s %12s %10s  %5s"
    log.info(templ % ("New Plot Drive", "Size", "Avail Plots", "Serial #", "Temp °C",
                      "Mount Point"))

    usage = psutil.disk_usage(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][0])

    log.info(templ % (
        get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1],
        bytes2human(usage.total),
        get_drive_info('space_free_plots_by_mountpoint', (get_plot_drive_to_use()[0])),
        Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).serial,
        Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).temperature,
        get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][0]))


def online_offline_drive(drive, onoffline):
    """
    Function to online and offline a drive for maintenance, etc. A drive that has been
    'offlined' will not have any plots written to it.
    """
    log.debug(f'online_offline_drive() called with [{drive}] , [{onoffline}]')
    if get_device_info_by_drive_number(drive) == None:
        print()
        print(f'{red}WARNING{nc}: {blue}{drive}{nc} does not exist or is not mounted on this system!')
        print()
        log.debug(f'Drive: {drive} does not exist or is not mounted on this system!')
    else:
        if onoffline == 'offline':
            if drive in chianas.offlined_drives:
                print()
                print(f'Drive: {blue}{drive}{nc} Already in {red}OFFLINE{nc} mode! No action taken.')
                print()
                log.debug(f'Drive: {drive} Already in offline mode!')
            else:
                chianas.onoffline_drives('offline', drive)
                print()
                print(f'Drive: {blue}{drive}{nc} Put into {red}OFFLINE{nc} mode! Plots will not be written to this drive!')
                print()
                log.debug(f'Drive: {drive} Put into OFFLINE mode! Plots will not be written to this drive!')
        elif onoffline == 'online':
            if drive in chianas.offlined_drives:
                chianas.onoffline_drives('online', drive)
                print()
                print(f'Drive: {blue}{drive}{nc} Put into {green}ONLINE{nc} mode! Plots will now be written to this drive!')
                print()
                log.debug(f'Drive: {drive} Put into ONLINE mode! Plots will now be written to this drive!')
            else:
                print()
                print(f'Drive: {blue}{drive}{nc} was not in {red}OFFLINE{nc} mode! No action taken.')
                print()
                log.debug(f'Drive: {drive} was not offline!')
        elif onoffline == 'check':
            if drive in chianas.offlined_drives:
                return True
            else:
                return False


def replace_plot():
    log.debug("replace_plot() Called.....")
    if not chianas.replace_non_pool_plots: #Let's just verify that we really want to replace our old plots...
        log.debug('Non-Pool Plot Replacement set to False, moving on......')
        update_receive_plot()
    else:
        if not chianas.fill_empty_drives_first:
            if chiaplots.plots_to_replace:
                if check_space_available(chiaplots.plot_drive): # Check to see if we have any space available on the drive before we delete a plot
                    log.debug(f'We have {chiaplots.number_of_old_plots} plots to replace.')
                    log.debug(f'The next inbound plot will be saved here: {chiaplots.plot_drive}')
                    log.debug(f'We currently have {chiaplots.number_of_portable_plots} portable plots on the system.')
                    log.debug(f'We have room on [{chiaplots.plot_drive}] for another plot, no need to delete plot..... ')
                    update_receive_plot()
                else:
                    log.debug(f'We have {chiaplots.number_of_old_plots} plots to replace.')
                    log.debug(f'We will remove this plot first: {chiaplots.next_plot_to_replace}')
                    log.debug(f'The next inbound plot will be saved here: {chiaplots.plot_drive}')
                    log.debug(f'We currently have {chiaplots.number_of_portable_plots} portable plots on the system.')
                    os.remove(chiaplots.next_plot_to_replace)
                    if not os.path.isfile(chiaplots.next_plot_to_replace):
                        log.debug('Old Plot has been removed, making room for new Portable Plot! Continuing..... ')
                        update_receive_plot()
                    else:
                        log.debug('ERROR: Plot Still Exists!! EXITING')
                        raise Exception
            else:
                print('No further old plots to replace!!')
                update_receive_plot()
        else:
            if (get_all_available_system_space("free")[1]) < chianas.empty_drives_low_water_mark: # Do we have an empty drive space left?
                if chiaplots.plots_to_replace:
                    if check_space_available(chiaplots.plot_drive):
                        log.debug(f'We have {chiaplots.number_of_old_plots} plots to replace.')
                        log.debug(f'The next inbound plot will be saved here: {chiaplots.plot_drive}')
                        log.debug(f'We currently have {chiaplots.number_of_portable_plots} portable plots on the system.')
                        log.debug(f'We have room on [{chiaplots.plot_drive}] for another plot, no need to delete plot..... ')
                        update_receive_plot()
                    else:
                        log.debug(f'We have {chiaplots.number_of_old_plots} plots to replace.')
                        log.debug(f'We will remove this plot first: {chiaplots.next_plot_to_replace}')
                        log.debug(f'The next inbound plot will be saved here: {chiaplots.plot_drive}')
                        log.debug(f'We currently have {chiaplots.number_of_portable_plots} portable plots on the system.')
                        os.remove(chiaplots.next_plot_to_replace)
                        if not os.path.isfile(chiaplots.next_plot_to_replace):
                            print('Old Plot has been removed, making room for new Portable Plot! Continuing..... ')
                            update_receive_plot()
                        else:
                            log.debug('ERROR: Plot Still Exists!! EXITING')
                            raise Exception
                else:
                    log.debug('No further old plots to replace!')
                    update_receive_plot()
            else:
                log.debug('replace_plot() called, but fill_empty_drives_first is set and we have drive space available.') # Call build script and point to current plot drive
                log.debug(f'Low Water Mark: {chianas.empty_drives_low_water_mark} and we have {get_all_available_system_space("free")[1]} available')
                log.debug('Defaulting to SAVING plot instead of REPLACING plot until we fall below our Low Water Mark.')
                update_receive_plot()


def check_space_available(drive):
    """
    Determine if we have space on our local move drive and if not, flag it.
    """
    log.debug(f'check_space_available() called with: [{drive}]')
    space_available = get_drive_info("space_free_plots_by_mountpoint", drive)
    if space_available > 0:
        log.debug(f'We can store an additional [{space_available}] plots on [{drive}]')
        return True
    else:
        log.debug(f'There is no free space available on [{drive}] for any additional plots.')
        return False


def update_receive_plot():
    """
    This utilizes the get_plot_drive_to_use() function and builds out
    our netcat receive_plot.sh script that is called by our plotting
    server when it is ready to send over a new plot. The plotting server
    sends the plot 'in the blind' so-to-speak, this function determines
    what drive the plot will go on and updates the receive shell script
    accordingly. Eventually I will do all of the netcat within the script
    here. See TODO: Update to use netcat native to python.
    """
    log.debug("update_receive_plot() Started")
    if not chianas.replace_non_pool_plots: # If we are not replacing old plots with new portable plots, run the following code
        log.debug('Replace Plots has NOT been set in config, will call build script for normal operation.')
        drive = get_plot_drive_to_use()[0]
        if not os.path.isfile(receive_script):
            log.debug(f'{receive_script} not found. Building it now...')
            build_receive_plot('normal', drive)
        else:
            if os.path.isfile(script_path.joinpath('remote_transfer_is_active')):
                log.debug('Remote Transfer in Progress, will try again soon!')
                quit() # TODO Think about what we really want to do here. If we are running a remote transfer, can we still do other things?
            else:
                if chianas.current_plotting_drive == drive:
                    log.debug(f'Currently Configured Plot Drive: {chianas.current_plotting_drive}')
                    log.debug(f'System Selected Plot Drive:      {drive}')
                    log.debug('Configured and Selected Drives Match!')
                    log.debug(f'No changes necessary to {receive_script}')
                    log.debug(f'Plots left available on configured plotting drive: {get_drive_info("space_free_plots_by_mountpoint", chianas.current_plotting_drive)}')
                else:
                    send_new_plot_disk_email()  # This is the full Plot drive report. This is in addition to the generic email sent by the
                                                # notify() function.
                    notify('Plot Drive Updated', f'Plot Drive Updated: Was: {chianas.current_plotting_drive},  Now: {drive}')
                    build_receive_plot('normal', drive)
    else:
        log.debug('Replace Plots Set, will call build script for plot replacement!')
        log.debug('Checking to see if we need to fill empty drives first......')
        if chianas.fill_empty_drives_first:
            log.debug('fill_empty_drives_first flag is set. Checking for empty drive space.....')
            if (get_all_available_system_space("free")[1]) > chianas.empty_drives_low_water_mark:
                log.debug('Found Empty Drive Space!')
                log.debug(f'Low Water Mark: {chianas.empty_drives_low_water_mark} and we have {get_all_available_system_space("free")[1]} available')
                drive = get_plot_drive_to_use()[0]
                if not os.path.isfile(receive_script):
                    log.debug(f'{receive_script} not found. Building it now...')
                    build_receive_plot('normal', drive)
                else:
                    if os.path.isfile(script_path.joinpath('remote_transfer_is_active')):
                        log.debug('Remote Transfer in Progress, will try again soon!')
                        quit()  # TODO Think about what we really want to do here. If we are running a remote transfer, can we still do other things?
                    else:
                        if chianas.current_plotting_drive == drive:
                            log.debug(f'Currently Configured Plot Drive: {chianas.current_plotting_drive}')
                            log.debug(f'System Selected Plot Drive:      {drive}')
                            log.debug('Configured and Selected Drives Match!')
                            log.debug(f'No changes necessary to {receive_script}')
                            log.debug(f'Plots left available on configured plotting drive: {get_drive_info("space_free_plots_by_mountpoint", chianas.current_plotting_drive)}')
                        else:
                            send_new_plot_disk_email()  # This is the full Plot drive report. This is in addition to the generic email sent by the
                            # notify() function.
                            notify('Plot Drive Updated', f'Plot Drive Updated: Was: {chianas.current_plotting_drive},  Now: {drive}')
                            build_receive_plot('normal', drive)
            else:
                log.debug('fill_empty_drives_first flag is set, but we have no available free drive space....Defaulting to REPLACE PLOTS!')
                log.debug(f'Low Water Mark: {chianas.empty_drives_low_water_mark} and we have {get_all_available_system_space("free")[1]} available')
                log.debug('Checking to see if we have any old plots to replace.....')
                if chiaplots.plots_to_replace:
                    log.debug(f'We found [{chiaplots.number_of_old_plots}] to replace. Continuing....')
                    drive = chiaplots.plot_drive
                    if not os.path.isfile(receive_script):
                        log.debug(f'{receive_script} not found. Building it now...')
                        build_receive_plot('portable', drive)
                    else:
                        if chianas.current_plot_replacement_drive == drive:
                            log.debug(f'Currently Configured Replacement Drive: {chianas.current_plot_replacement_drive}')
                            log.debug(f'System Selected Replacement Drive:      {drive}')
                            log.debug('Configured and Selected Drives Match!')
                            log.debug(f'No changes necessary to {receive_script}')
                        else:
                            notify('Plot Replacement Drive Updated', f'Plot Drive Updated: Was: {chianas.current_plot_replacement_drive},  Now: {drive}')
                            build_receive_plot('portable', drive)
                else:
                    log.debug(f'ERROR: Replace Plots Configured, but no old plots exist!')
                    quit()
        else:
            log.debug('fill_empty_drives_first flag NOT set, continuing....')
            log.debug('Checking to see if we have any old plots to replace.....')
            if chiaplots.plots_to_replace:
                log.debug(f'We found [{chiaplots.number_of_old_plots}] to replace. Continuing....')
                drive = chiaplots.plot_drive
                if not os.path.isfile(receive_script):
                    log.debug(f'{receive_script} not found. Building it now...')
                    build_receive_plot('portable', drive)
                else:
                    if chianas.current_plot_replacement_drive == drive:
                        log.debug(f'Currently Configured Replacement Drive: {chianas.current_plot_replacement_drive}')
                        log.debug(f'System Selected Replacement Drive:      {drive}')
                        log.debug('Configured and Selected Drives Match!')
                        log.debug(f'No changes necessary to {receive_script}')
                    else:
                       # send_new_plot_disk_email()  # This is the full Plot drive report. This is in addition to the generic email sent by the
                                                    # notify() function. - TODO Do we need to send this here or do we need to update the function?
                        notify('Plot Replacement Drive Updated', f'Plot Drive Updated: Was: {chianas.current_plot_replacement_drive},  Now: {drive}')
                        build_receive_plot('portable', drive)
            else:
                log.debug(f'ERROR: Replace Plots Configured, but no old plots exist!')
                quit()

def build_receive_plot(type, drive):
    """
    Function to build or rebuild our receive_plot.sh script.
    :return:
    """
    f = open(receive_script, 'w+')
    f.write('#! /bin/bash \n')
    f.write(f'nc -l -q5 -p 4040 > "{drive}/$1" < /dev/null')
    f.close()
    os.chmod(receive_script, 0o755)
    chianas.update_current_plot_replacement_drive(drive)
    chianas.update_current_plotting_drive(drive)
    if type == 'portable':
        log.info(f'Updated {receive_script} and system config file with new plot replacement drive.')
        log.info(f'Was: {chianas.current_plot_replacement_drive},  Now: {drive}')
    else:
        log.info(f'Updated {receive_script} and system config file with new plot drive.')
        log.info(f'Was: {chianas.current_plotting_drive},  Now: {drive}')


def send_new_plot_disk_email():
    """
    This is the function that we call when we want to send an email letting you know that a new
    plot has been created.
    """
    usage = psutil.disk_usage(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][0])
    try:
        days_to_fill_drives = (int(get_all_available_system_space('free')[1] / chianas.current_total_plots_daily))
    except ZeroDivisionError:
        days_to_fill_drives = 0
    if chianas.new_plot_drive:
        for email_address in chianas.emails:
            send_template_email(template='new_plotting_drive.html',
                                recipient=email_address,
                                subject='New Plotting Drive Selected\nContent-Type: text/html',
                                current_time=current_military_time,
                                nas_server=chianas.hostname,
                                previous_plotting_drive=chianas.current_plotting_drive,
                                plots_on_previous_plotting_drive=get_drive_info('total_current_plots_by_mountpoint',chianas.current_plotting_drive),
                                current_plotting_drive_by_mountpoint=get_plot_drive_to_use()[0],
                                current_plotting_drive_by_device=get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1],
                                drive_size=bytes2human(usage.total),
                                plots_available=get_drive_info('space_free_plots_by_mountpoint', (get_plot_drive_to_use()[0])),
                                drive_serial_number=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).serial,
                                current_drive_temperature=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).temperature,
                                smart_health_assessment=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).assessment,
                                total_serverwide_plots=get_all_available_system_space('used')[1],
                                total_serverwide_plots_chia=check_plots()[0],
                                total_serverwide_space_per_chia=check_plots()[1],
                                total_number_of_drives=get_all_available_system_space('total')[0],
                                total_k32_plots_until_full=get_all_available_system_space('free')[1],
                                max_number_of_plots=get_all_available_system_space('total')[1],
                                days_to_fill_drives=days_to_fill_drives)
    else:
        pass


def send_daily_update_email():
    """
    Function that generates and sends the daily update email.
    """
    usage = psutil.disk_usage(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][0])
    if chianas.daily_update:
        for email_address in chianas.emails:
            print(email_address)
            send_template_email(template='daily_update.html',
                              recipient=email_address,
                              subject='NAS Server Daily Update\nContent-Type: text/html',
                              current_time=current_military_time,
                              nas_server=chianas.hostname, current_plotting_drive_by_mountpoint=get_plot_drive_to_use()[0],
                              current_plotting_drive_by_device=get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1],
                              drive_size=bytes2human(usage.total),
                              drive_serial_number=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).serial,
                              current_drive_temperature=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).temperature,
                              smart_health_assessment=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).assessment,
                              total_serverwide_plots=get_all_available_system_space('used')[1],
                              total_number_of_drives=get_all_available_system_space('total')[0],
                              total_k32_plots_until_full=get_all_available_system_space('free')[1],
                              max_number_of_plots=get_all_available_system_space('total')[1],
                              total_serverwide_plots_chia=check_plots()[0],
                              total_serverwide_space_per_chia=check_plots()[1],
                              total_plots_last_day=chianas.current_total_plots_daily,
                              days_to_fill_drives=(int(get_all_available_system_space('free')[1] / chianas.current_total_plots_daily)),
                              average_plots_per_hour=round((chianas.current_total_plots_daily) / 24, 1),
                              average_plotting_speed=chianas.current_total_plots_daily * int(plot_size_g) / 1000)
    else:
        pass


def create_new_index_html_report():
    """
    Not is use, but can be used to generate a new web index.html for a static website.
    """
    usage = psutil.disk_usage(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][0])
    create_index_html(template='index.html',
                      current_time=current_military_time,
                      nas_server=chianas.hostname, current_plotting_drive_by_mountpoint=get_plot_drive_to_use()[0],
                      current_plotting_drive_by_device=get_device_by_mountpoint(get_plot_drive_to_use())[0][1],
                      drive_size=bytes2human(usage.total),
                      drive_serial_number=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).serial,
                      current_drive_temperature=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).temperature,
                      smart_health_assessment=Device(get_device_by_mountpoint(get_plot_drive_to_use()[0])[0][1]).assessment,
                      total_serverwide_plots=get_all_available_system_space('used')[1],
                      total_number_of_drives=get_all_available_system_space('total')[0],
                      total_k32_plots_until_full=get_all_available_system_space('free')[1],
                      max_number_of_plots=get_all_available_system_space('total')[1],
                      total_serverwide_plots_chia=check_plots()[0],
                      total_serverwide_space_per_chia=check_plots()[1],
                      total_plots_last_day=chianas.current_total_plots_daily,
                      days_to_fill_drives=(int(get_all_available_system_space('free')[1] / chianas.current_total_plots_daily)),
                      average_plots_per_hour=round(chianas.current_total_plots_daily / 24, 1),
                      average_plotting_speed=chianas.current_total_plots_daily * int(plot_size_g) / 1000)





def space_report():
    """
    Function that creates the space report from the command line.
    """
    replace_plots = chianas.replace_non_pool_plots
    plots_last_day = chianas.current_total_plots_daily
    if plots_last_day == 0:
        plots_last_day = 1
    if replace_plots:
        days_to_fill = round((int((get_all_available_system_space("free")[1]) + int(chiaplots.number_of_old_plots)) / plots_last_day) , 0)
    else:
        days_to_fill = int(get_all_available_system_space('free')[1] / plots_last_day)
    try:
        current_plot_drive = (get_device_by_mountpoint(chianas.current_plotting_drive)[0][1])
    except Exception as e:
        current_plot_drive = 'N/A'
    try:
        current_plot_drive_temp = Device((get_device_by_mountpoint(chianas.current_plotting_drive)[0][1])).temperature
    except Exception as e:
        current_plot_drive_temp = 'N/A'
    try:
        current_plot_drive_smart_assesment = Device((get_device_by_mountpoint(chianas.current_plotting_drive)[0][1])).assessment
    except Exception as e:
        current_plot_drive_smart_assesment = 'N/A'
    print('')
    print(f'{blue}############################################################{nc}')
    print(f'{blue}################### {green}{chianas.hostname} Plot Report{blue} ##################{nc}' )
    #print(f'{blue}############################################################{nc}')
    if replace_plots:
        print(f'{blue}############################################################{nc}')
        print(f'{blue}######### {yellow}*** {red}OLD PLOT REPLACEMENT IN PROGRESS{yellow} ***{blue} #########')
        print(f'{blue}############################################################{nc}')
    else:
        print(f'{blue}############################################################{nc}')
    print (f'Total Number of Plots on {green}{chianas.hostname}{nc}:                     {yellow}{get_all_available_system_space("used")[1]}{nc}')
    if replace_plots:
        print(f'Total Number of {red}OLD{nc} Plots on {green}{chianas.hostname}{nc}:                 {yellow}{chiaplots.number_of_old_plots}{nc}')
        print(f'Total Number of {red}PORTABLE{nc} Plots on {green}{chianas.hostname}{nc}:             {yellow}{chiaplots.number_of_portable_plots}{nc}')
    print (f'Total Number of Plots {green}Chia{nc} is Farming:                  {yellow}{check_plots()[0]}{nc}')
    print (f'Total Amount of Drive Space (TiB) {green}Chia{nc} is Farming:       {yellow}{check_plots()[1]}{nc}')
    print (f'Total Number of Systemwide Plots Drives:                  {yellow}{get_all_available_system_space("total")[0]}{nc}')
    print (f'Total Number of k32 Plots until full:                   {yellow}{get_all_available_system_space("free")[1]}{nc}')
    print (f'Maximum # of plots when full:                           {yellow}{get_all_available_system_space("total")[1]}{nc}')
    print (f"Plots completed in the last 24 Hours:                     {yellow}{plots_last_day}{nc}")
    print (f"Average Plots per Hours:                                 {yellow}{round(chianas.current_total_plots_daily / 24, 1)}{nc}")
    print (f"Average Plotting Speed Last 24 Hours (TiB/Day):         {yellow}{round((chianas.current_total_plots_daily * int(plot_size_g) / 1000), 2)}{nc} ")
    if replace_plots:
        print (f"Days to fill/replace all current drives/plots:        {yellow} {days_to_fill} {nc} ")
    else:
        print(f"Days to fill all current drives:                          {yellow} {days_to_fill} {nc} ")
    print (f"Current Plot Storage Drive:                       {yellow}{current_plot_drive}{nc}")
    print (f"Temperature of Current Plot Drive:                      {yellow}{current_plot_drive_temp}°C{nc}")
    print (f"Latest Smart Drive Assessment of Plot Drive:            {yellow}{current_plot_drive_smart_assesment}{nc}")
    print(f'{blue}############################################################{nc}')
    print('')
    print('')

def nas_report_export():
    """
    This function generates the json file with all of the server information for
    our total farm report for those running multiple harvesters as well as doing
    health checks. Used to pass information on to our plotter as well.
    """
    chianas = DriveManager.read_configs() #reread in case of changes
    chiaplots = PlotManager.get_plot_info() #reread in case of changes
    log.debug('nas_report_export() started')
    plots_last_day = chianas.current_total_plots_daily
    if plots_last_day == 0:
        plots_last_day = 1
    if chianas.replace_non_pool_plots and not chianas.fill_empty_drives_first:
        total_plots_until_full = (int(get_all_available_system_space("free")[1]) + int(chiaplots.number_of_old_plots))
        current_plot_replacement_drive = chiaplots.plot_drive
        approx_days_to_fill_drives = round((int(total_plots_until_full / plots_last_day)), 0)
    elif chianas.replace_non_pool_plots and chianas.fill_empty_drives_first and (get_all_available_system_space("free")[1]) < chianas.empty_drives_low_water_mark:
        total_plots_until_full = (int(get_all_available_system_space("free")[1]) + int(chiaplots.number_of_old_plots))
        current_plot_replacement_drive = chiaplots.plot_drive
        approx_days_to_fill_drives = round((int(total_plots_until_full / plots_last_day)), 0)
    else:
        total_plots_until_full = int(get_all_available_system_space("free")[1])
        current_plot_replacement_drive = 'N/A'
        approx_days_to_fill_drives = round((int(get_all_available_system_space('free')[1] / plots_last_day)), 0)
    nas_server_export = dict([
        ('server', chianas.hostname),
        ('total_plots', int(get_all_available_system_space("used")[1])),
        ('total_plots_farming', int(check_plots()[0])),
        ('total_tib_farming', int(check_plots()[1])),
        ('total_plot_drives', int(get_all_available_system_space("total")[0])),
        ('total_plots_until_full', total_plots_until_full),
        ('total_empty_space_plots_until_full', int(get_all_available_system_space("free")[1])),
        ('max_plots_when_full', int(get_all_available_system_space("total")[1])),
        ('plots_last_day', plots_last_day),
        ('avg_plots_per_hour', round((int(chianas.current_total_plots_daily)) / 24, 1)),
        ('avg_plotting_speed', round((int(chianas.current_total_plots_daily)) * int(plot_size_g) / 1000, 2)),
        ('approx_days_to_fill_drives', approx_days_to_fill_drives),
        ('current_plot_drive', chianas.current_plotting_drive),
        ('replace_non_pool_plots', chianas.replace_non_pool_plots),
        ('total_number_of_old_plots', chiaplots.number_of_old_plots),
        ('current_plot_replacement_drive', current_plot_replacement_drive)
    ])
    try:
        with open(local_export_file, 'w') as nas_export:
            nas_export.write(json.dumps(nas_server_export))
    except:
        log.debug(f'Unable to write to export file! Check \"{local_export_file}\" path above and try again!')
    return nas_server_export


def generate_uuid_dict():
   result = subprocess.run(['lsblk', '-nolabel', '-o', 'UUID,MOUNTPOINT'], capture_output=True)
   fstab_dict = []
   for item in result.stdout.splitlines():
       if b'enclosure' not in item: continue
       uuid, mnt = item.decode().split()
       fstab_dict.append((uuid, (chianas.hostname, mnt)))
   try:
       dsks = dict()
       dsks.update(fstab_dict)
       with open(uuid_export_file, 'w') as uuid_export:
           json.dump(dsks, uuid_export)
   except Exception:
       log.debug(f'Unable to write to export file! Check \"{uuid_export_file}\" path above and try again!')
       raise


def temperature_report():
    """
    Prints out the temperatures of all plot drives on the system.
    """
    print('')
    print(f'{blue}#################################################################{nc}')
    print(f'{blue}################# {green}{chianas.hostname} Temperature Report {blue}##################{nc}')
    print(f'{blue}#################################################################{nc}')
    print(f'{blue}#    {nc}Serial#{blue}     #{nc}     Device{blue}     #{nc}     Drive{blue}     #{nc}    Temp{blue}     #{nc}')
    print(f'{blue}#################################################################{nc}')
    for drive in get_sorted_drive_list():
        print(f'{blue}#{nc}   {Device(drive[1]).serial}'f'{blue}     #{nc}'f'   {drive[1]}{blue}    #{nc}' f'    {((get_drive_by_mountpoint(drive[0])))}{blue}    #{nc}' f'     {Device(drive[1]).temperature}°C'f'{blue}     #{nc}')
    print(f'{blue}##################################################################{nc}')
    print('')
    print('')

# You should run this once per day to see total daily plots
# in your reports. If you run it more often, the numbers will
# not be correct. I use midnight here for my purposes, but
# this is just a var name.
def update_daily_plot_counts():
    if not chianas.pools:
        current_total_plots_midnight = chianas.current_total_plots_midnight # Old plots if converting to new portable plots
        total_serverwide_plots = int(get_all_available_system_space('used')[1]) # Total number of plots on the server as a whole, old and new
        chianas.update_current_total_plots_midnight('old', total_serverwide_plots) # New Midnight TOTAL server plots, old and portable
        total_plots_daily = (total_serverwide_plots - current_total_plots_midnight)
        chianas.update_current_total_plots_daily('old', total_plots_daily)
    else:
        current_portable_plots_midnight = chianas.current_portable_plots_midnight
        total_serverwide_portable_plots = chiaplots.number_of_portable_plots
        total_serverwide_plots = int(get_all_available_system_space('used')[1])  # Total number of plots on the server as a whole, old and new
        chianas.update_current_total_plots_midnight('old', total_serverwide_plots)  # New Midnight TOTAL server plots, old and portable
        chianas.update_current_total_plots_midnight('portable', total_serverwide_portable_plots)  # New Midnight TOTAL server plots, old and portable
        total_plots_daily = (total_serverwide_portable_plots - current_portable_plots_midnight)
        chianas.update_current_total_plots_daily('old', total_plots_daily)
        chianas.update_current_total_plots_daily('portable', total_plots_daily)


def send_email(recipient, subject, body):
    """
    Part of our notification system.
    Setup to send email via the builtin linux mail command.
    Your local system **must** be configured already to send mail or this will fail.
    https://stackoverflow.com/questions/27874102/executing-shell-mail-command-using-python
    https://nedbatchelder.com/text/unipain.html
    https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postfix-as-a-send-only-smtp-server-on-ubuntu-20-04
    """
    try:
        subprocess.run(['mail', '-s', subject, recipient], input=body, encoding='utf-8')
        log.debug(f"Email Notification Sent: Subject: {subject}, Recipient: {recipient}, Message: {body}")
    except subprocess.CalledProcessError as e:
        log.debug(f'send_email error: {e}')
    except Exception as e:
        log.debug(f'send_email: Unknown Error! Email not sent.')


# Setup to send out Pushbullet alerts. Pushbullet config is in system_info.py
def send_push_notification(title, message):
    """Part of our notification system. This handles sending PushBullets."""
    try:
        pb = Pushbullet(chianas.pb_api)
        push = pb.push_note(title, message)
        log.debug(f"Pushbullet Notification Sent: {title} - {message}")
    except pb_errors.InvalidKeyError as e:
        log.debug(f'Pushbullet Exception: Invalid API Key! Message not sent.')
    except Exception as e:
        log.debug(f'Pushbullet Exception: Unknown Pushbullet Error: {e}. Message not sent.')

def send_sms_notification(body, phone_number):
    """Part of our notification system. This handles sending SMS messages."""
    try:
        client = Client(chianas.twilio_account, chianas.twilio_token)
        message = client.messages.create(to=phone_number, from_=chianas.twilio_from, body=body)
        log.debug(f"SMS Notification Sent: {body}.")
    except TwilioRestException as e:
        log.debug(f'Twilio Exception: {e}. Message not sent.')
    except Exception as e:
        log.debug(f'Twilio Exception: {e}. Message not sent.')



def notify(title, message):
    """ Notify system for email, pushbullet and sms (via Twilio)"""
    log.debug(f'notify() called with Title: {title} and Message: {message}')
    if chianas.notifications:
        if chianas.pb:
            send_push_notification(title, message)
        if chianas.email:
            for email_address in chianas.emails:
                send_email(email_address, title, message)
        if chianas.sms:
            for phone_number in chianas.phones:
                send_sms_notification(message, phone_number)
    else:
        pass


# Thank You - https://frankcorso.dev/email-html-templates-jinja-python.html
def send_template_email(template, recipient, subject, **kwargs):
    """Sends an email using a jinja template."""
    env = Environment(
        loader=FileSystemLoader('%s/templates/' % os.path.dirname(__file__)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template)
    send_email(recipient, subject, template.render(**kwargs))



# Create/Update our Report Web Interface
def create_index_html(template, **kwargs):
    """Sends an email using a jinja template."""
    env = Environment(
        loader=FileSystemLoader('%s/templates/' % os.path.dirname(__file__)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template)
    index_html(template.render(**kwargs))

def index_html(report):
    with open ('web/index.html', 'w') as report_body:
        report_body.write(report)



# This function called from crontab. First run the daily update (-ud) then (-dr):
# 01 00 * * * /usr/bin/python3 /root/plot_manager/drive_manager.py -ud >/dev/null 2>&1
# 02 00 * * * /usr/bin/python3 /root/plot_manager/drive_manager.py -dr >/dev/null 2>&1
def send_daily_email():
    log.debug('send_daily_email() Started')
    send_daily_update_email()
    log.info('Daily Update Email Sent!')

def send_new_plot_notification():
    log.debug('send_new_plot_notification() Started')
    if os.path.isfile('new_plot_received'):
        log.debug('New Plot Received')
        if chianas.per_plot:
            notify('New Plot Received', 'New Plot Received')
        os.remove('new_plot_received')

def check_plots():
    with open(chianas.chia_log_file, 'rb', 0) as f:
        m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        i = m.rfind(b'Loaded')
        try:
            m.seek(i)
        except ValueError as e:
            return 0, 0
        line = m.readline()
        newline = line.decode("utf-8")
        x = newline.split()
        try:
            plots = x[4]
            TiB = float(x[8])
        except IndexError:
            plots = 0
            TiB = 0
        return plots, f'{TiB:.0f}'


def check_temp_drive_utilization():
    """
    This function checks our dst drives
    for utilization in excess of the limits we have
    set in our config file and sends us a notification
    in the event we exceed this utilization.
    """
    log.debug('check_temp_drive_utilization() started')
    if chianas.local_plotter:
        if chianas.get_critical_temp_dir_usage() != {}:
            if not chianas.temp_dirs_critical_alert_sent:
                chianas.toggle_alert_sent('temp_dirs_critical_alert_sent')
                for dirs in chianas.get_critical_temp_dir_usage().keys():
                    log.debug(f'WARNING: {dirs} is nearing capacity. Sending Alert!')
                    notify('WARNING: Directory Utilization Nearing Capacity',
                           f'WARNING: {dirs} is nearing Capacity\nPlotting is in Jeopardy!\nCheck Your Drives IMMEDIATELY!')
            else:
                for dirs in chianas.get_critical_temp_dir_usage().keys():
                    log.debug(f'WARNING: {dirs} is nearing capacity. Alert has already been sent!')
        elif chianas.temp_dirs_critical_alert_sent:
            chianas.toggle_alert_sent('temp_dirs_critical_alert_sent')
            notify('INFORMATION: Directory Utilization', 'INFORMATION: Your Temp Directory is now below High Capacity Warning\nPlotting will Continue')
        else:
            log.debug('Temp Drive(s) check complete. All OK!')

    else:
        log.debug('Local Plotting is Disabled. No Drive Checks.')


def check_dst_drive_utilization():
    """
    This function checks our dst drives
    for utilization in excess of the limits we have
    set in our config file and sends us a notification
    in the event we exceed this utilization.
    """
    log.debug('check_dst_drive_utilization() started')
    if chianas.local_plotter:
        if chianas.get_critical_dst_dir_usage() != {}:
            if not chianas.dst_dirs_critical_alert_sent:
                chianas.toggle_alert_sent('dst_dirs_critical_alert_sent')
                for dirs in chianas.get_critical_dst_dir_usage().keys():
                    log.debug(f'WARNING: {dirs} is nearing capacity. Sending Alert!')
                    notify('WARNING: Directory Utilization Nearing Capacity',
                           f'WARNING: {dirs} is nearing Capacity\nPlotting is in Jeopardy!\nCheck Your Drives IMMEDIATELY!')
            else:
                for dirs in chianas.get_critical_dst_dir_usage().keys():
                    log.debug(f'WARNING: {dirs} is nearing capacity. Alert has already been sent!')
        elif chianas.dst_dirs_critical_alert_sent:
            chianas.toggle_alert_sent('dst_dirs_critical_alert_sent')
            notify('INFORMATION: Directory Utilization', 'INFORMATION: Your Temp Directory is now below High Capacity Warning\nPlotting will Continue')
        else:
            log.debug('DST Drive(s) check complete. All OK!')
    else:
        log.debug('Local Plotting is Disabled. No Drive Checks.')

def checks_plots_available():
    log.debug('check_plots_available() started')
    if int(get_all_available_system_space("free")[1]) < chianas.total_plot_highwater_warning:
        if not chianas.total_plots_alert_sent:
            chianas.toggle_alert_sent('total_plots_alert_sent')
            log.debug(f'WARNING: Total Plots is nearing capacity. Sending Alert!')
            notify('WARNING: Running out of Plot Space!', f'You have {get_all_available_system_space("free")[1]} plots left before you are full!\nYou will only get this Alert ONCE!')
        else:
            log.debug(f'WARNING: Total Plots is nearing capacity. Alert has already been sent!')
    elif chianas.total_plots_alert_sent:
        chianas.toggle_alert_sent('total_plots_alert_sent')
        notify('INFORMATION: Total Plots Available',
               'INFORMATION: Your Total Plots available is now Above the Warning Limit\nPlotting will Continue')
    else:
        log.debug('Plot check complete. All OK!')


def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() == proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def system_checks():
    """
    These are the various system checks. Limits are set in the
    configuration file.
    """
    check_temp_drive_utilization()
    check_dst_drive_utilization()
    checks_plots_available()

def main():
    log.debug(f'Welcome to drive_manager.py Version: {VERSION}')
    are_we_configured()
    parser = init_argparser()
    args = parser.parse_args()
    if args.daily_report:
        send_daily_email()
    elif args.plot_report:
        space_report()
    elif args.farm_report:
        farm_wide_space_report()
    elif args.update_daily:
        update_daily_plot_counts()
    elif args.check_temps:
        temperature_report()
    elif args.check_uuid:
        uuid_report(args.check_uuid)
    elif args.offline_hdd:
        online_offline_drive(args.offline_hdd, 'offline')
    elif args.replace_plot:
        replace_plot()
    elif get_offlined_drives():
        if args.online_hdd:
            online_offline_drive(args.online_hdd, 'online')
        else:
            config_file_update()
            system_checks()
            nas_report_export()
            generate_uuid_dict()
            send_new_plot_notification()
            update_receive_plot()
    else:
        config_file_update()
        system_checks()
        nas_report_export()
        generate_uuid_dict()
        send_new_plot_notification()
        update_receive_plot()



if __name__ == '__main__':
    main()




