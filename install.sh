#! /bin/bash

# Simple Install script for NEW clean Ubuntu 20.04 install, updates
# the system with various tools and tings required to run the various
# parts of chia_plot_manager.

# I use this to create new NAS/Plotter servers.

red='\033[0;31m'
yellow='\033[0;33m'
green='\033[0;32m'
white='\033[0;37m'
blue='\033[0;34m'
nc='\033[0m'


## Due to the nature of this script, it must be run as root or via sudo/su.
must_run_as_root(){
    if [[ $(id -u) -ne 0 ]]; then
        echo
        echo -e "${red}ERROR${nc}: Must run as root!"
        echo "sudo install.sh option"
        echo "or su- first."
        echo
        exit 1
    fi
}

welcome_message() {
        echo -e "\n\n*** Welcome to the ${red}P${yellow}l${green}o${white}t ${blue}M${red}a${yellow}n${green}g${white}e${blue}r${nc} Install Script ***\n"
}

create_example_directory_structure(){
    echo -e -n "\nShould we ${yellow}CREATE${nc} mount points using example directory structure? "
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      nl $current_directory/extras/drive_structures/drive_structures
        count="$(wc -l $current_directory/extras/drive_structures/drive_structures | cut -f 1 -d' ')"
		    n=""
	     	while true; do
         			echo
         			read -p "Please Select Drive Structure to CREATE: "  n
         			if [ "$n" -eq "$n" ] && [ "$n" -gt 0 ] && [ "$n" -le "$count" ]
         			then
       			      	break
         			fi
	     	done
	     	structure_selected="$(sed -n "${n}p" $current_directory/extras/drive_structures/drive_structures)"
	     	echo
	     	echo -e -n "You selected ${yellow}$structure_selected${nc}. Is this ${yellow}CORRECT${nc}? "
	     	read -n 1 -r
            		echo
            	if [[ $REPLY =~ ^[Yy]$ ]]
             	then
                     	echo -e "We will duplicate ${blue}$structure_selected${nc}"
                     	xargs mkdir -p < $current_directory/extras/drive_structures/$structure_selected
             	else
              create_example_directory_structure
              fi
    fi
}

