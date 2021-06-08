#!/usr/bin/python3

# -*- coding: utf-8 -*-

__author__ = 'Richard J. Sears'
VERSION = "0.92 (2021-06-08)"

"""
STAND ALONE STAND ALONE STAND ALONE
This script is part of the chia_plot_manager set of scripts.
This is the STAND ALONE version of this script and will work
without needing the rest of the repo.
Script to help automate the addition of new hard drives
to a Chia NAS/Harvester. Please make sure you understand
everything that this script does before using it!
This script is intended to make my life easier. It is ONLY
designed to 1) work with unformatted drives with no existing
partitions, and 2) utilizing the directory structure found
in the readme.
This script WILL NOT work if you are utilizing hard drives wiht
no partitions as we would have no way to determine if the drive
is newly added.
It can be modified, of course, to do other things.
1) Looks for any drive device that is on the system but does not
end in a '1'. For example: /dev/sda1 vs. /dev/sdh - In this case
/dev/sdh has no partition so it likely is not mounted or being
used.
2) Utilizing the directory structure that I have shared in the
main readme, locate the next available mountpoint to use.
3) Utilizing sgdisk, creates a new GPT partition on the new
drive.
4) Formats the drive with the xfs filesystem.
5) Verifies that the UUID of the drive does not already exist
in /etc/fstab and if not, adds the correct entry to /etc/fstab.
6) Mounts the new drive
7) Add the new mountpoint to your chia harvester configuration.
"""

from glob import glob
from os.path import ismount, abspath, exists
import string
import subprocess
import yaml
from natsort import natsorted
import pathlib
script_path = pathlib.Path(__file__).parent.resolve()

# Do some housekeeping
# Define some colors for our help message
red='\033[0;31m'
yellow='\033[0;33m'
green='\033[0;32m'
white='\033[0;37m'
blue='\033[0;34m'
nc='\033[0m'

# Where can we find your Chia Config File?
chia_config_file = '/root/.chia/mainnet/config/config.yaml'

#Where did we put the get_drive_uuid.sh script:
get_drive_uuid = script_path.joinpath('get_drive_uuid.sh')

# What filesystem are you using: ext4 or xfs?
file_system = 'xfs'


# mark any drives here that you do not want touched at all for any reason,
# formatted or not.
do_not_use_drives = {'/dev/sda'}


# Let's get started.......

def get_next_mountpoint():
    """
    This function looks at the entire directory structure listed
    in the path_glob and then checks to see what directories are
    mounted and which are not. It then returns that in a sorted
    dictionary but only for those directories that are not
    mounted. We then return just the first one for use as our
    next mountpoint.
    abspath(d) = the full path to the directory
    ismount(d) = Returns True if abspath(d) is a mountpoint
    otherwise returns false.
    (d) looks like this:
    {'/mnt/enclosure0/front/column0/drive0': True}
    Make sure your path already exists and that the 'path_glob'
    ends with a `/*`.
    Notice that the path_glob does NOT include the actual drive0,
    drive1, etc. Your glob needs to be parsed with the *.
    So for this glob: path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*'
    this would be the directory structure:
     /mnt
     ├── enclosure0
     │   ├── front
     │   │   ├── column0
     │   │   │   ├── drive2
     │   │   │   ├── drive3
     │   │   │   ├── drive4
     │   │   │   └── drive5
     ├── enclosure1
     │   ├── rear
     │   │   ├── column0
     │   │   │   ├── drive6
     │   │   │   ├── drive7
    """
    try:
        path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*'
        d = {abspath(d): ismount(d) for d in glob(path_glob)}
        return natsorted([p for p in d if not d[p]])[0]
    except IndexError:
        print(f'\nNo usable {green}Directories{nc} found, Please check your {green}path_glob{nc}, ')
        print(f'and verify that your directory structure exists. Also, please make sure your')
        print(f'{green}path_glob{nc} ends with a trailing backslash and an *:')
        print(f'Example:  /mnt/enclosure[0-9]/*/column[0-9]{green}/*{nc}\n')


