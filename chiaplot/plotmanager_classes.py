#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Part of drive_manager. These classes are for reading and updating out yaml
config file.
"""

VERSION = "V0.92 (2021-06-04)"

import os
import yaml
from pathlib import Path
import logging
from system_logging import setup_logging


user_home_dir = str(Path.home())
config_file = (user_home_dir + '/.config/plot_manager/plot_manager.yaml')


# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
with open(config_file, 'r') as config:
    server = yaml.safe_load(config)
level = server['log_level']
level = logging._checkLevel(level)
log = logging.getLogger(__name__)
log.setLevel(level)


class PlotManager:
    if not os.path.isfile(config_file):
        log.debug(f'Plot_Manager config file does not exist at: {config_file}')
        log.debug("Please check file path and try again.")
        exit()
    else:
        def __init__(self, configured, hostname, remote_harvesters,
                     notifications, pb, email, sms, temp_dirs, network_interface,
                     plot_dir, warnings, emails, phones, twilio_from, twilio_account,
                     twilio_token, pb_api, logging, log_level):
            self.configured = configured
            self.hostname = hostname
            self.remote_harvesters = remote_harvesters
            self.network_interface = network_interface
            self.notifications = notifications
            self.pb = pb
            self.email = email
            self.sms = sms
            self.warnings = warnings
            self.emails = emails
            self.phones = phones
            self.twilio_from = twilio_from
            self.twilio_account = twilio_account
            self.twilio_token = twilio_token
            self.pb_api = pb_api
            self.temp_dirs = temp_dirs
            self.plot_dir = plot_dir
            self.logging = logging
            self.log_level = log_level

        @classmethod
        def read_configs(cls):
            with open (config_file, 'r') as config:
                server = yaml.safe_load(config)
                return cls(
                    configured=server['configured'],
                    hostname=server['hostname'],
                    remote_harvesters=server['remote_harvesters'],
                    network_interface=server['network_interface'],
                    notifications=server['notifications']['active'],
                    pb=server['notifications']['methods']['pb'],
                    email=server['notifications']['methods']['email'],
                    sms=server['notifications']['methods']['sms'],
                    warnings=server['notifications']['types']['warnings'],
                    emails=server['notifications']['emails'],
                    phones=server['notifications']['phones'],
                    twilio_from=server['notifications']['accounts']['twilio']['from'],
                    twilio_account=server['notifications']['accounts']['twilio']['account'],
                    twilio_token=server['notifications']['accounts']['twilio']['token'],
                    pb_api=server['notifications']['accounts']['pushBullet']['api'],
                    temp_dirs=server['local_plotter']['temp_dirs'],
                    plot_dir=server['local_plotter']['plot_dir'],
                    logging=server['logging'],
                    log_level=server['log_level'])


        def toggle_notification(self, notification):
            if getattr(self, notification):
                print('Changing to False')
                with open (config_file) as f:
                    server = yaml.safe_load(f)
                    server['notifications']['methods'][notification] = False
                    with open('plot_manager.yaml', 'w') as f:
                        yaml.safe_dump(server, f)
            else:
                print ('Changing to True')
                with open(config_file) as f:
                    server = yaml.safe_load(f)
                    server['notifications']['methods'][notification] = True
                    with open(config_file, 'w') as f:
                        yaml.safe_dump(server, f)

        def set_notification(self, notification, value):
            if getattr(self, notification) == value:
                pass
            else:
                with open(config_file) as f:
                    server = yaml.safe_load(f)
                    server['notifications']['methods'][notification] = value
                    with open(config_file, 'w') as f:
                        yaml.safe_dump(server, f)

def main():
    print("Not intended to be run directly.")
    print("This is the systemwide DriveManager Class module.")
    print("It is called by other modules.")
    exit()

if __name__ == '__main__':
    main()
