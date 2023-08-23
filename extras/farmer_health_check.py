#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Simple script that checks to make sure our chia_farmer is running and if not
attempts to (re)start it. Sends notifications when necessary via email to text.

Set the email address and hostname below and load in your chia user crontab.

In order to receive email notifications, please make sure you can email utilizing
the linux mail command.

"""

VERSION = "V0.991 (2023-08-22)"

import subprocess
import time
import apt
import os

# House Keeping
# Where are we sending the email notification?
notify_address = '8585551212@vtext.com' # Replace with your Email
from_address = 'chianode1@yourdomain.com' # Replace with correct 'From' address

# What is our Host Name?
host = 'chianode01'


# First, let's try and detect how we were installed
# Depending on how were were installed (APT vs. Git) will
# depend on how we call chia. If you installed via Git,
# it is assumed that you installed at '/home/chia/', if
# this is incorrect, you need to update the paths below.
# This works for Ubuntu so it may not work for your distro!

def how_installed():
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
    return (response)

# This basically makes a call to the Chia daemon and checks to see if we are
# actually "Farming". If not, it checks a second time and then reboots the farmer.

def is_farmer_running():
    installed = how_installed()
    try:
        if installed == 'apt':
            output = subprocess.check_output(['/usr/bin/chia', 'farm', 'summary'])
        else:
            output = subprocess.check_output(['/home/chia/chia-blockchain/venv/bin/chia', 'farm', 'summary'])
        output = output.decode("utf-8")
        if "Farming status: Farming" in output:
            print("We are Farming")
        else:
            if "Farming status: Not synced or not connected to peers" in output:
                print("We are Syncing")
            else:
                send_email(notify_address, host, 'Farmer is NOT Running, attempting a restart!')
                print("Farmer is DOWN")
                time.sleep(10) # Let's check a second time before we force reboot the farmer!
                if installed == 'apt':
                    output = subprocess.check_output(['/usr/bin/chia', 'farm', 'summary'])
                else:
                    output = subprocess.check_output(['/home/chia/chia-blockchain/venv/bin/chia', 'farm', 'summary'])
                output = output.decode("utf-8")
                if "Farming status: Farming" in output:
                    print("We are Farming")
                    send_email(notify_address, host, 'Farmer is running again!')
                else:
                    if "Farming status: Not synced or not connected to peers" in output:
                        print("We are Still Syncing")
                        send_email(notify_address, host, 'Farmer is running, but we are still Syncing')
                    else:
                        restart_farmer_server()
    except subprocess.CalledProcessError as e:
        print("Error:", e)
        send_email(notify_address, host, 'farmer_health_check() Unknown Error!')

def restart_farmer_server():
    try:
        send_email(notify_address, host, 'Attempting a Farmer Reboot')
        subprocess.call(['sudo', 'reboot'])
    except Exception as e:
        print("An error occurred while restarting the server:", e)
        send_email(notify_address, host, 'An Error occurred while attempting to reboot your farmer!')

def send_email(recipient, subject, body):
    try:
        subprocess.run(['mail', '-s', subject, '-r', from_address, recipient], input=body, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        pass
    except Exception as e:
        pass


def main():
    how_installed()
    is_farmer_running()

if __name__ == '__main__':
    main()
