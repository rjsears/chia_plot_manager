#! /bin/bash
# Script to kill any lingering ncat processes

/usr/bin/killall -9 ncat >/dev/null 2>&1 
