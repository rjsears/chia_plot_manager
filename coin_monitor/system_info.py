#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
system_info.py for use with coin_monitor.py
"""

VERSION = "V0.991 (2023-08-22)"

# Clicksend is an email to SMS gateway service
new_coin_email = ['email_one@gmail.com', 'group_one@groups.clicksend.com']

# Use any email-to-text service here
new_coin_sms = ['group_one@groups.clicksend.com']

#Who do our emails come from:
from_address = 'chianode1@domain.com'


def main():
    print("This script is not intended to be run directly.")
    print("This is the systemwide Credentials & Settings module.")
    print("It is called by other modules.")
    exit()


if __name__ == '__main__':
    main()
