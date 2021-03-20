#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
system_info.py for use with drive_manager.py
"""

VERSION = "V0.1 (2021-03-16)"

# Are notifications Enabled?
notifications = True

# Which notification types do we want to use?
sms = False
email = True
pushbullet = False

## Set Notification Accounts#
alert_email = ['email_one@gmail.com', 'email_two@gmail.com']
twilio_from = '+10000000'
twilio_account = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
twilio_token = 'kjshdkjhfkjshlfkjhkajhfkjahsfdkj'
twilio_to = ['+17763540098', '+17763540086']
pushbilletAPI = "o.khjsdfiuwyifkjshkjshkajhdiurieuiufqw"  # pushbullet API token (http://www.pushbullet.com)


def main():
    print("This script is not intended to be run directly.")
    print("This is the systemwide Credentials & Settings module.")
    print("It is called by other modules.")
    exit()


if __name__ == '__main__':
    main()
