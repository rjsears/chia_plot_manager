#! /bin/bash
dstat -r -D $1 1 3 > drive_monitor.iostat
