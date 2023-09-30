#!/usr/bin/env python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "1.0.0a (2023-09-29)"

import os
import re
import argparse
import textwrap


# Define some colors for our messages
red='\033[0;31m'
yellow='\033[0;33m'
green='\033[0;32m'
white='\033[0;37m'
blue='\033[0;34m'
nc='\033[0m'

# Default chia_log_directory paths. These are two pretty common file locations, 
# but if your logs are somewhere else, just update the first entry here to 
# match your location.
chia_log_directory = "/home/chia/.chia/mainnet/log/"
fallback_log_directory = "/root/chia/.chia/mainnet/log/"

# Check if chia_log_directory exists, otherwise, use the fallback
if not os.path.isdir(chia_log_directory):
    if os.path.isdir(fallback_log_directory):
        chia_log_directory = fallback_log_directory
    else:
        print("Chia debug log directory not found in the default locations.")
        exit(1)


class RawFormatter(argparse.HelpFormatter):
    def _fill_text(self, text, width, indent):
        return "\n".join(
            [textwrap.fill(line, width) for line in textwrap.indent(textwrap.dedent(text), indent).splitlines()])


program_descripton = f'''
                {red}******** {green}Chia Simplified Log Viewer{nc} - {blue}{VERSION}{red} ********{nc}
    chia_logs.py is a simple python script to take a look at your chia long on your full node on
    harvesters and looks for errors, warnings, eligible plots, proofs, etc.
    
    When you run it, it will check your log directory (set above, automatically checks for user chia and root
    standard log file locations, but you can change this) and will show you all log files available. If there
    if more than one, it will allow you to select which file you want to parse. If you select 'debug.log' which
    is the active debug file for Chia, it will allow you to {yellow}'Tail'{nc} the file or {yellow}'Cat'{nc} the file. All others default
    to {yellow}'Cat'{nc}.

    There are several commandline switches you can use to get log information:


    {green}-pr {nc}or{green} --proofs{nc}       {blue} This looks for any line that includes {yellow}"Found [0-9] proofs"{blue}
                           It will ask you what {yellow}[0-9]{blue} pattern you it to you would like. For example if you want to find
                           only those lines with more than {yellow}0{blue} proofs, you would enter {yellow}1-9{blue} or {yellow}2-9{blue}, etc.{nc}
                                
    {green}-el {nc}or{green} --eligible{nc}     {blue} This looks for any line that includes {yellow}"[0-9] plots were eligible for farming"{blue}
                           It will ask you what {yellow}[0-9]{blue} pattern you it to you would like. For example if you want to find
                           only those lines with more than {yellow}0{blue} proofs, you would enter {yellow}1-9{blue} or {yellow}2-9{blue}, etc.{nc}
                                
    {green}-wa {nc}or{green} --warning{blue}       This will look for any lines with {yellow}WARNING{blue} in them.{nc}

    {green}-er {nc}or{green} --error{blue}         This will look for any lines with {yellow}ERROR{blue} in them.{nc}
    
    {green}-fr {nc}or{green} --free  {blue}        This will look for any lines that include your free form entry.{nc}
    
    {green}-sp {nc}or{green} --signage  {blue}     This will look for Signage Points.{nc}
                                

   
    USAGE:
'''

def init_argparser() -> any:
    parser = argparse.ArgumentParser(description=program_descripton, formatter_class=RawFormatter)
    parser.add_argument('-v', '--version', action='version', version=f'{parser.prog} {VERSION}')
    parser.add_argument('-pr', '--proofs', action='store_true', help='Look for any line with "Found [0-9] proofs')
    parser.add_argument('-el', '--eligible', action='store_true', help='Look for any line with [0-9] plots were eligible for farming')
    parser.add_argument('-wa', '--warning', action='store_true', help='Look for any line that includes WARNING')
    parser.add_argument('-er', '--error', action='store_true',help='Look for any line that includes ERROR')
    parser.add_argument('-si', '--signage', action='store_true', help='Monitor Signage Points')
    parser.add_argument('-fr', '--free', action='store_true', help='Look for any line that you specify')
    return parser

