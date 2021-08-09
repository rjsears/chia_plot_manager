#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Part of drive_manager. This is the logging module.
For use with plot_manager V0.9
"""

VERSION = "V0.94 (2021-08-08)"

import logging.config
import logging
import logging.handlers
import yaml
import pathlib

user_home_dir = str(pathlib.Path.home())
config_file = (user_home_dir + '/.config/plot_manager/plot_manager.yaml')
script_path = pathlib.Path(__file__).parent.resolve()


def setup_logging(default_level=logging.CRITICAL):
    """Module to configure program-wide logging."""
    with open(config_file, 'r') as config:
       server = yaml.safe_load(config)
    log = logging.getLogger(__name__)
    level = logging._checkLevel(server['log_level'])
    log.setLevel(level)
    if server['logging']:
        try:
            logging.config.dictConfig(log_config)
        except Exception as e:
            print(e)
            print('Error in Logging Configuration. Using default configs. Check File Permissions (for a start)!')
            logging.basicConfig(level=default_level)
        return log
    else:
        log.disabled = True

log_config = {
   "version": 1,
   "disable_existing_loggers": False,
   "formatters": {
      "console": {
         "format": "%(message)s"
      },
      "console_expanded": {
         "format": "%(module)2s:%(lineno)s - %(funcName)3s: %(levelname)3s:    %(message)s"
      },
      "standard": {
         "format": "%(asctime)s - %(module)2s:%(lineno)s - %(funcName)3s: %(levelname)3s %(message)s"
      },
      "error": {
         "format": "%(levelname)s <PID %(process)d:%(processName)s> %(module)s.%(funcName)s(): %(message)s"
      }
   },
   "handlers": {
      "console": {
         "class": "logging.StreamHandler",
         "formatter": "console",
         "stream": "ext://sys.stdout"
      },
      "expanded_console": {
         "class": "logging.StreamHandler",
         "formatter": "console_expanded",
         "stream": "ext://sys.stdout"
      },
      "info_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "INFO",
         "formatter": "standard",
         "filename": script_path.joinpath("logs/info.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "error_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "ERROR",
         "formatter": "error",
         "filename": script_path.joinpath("logs/errors.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "debug_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "DEBUG",
         "formatter": "standard",
         "filename": script_path.joinpath("logs/debug.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "critical_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "CRITICAL",
         "formatter": "standard",
         "filename": script_path.joinpath("logs/critical.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "warning_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "WARNING",
         "formatter": "standard",
         "filename": script_path.joinpath("logs/warning.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "drive_manager_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "formatter": "standard",
         "filename": script_path.joinpath("logs/drive_manager.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "drivemanager_classes_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "formatter": "standard",
         "filename": script_path.joinpath("logs/drivemanager_classes.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "move_local_plots_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "formatter": "standard",
         "filename": script_path.joinpath("logs/move_local_plots.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "config_file_updater_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "formatter": "standard",
         "filename": script_path.joinpath("logs/config_file_updater.log").as_posix(),
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      }
   },
   "root": {
      "level": "NOTSET",
      "handlers": None,
      "propogate": False
   },
   "loggers": {
      "__main__": {
         "handlers": [
            "console",
            "info_file_handler",
            "error_file_handler",
            "critical_file_handler",
            "debug_file_handler",
            "warning_file_handler",
            "drive_manager_handler"
         ],
         "propogate": False
      },
      "move_local_plots": {
         "handlers": [
            "console",
            "info_file_handler",
            "error_file_handler",
            "critical_file_handler",
            "debug_file_handler",
            "warning_file_handler",
            "move_local_plots_handler"
         ],
         "propogate": True
      },
      "config_file_updater": {
         "handlers": [
            "console",
            "info_file_handler",
            "error_file_handler",
            "critical_file_handler",
            "debug_file_handler",
            "warning_file_handler",
            "config_file_updater_handler"
         ],
         "propogate": True
      },
      "drivemanager_classes": {
         "handlers": [
            "console",
            "info_file_handler",
            "error_file_handler",
            "critical_file_handler",
            "debug_file_handler",
            "warning_file_handler",
            "drivemanager_classes_handler"
         ],
         "propogate": True
      }
   }
}

'''
def read_logging_config(file, section, status):
    pathname = script_path.joinpath(file)
    config.read(pathname)
    if status == "logging":
        current_status = config.getboolean(section, status)
    else:
        current_status = config.get(section, status)
    return current_status
'''

def main():
    print("This script is not intended to be run directly.")
    print("This is the systemwide logging module.")
    print("It is called by other modules.")
    exit()


if __name__ == '__main__':
    main()
