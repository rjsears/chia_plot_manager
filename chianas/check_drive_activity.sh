#! /bin/bash
dstat -r -D $1 1 5 > drive_monitor.iostat