def get_new_drives():
    """
    This functions creates two different lists. "all_drives" which
    is a sorted list of all drives as reported by the OS as read from
    `/dev/sd*` using glob(). The second is "formatted_drives" which is a list of
    all drives that end with a `1` indicating that they have a partition
    on them and as such we should not touch. We then strip the `1` off
    the back of the "formatted_drives" list and add it to a new set
    "formatted_set". We then iterate over the  "all_drives" sorted list,
    strip any digits off the end, check to see if it exists in the
    "formatted_set" and if it does not, then we go ahead and add it
    to our final set "unformatted_drives". We then sort that and
    return the first drive from that sorted set.
    """
    all_drives = sorted(glob('/dev/sd*'))
    formatted_drives = list(filter(lambda x: x.endswith('1'), all_drives))
    formatted_set = set()
    for drive in formatted_drives:
        drive = drive.rstrip(string.digits)
        formatted_set.add(drive)
    formatted_and_do_not_use = set.union(formatted_set, do_not_use_drives)
    unformatted_drives = set()
    for drive in all_drives:
        drive = drive.rstrip(string.digits)
        if drive not in formatted_and_do_not_use:
            # if drive not in formatted_set:
            unformatted_drives.add(drive)
    if unformatted_drives:
        return sorted(unformatted_drives)[0]
    else:
        return False


def add_new_drive():
    """
    This is the main function responsible for getting user input and calling all other
    functions. I tried to do a lot of error checking, but since we are working with a
    drive that `should` have zero data on it, we should not have too much of an issue.
    """
    print(f'Welcome to auto_drive.py {blue}Version{nc}:{green}{VERSION}{nc}')
    can_we_run()
    if not get_new_drives():
        print (f'\nNo new drives found!  {red}EXITING{nc}\n')
    else:
        drive = get_new_drives()
        mountpoint = get_next_mountpoint()
        print (f'\nWe are going to format: {blue}{drive}{nc}, add it to {yellow}/etc/fstab{nc} and mount it at {yellow}{mountpoint}{nc}\n')
        format_continue = sanitise_user_input(f'Would you like to {white}CONTINUE{nc}?:  {green}YES{nc} or {red}NO{nc}   ', range_=('Y', 'y', 'YES', 'yes', 'N', 'n', 'NO', 'no'))
        if format_continue in ('Y', 'YES', 'y', 'yes'):
            print (f'We will {green}CONTINUE{nc}!')
            if sgdisk(drive):
                print (f'Drive Partitioning has been completed {green}successfully{nc}!')
            else:
                print(f'There was a {red}PROBLEM{nc} partitioning your drive, please handle manually!')
                exit()
            if make_filesystem(drive):
                print(f'Drive has been formatted as {file_system} {green}successfully{nc}!')
            else:
                print(f'There was a {red}PROBLEM{nc} formatting your drive as {green}{file_system}{nc}, please handle manually!')
                exit()
            if add_uuid_to_fstab(drive):
                print(f'Drive added to system {green}successfully{nc}!\n\n')
            else:
                print(f'There was a {red}PROBLEM{nc} adding your drive to /etc/fstab or mounting, please handle manually!')
                exit()
            add_to_chia = sanitise_user_input(f'Would you like to add {yellow}{mountpoint}{nc} to your {green}Chia{nc} Config File?:  {green}YES{nc} or {red}NO{nc}   ', range_=('Y', 'y', 'YES', 'yes', 'N', 'n', 'NO', 'no'))
            if add_to_chia in ('Y', 'YES', 'y', 'yes'):
                print (f'Adding {yellow}{mountpoint}{nc} to {green}Chia{nc} Configuration File......')
                if update_chia_config(mountpoint):
                    print(f'Mountpoint: {green}{mountpoint}{nc} Successfully added to your Chia Config File')
                    print(f'\n\nDrive Process Complete - Thank You and have a {red}G{yellow}R{white}E{green}A{blue}T{nc} Day!\n\n')
                else:
                    print(f'\nThere was an {red}ERROR{nc} adding {mountpoint} to {chia_config_file}!')
                    print(f'You need to {yellow}MANUALLY{nc} add or verify that it has been added to your config file,')
                    print(f'otherwise plots on that drive will {red}NOT{nc} get {green}harvested{nc}!\n')
                    print(f'\n\nDrive Process Complete - Thank You and have a {red}G{yellow}R{white}E{green}A{blue}T{nc} Day!')
            else:
                print(f'\n\nDrive Process Complete - Thank You and have a {red}G{yellow}R{white}E{green}A{blue}T{nc} Day!\n\n')
        else:
            print (f'{yellow}EXITING{nc}!')
            exit()

