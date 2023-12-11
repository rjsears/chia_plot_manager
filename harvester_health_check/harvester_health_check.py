#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Simple script that checks to make sure our chia_harvester is running and if not
attempts to (re)start it. Sends notifications when necessary via email to text.

This ONLY checks to see if 'chia_harvester' is a zombie process, or if it is not
running at all. All other psutil p.info(status) just pass through.

Set the email address and hostname below and load in your chia user crontab.
"""
VERSION = "V1.00a (2023-12-10)"

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
import psutil

# Gigahorse in use?
# If you are farming or plotting/farming with GigaHorse, set this to 'True'. If
# you do not know what Gigahorse is, set this to 'False'.

# IMPORTANT: We assume Gigihorse is installed at `/home/chia/gigahorse', if it
# is installed elsewhere, please make the necessary changes to the code.
gigahorse = True



# Set config
config = configparser.ConfigParser()

# Do some housework
today = datetime.today().strftime('%A').lower()
current_military_time = datetime.now().strftime('%H:%M:%S')
current_timestamp = int(time.time())


# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
level = read_logging_config('harvester_health_config', 'system_logging', 'log_level')
level = logging._checkLevel(level)
log = logging.getLogger(__name__)
log.setLevel(level)

# Setup to read and write to our config file.
# If we are expecting a boolean back pass True/1 for bool,
# otherwise False/0
def read_config_data(file, section, item, bool):
    log.debug('read_config_data() Started')
    pathname = '/home/chia/harvester_health/' + file
    config.read(pathname)
    if bool:
        return config.getboolean(section, item)
    else:
        return config.get(section, item)

def update_config_data(file, section, item, value):
    log.debug('update_config_data() Started')
    pathname = '/home/chia/harvester_health/' + file
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
    log.debug('how_installed() Started')
    if gigahorse:
        response = 'gigahorse'
    else:
        cache = apt.Cache()
        cache.open()
        response = "apt"
        try:
            cache['chia-blockchain'].is_installed or cache['chia-blockchain-cli'].is_installed
        except KeyError:
            if os.path.isfile('/home/chia/chia-blockchain/venv/bin/chia'):
                response = "venv"
            else:
                log.debug('A Chia Installation was not found. Exiting!')
                exit()
    log.debug(f'how_installed() returned: {response}')
    return (response)


def get_process(process_name):
    log.debug('get_process() called')
    procs = {p.pid: p.info for p in psutil.process_iter(['status']) if p.name() == process_name}
    for i in procs:
            for j, k in procs[i].items():
                    return (k)

def return_process_status(process_name):
    log.debug('return_process_status() called')
    status = (get_process(process_name))
    if status is None:
        return False
    else:
        return(status)

def check_status(process):
    log.debug('check_status() called')
    status = return_process_status(process)
    if not status:
        return ('not_running')
    elif status == 'zombie':
        return ('zombie')
    else:
        return (status)


def start_chia_harvester():
    log.debug('start_chia_harvester() called')
    installed = how_installed()
    if installed == 'gigahorse':
        output = subprocess.check_output(['/home/chia/gigahorse/chia.bin', 'farm', 'summary'])
    elif installed == 'apt':
        subprocess.call(['/usr/bin/chia', 'stop', '-d', 'all'])
        time.sleep(10)
        subprocess.call(['/usr/bin/chia', 'start', 'harvester'])
    else:
        subprocess.call(['/home/chia/chia-blockchain/venv/bin/chia', 'stop', '-d', 'all'])
        time.sleep(10)
        subprocess.call(['/home/chia/chia-blockchain/venv/bin/chia', 'start', 'harvester', '-r'])

def check_chia_harvester():
    log.debug('check_chia_haravester() called')
    status = check_status('chia_harvester')
    if status == 'zombie':
        start_chia_harvester()
        time.sleep(10)
        status = check_status('chia_harvester')
        if status == 'zombie':
            notify('Zombie Infection', f'Harvester {host} has a Zombie Infection - Attempted Restart Failed - HELP ME!')
            log.debug('Zombie detected and we could not restart, we are exiting....')
            exit()
        else:
            send_email(notify_email_address, host, 'Zombie Killed, Harvester Restarted')
            notify('Zombie Infection Killed', f'Harvester {host} had a Zombie Infection - Attempted Restart Succeeded')
            log.debug('Zombie detected and Harvester Restart successful....')
    elif status == 'not_running':
        start_chia_harvester()
        time.sleep(5)
        status = check_status('chia_harvester')
        if status == 'not_running':
            notify('Harvester Not Running!', f'Harvester {host} NOT Running - Attempted Start Failed - HELP ME!')
            log.debug('Harvester not running and an attempted restart failed...we are exiting')
            exit()
        else:
            notify('Harvester Restart Successful', f'Harvester {host} has been restarted.')
            log.debug('Harvester not running and an attempted restart was successful.....')
    else:
        print(status)

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
    if (read_config_data('harvester_health_config', 'notifications', 'alerting', True)):
        if (read_config_data('harvester_health_config', 'notifications', 'email', True)):
            for email_address in notify_email_address:
                send_email(email_address, title, message)
        if (read_config_data('harvester_health_config', 'notifications', 'sms', True)):
            for email_address in notify_sms_address:
                send_email(email_address, title, message)
    else:
        pass




def main():
    log.debug('harvester_health_check.py started')
    check_chia_harvester()

if __name__ == '__main__':
    main()
