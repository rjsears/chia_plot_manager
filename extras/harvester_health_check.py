#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Simple script that checks to make sure our chia_harvester is running and if not
attempts to (re)start it. Sends notifications when necessary via email to text.

This ONLY checks to see if 'chia_harvester' is a zombie process, or if it is not
running at all. All other psutil p.info(status) just pass through. 

Set the email address and hostname below and load in your root user crontab by utilizing
wpython.py (see below)

I run this by utilizing https://github.com/rjsears/wpython
"""

VERSION = "V0.93 (2021-07-15)"

import psutil
import subprocess
import time


# House Keeping
# Where are we sending the email notification?
notify_address = '8585551212@vtext.com'

# What is our Host Name?
host = 'ChiaNAS01'



def get_process(process_name):
    procs = {p.pid: p.info for p in psutil.process_iter(['status']) if p.name() == process_name}
    for i in procs:
            for j, k in procs[i].items():
                    return (k)

def return_process_status(process_name):
    status = (get_process(process_name))
    if status is None:
        return False
    else:
        return(status)

def check_status(process):
    status = return_process_status(process)
    if not status:
        return ('not_running')
    elif status == 'zombie':
        return ('zombie')
    else:
        return (status)


def start_chia_harvester():
    subprocess.call(['/home/chia/chia-blockchain/venv/bin/chia', 'start', 'harvester', '-r'])

def check_chia_harvester():
    status = check_status('chia_harvester')
    if status == 'zombie':
        start_chia_harvester()
        time.sleep(5)
        status = check_status('chia_harvester')
        if status == 'zombie':
            send_email(notify_address, host, 'Zombie Infection - Attempted Restart Failed - HELP ME!')
            exit()
        else:
            send_email(notify_address, host, 'Zombie Killed, Harvester Restarted')
    elif status == 'not_running':
        start_chia_harvester()
        time.sleep(5)
        status = check_status('chia_harvester')
        if status == 'not_running':
            send_email(notify_address, host, 'Harvester NOT Running - Attempted Start Failed - HELP ME!')
            exit()
        else:
            send_email(notify_address, host, 'Chia Harvester WAS NOT Running, it has been restarted!')
    else:
        print(status)


def send_email(recipient, subject, body):
    try:
        subprocess.run(['mail', '-s', subject, recipient], input=body, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        pass
    except Exception as e:
        pass


def main():
    check_chia_harvester()

if __name__ == '__main__':
    main()