set_permissions (){
  echo -e "\n\n${green}Setting File Permissions.........${nc}\n"
  chmod +x $current_directory/auto_drive/auto_drive.py
  chmod +x $current_directory/auto_drive/get_drive_uuid.sh
  chmod +x $current_directory/chianas/*.py
  chmod +x $current_directory/chianas/*.sh
  chmod +x $current_directory/chiaplot/*.py
  chmod +x $current_directory/chiaplot/*.sh
  chmod +x $current_directory/coin_monitor/*.py
  echo -e "${green}DONE${nc}\n"
}

nuke_snap (){
    if [ $(dpkg-query -W -f='${Status}' snapd 2>/dev/null | grep -c "ok installed") -eq 1 ];
    then
        echo -e -n "\nShould we [${yellow}UNINSTALL${nc}] SNAP? "
        read -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "\n\n${green}Uninstalling SNAP.........${nc}\n"
            systemctl stop snapd && systemctl disable snapd
            apt purge snapd
            rm -rf ~/snap
            rm -rf /snap /var/snap /var/lib/snapd /var/cache/snapd /usr/lib/snapd
            mv $current_directory/extras/no-snap.pref /etc/apt/preferences.d/
            chown root:root /etc/apt/preferences.d/no-snap.pref
            echo -e "${green}DONE${nc}\n"
        else
            echo -e -n "\nSNAP ${yellow}PRESERVED${nc}!"
        fi
   fi

}

## Here is where we do all of the software updating that we need to do to
update_software_and_system(){
  echo -e "\n\n${green}Updating System Software and Installing Required Packages.........${nc}\n"
  apt update && apt upgrade -y  # Let's do the basic update of our software before we do anything else
  apt install locate vim wget dstat smartmontools tree unzip net-tools tmux glances python3-pip pv postfix mailutils -y
  pip3 install -r $current_directory/chianas/requirements.txt
  echo -e "${green}DONE${nc}\n"
}

get_current_directory(){
  SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
current_directory="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
if [ $current_directory != '/root/plot_manager' ]; then
    echo -e "\n\n ${red}* * * * *${yellow} IMPORTANT ${red}* * * * *${nc}"
    echo -e "${green}All scripts assume that they have been installed at ${white}/root/plot_manager${green}"
    echo -e "and are configured as such. If you are changing the install directory,"
    echo -e "please review all scripts for the proper paths or they will fail.\n\n"
else
  echo
fi
}

final_goodbye(){
  echo -e "Thank you for choosing to try ${green}plot_manager${nc}, I hope it works well for you. If you"
  echo -e "Have any trouble or issues, please feel free to reach me on my github page.\n"
  echo -e "Before you go, there are some files and configurations that you should check to make sure they"
  echo -e "agree with your configuration, otherwise you will have issues with the script(s)."
  echo -e "By default, the file paths assume installation at /root/plot_manager\n\n"
  echo -e "Please check the following files to see if they need to be changed:\n"
  echo -e "${green}$current_directory/auto_drive/auto_drive.py${nc}:"
  echo -e "Verify the following: chia_config_file, get_drive_uuid & file_system"
  echo -e "Also verify that your path_glob is correct for get_next_mountpoint()\n"
  echo -e "${green}$current_directory/chia_nas/drive_manager.py${nc}:"
  echo -e "Verify the following: sys.path.append, receive_script & chia_log_file"
  echo -e "Also verify the correct path in the read_config_data & update_config_data functions.\n"
  echo -e "${green}$current_directory/chia_nas/logging.yaml${nc}:"
  echo -e "Verify correct filename and paths for your logging files, should be ${green}$current_directory/logs${nc}\n"
  echo -e "${green}$current_directory/chia_nas/move_local_plots.py${nc}:"
  echo -e "Verify sys.path.append, drive_activity_test, drive_activity_log, read_config_data\n"
  echo -e "${green}$current_directory/chia_nas/offlined_drives${nc}:"
  echo -e "Enter any drives you want 'offlined'. Should match drives returned bu path_glob in drive_manager.py\n"
  echo -e "${green}$current_directory/chia_nas/system_info.py${nc}:"
  echo -e "Update information as necessary.\n"
  echo -e "${green}$current_directory/chia_nas/system_logging.py${nc}:"
  echo -e "Verify sys.path.append, default_logging() and read_logging_config() for correct paths.\n"
  echo -e "${green}$current_directory/chiaplot/logging.yaml${nc}:"
  echo -e "Verify correct filename and paths for your logging files, should be ${green}$current_directory/logs${nc}\n"
  echo -e "${green}$current_directory/chiaplot/plot_manager.py${nc}:"
  echo -e "Verify sys.path.append, nas_server, plot_server(.self), network_interface, plot_dir, & remote_checkfile"
  echo -e "Also verify paths in process_plot().\n"
  echo -e "${green}$current_directory/chiaplot/send_plot.sh${nc}:"
  echo -e "Verify correct hostnames and paths. Change ${green}chianas01-internal${nc} to your nas hostname.\n"
  echo -e "${green}$current_directory/chiaplot/system_logging.py${nc}:"
  echo -e "Verify sys.path.append, default_logging() and read_logging_config() for correct paths.\n"
  echo -e "${green}$current_directory/coin_monitor/coin_monitor.py${nc}:"
  echo -e "Verify sys.path.append, chia_log, new_coin_log and read_config_data() for correct paths.\n"
  echo -e "${green}$current_directory/coin_monitor/coin_monitor_config${nc}:"
  echo -e "Verify notification settings and how many current coins you have.\n"
  echo -e "${green}$current_directory/coin_monitor/logging.yaml${nc}:"
  echo -e "Verify correct filename and paths for your logging files, should be ${green}$current_directory/logs${nc}\n"
  echo -e "${green}$current_directory/coin_monitor/system_info.py${nc}:"
  echo -e "Update information as necessary.\n"
  echo -e "${green}$current_directory/coin_monitor/system_logging.py${nc}:"
  echo -e "Verify sys.path.append, default_logging() and read_logging_config() for correct paths.\n\n"
  echo -e "To view this list again at any time run $current_directory/install.sh -h\n"
  echo -e "Install Process Complete - Thank You and have a ${red}G${yellow}R${white}E${green}A${blue}T${nc} Day!\n\n"
}


while getopts ":h" option; do
   case $option in
      h) # display Help
         must_run_as_root
         final_goodbye
         exit;;
     \?) # incorrect option
         echo -e "${red}ERROR${nc}: Invalid option"
         exit;;
   esac
done


must_run_as_root
welcome_message
get_current_directory
nuke_snap
update_software_and_system
set_permissions
create_example_directory_structure
final_goodbye