def sgdisk(drive):
    """
    Function to call sgdisk to create the disk partition and set GPT.
    """
    try:
      print(f'Please wait while we get {blue}{drive}{nc} ready to partition.......')
      sgdisk_results =  subprocess.run(['sgdisk', '-Z', drive], capture_output=True, text=True)
      print (sgdisk_results.stdout)
      print (sgdisk_results.stderr)
    except subprocess.CalledProcessError as e:
        print(f'sgdisk {red}Error{nc}: {e}')
        return False
    except Exception as e:
        print(f'sgdisk: Unknown {red}Error{nc}! Drive not Partitioned')
        return False
    try:
        print(f'Creating partition on {blue}{drive}{nc}.......')
        sgdisk_results = subprocess.run(['sgdisk', '-N0', drive], capture_output=True, text=True)
        print(sgdisk_results.stdout)
        print(sgdisk_results.stderr)
    except subprocess.CalledProcessError as e:
        print(f'sgdisk {red}Error{nc}: {e}')
        return False
    except Exception as e:
        print(f'sgdisk: Unknown {red}Error{nc}! Drive not Partitioned')
        return False
    try:
        print(f'Creating unique {white}UUID{nc} for drive {drive}....')
        sgdisk_results = subprocess.run(['sgdisk', '-G', drive], capture_output=True, text=True)
        print(sgdisk_results.stdout)
        print(sgdisk_results.stderr)
        print('')
        print(f'Process (sgdisk) {green}COMPLETE{nc}!')
        return True
    except subprocess.CalledProcessError as e:
        print(f'sgdisk {red}Error{nc}: {e}')
        return False
    except Exception as e:
        print(f'sgdisk: Unknown {red}Error{nc}! Drive not Partitioned')
        return False

def make_filesystem(drive):
    """
    Formats the new drive to selected filesystem
    """
    drive = drive + '1'
    try:
        print(f'Please wait while we format {blue}{drive}{nc} as {green}{file_system}{nc}.................')
        if file_system=='xfs':
            mkfs_results = subprocess.run([f'mkfs.xfs', '-q', '-f', drive], capture_output=True, text=True)
        elif file_system=='ext4':
            mkfs_results = subprocess.run([f'mkfs.ext4', '-F', drive], capture_output=True, text=True)
        else:
            print(f'{red}ERROR{nc}: Unsupported Filesystem: {file_system}')
            return False
        print (mkfs_results.stdout)
        print (mkfs_results.stderr)
        print('')
        print(f'Process (mkfs.{file_system}) {green}COMPLETE{nc}!')
        return True
    except subprocess.CalledProcessError as e:
        print(f'mkfs {red}Error{nc}: {e}')
        return False
    except Exception as e:
        print(f'mkfs: Unknown {red}Error{nc}! Drive not Partitioned')
        return False


