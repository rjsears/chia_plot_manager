#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Part of drive_manager. These classes are for reading and updating our yaml
config file.
"""

VERSION = "V0.96 (2021-09-05)"

import os
import yaml
from pathlib import Path
import logging
from system_logging import setup_logging
import psutil
from flatten_dict import flatten
from flatten_dict import unflatten
from datetime import datetime

script_path = Path(__file__).parent.resolve()
#user_home_dir = str(Path.home())
config_file = (str(Path.home()) + '/.config/plot_manager/plot_manager.yaml')
#config_file = (user_home_dir + '/.config/plot_manager/plot_manager.yaml')
skel_config_file = script_path.joinpath('plot_manager.skel.yaml')

# Date and Time Stuff
current_military_time = datetime.now().strftime('%Y%m%d%H%M%S')

# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
with open(config_file, 'r') as config:
    server = yaml.safe_load(config)
level = server['log_level']
level = logging._checkLevel(level)
log = logging.getLogger(__name__)
log.setLevel(level)


def config_file_update():
    """
    Function to determine if we need to update our yaml configuration file after an upgrade.
    """
    log.debug('config_file_update() Started....')
    if os.path.isfile(skel_config_file):
        with open(config_file, 'r') as current_config:
            current_config = yaml.safe_load(current_config)
        with open(skel_config_file, 'r') as temp_config:
            temp_config = yaml.safe_load(temp_config)
        temp_current_config = flatten(current_config)
        temp_temp_config = flatten(temp_config)
        updates = (dict((k, v) for k, v in temp_temp_config.items() if k not in temp_current_config))
        if updates != {}:
            copyfile(skel_config_file, (str(Path.home()) + '/.config/plot_manager/Config_Instructions.yaml'))
            copyfile(config_file, (str(Path.home()) + f'/.config/plot_manager/plot_manager.yaml.{current_military_time}'))
            temp_current_config.update(updates)
            new_config = (dict((k, v) for k, v in temp_current_config.items() if k in temp_temp_config))
        else:
            new_config = (dict((k, v) for k, v in temp_current_config.items() if k not in temp_temp_config))
        if new_config != {}:
            new_config = (dict((k, v) for k, v in temp_current_config.items() if k in temp_temp_config))
            current_config = unflatten(new_config)
            current_config.update({'configured': False})
            with open((str(Path.home()) + '/.config/plot_manager/plot_manager.yaml'), 'w') as f:
                yaml.safe_dump(current_config, f)
            log.debug(f'Config File: {config_file} updated. Update as necessary to run this script.')
            exit()
        else:
            log.debug('No config file changes necessary! No changes made.')
    else:
        log.debug('New configuration file not found. No changes made.')



class PlotManager:
    if not os.path.isfile(config_file):
        log.debug(f'Plot_Manager config file does not exist at: {config_file}')
        log.debug("Please check file path and try again.")
        exit()
    else:
        def __init__(self, configured, hostname, pools, remote_harvesters, network_interface_threshold, domain_name,
                     notifications, pb, email, sms, temp_dirs, temp_dirs_critical, remote_harvester_priority, network_interface,
                     dst_dirs, dst_dirs_critical, dst_dirs_critical_alert_sent,temp_dirs_critical_alert_sent,
                     warnings, emails, phones, twilio_from, twilio_account,
                     twilio_token, pb_api, logging, log_level):
            self.configured = configured
            self.hostname = hostname
            self.domain_name = domain_name
            self.pools = pools
            self.remote_harvesters = remote_harvesters
            self.remote_harvester_priority = remote_harvester_priority
            self.network_interface = network_interface
            self.network_interface_threshold = network_interface_threshold
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
            self.temp_dirs_critical = temp_dirs_critical
            self.temp_dirs_critical_alert_sent = temp_dirs_critical_alert_sent
            self.dst_dirs = dst_dirs
            self.dst_dirs_critical = dst_dirs_critical
            self.dst_dirs_critical_alert_sent = dst_dirs_critical_alert_sent
            self.logging = logging
            self.log_level = log_level

        @classmethod
        def read_configs(cls):
            with open (config_file, 'r') as config:
                server = yaml.safe_load(config)
                return cls(
                    configured=server['configured'],
                    hostname=server['hostname'],
                    domain_name=server['domain_name'],
                    pools=server['pools'],
                    remote_harvesters=server['remote_harvesters'],
                    remote_harvester_priority=server['remote_harvester_priority'],
                    network_interface=server['network_interface'],
                    network_interface_threshold=server['network_interface_threshold'],
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
                    temp_dirs=server['local_plotter']['temp_dirs']['dirs'],
                    temp_dirs_critical=server['local_plotter']['temp_dirs']['critical'],
                    temp_dirs_critical_alert_sent=server['local_plotter']['temp_dirs']['critical_alert_sent'],
                    dst_dirs=server['local_plotter']['dst_dirs']['dirs'],
                    dst_dirs_critical=server['local_plotter']['dst_dirs']['critical'],
                    dst_dirs_critical_alert_sent=server['local_plotter']['dst_dirs']['critical_alert_sent'],
                    logging=server['logging'],
                    log_level=server['log_level'])


        def toggle_notification(self, notification):
            if getattr(self, notification):
                print('Changing to False')
                with open(config_file) as f:
                    server = yaml.safe_load(f)
                    server['notifications']['methods'][notification] = False
                    with open(config_file, 'w') as f:
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

        def temp_dir_usage(self):
            temp_dir_usage = {}
            for dir in self.temp_dirs:
                usage = psutil.disk_usage(dir)
                temp_dir_usage[dir] = int(usage.percent)
            return temp_dir_usage

        def get_critical_temp_dir_usage(self):
            paths = self.temp_dir_usage()
            return dict((k, v) for k, v in paths.items() if v > self.temp_dirs_critical)


        def dst_dir_usage(self):
            dst_dir_usage = {}
            for dir in self.dst_dirs:
                usage = psutil.disk_usage(dir)
                dst_dir_usage[dir] = int(usage.percent)
            return dst_dir_usage

        def get_critical_dst_dir_usage(self):
            paths = self.dst_dir_usage()
            return dict((k, v) for k, v in paths.items() if v > self.dst_dirs_critical)


        def toggle_alert_sent(self, alert):
            if alert == 'temp_dirs_critical_alert_sent':
                if getattr(self, alert):
                    print('Changing to False')
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['temp_dirs']['critical_alert_sent'] = False
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)
                else:
                    print ('Changing to True')
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['temp_dirs']['critical_alert_sent'] = True
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)
            elif alert == 'dst_dirs_critical_alert_sent':
                if getattr(self, alert):
                    print('Changing to False')
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['dst_dirs']['critical_alert_sent'] = False
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)
                else:
                    print('Changing to True')
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['dst_dirs']['critical_alert_sent'] = True
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)

def main():
    print("Not intended to be run directly.")
    print("This is the systemwide DriveManager Class module.")
    print("It is called by other modules.")
    exit()

if __name__ == '__main__':
    main()
