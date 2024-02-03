#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Part of drive_manager. These classes are for reading and updating out yaml
config file.
"""

VERSION = "1.0.0a (2024-02-02)"

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


# What does our directory structure look like?
directory_structure_glob = "/mnt/enclosure[0-9]/*/column[0-9]/*/"

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
        def __init__(self, configured, hostname, plot_movement_internal, drive_temperature_limit, pools, replace_non_pool_plots, compressed_plots, gpu_decompression, fill_empty_drives_first,
                     empty_drives_low_water_mark, chia_log_file, chia_config_file, compression_in_use, remote_harvester_reports, remote_harvesters, notifications, pb, email, sms, directory_glob,
                     daily_update, farm_update, new_plot_drive, per_plot, local_plotter, temp_dirs, temp_dirs_critical, temp_dirs_critical_alert_sent, dst_dirs, dst_dirs_critical, minutes_of_log_to_return,
                     dst_dirs_critical_alert_sent, warnings, emails, phones, twilio_from, twilio_account, twilio_token, pb_api, replace_noncompressed_plots, compressed_plots_midnight,
                     current_internal_drive, current_plotting_drive, total_plot_highwater_warning, total_plots_alert_sent, plot_receive_interface_threshold, compressed_plots_daily,
                     current_total_plots_midnight, current_total_plots_daily, offlined_drives, logging, log_level, plot_receive_interface, farmer_ip_address, farmer_user, farmer_password,
                     current_portable_plots_midnight, current_portable_plots_daily, current_plot_replacement_drive, local_move_error, local_move_error_alert_sent, my_local_ip_address, compression_type):
            self.configured = configured
            self.hostname = hostname
            self.plot_movement_internal = plot_movement_internal
            self.drive_temperature_limit = drive_temperature_limit
            self.pools = pools
            self.replace_non_pool_plots = replace_non_pool_plots
            self.compressed_plots = compressed_plots
            self.gpu_decompression = gpu_decompression
            self.compression_in_use = compression_in_use
            self.compressed_plots_midnight = compressed_plots_midnight
            self.compressed_plots_daily = compressed_plots_daily
            self.replace_noncompressed_plots = replace_noncompressed_plots
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
            self.minutes_of_log_to_return = minutes_of_log_to_return
            self.daily_update = daily_update
            self.farm_update = farm_update
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
            self.farmer_ip_address = farmer_ip_address
            self.farmer_user = farmer_user
            self.farmer_password = farmer_password
            self.my_local_ip_address = my_local_ip_address
            self.directory_glob = directory_glob
            self.compression_type = compression_type

        @classmethod
        def read_configs(cls):
            with open (config_file, 'r') as config:
                server = yaml.safe_load(config)
                return cls(
                    configured=server['configured'],
                    hostname=server['hostname'],
                    plot_movement_internal=server['plot_movement_internal'],
                    drive_temperature_limit=server['drive_temperature_limit'],
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
                    farm_update=server['notifications']['types']['farm_update'],
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
                    minutes_of_log_to_return=server['harvester']['minutes_of_log_to_return'],
                    compressed_plots=server['harvester']['compression']['compressed_plots'],
                    gpu_decompression=server['harvester']['compression']['gpu_decompression'],
                    compression_in_use=server['harvester']['compression']['compression_in_use'],
                    replace_noncompressed_plots=server['harvester']['compression']['replace_noncompressed_plots'],
                    compressed_plots_midnight=server['harvester']['compression']['compressed_plots_midnight'],
                    compressed_plots_daily=server['harvester']['compression']['compressed_plots_daily'],
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
                    local_move_error_alert_sent=server['local_plotter']['local_move_error_alert_sent'],
                    farmer_ip_address=server['remote_farmer']['ip_address'],
                    farmer_user=server['remote_farmer']['user'],
                    farmer_password=server['remote_farmer']['password'],
                    directory_glob=server['directory_glob'],
                    my_local_ip_address=server['my_local_ip_address'],
                    compression_type=server['harvester']['compression']['compression_type'])


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

        def update_current_total_plots_midnight(self, plots):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                server['harvester']['current_total_plots_midnight'] = plots
                with open(config_file, 'w') as f:
                    yaml.safe_dump(server, f)

        def update_compressed_plots_midnight(self, plots):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                server['harvester']['compression']['compressed_plots_midnight'] = plots
                with open(config_file, 'w') as f:
                    yaml.safe_dump(server, f)

        def update_current_total_plots_daily(self, plots):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                server['harvester']['current_total_plots_daily'] = plots
                with open(config_file, 'w') as f:
                    yaml.safe_dump(server, f)

        def update_compressed_plots_daily(self, plots):
            with open(config_file) as f:
                server = yaml.safe_load(f)
                server['harvester']['compression']['compressed_plots_daily'] = plots
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
    directories = glob(directory_structure_glob)
    if not directories:
        raise FileNotFoundError(f"No matching directories found for: {directory_structure_glob}")
    else:
        def __init__(self, plots_to_replace, number_of_old_plots, number_of_portable_plots, number_of_compressed_plots, plot_drive,
                     next_plot_to_replace, next_local_plot_to_replace, local_plot_drive, plot_count):
            self.plots_to_replace = plots_to_replace
            self.number_of_old_plots = number_of_old_plots
            self.number_of_portable_plots = number_of_portable_plots
            self.number_of_compressed_plots = number_of_compressed_plots
            self.plot_drive = plot_drive
            self.next_plot_to_replace = next_plot_to_replace
            self.next_local_plot_to_replace = next_local_plot_to_replace
            self.local_plot_drive = local_plot_drive
            self.plot_count = plot_count

        @classmethod
        def get_plot_info(cls):
            return cls(
            plots_to_replace = number_of_plots_in_system('old')[1],
            number_of_old_plots = number_of_plots_in_system('old')[0],
            number_of_portable_plots = number_of_plots_in_system('portable')[0],
            number_of_compressed_plots=number_of_plots_in_system('compressed')[0],
            plot_drive = os.path.dirname(str(get_next_plot_replacement('old')[0])),
            next_plot_to_replace= str(get_next_plot_replacement('old')[0]),
            next_local_plot_to_replace = str(get_next_plot_replacement('local')[0]),
            local_plot_drive = os.path.dirname(str(get_next_plot_replacement('local')[0])),
            plot_count = count_plots(directory_structure_glob)
            )

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
            #file_path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/portable*'
            file_path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/plot-k32-c05*'
            d = {abspath(d): d for d in glob(file_path_glob)}
            old_plot_count = len(d)
            return natsorted([p for p in d])[0], old_plot_count
        except IndexError:
            return False, 0
    elif type == 'compressed':
        try:
            file_path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/plot-k32-c05*'
            d = {abspath(d): d for d in glob(file_path_glob)}
            compressed_plot_count = len(d)
            return natsorted([p for p in d])[0], compressed_plot_count
        except IndexError:
            return False, 0
    else:
        try:
            file_path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*/plot-k32*'
            d = {abspath(d): d for d in glob(file_path_glob)}
            old_plot_count = len(d)
            return natsorted([p for p in d], reverse=True)[0], old_plot_count
        except IndexError:
            return False
def number_of_plots_in_system(type):
    if type == 'old':
        plots_left = get_next_plot_replacement('old')
        if not plots_left[0]:
            return 0, False
        else:
            return plots_left[1], True
    elif type == 'compressed':
        plots_left = get_next_plot_replacement('compressed')
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

# The count_plots() function returns a list:
# [8717, 1, 8716, 0, 0, 0, 0, 1, 0, 0]
# Total # of Plots, # Compressed Plots, # Portable Plots, c01 plots, c02 plots, c03 plots, c04 plots, c05 plots, c06 plots, c07 plots.....c20 plots)
def count_plots(directory_structure_glob):
    directories = glob(directory_structure_glob)
    compression_levels = ['c01', 'c02', 'c03', 'c04', 'c06', 'c07','c08', 'c09', 'c10', 'c11', 'c12', 'c13', 'c14', 'c15', 'c16', 'c17', 'c18', 'c19', 'c20'] #removed `c05` to remove that from count to make this work during replotting.
    counts = {level: 0 for level in compression_levels}
    total_plots = 0
    total_compressed_plots = 0
    total_portable_plots = 0

    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.plot'):
                    total_plots += 1
                    for level in compression_levels:
                        if file.startswith(f"plot-k32-{level}"):
                            counts[level] += 1
                            total_compressed_plots += 1
                if file.startswith("plot-k32-c05"):
                #if file.startswith("portable.plot-k32"):
                    total_portable_plots += 1

    return [total_plots, total_compressed_plots, total_portable_plots] + [counts[level] for level in compression_levels]


def main():
    print("Not intended to be run directly.")
    print("This is the systemwide DriveManager Class module.")
    print("It is called by other modules.")
    exit()

if __name__ == '__main__':
    main()
