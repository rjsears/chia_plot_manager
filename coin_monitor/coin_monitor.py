#!/usr/bin/python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.991 (2023-08-22)"

# Simple script to check to see if we have any new Chia coins.
# This does assume that you installed in '/home/chia/coin_monitor'
# Adjust as necessary if you have installed elsewhere.


import sys
import re
import os
sys.path.append('/home/chia/coin_monitor')
import subprocess
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
import time
import apt


# Set config
config = configparser.ConfigParser()

# Are we utilizing pooling plots? If set to True, this will run a plotnft check
# to see if we have additional chia and claim them if we do. Make sure to set
# your correct plotnft wallet id.
plotnft = True
plotnft_wallet = 2


# Do some housework
today = datetime.today().strftime('%A').lower()
current_military_time = datetime.now().strftime('%H:%M:%S')
current_timestamp = int(time.time())


# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
level = read_logging_config('coin_monitor_config', 'system_logging', 'log_level')
level = logging._checkLevel(level)
log = logging.getLogger(__name__)
log.setLevel(level)

# Setup to read and write to our config file.
# If we are expecting a boolean back pass True/1 for bool,
# otherwise False/0
def read_config_data(file, section, item, bool):
    log.debug('read_config_data() Started')
    pathname = '/home/chia/coin_monitor/' + file
    config.read(pathname)
    if bool:
        return config.getboolean(section, item)
    else:
        return config.get(section, item)


def update_config_data(file, section, item, value):
    log.debug('update_config_data() Started')
    pathname = '/home/chia/coin_monitor/' + file
    config.read(pathname)
    cfgfile = open(pathname, 'w')
    config.set(section, item, value)
    config.write(cfgfile)
    cfgfile.close()

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


# First we need to check if we have a plotnft balance available and if we do, we need to go ahead and claim those chia.
def check_plotnft_balance():
    log.debug('check_plotnft_balance() Started')
    if plotnft:
        log.debug('plotnft configured, checking for pooling coins')
        try:
            if how_installed() == 'apt':
                check_plotnft_balance_output = subprocess.check_output(['/usr/bin/chia', 'plotnft', 'show'])
            else:
                check_plotnft_balance_output = subprocess.check_output(['/home/chia/chia-blockchain/venv/bin/chia', 'plotnft', 'show'])
            plotnft_balance = check_plotnft_balance_output.decode("utf-8")
            for line in plotnft_balance.split('\n'):
                parts = line.strip().split(':', 1)
                if len(parts) == 2 and parts[0] == 'Claimable balance':
                    value_part = parts[1].split()[0]  # Extract the numerical value part
                    if float(value_part) > 0:
                        log.debug(f'You have {value_part} new coins! We will claim them!')
                        log.critical(f'You have {value_part} new coins! We will claim them!')
                        if how_installed() == 'apt':
                            subprocess.check_output(['/usr/bin/chia', 'plotnft', 'claim', '-i', plotnft_wallet])
                        else:
                            subprocess.check_output(['/home/chia/chia-blockchain/venv/bin/chia', 'plotnft', 'claim', '-i', plotnft_wallet])
                else:
                    log.debug('No new Pooling coins found!')
                    break  # No need to continue processing lines
        except subprocess.CalledProcessError as e:
            print("Error:", e)
    else:
        log.debug('plotnft not configured, skipping!')


# Next we need to see if the claim was successful by seeing if we have more coins in out wallet.
# This may actually take a few minutes to show up after we claim them.
def check_for_chia_coins():
    log.debug('check_for_chia_coins() Started')
    if get_total_chia_balance() == float(read_config_data('coin_monitor_config', 'current_coins', 'coins', False)):
        log.debug('No new coins found!')
    else:
        log.info('New Coins Found!')
        total_coins = str(get_total_chia_balance())
        log.critical(f'You now have {total_coins} Chia!')
        update_config_data('coin_monitor_config', 'current_coins', 'coins', total_coins)
        #notify(f"You Now have {read_config_data('coin_monitor_config', 'current_coins', 'coins', False)} Chia Coins",
        #    f"You Now have {read_config_data('coin_monitor_config', 'current_coins', 'coins', False)} Chia Coins")
        send_new_coin_email()

