#! /bin/bash

# Ubuntu likes to install SNAP which I do not use on my servers at all.
# This script removes snap from the system!

# stop snapd services
sudo systemctl stop snapd && sudo systemctl disable snapd
# purge snapd
sudo apt purge snapd
# remove no longer needed folders
rm -rf ~/snap
sudo rm -rf /snap /var/snap /var/lib/snapd /var/cache/snapd /usr/lib/snapd
