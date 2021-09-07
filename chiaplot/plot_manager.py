#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.96 (2021-09-05)"

"""
Simple python script that helps to move my chia plots from my plotter to
my nas. I wanted to use netcat as it was much faster on my 10GBe link than
rsync and the servers are secure so I wrote this script to manage that
move process.
This is part of a two part process. On the NAS server there is drive_manager.py
that manages the drives themselves and decides based on various criteria where
the incoming plots will be placed. This script simply sends those plots when
they are ready to send.
Updates
  v0.94 2021-08-08
  - Added ability to remove and replace old style plots one-at-a-time if the receiving
    nas is configured properly. Depending on configuration the NAS that is receiving
    the plot will show how many total old style plots as the total available plots
    and as a result you can manage where you send your new plots better.
  v0.93 2021-07-21
  - Added ability to identify pool plots by prepending 'portable.' to the plot name
    so we can manage them at a later time.
  v0.9 2021-05-28
  - Rewritten logging to support path autodetection, support for multiple
    NAS/Harvesters. Chooses Harvester with the most available plots on it
    and sends the next plot to that NAS. 
  - Various functions added to support multiple harvesters
  - Adding in host checking to verify host is up, if not, sends notification.
  V0.4 2021-04013 (bumped version to match drive_manager.py
  - Due to issue with plot size detection happening after plot selection
    caused an issue where plots did not get moved at all if the first selected
    plot was the wrong size. Updated get_list_of_plots() to use pathlib to check
    for proper filesize before passing along the plot name.
  V0.2 2021-03-23
  - Added per_plot system notification function (send_new_plot_notification()
    in chianas drive_manager.py and updated process_plot() and verify_plot_move()
    to support the new function
  - Moved remote_mount lookup to happen before starting the plot move
"""


import os
import subprocess
import logging
from system_logging import setup_logging
import pathlib
import json
import psutil
from pushbullet import Pushbullet, errors as pb_errors
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import paramiko
import yaml
import configparser
config = configparser.ConfigParser()
script_path = pathlib.Path(__file__).parent.resolve()
from plotmanager_classes import PlotManager, config_file
chiaplot = PlotManager.read_configs()
import time

# Are We Testing?
testing = False

if testing:
    plot_dir = script_path.joinpath('test_plots/')
    print (f'This is your plot Dir: {plot_dir}')
    plot_size = 10000000
    status_file = script_path.joinpath('transfer_job_running_testing')
else:
    plot_dir = chiaplot.dst_dirs[0]
    plot_size = 108644374730  # Based on K32 plot size
    status_file = script_path.joinpath('transfer_job_running')

# Make sure we configured our YAML file....
def are_we_configured():
    if not chiaplot.configured:
        log.debug('We have not been configured! Please edit the main config file')
        log.debug(f'{config_file} and try again!')
        exit()
    else:
        pass


# If you are running multiple harvesters/NAS, make sure to set your YAML config file
# up correctly.
#TODO Build in notification to let us know when we run out of available space on all harvesters!
def remote_harvesters_check():
    log.debug('remote_harvesters_check() Started')
    global nas_server
    global remote_mount
    global replace_plots
    nas_server = get_next_nas()
    if not nas_server:
        log.debug('Could not find any available Plot space on configured Harvesters. Stopping Here.')
        quit()
    else:
        log.debug(f'Remote Harvester(s) Found - Selected NAS/Harvester: {nas_server}')
        with open(script_path.joinpath(f'export/{nas_server}_export.json'), 'r') as f:
            server = yaml.safe_load(f)
            remote_mount=server['current_plot_drive']
            replace_plots=server['replace_non_pool_plots']


# Let's do some housekeeping
"""
This network interface is the name (as shown by `ip a`) of the interface that you
transfer your plots over to your Harvester. We utilize this to determine is there is
network traffic flowing across it during a transfer. 
"""
#network_interface = chiaplot.network_interface
remote_checkfile = script_path.joinpath('remote_transfer_is_active')
network_check = script_path.joinpath('check_network_io.sh')
network_check_output = script_path.joinpath('network_stats.io')



# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
level = logging._checkLevel(chiaplot.log_level)
log = logging.getLogger(__name__)
log.setLevel(level)


