#!/usr/bin/python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.3 (2021-04-06)"

# Simple script to check to see if we have any new Chia coins.
# This is NOT 100% foolproof as it just reads the log files,
# always check your wallet for actual coin information.



import sys
import re

sys.path.append('/root/coin_monitor')
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
config = configparser.ConfigParser()
import mmap



# Do some housework
today = datetime.today().strftime('%A').lower()
current_military_time = datetime.now().strftime('%H:%M:%S')
current_timestamp = int(time.time())

# Where is Chia our logfile located?
chia_log = '/home/chia/.chia/mainnet/log/debug.log'
new_coin_log = '/root/coin_monitor/logs/new_coins.log'

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
    pathname = '/root/coin_monitor/' + file
    config.read(pathname)
    if bool:
        return config.getboolean(section, item)
    else:
        return config.get(section, item)


def update_config_data(file, section, item, value):
    pathname = '/root/coin_monitor/' + file
    config.read(pathname)
    cfgfile = open(pathname, 'w')
    config.set(section, item, value)
    config.write(cfgfile)
    cfgfile.close()


def check_for_chia_coins():
    log.debug('check_for_chia_coins() Started')
    coin_pattern = re.compile(r'\bAdding coin')
    read_chia_log_started = True
   # winning_total = 0
    with open (chia_log, 'rt') as my_chia_logfile:
        for line in my_chia_logfile:
            if coin_pattern.search(line) != None:
                new_coin = []
                new_coin.append(re.match((r'[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,3})'), line).group(0))
                new_coin.append(re.search((r"[0-9]{8,13}"), line).group(0))
                with open (new_coin_log, 'rb', 0) as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as coin:
                    if coin.find(bytearray(str(new_coin[0]), encoding='utf8')) != -1:
                        log.debug(f'Found coins that were already accounted for in the log!: {new_coin}')
                    else:
                        log.critical(new_coin)
                        log.info(f'New Coins Found!{new_coin}')
                        if read_chia_log_started:
                            update_config_data('coin_monitor_config', 'current_coins', 'coins', str(
                                int(read_config_data('coin_monitor_config', 'current_coins', 'coins', False)) + 2))
                            notify(f"You Now have {read_config_data('coin_monitor_config', 'current_coins', 'coins', False)} Chia Coins",
           f"You Now have {read_config_data('coin_monitor_config', 'current_coins', 'coins', False)} Chia Coins")
                            send_new_coin_email()
                            read_chia_log_started = False
                        else:
                            pass

def send_new_coin_email():
    if read_config_data('coin_monitor_config', 'notifications', 'per_coin', True):
        for email_address in system_info.alert_email:
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
    check_for_chia_coins()

if __name__ == '__main__':
    main()