def get_total_chia_balance():
    log.debug('get_total_chia_balance() Started')
    if how_installed() == 'apt':
        check_total_chia_balance_output = subprocess.check_output(['/usr/bin/chia', 'wallet', 'show', '-w', 'standard_wallet'])
    else:
        check_total_chia_balance_output = subprocess.check_output(['/home/chia/chia-blockchain/venv/bin/chia', 'wallet', 'show', '-w', 'standard_wallet'])
    total_chia_balance = check_total_chia_balance_output.decode("utf-8")
    result = float(extract_total_balance(total_chia_balance))
    if result is not None:
        return (result)
    else:
        log.debug("Total Balance not found in the output")

def extract_total_balance(output):
    log.debug('extract_total_balance() Started')
    pattern = r"-Total Balance:\s+([\d.]+)"
    match = re.search(pattern, output)
    if match:
        total_balance = float(match.group(1))
        return total_balance
    else:
        return None


# Here we check to see if we are configured to send a "per new coin" email and if so, we send that email.
def send_new_coin_email():
    log.debug('send_new_coin_email() Started')
    if read_config_data('coin_monitor_config', 'notifications', 'per_coin_email', True):
        for email_address in system_info.new_coin_email:
            send_template_email(template='new_coin.html',
                                recipient=email_address,
                                subject='New Chia Coin Received!\nContent-Type: text/html',
                                current_time=current_military_time,
                                current_chia_coins=read_config_data('coin_monitor_config', 'current_coins', 'coins', False))
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
        pb = Pushbullet(system_info.pushbilletAPI)
        push = pb.push_note(title, message)
        log.debug(f"Pushbullet Notification Sent: {title} - {message}")
    except pb_errors.InvalidKeyError as e:
        log.debug(f'Pushbullet Exception: Invalid API Key! Message not sent.')
    except Exception as e:
        log.debug(f'Pushbullet Exception: Unknown Pushbullet Error: {e}. Message not sent.')



def send_sms_notification(body, phone_number):
    """Part of our notification system. This handles sending SMS messages."""
    try:
        client = Client(system_info.twilio_account, system_info.twilio_token)
        message = client.messages.create(to=phone_number, from_=system_info.twilio_from, body=body)
        log.debug(f"SMS Notification Sent: {body}.")
    except TwilioRestException as e:
        log.debug(f'Twilio Exception: {e}. Message not sent.')
    except Exception as e:
        log.debug(f'Twilio Exception: {e}. Message not sent.')


def notify(title, message):
    """ Notify system for email, pushbullet and sms (via Twilio)"""
    log.debug(f'notify() called with Title: {title} and Message: {message}')
    if (read_config_data('coin_monitor_config', 'notifications', 'alerting', True)):
        if (read_config_data('coin_monitor_config', 'notifications', 'pb', True)):
            send_push_notification(title, message)
        if (read_config_data('coin_monitor_config', 'notifications', 'email', True)):
            for email_address in system_info.alert_email:
                send_email(email_address, title, message)
        if (read_config_data('coin_monitor_config', 'notifications', 'sms', True)):
            for phone_number in system_info.twilio_to:
                send_sms_notification(message, phone_number)
    else:
        pass


# Thank You - https://frankcorso.dev/email-html-templates-jinja-python.html
def send_template_email(template, recipient, subject, **kwargs):
    """Sends an email using a jinja template."""
    env = Environment(
        loader=PackageLoader('coin_monitor', 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template)
    send_email(recipient, subject, template.render(**kwargs))


def main():
    how_installed()
    check_plotnft_balance()
    check_for_chia_coins()


if __name__ == '__main__':
    main()
