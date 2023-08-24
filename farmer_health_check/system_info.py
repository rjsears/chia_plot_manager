#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
system_info.py for use with farmer_health_check.py
"""

VERSION = "V0.991 (2023-08-24)"

# What email gets our notifications?
notify_email_address = ['your_email@gmail.com']

# You can use any email to sms gateway, I use clicksend but
# most cell carriers have a email to sms address.
notify_sms_address = ['group_one@groups.clicksend.com']

# What email address are we sending alerts from?
from_address = 'chianode1@domain.com'

# What is the Host Name of our farmer?
host = 'chianode01'


def main():
    print("This script is not intended to be run directly.")
    print("It is called by other modules.")
    exit()


if __name__ == '__main__':
    main()
