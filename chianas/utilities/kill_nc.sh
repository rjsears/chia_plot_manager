#! /bin/bash
# Script to kill any lingering nc processes

/usr/bin/killall -9 nc >/dev/null 2>&1 