def add_uuid_to_fstab(drive):
    """
    Uses a little shell script (get_drive_uuid.sh) to get our drive UUID after it have been
    formatted.
    """
    drive = drive + '1'
    try:
        print(f'Please wait while we add {blue}{drive}{nc} to /etc/fstab.......')
        uuid_results = subprocess.check_output([get_drive_uuid, drive]).decode('ascii').rstrip()
        if uuid_results == '':
            print(f'{red}BAD{nc} or {yellow}NO{nc} UUID returned! Please handle this drive manually!')
            return False
        print(f'Your drive UUID is: {green}{uuid_results}{nc}')
        print(f'Verifying that {green}{uuid_results}{nc} does not exist in /etc/fstab')
        with open('/etc/fstab') as fstab:
            if uuid_results in fstab.read():
                print (f'{red}ERROR!{nc}: {green}{uuid_results}{nc} already exists /etc/fstab, exiting!')
                return False
            else:
                print (f'UUID: {green}{uuid_results}{nc} does not exist in /etc/fstab, adding it now.')
                mountpoint = get_next_mountpoint()
                with open ('/etc/fstab', 'a') as fstab_edit:
                    fstab_edit.write(f'/dev/disk/by-uuid/{uuid_results} {mountpoint} xfs defaults,user 0 0   #Added by auto_drive.py\n')
                with open('/etc/fstab') as fstab:
                    if uuid_results in fstab.read():
                        print(f'UUID: {green}{uuid_results}{nc} now exists in /etc/fstab, {green}continuing{nc}.....')
                    else:
                         print(f'{red}ERROR! {green}{uuid_results}{nc} was not added to /etc/fstab!')
                         return False
                    print(f'{blue}{drive}{nc} added to {red}/etc/fstab{nc} and will be mounted at {green}{mountpoint}{nc}')
                    subprocess.run(['mount', mountpoint], capture_output=True, text=True)
                    if ismount(mountpoint):
                        print(f'Drive {blue}{drive}{nc} Successfully Mounted')
                    else:
                        print(f'Drive mount {red}FAILED!{nc}. Please manually check your system.')
                        return False
        return True
    except subprocess.CalledProcessError as e:
        print(f'uuid error: {e}')
        return False
    except Exception as e:
        print(f'uuid error: {e}')
        return False


def can_we_run():
    """
    Check to see if the chia configuration file noted above exists, exits if it does not.
    Check to see we are using a supported filesystem.
    """
    if exists(chia_config_file):
        pass
    else:
        print(f'\n{red}ERROR{nc} opening {green}{chia_config_file}{nc}\nPlease check your {green}filepath{nc} and try again!\n\n')
        exit()
    if file_system not in {'ext4', 'xfs'}:
        print (f'\n{red}ERROR{nc}: {green}{file_system}{nc} is not a supported filesystem.\nPlease choose {green}ext4{nc} or {green}xfs{nc} and try again!\n\n')
        exit()
    else:
        pass
    if exists (get_drive_uuid):
        pass
    else:
        print(f'\n{red}ERROR{nc} opening {green}{get_drive_uuid}{nc}\nPlease check your {green}filepath{nc} and try again!\n\n')
        exit()


def update_chia_config(mountpoint):
    """
    This function adds the new mountpoint to your chia configuration file.
    """
    try:
        with open(chia_config_file) as f:
            chia_config = yaml.safe_load(f)
            if mountpoint in f:
                print(f'{green}Mountpoint {red}Already{nc} Exists - We will not add it again!\n\n')
                return True
            else:
                chia_config['harvester']['plot_directories'].append(mountpoint)
    except IOError:
        print(f'{red}ERROR{nc} opening {yellow}{chia_config_file}{nc}! Please check your {yellow}filepath{nc} and try again!\n\n')
        return False
    try:
        with open(chia_config_file, 'w') as f:
            yaml.safe_dump(chia_config, f)
            return True
    except IOError:
        print(f'{red}ERROR{nc} opening {yellow}{chia_config_file}{nc}! Please check your {yellow}filepath{nc} and try again!\n\n')
        return False

def sanitise_user_input(prompt, type_=None, min_=None, max_=None, range_=None):
    """
    Quick and simple function to grab user input and make sure it's correct.
    """
    if min_ is not None and max_ is not None and max_ < min_:
        raise ValueError("min_ must be less than or equal to max_.")
    while True:
        ui = input(prompt)
        if type_ is not None:
            try:
                ui = type_(ui)
            except ValueError:
                print("Input type must be {0}.".format(type_.__name__))
                continue
        if max_ is not None and ui > max_:
            print("Input must be less than or equal to {0}.".format(max_))
        elif min_ is not None and ui < min_:
            print("Input must be greater than or equal to {0}.".format(min_))
        elif range_ is not None and ui not in range_:
            if isinstance(range_, range):
                template = "Input must be between {0.start} and {0.stop}."
                print(template.format(range_))
            else:
                template = "Input must be {0}."
                if len(range_) == 1:
                    print(template.format(*range_))
                else:
                    expected = " or ".join((
                        ", ".join(str(x) for x in range_[:-1]),
                        str(range_[-1])
                    ))
                    print(template.format(expected))
        else:
            return ui


def main():
    add_new_drive()


if __name__ == '__main__':
    main()
