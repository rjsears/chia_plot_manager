#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Simple script that checks to make sure our chia_farmer is running and if not
attempts to (re)start it. Sends notifications when necessary via email to text.

Set the email address and hostname below and load in your chia user crontab.

In order to receive email notifications, please make sure you can email utilizing
the linux mail command.

"""

VERSION = "V0.99 (2023-08-24)"

import subprocess
import apt
import os
import configparser
import logging
from system_logging import setup_logging
from system_logging import read_logging_config
from datetime import datetime
import time
from system_info import notify_email_address, notify_sms_address, from_address, host

# Set config
config = configparser.ConfigParser()

# Do some housework
today = datetime.today().strftime('%A').lower()
current_military_time = datetime.now().strftime('%H:%M:%S')
current_timestamp = int(time.time())


# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
level = read_logging_config('farmer_health_config', 'system_logging', 'log_level')
level = logging._checkLevel(level)
log = logging.getLogger(__name__)
log.setLevel(level)

# Setup to read and write to our config file.
# If we are expecting a boolean back pass True/1 for bool,
# otherwise False/0
def read_config_data(file, section, item, bool):
    log.debug('read_config_data() Started')
    pathname = '/home/chia/farmer_health/' + file
    config.read(pathname)
    if bool:
        return config.getboolean(section, item)
    else:
        return config.get(section, item)


def update_config_data(file, section, item, value):
    log.debug('update_config_data() Started')
    pathname = '/home/chia/farmer_health/' + file
    config.read(pathname)
    cfgfile = open(pathname, 'w')
    config.set(section, item, value)
    config.write(cfgfile)
    cfgfile.close()

# First, let's try and detect how we were installed
# Depending on how we were installed (APT vs. Git) will
# depend on how we call chia. If you installed via Git,
# it is assumed that you installed at '/home/chia/', if
# this is incorrect, you need to update the paths below.

def how_installed():
    log.debug('how_installed() called')
    cache = apt.Cache()
    cache.open()
    response = "apt"
    try:
        cache['chia-blockchain'].is_installed or cache['chia-blockchain-cli'].is_installed
    except KeyError:
        log.debug('A Binary APT installation of Chia was not found, falling back to VENV!')
        if os.path.isfile('/home/chia/chia-blockchain/venv/bin/chia'):
            response = "venv"
        else:
            log.debug('A Chia Installation was not found. Exiting!')
            exit()
    return (response)


def is_farmer_running():
    log.debug('is_farmer_running() called')
    # Check to see how we were installed and make sure we were actually installed before running!
    installed = how_installed()
    try:
        if installed == 'apt':
            output = subprocess.check_output(['/usr/bin/chia', 'farm', 'summary'])
        else:
            output = subprocess.check_output(['/home/chia/chia-blockchain/venv/bin/chia', 'farm', 'summary'])
        output = output.decode("utf-8")
        if "Farming status: Farming" in output:
            log.debug('We are Farming')
        else:
            if "Farming status: Not synced or not connected to peers" in output:
                log.debug('We are Syncing')
            else:
                notify('Farmer Error', f'Farmer {host} is NOT Running, attempting a restart!')
                log.critical(f'Farmer {host} is DOWN')
                time.sleep(10) # Let's check a second time before we force reboot the farmer!
                if installed == 'apt':
                    output = subprocess.check_output(['/usr/bin/chia', 'farm', 'summary'])
                else:
                    output = subprocess.check_output(['/home/chia/chia-blockchain/venv/bin/chia', 'farm', 'summary'])
                output = output.decode("utf-8")
                if "Farming status: Farming" in output:
                    log.debug('We are Farming')
                    notify('Farmer back online', f'Farmer {host} is running again!')
                else:
                    if "Farming status: Not synced or not connected to peers" in output:
                        log.debug('We are Still Syncing')
                        notify('Farmer Syncing', f'Farmer {host} is running, but we are still Syncing')
                    else:
                        log.critical(f'Forcing Restart/Reboot of Farmer: {host}')
                        restart_farmer_server()
    except subprocess.CalledProcessError as e:
        log.critical(f'Error: {e}')
        notify('Critical Error', f'Critical Error on: {host}: {e}')


def restart_farmer_server():
    log.debug('restart_farmer_server() called')
    try:
        notify('Attempting Farmer Reboot', f'Attempting a Farmer Reboot on {host}')
        subprocess.call(['sudo', 'reboot'])
    except Exception as e:
        log.critical(f'An Error occurred while restarting {host}: {e}')
        notify('Critical Error on Reboot', f'An Error: {e} occurred while attempting to reboot {host}!')

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
        subprocess.run(['mail', '-s', subject, '-r', from_address, recipient], input=body, encoding='utf-8')
        log.debug(f"Email Notification Sent: Subject: {subject}, Recipient: {recipient}, Message: {body}")
    except subprocess.CalledProcessError as e:
        log.debug(f'send_email error: {e}')
    except Exception as e:
        log.debug(f'send_email: Unknown Error! Email not sent.')


def notify(title, message):
    """ Notify system for email, and sms (via Email to SMS)"""
    log.debug(f'notify() called with Title: {title} and Message: {message}')
    if (read_config_data('farmer_health_config', 'notifications', 'alerting', True)):
        if (read_config_data('farmer_health_config', 'notifications', 'email', True)):
            for email_address in notify_email_address:
                send_email(email_address, title, message)
        if (read_config_data('farmer_health_config', 'notifications', 'sms', True)):
            for email_address in notify_sms_address:
                send_email(email_address, title, message)
    else:
        pass


def main():
    is_farmer_running()

if __name__ == '__main__':
    main()
