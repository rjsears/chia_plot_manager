#! /bin/bash
blkid -u filesystem $1 | awk -F "[= ]" '{print $3}' |tr -d "\""
