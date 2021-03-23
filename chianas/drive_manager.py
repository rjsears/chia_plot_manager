#!/usr/bin/python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.2 (2021-03-23)"

### Simple python script that helps to move my chia plots from my plotter to
### my nas. I wanted to use netcat as it was much faster on my 10GBe link than
### rsync and the servers are secure so I wrote this script to manage that
### move process. It will get better with time as I add in error checking and
### other things like notifications and stuff.

# Updates
#   V0.2 2021-30-23
# - Moved system logging types to plot_manager_config and update
#   necessary functions.
# - Added per_plot system notification function (send_new_plot_notification())
# - Updated read_config_data() to support ConfigParser boolean returns
# - Updated necessary functions for read_config_data() change


import os
import sys
sys.path.append('/root/plot_manager')
import subprocess
import shutil
import psutil
from pySMART import Device #CAUTION - DO NOT use PyPI version, use https://github.com/truenas/py-SMART
from psutil._common import bytes2human
import logging
from system_logging import setup_logging
from system_logging import read_logging_config
import system_info
from pushbullet import Pushbullet, errors as pb_errors
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import configparser
from jinja2 import Environment, PackageLoader, select_autoescape
from datetime import datetime
from datetime import timedelta
import time
config = configparser.ConfigParser()

import sentry_sdk
sentry_sdk.init(
   "https://xxxxxxxxxxxxxxxxx8@o3xxxxxx.ingest.sentry.io/5xxxxxxxxx",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)
from sentry_sdk import capture_exception


# Let's do some housekeeping
nas_server = 'chiaplot01'
plot_size_k = 108995911228
plot_size_g = 101.3623551
receive_script = '/root/plot_manager/receive_plot.sh'
today = datetime.today().strftime('%A').lower()
current_military_time = datetime.now().strftime('%H:%M:%S')
current_timestamp = int(time.time())

# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
level = read_logging_config('plot_manager_config', 'system_logging', 'log_level')
level = logging._checkLevel(level)
log = logging.getLogger(__name__)
log.setLevel(level)

# Setup to read and write to our config file.
# If we are expecting a boolean back pass True/1 for bool,
# otherwise False/0
def read_config_data(file, section, item, bool):
    pathname = '/root/plot_manager/' + file
    config.read(pathname)
    if bool:
        return config.getboolean(section, item)
    else:
        return config.get(section, item)

def update_config_data(file, section, item, value):
    pathname = '/root/plot_manager/' + file
    config.read(pathname)
    cfgfile = open(pathname, 'w')
    config.set(section, item, value)
    config.write(cfgfile)
    cfgfile.close()

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
        return int(bytesto(shutil.disk_usage(get_device_info_by_drive_number(drive)[0][0])[0],'g'))
    if action == 'space_used':
        return int(bytesto(shutil.disk_usage(get_device_info_by_drive_number(drive)[0][0])[1],'g'))
    if action == 'space_free':
        return int(bytesto(shutil.disk_usage(get_device_info_by_drive_number(drive)[0][0])[2],'g'))
    if action == 'space_free_plots':
        return int(bytesto(shutil.disk_usage(get_device_info_by_drive_number(drive)[0][0])[2],'g') / plot_size_g)
    if action == 'space_free_plots_by_mountpoint':
        return int(bytesto(shutil.disk_usage(drive)[2],'g') / plot_size_g)
    if action == 'total_current_plots':
        return int(bytesto(shutil.disk_usage(get_mountpoint_by_drive_number(drive)[0])[1], 'g') / plot_size_g)
    if action == 'total_current_plots_by_mountpoint':
        return int(bytesto(shutil.disk_usage(drive)[1], 'g') / plot_size_g)

def get_mountpoint_by_drive_number(drive):
    """
    This accepts a drive number (drive0) and returns the device assignment: /dev/sda1 and mountpoint:
    /mnt/enclosure0/front/column0/drive0
    """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/enclosure') and p.mountpoint.endswith(drive):
            return [(p.mountpoint)]

def get_device_info_by_drive_number(drive):
    """
    This accepts a drive number (drive0) and returns the device assignment: /dev/sda1 and mountpoint
    """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/enclosure') and p.mountpoint.endswith(drive):
            return [(p.mountpoint, p.device)]

def get_device_by_mountpoint(mountpoint):
    """
        This accepts a mountpoint and returns the device assignment: /dev/sda1 and mountpoint
        """
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith(mountpoint):
            return [(p.mountpoint, p.device)]

def get_list_of_plot_drives():
    """
    Return list of tuples of all available plot drives on the system and the device assignment
    [('/mnt/enclosure0/front/column0/drive3', '/dev/sde1')]
    ===> Currently Unused
    """
    partitions = psutil.disk_partitions(all=False)
    mountpoint = []
    for p in partitions:
        if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/enclosure'):
            mountpoint.append((p.mountpoint, p.device, p.fstype))
    return mountpoint