# Look in our plot directory and get a list of plots. Do a basic
# size check for sanity's sake.
def get_list_of_plots():
    log.debug('get_list_of_plots() Started')
    try:
        plot_to_process = [plot for plot in pathlib.Path(plot_dir).glob("*.plot") if plot.stat().st_size > plot_size]
        log.debug(f'We will process this plot: {plot_to_process[0].name}')
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
            plot_path = plot_dir + plot_to_process
            log.info(f'Processing Plot: {plot_path}')
            log.debug(f'{nas_server} reports remote mount as {remote_mount}')
            if replace_plots:
                log.debug(f'Executing "drive_manager.py -rp" on {nas_server}.')
                result = (subprocess.run(['ssh', nas_server, f'{script_path.joinpath("drive_manager.py -rp")}'],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                if result.returncode != 0:
                    log.debug(result.returncode)
                    log.debug(f'replace_plot() Script on {nas_server} FAILED! Fix Immediately!')
                    notify('URGENT', f'replace_plot() Script on {nas_server} FAILED! Fix Immediately!')
                    quit()
            process_control('set_status', 'start')
            if chiaplot.pools:
                plot_to_process = 'portable.'+plot_to_process
            subprocess.call([f'{script_path.joinpath("send_plot.sh")}', plot_path, plot_to_process, nas_server])
            try:
                subprocess.call(['ssh', nas_server, f'{script_path.joinpath("utilities/kill_nc.sh")}'])  # make sure all of the nc processes are dead on the receiving end
                log.debug('Remote nc kill called!')
            except subprocess.CalledProcessError as e:
                log.warning(e.output)
            if verify_plot_move(remote_mount, plot_path, plot_to_process):
                log.info('Plot Sizes Match, we have a good plot move!')
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


# This assumes passwordless SSH between this host and remote host.
# Make changes as necessary! Checks to make sure we are not already
# doing a file transfer. If we are we just return. If not we go ahead
# and start the process notifying this local machine as well as the
# remote NAS that a file transfer will be in progress. Right now the
# remote notification does not do anything, but I have plans to use
# it for more control so I am leaving it here.

def process_control(command, action):
    log.debug(f'process_control() called with [{command}] and [{action}]')
    if host_check(nas_server):
        if command == 'set_status':
            if action == "start":
                if os.path.isfile(status_file):
                    log.debug(f'Status File: [{status_file}] already exists!')
                    try:
                        log.debug(f'Remote Checkfile is: {remote_checkfile}')
                        subprocess.check_output(['ssh', nas_server, 'touch %s' % f'{remote_checkfile}'])
                    except subprocess.CalledProcessError as e:
                        log.warning(e.output) #Nothing to add here yet as we are not using this function remotely (yet)
                    return
                else:
                    os.open(status_file, os.O_CREAT)
                    log.debug(f'Remote Checkfile is: {remote_checkfile}')
                    try:
                        subprocess.check_output(['ssh', nas_server, 'touch %s' % f'{remote_checkfile}'])
                    except subprocess.CalledProcessError as e:
                        log.warning(e.output) #Nothing to add here yet as we are not using this function remotely (yet)
                    return
            if action == "stop":
                if os.path.isfile(status_file):
                    os.remove(status_file)
                    log.debug(f'Removing remote checkfile from {nas_server}')
                    try:
                        subprocess.check_output(['ssh', nas_server, 'rm %s' % f'{remote_checkfile}'])
                    except subprocess.CalledProcessError as e:
                        log.warning(e.output) #Nothing to add here yet as we are not using this function remotely (yet)
                else:
                    log.debug(f'Status File: [{status_file}] does not exist!')
                    log.debug(f'Removing remote checkfile from {nas_server}')
                    try:
                        subprocess.check_output(['ssh', nas_server, 'rm %s' % f'{remote_checkfile}'])
                    except subprocess.CalledProcessError as e:
                        log.warning(e.output) #Nothing to add here yet as we are not using this function remotely (yet)
        elif command == 'check_status':
            transfer_in_progress = check_transfer()
            process_running = checkIfProcessRunning('ncat')
            if process_running and transfer_in_progress:
                log.debug(f'NCAT is running and Network Traffic Exists, We are currently Running a Transfer, Exiting')
                return True
            elif process_running and not transfer_in_progress:
                log.debug('WARNING! - NCAT is running but there is no network traffic! Forcing Reset')
                log.debug(f'Removing remote checkfile from {nas_server}')
                try:
                    subprocess.check_output(['ssh', nas_server, 'rm %s' % f'{remote_checkfile}'])
                except subprocess.CalledProcessError as e:
                    log.warning(e.output)
                try:
                    subprocess.call(['ssh', nas_server, script_path.joinpath('utilities/kill_nc.sh')])  # make sure all of the nc processes are dead on the receiving end
                    log.debug('Remote nc kill called!')
                except subprocess.CalledProcessError as e:
                    log.warning(e.output)
                main()
            else:
                log.debug(f'NCAT is not running and there is no network traffic!')
                return False
        else:
            return
    else:
        log.debug(f'WARNING: {nas_server} is OFFLINE! We Cannot Continue......')
        notify(f'{nas_server}.{chiaplot.domain_name} OFFLINE', f'Your NAS Server: {nas_server} cannot be reached. Plots cannot move! Please Correct IMMEDIATELY!')
        exit()


def verify_plot_move(remote_mount, plot_path, plot_to_process):
    log.debug('verify_plot_move() Started')
    log.debug (f'Verifing: {nas_server}: {remote_mount}/{plot_to_process}')
    try:
        remote_plot_size = (int(subprocess.check_output(['ssh', nas_server, 'ls -al %s | awk {\'print $5\'}' % f'{remote_mount}/{plot_to_process}'])))
    except subprocess.CalledProcessError as e:
        log.warning(e.output) #TODO Do something here...cannot go on...
        quit()
    log.debug(f'Remote Plot Size Reported as: {remote_plot_size}')
    local_plot_size = os.path.getsize(plot_path)
    log.debug(f'Local Plot Size Reported as: {local_plot_size}')
    if remote_plot_size == local_plot_size:
        return True
    else:
        log.debug(f'Plot Size Mismatch!')
        return False


def check_transfer():
    """
        Here we are checking network activity on the network interface we are sending plots to from our plotter. If there is
        network activity, then we are most likely receiving a plot and don't want to make any changes.
        """
    log.debug('check_transfer() called')
    try:
        subprocess.call([network_check, chiaplot.network_interface])
    except subprocess.CalledProcessError as e:
        log.warning(e.output)
    with open(network_check_output, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()
        network_traffic_load = float((str.split(last_line)[9]))
    if network_traffic_load >= chiaplot.network_interface_threshold:
        log.debug(f'Network Activity detected on {chiaplot.network_interface}')
        os.remove(network_check_output)
        return True
    else:
        log.debug(f'No Network Activity detected on {chiaplot.network_interface}')
        os.remove(network_check_output)
        return False


def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    #Iterate over the all the running process
    log.debug('checkifprocessrunning() called')
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() == proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def host_check(host):
    """
    Check to see if a specific host is alive
    """
    log.debug('host_check() called')
    proc = subprocess.run(
        ['ping', '-W1', '-q', '-c', '2', host],
        stdout=subprocess.DEVNULL)
    return proc.returncode == 0

def notify(title, message):
    """ Notify system for email, pushbullet and sms (via Twilio)"""
    log.debug(f'notify() called with Title: {title} and Message: {message}')
    if chiaplot.notifications:
        if chiaplot.pb:
            send_push_notification(title, message)
        if chiaplot.email:
            for email_address in chiaplot.emails:
                send_email(email_address, title, message)
        if chiaplot.sms:
            for phone_number in chiaplot.phones:
                send_sms_notification(message, phone_number)
    else:
        pass


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
        pb = Pushbullet(chiaplot.pb_api)
        push = pb.push_note(title, message)
        log.debug(f"Pushbullet Notification Sent: {title} - {message}")
    except pb_errors.InvalidKeyError as e:
        log.debug(f'Pushbullet Exception: Invalid API Key! Message not sent.')
    except Exception as e:
        log.debug(f'Pushbullet Exception: Unknown Pushbullet Error: {e}. Message not sent.')


def send_sms_notification(body, phone_number):
    """Part of our notification system. This handles sending SMS messages."""
    try:
        client = Client(chiaplot.twilio_account, chiaplot.twilio_token)
        message = client.messages.create(to=phone_number, from_=chiaplot.twilio_from, body=body)
        log.debug(f"SMS Notification Sent: {body}.")
    except TwilioRestException as e:
        log.debug(f'Twilio Exception: {e}. Message not sent.')
    except Exception as e:
        log.debug(f'Twilio Exception: {e}. Message not sent.')


def check_remote_harvesters():
    """
    This verifies that the remote_harvesters listed above are actually alive.
    """
    log.debug('check_remote_harvesters() called')
    harvesters_check = {}
    for harvester in chiaplot.remote_harvesters:
        harvesters_check[harvester] = host_check(harvester)
    dead_hosts = [host for host, alive in harvesters_check.items() if not alive]
    if dead_hosts != []:
        log.debug(f'WARNING: {dead_hosts} is OFFLINE!')
    alive_hosts = [host for host, alive in harvesters_check.items() if alive]
    return(alive_hosts)


def remote_harvester_report():
    """
    This reaches out to each 'alive' remote harvester and get all of
    their export information.
    """
    log.debug('remote_harvester_report() called')
    remote_harvesters = check_remote_harvesters()
    servers = []
    for harvester in remote_harvesters:
        remote_export_file = (script_path.joinpath(f'export/{harvester}_export.json').as_posix())
        get_remote_exports(harvester, remote_export_file)
        with open(remote_export_file, 'r') as remote_host:
            harvester = json.loads(remote_host.read())
            servers.append(harvester)
    return servers, remote_harvesters


def get_remote_exports(host, remote_export_file):
    """
    Utilize Paramiko to grab our harvester export information files.
    """
    log.debug('get_remote_exports called')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host)
        sftp = ssh.open_sftp()
        sftp.get(remote_export_file, remote_export_file)
    finally:
        ssh.close()


def get_next_nas():
    """
    Returns the server name of the server with the most space left.
    This is where we will be sending our next plot! If you only have
    a single harvester/NAS just returns that one. If there are 0
    available plots on all servers, returns False. If you have your
    plotter set to prioritize filling empty drive space, AND you have
    harvesters reporting empty drive space (based on their own configuration)
    then this will return the NAS with the most EMPTY drive space, if there
    is no empty drive space or you have not prioritized empty drive space,
    it will return the harvester with the most OLD plots to replace.
    """
    log.debug('get_next_nas() called')
    servers = (remote_harvester_report()[0])
    next_nas = []
    if chiaplot.remote_harvester_priority == 'fill':
        log.debug('plotter set to prioritize: FILL')
        for server in servers:
            nas_server = {'server': server['server'], 'total_empty_space_plots_until_full': server['total_empty_space_plots_until_full'], 'free_space_available': server['free_space_available']}
            log.debug(nas_server) # Should log all nas servers that it is configured to check
            if nas_server['free_space_available']:
                next_nas.append(nas_server)
        if not next_nas: # If we have prioritized filling but there is no more empty drive space available fall back to replacing old plots.
            log.debug('plotter set to prioritize: FILL, however there is no empty space available on configured harvesters.')
            for server in servers:
                nas_server = {'server': server['server'], 'total_plots_until_full': server['total_plots_until_full']}
                log.debug(nas_server) # Should log all nas servers that is is configured to check
                if nas_server['total_plots_until_full'] > 0:
                    next_nas.append(nas_server)
            if not next_nas:
                log.debug('First there was no empty space available on configured harvesters, then we could not find any old plots to replace.')
                return False
            else:
                return sorted(next_nas, key=lambda i: i['total_plots_until_full'], reverse=True)[0].get('server')
        else:
            return sorted(next_nas, key=lambda i: i['total_empty_space_plots_until_full'], reverse=True)[0].get('server')
    else: # Start here is we did not prioritize filling empty space first
        log.debug('plotter set to prioritize: REPLACE')
        for server in servers:
            nas_server = {'server': server['server'], 'total_plots_until_full': server['total_plots_until_full']}
            log.debug(nas_server)
            if nas_server['total_plots_until_full'] > 0:
                next_nas.append(nas_server)
        if not next_nas: # If we cannot find any servers with old plots, go here
            for server in servers:
                nas_server = {'server': server['server'], 'total_empty_space_plots_until_full': server['total_empty_space_plots_until_full'], 'free_space_available': server['free_space_available']}
                log.debug(nas_server)  # Should log all nas servers that it is configured to check
                if nas_server['free_space_available']:
                    next_nas.append(nas_server)
            if not next_nas:
                log.debug('First there was no old plots to replace and then we could not find any free space.')
                return False
            else:
                return sorted(next_nas, key=lambda i: i['total_empty_space_plots_until_full'], reverse=True)[0].get('server')
        else:
            return sorted(next_nas, key=lambda i: i['total_plots_until_full'], reverse=True)[0].get('server')


def check_temp_drive_utilization():
    """
    This function checks our dst drives
    for utilization in excess of the limits we have
    set in our config file and sends us a notification
    in the event we exceed this utilization.
    """
    log.debug('check_temp_drive_utilization() started')
    if chiaplot.get_critical_temp_dir_usage() != {}:
        if not chiaplot.temp_dirs_critical_alert_sent:
            chianas.toggle_alert_sent('temp_dirs_critical_alert_sent')
            for dirs in chiaplot.get_critical_temp_dir_usage().keys():
                log.debug(f'WARNING: {dirs} is nearing capacity. Sending Alert!')
                notify('WARNING: Directory Utilization Nearing Capacity',
                       f'WARNING: {dirs} is nearing Capacity\nPlotting is in Jeopardy!\nCheck Your Drives IMMEDIATELY!')
        else:
            for dirs in chiaplot.get_critical_temp_dir_usage().keys():
                log.debug(f'WARNING: {dirs} is nearing capacity. Alert has already been sent!')
    elif chiaplot.temp_dirs_critical_alert_sent:
        chiaplot.toggle_alert_sent('temp_dirs_critical_alert_sent')
        notify('INFORMATION: Directory Utilization', 'INFORMATION: Your Temp Directory is now below High Capacity Warning\nPlotting will Continue')
    else:
        log.debug('Temp Drive(s) check complete. All OK!')

def check_dst_drive_utilization():
    """
    This function checks our dst drives
    for utilization in excess of the limits we have
    set in our config file and sends us a notification
    in the event we exceed this utilization.
    """
    log.debug('check_dst_drive_utilization() started')
    if chiaplot.get_critical_dst_dir_usage() != {}:
        if not chiaplot.dst_dirs_critical_alert_sent:
            chiaplot.toggle_alert_sent('dst_dirs_critical_alert_sent')
            for dirs in chiaplot.get_critical_dst_dir_usage().keys():
                log.debug(f'WARNING: {dirs} is nearing capacity. Sending Alert!')
                notify('WARNING: Directory Utilization Nearing Capacity',
                       f'WARNING: {dirs} is nearing Capacity\nPlotting is in Jeopardy!\nCheck Your Drives IMMEDIATELY!')
        else:
            for dirs in chiaplot.get_critical_dst_dir_usage().keys():
                log.debug(f'WARNING: {dirs} is nearing capacity. Alert has already been sent!')
    elif chiaplot.dst_dirs_critical_alert_sent:
        chiaplot.toggle_alert_sent('dst_dirs_critical_alert_sent')
        notify('INFORMATION: Directory Utilization', 'INFORMATION: Your Temp Directory is now below High Capacity Warning\nPlotting will Continue')
    else:
        log.debug('DST Drive(s) check complete. All OK!')


def exists_remote(host, path):
    """Test if a file exists at path on a host accessible with SSH."""
    status = subprocess.call(
        ['ssh', host, 'test -f {}'.format(pipes.quote(path))])
    if status == 0:
        return True
    if status == 1:
        return False
    raise Exception('SSH failed')


def system_checks():
    """
    These are the various system checks. Limits are set in the
    configuration file.
    """
    check_temp_drive_utilization()
    check_dst_drive_utilization()


def main():
    log.debug(f'Welcome to plot_manager.py Version: {VERSION}')
    system_checks()
    remote_harvesters_check()
    process_plot()


if __name__ == '__main__':
    main()

