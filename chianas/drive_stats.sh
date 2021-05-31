#! /bin/bash

# Checks to see if 'move_local_plots.py' is running and is so
# how much drive IO is being used.

/usr/bin/pidstat -G move_local_plots.py -dlhH 5 1 > drive_stats.io
