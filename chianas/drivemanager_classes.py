#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Part of drive_manager. These classes are for reading and updating out yaml
config file.
"""

VERSION = "V0.96 (2021-09-05)"

import os
import yaml
from pathlib import Path
import logging
from system_logging import setup_logging
import psutil
from shutil import copyfile
from flatten_dict import flatten
from flatten_dict import unflatten
from datetime import datetime
from glob import glob
import os
from os.path import abspath
from natsort import natsorted

script_path = Path(__file__).parent.resolve()

# Date and Time Stuff
current_military_time = datetime.now().strftime('%Y%m%d%H%M%S')

config_file = (str(Path.home()) + '/.config/plot_manager/plot_manager.yaml')
skel_config_file = script_path.joinpath('plot_manager.skel.yaml')

# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
with open(config_file, 'r') as config:
    server = yaml.safe_load(config)
level = server['log_level']
level = logging._checkLevel(level)
log = logging.getLogger('drivemanager_classes.py')
log.setLevel(level)

class DriveManager:
    if not os.path.isfile(config_file):
        log.debug(f'Plot_Manager config file does not exist at: {config_file}')
        log.debug("Please check file path and try again.")
        exit()
    else:
        def __init__(self, configured, hostname, pools, replace_non_pool_plots, fill_empty_drives_first, empty_drives_low_water_mark, chia_log_file, chia_config_file,
                     remote_harvester_reports, remote_harvesters, notifications, pb, email, sms, daily_update, new_plot_drive, per_plot,
                     local_plotter, temp_dirs, temp_dirs_critical, temp_dirs_critical_alert_sent, dst_dirs, dst_dirs_critical,
                     dst_dirs_critical_alert_sent, warnings, emails, phones, twilio_from, twilio_account, twilio_token, pb_api,
                     current_internal_drive, current_plotting_drive, total_plot_highwater_warning, total_plots_alert_sent, plot_receive_interface_threshold,
                     current_total_plots_midnight, current_total_plots_daily, offlined_drives, logging, log_level, plot_receive_interface,
                     current_portable_plots_midnight, current_portable_plots_daily, current_plot_replacement_drive, local_move_error, local_move_error_alert_sent):
            self.configured = configured
            self.hostname = hostname
            self.pools = pools
            self.replace_non_pool_plots = replace_non_pool_plots
            self.fill_empty_drives_first = fill_empty_drives_first
            self.empty_drives_low_water_mark = empty_drives_low_water_mark
            self.chia_log_file = chia_log_file
            self.chia_config_file = chia_config_file
            self.remote_harvester_reports = remote_harvester_reports
            self.remote_harvesters = remote_harvesters
            self.notifications = notifications
            self.pb = pb
            self.email = email
            self.sms = sms
            self.daily_update = daily_update
            self.new_plot_drive = new_plot_drive
            self.per_plot = per_plot
            self.warnings = warnings
            self.emails = emails
            self.phones = phones
            self.twilio_from = twilio_from
            self.twilio_account = twilio_account
            self.twilio_token = twilio_token
            self.pb_api = pb_api
            self.local_plotter = local_plotter
            self.temp_dirs = temp_dirs
            self.temp_dirs_critical = temp_dirs_critical
            self.temp_dirs_critical_alert_sent = temp_dirs_critical_alert_sent
            self.dst_dirs = dst_dirs
            self.dst_dirs_critical = dst_dirs_critical
            self.dst_dirs_critical_alert_sent = dst_dirs_critical_alert_sent
            self.current_internal_drive = current_internal_drive
            self.current_plotting_drive = current_plotting_drive
            self.total_plot_highwater_warning = total_plot_highwater_warning
            self.total_plots_alert_sent = total_plots_alert_sent
            self.current_portable_plots_midnight = current_portable_plots_midnight
            self.current_portable_plots_daily = current_portable_plots_daily
            self.current_total_plots_midnight = current_total_plots_midnight
            self.current_total_plots_daily = current_total_plots_daily
            self.offlined_drives = offlined_drives
            self.logging = logging
            self.log_level = log_level
            self.plot_receive_interface = plot_receive_interface
            self.plot_receive_interface_threshold = plot_receive_interface_threshold
            self.current_plot_replacement_drive = current_plot_replacement_drive
            self.local_move_error = local_move_error
            self.local_move_error_alert_sent = local_move_error_alert_sent

        @classmethod
        def read_configs(cls):
            with open (config_file, 'r') as config:
                server = yaml.safe_load(config)
                return cls(
                    configured=server['configured'],
                    hostname=server['hostname'],
                    pools=server['pools']['active'],
                    replace_non_pool_plots=server['pools']['replace_non_pool_plots'],
                    fill_empty_drives_first=server['pools']['fill_empty_drives_first'],
                    empty_drives_low_water_mark=server['pools']['empty_drives_low_water_mark'],
                    chia_log_file=server['chia_log_file'],
                    chia_config_file=server['chia_config_file'],
                    remote_harvester_reports=server['remote_harvester_reports']['active'],
                    remote_harvesters=server['remote_harvester_reports']['remote_harvesters'],
                    notifications=server['notifications']['active'],
                    pb=server['notifications']['methods']['pb'],
                    email=server['notifications']['methods']['email'],
                    sms=server['notifications']['methods']['sms'],
                    daily_update=server['notifications']['types']['daily_update'],
                    new_plot_drive=server['notifications']['types']['new_plot_drive'],
                    per_plot=server['notifications']['types']['per_plot'],
                    warnings=server['notifications']['types']['warnings'],
                    emails=server['notifications']['emails'],
                    phones=server['notifications']['phones'],
                    twilio_from=server['notifications']['accounts']['twilio']['from'],
                    twilio_account=server['notifications']['accounts']['twilio']['account'],
                    twilio_token=server['notifications']['accounts']['twilio']['token'],
                    pb_api=server['notifications']['accounts']['pushBullet']['api'],
                    local_plotter=server['local_plotter']['active'],
                    temp_dirs=server['local_plotter']['temp_dirs']['dirs'],
                    temp_dirs_critical=server['local_plotter']['temp_dirs']['critical'],
                    temp_dirs_critical_alert_sent=server['local_plotter']['temp_dirs']['critical_alert_sent'],
                    dst_dirs=server['local_plotter']['dst_dirs']['dirs'],
                    dst_dirs_critical=server['local_plotter']['dst_dirs']['critical'],
                    dst_dirs_critical_alert_sent=server['local_plotter']['dst_dirs']['critical_alert_sent'],
                    current_internal_drive=server['local_plotter']['current_internal_drive'],
                    current_plotting_drive=server['harvester']['current_plotting_drive'],
                    total_plot_highwater_warning=server['harvester']['total_plot_highwater_warning'],
                    total_plots_alert_sent=server['harvester']['total_plots_alert_sent'],
                    current_total_plots_midnight=server['harvester']['current_total_plots_midnight'],
                    current_total_plots_daily=server['harvester']['current_total_plots_daily'],
                    current_portable_plots_midnight=server['pools']['current_portable_plots_midnight'],
                    current_portable_plots_daily=server['pools']['current_portable_plots_daily'],
                    offlined_drives=server['harvester']['offlined_drives'],
                    logging=server['logging'],
                    log_level=server['log_level'],
                    plot_receive_interface=server['plot_receive_interface'],
                    plot_receive_interface_threshold=server['plot_receive_interface_threshold'],
                    current_plot_replacement_drive=server['pools']['current_plot_replacement_drive'],
                    local_move_error=server['local_plotter']['local_move_error'],
                    local_move_error_alert_sent=server['local_plotter']['local_move_error_alert_sent'])


        def toggle_notification(self, notification):
            if getattr(self, notification):
                with open (config_file) as f:
                    server = yaml.safe_load(f)
                    server['notifications']['methods'][notification] = False
                    with open('plot_manager.yaml', 'w') as f:
                        yaml.safe_dump(server, f)
            else:
                with open(config_file) as f:
                    server = yaml.safe_load(f)
                    server['notifications']['methods'][notification] = True
                    with open(config_file, 'w') as f:
                        yaml.safe_dump(server, f)

        def set_local_move_error(self):
            if getattr(self, 'local_move_error'):
                log.debug('local_move_error already set to True! Nothing to do here.')
                pass
            else:
                with open(config_file) as f:
                    server = yaml.safe_load(f)
                    server['local_plotter']['local_move_error'] = True
                    with open(config_file, 'w') as f:
                        yaml.safe_dump(server, f)
                log.debug('local_move_error toggled to True!')



        def set_notification(self, notification, value):
            if getattr(self, notification) == value:
                pass
            else:
                with open(config_file) as f:
                    server = yaml.safe_load(f)
                    server['notifications']['methods'][notification] = value
                    with open(config_file, 'w') as f:
                        yaml.safe_dump(server, f)

        def update_current_plotting_drive(self, new_drive):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                server['harvester']['current_plotting_drive'] = new_drive
                with open(config_file, 'w') as f:
                    yaml.safe_dump(server, f)

        def update_current_internal_drive(self, new_drive):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                server['local_plotter']['current_internal_drive'] = new_drive
                with open(config_file, 'w') as f:
                    yaml.safe_dump(server, f)

        def update_current_plot_replacement_drive(self, new_drive):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                server['pools']['current_plot_replacement_drive'] = new_drive
                with open(config_file, 'w') as f:
                    yaml.safe_dump(server, f)

        def update_current_total_plots_midnight(self, type, plots):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                if type == 'old':
                    server['harvester']['current_total_plots_midnight'] = plots
                else:
                    server['pools']['current_portable_plots_midnight'] = plots
                with open(config_file, 'w') as f:
                    yaml.safe_dump(server, f)

        def update_current_total_plots_daily(self, type, plots):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                if type == 'old':
                    server['harvester']['current_total_plots_daily'] = plots
                else:
                    server['pools']['current_portable_plots_daily'] = plots
                with open(config_file, 'w') as f:
                    yaml.safe_dump(server, f)


        def onoffline_drives(self, onoffline, drive):
            if onoffline == 'offline':
                with open(config_file) as f:
                    server = yaml.safe_load(f)
                    server['harvester']['offlined_drives'].append(drive)
                    with open(config_file, 'w') as f:
                        yaml.safe_dump(server, f)
            else:
                with open(config_file) as f:
                    server = yaml.safe_load(f)
                    server['harvester']['offlined_drives'].remove(drive)
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
                    with open (config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['temp_dirs']['critical_alert_sent'] = False
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)
                else:
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['temp_dirs']['critical_alert_sent'] = True
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)

            elif alert == 'dst_dirs_critical_alert_sent':
                if getattr(self, alert):
                    with open (config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['dst_dirs']['critical_alert_sent'] = False
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)
                else:
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['dst_dirs']['critical_alert_sent'] = True
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)

            elif alert == 'total_plots_alert_sent':
                if getattr(self, alert):
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['harvester']['total_plots_alert_sent'] = False
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)
                else:
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['harvester']['total_plots_alert_sent'] = True
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)

            elif alert == 'local_move_error_alert_sent':
                if getattr(self, alert):
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['local_move_error_alert_sent'] = False
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)
                    log.debug('local_move_error_alert_sent set to FALSE')
                else:
                    with open(config_file) as f:
                        server = yaml.safe_load(f)
                        server['local_plotter']['local_move_error_alert_sent'] = True
                        with open(config_file, 'w') as f:
                            yaml.safe_dump(server, f)
                    log.debug('local_move_error_alert_sent set to TRUE')

class PlotManager:
    def __init__(self, plots_to_replace, number_of_old_plots, number_of_portable_plots, plot_drive,
                 next_plot_to_replace, next_local_plot_to_replace, local_plot_drive):
        self.plots_to_replace = plots_to_replace
        self.number_of_old_plots = number_of_old_plots
        self.number_of_portable_plots = number_of_portable_plots
        self.plot_drive = plot_drive
        self.next_plot_to_replace = next_plot_to_replace
        self.next_local_plot_to_replace = next_local_plot_to_replace
        self.local_plot_drive = local_plot_drive

    @classmethod
    def get_plot_info(cls):
        return cls(
        plots_to_replace = number_of_plots_in_system('old')[1],
        number_of_old_plots = number_of_plots_in_system('old')[0],
        number_of_portable_plots = number_of_plots_in_system('portable')[0],
        plot_drive = os.path.dirname(str(get_next_plot_replacement('old')[0])),
        next_plot_to_replace= str(get_next_plot_replacement('old')[0]),
        next_local_plot_to_replace = str(get_next_plot_replacement('local')[0]),
        local_plot_drive = os.path.dirname(str(get_next_plot_replacement('local')[0])))

def get_next_plot_replacement(type):
    if type == 'old':
        try:
            file_path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/plot-*'
            d = {abspath(d): d for d in glob(file_path_glob)}
            old_plot_count = len(d)
            return natsorted([p for p in d])[0], old_plot_count
        except IndexError:
            return False, 0
    elif type == 'portable':
        try:
            file_path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/portable*'
            d = {abspath(d): d for d in glob(file_path_glob)}
            old_plot_count = len(d)
            return natsorted([p for p in d])[0], old_plot_count
        except IndexError:
            return False, 0
    else:
        try:
            file_path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/plot-*'
            d = {abspath(d): d for d in glob(file_path_glob)}
            old_plot_count = len(d)
            return natsorted([p for p in d], reverse=True)[0], old_plot_count
        except IndexError:
            return False, 0

def number_of_plots_in_system(type):
    if type == 'old':
        plots_left = get_next_plot_replacement('old')
        if not plots_left[0]:
            return 0, False
        else:
            return plots_left[1], True
    else:
        plots_left = get_next_plot_replacement('portable')
        if not plots_left[0]:
            return 0, False
        else:
            return plots_left[1], True


def main():
    print("Not intended to be run directly.")
    print("This is the systemwide DriveManager Class module.")
    print("It is called by other modules.")
    exit()

if __name__ == '__main__':
    main()
