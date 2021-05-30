#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Part of drive_manager. This is the logging module.
For use with plot_manager V0.9
"""

VERSION = "V0.9 (2021-05-27)"

import logging.config
import logging
import logging.handlers
import configparser
config = configparser.ConfigParser()
import pathlib
script_path = pathlib.Path(__file__).parent.resolve()


def setup_logging(default_level=logging.CRITICAL):
    """Module to configure program-wide logging."""
    log_level = read_logging_config('plot_manager_config', 'system_logging', 'log_level')
    log = logging.getLogger(__name__)
    level = logging._checkLevel(log_level)
    log.setLevel(level)
    system_logging = read_logging_config('plot_manager_config', 'system_logging', 'logging')
    if system_logging:
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
   "disable_existing_loggers": false,
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
         "filename": "/root/plot_manager/logs/info.log",
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "error_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "ERROR",
         "formatter": "error",
         "filename": "/root/plot_manager/logs/errors.log",
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "debug_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "DEBUG",
         "formatter": "standard",
         "filename": "/root/plot_manager/logs/debug.log",
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "critical_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "CRITICAL",
         "formatter": "standard",
         "filename": "/root/plot_manager/logs/critical.log",
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "warning_file_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "level": "WARNING",
         "formatter": "standard",
         "filename": "/root/plot_manager/logs/warning.log",
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "drive_manager_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "formatter": "standard",
         "filename": "/root/plot_manager/logs/drive_manager.log",
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      },
      "move_local_plots_handler": {
         "class": "logging.handlers.RotatingFileHandler",
         "formatter": "standard",
         "filename": "/root/plot_manager/logs/move_local_plots.log",
         "maxBytes": 10485760,
         "backupCount": 2,
         "encoding": "utf8"
      }
   },
   "root": {
      "level": "NOTSET",
      "handlers": null,
      "propogate": "no"
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
         "propogate": "no"
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
         "propogate": "yes"
      }
   }
}


def read_logging_config(file, section, status):
    pathname = script_path.joinpath(file)
    config.read(pathname)
    if status == "logging":
        current_status = config.getboolean(section, status)
    else:
        current_status = config.get(section, status)
    return current_status


def main():
    print("This script is not intended to be run directly.")
    print("This is the systemwide logging module.")
    print("It is called by other modules.")
    exit()


if __name__ == '__main__':
    main()
