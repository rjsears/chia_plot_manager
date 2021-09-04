#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Part of drive_manager. Checks to see if our config file needs updating and updated it for us.
"""
VERSION = "V0.95 (2021-09-03)"

import os
import yaml
from pathlib import Path
import logging
from system_logging import setup_logging
from shutil import copyfile
from flatten_dict import flatten
from flatten_dict import unflatten
from datetime import datetime

script_path = Path(__file__).parent.resolve()

# Date and Time Stuff
current_military_time = datetime.now().strftime('%Y%m%d%H%M%S')

config_file = (str(Path.home()) + '/.config/plot_manager/plot_manager.yaml')
skel_config_file = script_path.joinpath('plot_manager.skel.yaml')

# Define some colors for our help message
red='\033[0;31m'
yellow='\033[0;33m'
green='\033[0;32m'
white='\033[0;37m'
blue='\033[0;34m'
nc='\033[0m'


# Setup Module logging. Main logging is configured in system_logging.py
setup_logging()
with open(config_file, 'r') as config:
    server = yaml.safe_load(config)
level = server['log_level']
level = logging._checkLevel(level)
log = logging.getLogger('config_file_updater.py')
log.setLevel(level)


def config_file_update():
    """
    Function to determine if we need to update our yaml configuration file after an upgrade.
    """
    log.debug('config_file_update() Started....')
    if os.path.isfile(skel_config_file):
        log.debug('New config SKEL file located, checking to see if an update is needed:')
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
            log.debug('Your config files needs updating!')
            log.debug(f'Config File: {config_file} updated. Update as necessary to run chia_plot_manager.')
            exit()
        else:
            log.debug('No config file changes necessary! No changes made.')
            log.debug(f'{skel_config_file} has been deleted!')
            os.remove(skel_config_file)
    else:
        log.debug('New configuration file not found. No changes made.')



def main():
    print(f'Welcome to {green}config_file_updater.py{nc} {blue}VERSION: {nc}{VERSION}')
    config_file_update()


if __name__ == '__main__':
    main()