# Function to ask whether to tail or cat
def ask_tail_or_cat():
    while True:
        choice = input("Tail or Cat? (T/C): ").strip().lower()
        if choice in ['t', 'tail']:
            return True
        elif choice in ['c', 'cat']:
            return False
        else:
            print("Invalid choice. Please enter 'T' for Tail or 'C' for Cat.")

# Function to ask for the range of proofs
def get_range():
    while True:
        range_input = input("Number of Proofs (0-9, 1-9, 2-9, etc): ").strip()
        if re.match(r'^[0-9]-[0-9]$', range_input):
            return range_input
        else:
            print("Invalid input. Please enter a valid range (e.g., 0-9, 1-9, 2-9, etc).")


def get_input():
    while True:
        free_input = input("Enter what you are searching for: ").strip()
        return free_input

# Function to run the chosen command
def run_command(command, pattern):
    if command:
        os.system(f"tail -F {chia_log_file} | grep -E '{pattern}'")
    else:
        os.system(f"cat {chia_log_file} | grep -E '{pattern}'")

if __name__ == "__main__":
    print(f'Welcome to chia_logs.py Version: {VERSION}')
    parser = init_argparser()
    args = parser.parse_args()


    if not (args.proofs or args.eligible or args.warning or args.error or args.signage or args.free):
        print(f"{red}No operation specified! {yellow}try ./chia_logs.py -h")
        exit(1)

    debug_logs = sorted([file for file in os.listdir(os.path.dirname(chia_log_directory)) if file.startswith("debug.log")])

    if len(debug_logs) > 1:
        print("Multiple debug log files found:")
        for i, log_file in enumerate(debug_logs, start=1):
            print(f"{i}: {log_file}")
        log_choice = input("Enter the number of the log file to use: ").strip()
        if log_choice.isdigit() and 1 <= int(log_choice) <= len(debug_logs):
            chia_log_file = os.path.join(os.path.dirname(chia_log_directory), debug_logs[int(log_choice) - 1])
            log_file = debug_logs[int(log_choice) - 1]  # Strip the directory information and return just the debug file selected.
    else:
        print('Only one debug log file found')
        chia_log_file = os.path.join(os.path.dirname(chia_log_directory), 'debug.log')
        log_file = 'debug.log'

    if args.proofs:
        if log_file == "debug.log":
            tail_or_cat = ask_tail_or_cat()
        else:
            tail_or_cat = False
        range_input = get_range()
        pattern = f"Found [{range_input}] proofs"
        run_command(tail_or_cat, pattern)

    elif args.eligible:
        if log_file == "debug.log":
            tail_or_cat = ask_tail_or_cat()
        else:
            tail_or_cat = False
        range_input = get_range()
        pattern = f"[{range_input}] plots were eligible for farming"
        run_command(tail_or_cat, pattern)

    elif args.warning:
        if log_file == "debug.log":
            tail_or_cat = ask_tail_or_cat()
        else:
            tail_or_cat = False
        pattern = "WARNING"
        run_command(tail_or_cat, pattern)

    elif args.error:
        if log_file == "debug.log":
            tail_or_cat = ask_tail_or_cat()
        else:
            tail_or_cat = False
        pattern = "ERROR"
        run_command(tail_or_cat, pattern)

    elif args.signage:
        if log_file == "debug.log":
            tail_or_cat = ask_tail_or_cat()
        else:
            tail_or_cat = False
        pattern = "Finished signage point"
        run_command(tail_or_cat, pattern)

    elif args.free:
        if log_file == "debug.log":
            tail_or_cat = ask_tail_or_cat()
        else:
            tail_or_cat = False
        pattern = get_input()
        run_command(tail_or_cat, pattern)

