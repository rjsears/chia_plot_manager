#! /bin/bash

# Ubuntu likes to install SNAP which I do not use on my servers at all.
# This script removes snap from the system!

# Run me as root......
if (( $EUID != 0 )); then
    echo "Please run me as root"
    exit
fi

# Stop all snapd services on the server
systemctl stop snapd && sudo systemctl disable snapd
# Purge snapd from the server
apt purge snapd
# Get rid of unneeded snap folders
rm -rf ~/snap
rm -rf /snap /var/snap /var/lib/snapd /var/cache/snapd /usr/lib/snapd


# Make sure nothing reinstalls SNAP again......
cat << EOF > no-snap.pref
Package: snapd
Pin: release a=*
Pin-Priority: -10
EOF

mv no-snap.pref /etc/apt/preferences.d/
chown root:root /etc/apt/preferences.d/no-snap.pref
