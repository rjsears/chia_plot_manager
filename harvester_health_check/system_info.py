#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
system_info.py for use with harvester_health_check.py
"""

VERSION = "V0.991b (2023-09-04)"

# What email gets our notifications?
notify_email_address = ['your_email@gmail.com']

# You can use any email to sms gateway, I use clicksend but
# most cell carriers have a email to sms address.
notify_sms_address = ['group_one@groups.clicksend.com']

# What email address are we sending alerts from?
from_address = 'chianas01@domain.com'

# What is the Host Name of our farmer?
host = 'chianode01'


def main():
    print("This script is not intended to be run directly.")
    print("It is called by other modules.")
    exit()


if __name__ == '__main__':
    main()