# Thank you: https://gist.github.com/shawnbutts/3906915
def bytesto(bytes, to, bsize=1024):
    a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
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
    """
    available_drives = []
    for part in psutil.disk_partitions(all=False):
        if part.device.startswith('/dev/sd') and part.mountpoint.startswith('/mnt/enclosure') and get_drive_info('space_free_plots_by_mountpoint', part.mountpoint)  >= 1:
            available_drives.append((part.mountpoint, part.device))
    return (sorted(available_drives, key=lambda x: x[1]))

def get_plot_drive_to_use():
    """
    This looks at all available plot drives that start with /dev/sd and include
    /mnt/enclosure in the mount path (this covers all of my plot drives), it then
    looks for any drive that has enough space for at least one plot (k32), sorts
    that list based on the /dev/sdx sorting and then returns the mountpoint of the
    device we want to use. Basically the same as above but simply returns the 'next'
    available drive we want to use.
    #TODO incorporate in get_plot_drive_with_available_space()
    """
    available_drives = []
    for part in psutil.disk_partitions(all=False):
        if part.device.startswith('/dev/sd') and part.mountpoint.startswith('/mnt/enclosure') and get_drive_info('space_free_plots_by_mountpoint', part.mountpoint)  >= 1:
            available_drives.append((part.mountpoint, part.device))
    return (sorted(available_drives, key=lambda x: x[1]))[0][0]

def get_current_plot_drive_info():
    """
    Designed for debugging and logging purposes when we switch drives
    """
    return Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).temperature


def log_drive_report():
    """
    Logs a drive report of our newly selected plot drive
    """
    templ = "%-15s %6s %15s %12s %10s  %5s"
    log.info(templ % ("New Plot Drive", "Size", "Avail Plots", "Serial #", "Temp °C",
                      "Mount Point"))

    usage = psutil.disk_usage(get_device_by_mountpoint(get_plot_drive_to_use())[0][0])

    log.info(templ % (
        get_device_by_mountpoint(get_plot_drive_to_use())[0][1],
        bytes2human(usage.total),
        get_drive_info('space_free_plots_by_mountpoint', (get_plot_drive_to_use())),
        Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).serial,
        Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).temperature,
        get_device_by_mountpoint(get_plot_drive_to_use())[0][0]))

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
    # First determine if there is a remote file transfer in process. If there is, pass until it is done:
    if os.path.isfile(read_config_data('plot_manager_config', 'remote_transfer', 'remote_transfer_active')):
        log.debug('Remote Transfer in Progress, will try again soon!')
        quit()
    else:
        current_plotting_drive = read_config_data('plot_manager_config', 'plotting_drives', 'current_plotting_drive')
        if current_plotting_drive == get_plot_drive_to_use():
            log.debug(f'Currently Configured Plot Drive: {current_plotting_drive}')
            log.debug(f'System Selected Plot Drive:      {get_plot_drive_to_use()}')
            log.debug('Configured and Selected Drives Match!')
            log.debug(f'No changes necessary to {receive_script}')
            log.debug(f'Plots left available on configured plotting drive: {get_drive_info("space_free_plots_by_mountpoint", current_plotting_drive)}')
        else:
            send_new_plot_disk_email()  # This is the full Plot drive report. This is in addition to the generic email sent by the
            # notify() function.
            notify('Plot Drive Updated', f'Plot Drive Updated: Was: {current_plotting_drive},  Now: {get_plot_drive_to_use()}')
            f = open(receive_script, 'w+')
            f.write('#! /bin/bash \n')
            f.write(f'nc -l -q5 -p 4040 > "{get_plot_drive_to_use()}/$1" < /dev/null')
            f.close()
            update_config_data('plot_manager_config', 'plotting_drives', 'current_plotting_drive', get_plot_drive_to_use())
            log.info(f'Updated {receive_script} and system config file with new plot drive.')
            log.info(f'Was: {current_plotting_drive},  Now: {get_plot_drive_to_use()}')
            log_drive_report()


def send_new_plot_disk_email():
    usage = psutil.disk_usage(get_device_by_mountpoint(get_plot_drive_to_use())[0][0])
    current_plotting_drive = read_config_data('plot_manager_config', 'plotting_drives', 'current_plotting_drive', False)
    if read_config_data('plot_manager_config', 'notifications', 'new_plot_drive', True):
        for email_address in system_info.alert_email:
            send_template_email(template='new_plotting_drive.html',
                                recipient=email_address,
                                subject='New Plotting Drive Selected\nContent-Type: text/html',
                                current_time=current_military_time,
                                nas_server=nas_server,
                                previous_plotting_drive=current_plotting_drive,
                                plots_on_previous_plotting_drive=get_drive_info('total_current_plots_by_mountpoint',
                                                                                current_plotting_drive),
                                current_plotting_drive_by_mountpoint=get_plot_drive_to_use(),
                                current_plotting_drive_by_device=get_device_by_mountpoint(get_plot_drive_to_use())[0][1],
                                drive_size=bytes2human(usage.total),
                                plots_available=get_drive_info('space_free_plots_by_mountpoint', (get_plot_drive_to_use())),
                                drive_serial_number=Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).serial,
                                current_drive_temperature=Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).temperature,
                                smart_health_assessment=Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).assessment,
                                total_serverwide_plots=get_all_available_system_space('used')[1],
                                total_number_of_drives=get_all_available_system_space('total')[0],
                                total_k32_plots_until_full=get_all_available_system_space('free')[1],
                                max_number_of_plots=get_all_available_system_space('total')[1])
    else:
        pass


def send_daily_update_email():
    usage = psutil.disk_usage(get_device_by_mountpoint(get_plot_drive_to_use())[0][0])
    if read_config_data('plot_manager_config', 'notifications', 'daily_update', True):
        for email_address in system_info.alert_email:
            send_template_email(template='daily_update.html',
                                recipient=email_address,
                                subject='NAS Server Daily Update\nContent-Type: text/html',
                                current_time=current_military_time,
                                nas_server=nas_server, current_plotting_drive_by_mountpoint=get_plot_drive_to_use(),
                                current_plotting_drive_by_device=get_device_by_mountpoint(get_plot_drive_to_use())[0][1],
                                drive_size=bytes2human(usage.total),
                                drive_serial_number=Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).serial,
                                current_drive_temperature=Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).temperature,
                                smart_health_assessment=Device(get_device_by_mountpoint(get_plot_drive_to_use())[0][1]).assessment,
                                total_serverwide_plots=get_all_available_system_space('used')[1],
                                total_number_of_drives=get_all_available_system_space('total')[0],
                                total_k32_plots_until_full=get_all_available_system_space('free')[1],
                                max_number_of_plots=get_all_available_system_space('total')[1])
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
        capture_exception(e)
    except Exception as e:
        log.debug(f'send_email: Unknown Error! Email not sent.')
        capture_exception(e)


# Setup to send out Pushbullet alerts. Pushbullet config is in system_info.py
def send_push_notification(title, message):
    """Part of our notification system. This handles sending PushBullets."""
    try:
        pb = Pushbullet(system_info.pushbilletAPI)
        push = pb.push_note(title, message)
        log.debug(f"Pushbullet Notification Sent: {title} - {message}")
    except pb_errors.InvalidKeyError as e:
        log.debug(f'Pushbullet Exception: Invalid API Key! Message not sent.')
        capture_exception(e)
    except Exception as e:
        log.debug(f'Pushbullet Exception: Unknown Pushbullet Error: {e}. Message not sent.')
        capture_exception(e)


def send_sms_notification(body, phone_number):
    """Part of our notification system. This handles sending SMS messages."""
    try:
        client = Client(system_info.twilio_account, system_info.twilio_token)
        message = client.messages.create(to=phone_number, from_=system_info.twilio_from, body=body)
        log.debug(f"SMS Notification Sent: {body}.")
    except TwilioRestException as e:
        log.debug(f'Twilio Exception: {e}. Message not sent.')
        capture_exception(e)
    except Exception as e:
        log.debug(f'Twilio Exception: {e}. Message not sent.')
        capture_exception(e)


def notify(title, message):
    """ Notify system for email, pushbullet and sms (via Twilio)"""
    if (read_config_data('plot_manager_config', 'notifications', 'alerting', True)):
        if (read_config_data('plot_manager_config', 'notifications', 'pb', True)):
            send_push_notification(title, message)
        if (read_config_data('plot_manager_config', 'notifications', 'email', True)):
            for email_address in system_info.alert_email:
                send_email(email_address, title, message)
        if (read_config_data('plot_manager_config', 'notifications', 'sms', True)):
            for phone_number in system_info.twilio_to:
                send_sms_notification(message, phone_number)
    else:
        pass

# Thank You - https://frankcorso.dev/email-html-templates-jinja-python.html
def send_template_email(template, recipient, subject, **kwargs):
    """Sends an email using a jinja template."""
    env = Environment(
        loader=PackageLoader('drive_manager','templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template)
    send_email(recipient, subject, template.render(**kwargs))

# This function called from crontab:
# 01 01 * * * cd /root/plot_manager/ && /usr/bin/python3 -c 'from drive_manager import *; send_daily_email()' >/dev/null 2>&1
def send_daily_email():
    log.debug('send_daily_email() Started')
    send_daily_update_email()
    log.info('Daily Update Email Sent!')


def send_new_plot_notification():
    log.debug('send_new_plot_notification() Started')
    if os.path.isfile('new_plot_received'):
        log.debug('New Plot Received')
        if read_config_data('plot_manager_config', 'notifications', 'per_plot', True):
            notify('New Plot Received', 'New Plot Received')
        os.remove('new_plot_received')


def main():
    send_new_plot_notification()
    update_receive_plot()


if __name__ == '__main__':
    main()
