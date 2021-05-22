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

## Welcome everyone....
welcome_message() {
        echo -e "\n\n                  * * * * * * * * Welcome to the ${red}P${yellow}l${green}o${white}t ${blue}M${red}a${yellow}n${green}g${white}e${blue}r${nc} Install Script * * * * * * * *\n"
        echo -e "${red}WARNING!${nc} - This script assumes you are installing it on a NAS/Harvester. Some of the items (such as cron entries)"
        echo -e "${red}WARNING!${nc} - may not be suitable for all installations. If you are ${yellow}UNSURE${nc} what options to choose"
        echo -e "${red}WARNING!${nc} - during the install (crontab, network performance, creating directories), I suggest that you do not"
        echo -e "${red}WARNING!${nc} - utilize those options until you understand them completely!."
        echo
        echo -e "${red}WARNING!${nc} - ${yellow}I have designed this install script for a Fresh, Clean installation of Ubuntu Linux!${nc}"
        echo
        echo -e "${red}WARNING!${nc} - Please ${yellow}CAREFULLY${nc} read the notes at the end (or run ./install.sh notes) at any time."
        echo -e "${red}WARNING!${nc} - There are a ${yellow}LOT${nc} of configuration changes and path updates that need to be done to"
        echo -e "${red}WARNING!${nc} - make these scripts your own!\n"
        echo -e -n "Should we ${green}CONTINUE${nc}? "
        read -n 1 -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "\n${yellow}GOODBYE${nc}"
            exit 1
        fi
}

## Creates our entire plot directory structure based on predefined layouts
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
                     	tree -d /mnt
             	else
              create_example_directory_structure
              fi
    fi
}

## Sets execute permission
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

## Let's get rid of SNAP, shall we..... 
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
  apt install locate vim wget dstat smartmontools tree unzip net-tools tmux glances python3-pip pv nmap postfix mailutils -y
  pip3 install -r $current_directory/chianas/requirements.txt
  apt autoremove -y
  echo -e "${green}DONE${nc}\n"
}

## Figure out exactly what directory we are in so we can make decisions...
get_current_directory(){
  SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
current_directory="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
if [ $current_directory != '/root/plot_manager' ]; then
    echo -e "\n ${red}* * * * *${white} IMPORTANT ${red}* * * * *${nc}${white} IMPORTANT ${red}* * * * *${nc}${white} IMPORTANT ${red}* * * * *${nc}"
    echo -e "${green}All scripts assume that they have been installed at ${white}/root/plot_manager${green}"
    echo -e "and are configured as such. If you are changing the install directory,"
    echo -e "please review all scripts for the proper paths or they will fail${nc}.\n\n"
else
  echo
fi
}

## Update our crontab with the necessary entries
update_crontab(){
  get_current_directory
  echo -e "This will update your root crontab to add the following entries If you need something"
  echo -e "different, remember to make the necessary changes after the installation has completed."
  echo -e ""
  echo -e "PATH=$current_directory:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  echo -e "01 00 * * * cd $current_directory && /usr/bin/python3 $current_directory/drive_manager.py -ud >/dev/null 2>&1"
  echo -e "02 00 * * * cd $current_directory && /usr/bin/python3 $current_directory/drive_manager.py -dr >/dev/null 2>&1"
  echo -e "*/1 * * * * cd $current_directory && /usr/bin/python3 $current_directory/drive_manager.py >/dev/null 2>&1"
  echo -e "*/2 * * * * cd $current_directory && /usr/bin/python3 $current_directory/move_local_plots.py >/dev/null 2>&1"
  echo -e -n "\nShould we ${yellow}UPDATE${nc} Crontab with these entries? "
        read -n 1 -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
          (crontab -l ; echo "PATH=$current_directory:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")| crontab -
          (crontab -l ; echo "01 00 * * * cd $current_directory && /usr/bin/python3 $current_directory/drive_manager.py -ud >/dev/null 2>&1")| crontab -
          (crontab -l ; echo "02 00 * * * cd $current_directory && /usr/bin/python3 $current_directory/drive_manager.py -dr >/dev/null 2>&1")| crontab -
          (crontab -l ; echo "*/1 * * * * cd $current_directory && /usr/bin/python3 $current_directory/drive_manager.py >/dev/null 2>&1")| crontab -
          (crontab -l ; echo "*/2 * * * * cd $current_directory && /usr/bin/python3 $current_directory/move_local_plots.py -ud >/dev/null 2>&1")| crontab -
          echo -e "\nCrontab has been ${yellow}UPDATED${nc}!\n"
        else
            echo -e "\nCrontab has ${red}NOT${nc} been ${yellow}UPDATED${nc}!\n"
        fi
}

## Add entries into sysctl to improve network performance
improve_network_performance(){
    must_run_as_root
    echo -e "\nNetwork Performance settings that >>> ${blue}I${nc} <<< use on my 10Gbe connected"
    echo -e "plotters, harvesters, and farmers. Your performance may vary from mine!\n"
    echo -e -n "\nShould we ${yellow}UPDATE${nc} Network Performance Configuration? "
        read -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "vm.swappiness=1" >> /etc/sysctl.conf
            echo "net.core.wmem_max=134217728" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_wmem=2097152 16777216 33554432" >> /etc/sysctl.conf
            echo "net.core.rmem_max=134217728" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_rmem=2097152 16777216 33554432" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_window_scaling = 1" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_timestamps=1" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_no_metrics_save=1" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_low_latency=0" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_mtu_probing=1" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_sack = 0" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_dsack = 0" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_fack = 0" >> /etc/sysctl.conf
            echo "net.ipv4.tcp_slow_start_after_idle = 0 " >> /etc/sysctl.conf
            echo "net.ipv4.ipfrag_high_threshold = 8388608" >> /etc/sysctl.conf
            echo "net.core.netdev_max_backlog = 30000" >> /etc/sysctl.conf
            sysctl -e -p /etc/sysctl.conf
            echo -e "${green}DONE${nc}\n"
        else
          echo -e "${green}DONE${nc}\n"
       fi
}


## Share some final notes...
final_notes(){
  clear
  get_current_directory
  echo -e "\n\nThank you for choosing to try ${green}plot_manager${nc}, I hope it works well for you. If you"
  echo -e "Have any trouble or issues, please feel free to reach me on my github page.\n"
  echo -e "Before you go, there are some files and configurations that you should check to make sure they"
  echo -e "agree with your configuration, otherwise you will have issues with the script(s)."
  echo -e "By default, the file paths assume installation at /root/plot_manager\n\n"
  echo -e "Please check the following files to see if they need to be changed:\n"
  echo -e "${green}$current_directory/auto_drive/auto_drive.py${nc}:"
  echo -e "   - Verify the following: chia_config_file, get_drive_uuid & file_system"
  echo -e "   - Also verify that your path_glob is correct for get_next_mountpoint()\n"
  echo -e "${green}$current_directory/chia_nas/drive_manager.py${nc}:"
  echo -e "   - Verify the following: sys.path.append, receive_script & chia_log_file"
  echo -e "   - Also verify the correct path in the read_config_data & update_config_data functions.\n"
  echo -e "${green}$current_directory/chia_nas/logging.yaml${nc}:"
  echo -e "   - Verify correct filename and paths for your logging files, should be ${green}$current_directory/logs${nc}\n"
  echo -e "${green}$current_directory/chia_nas/move_local_plots.py${nc}:"
  echo -e "   - Verify sys.path.append, drive_activity_test, drive_activity_log, read_config_data\n"
  echo -e "${green}$current_directory/chia_nas/offlined_drives${nc}:"
  echo -e "   - Enter any drives you want 'offlined'. Should match drives returned bu path_glob in drive_manager.py\n"
  echo -e "${green}$current_directory/chia_nas/system_info.py${nc}:"
  echo -e "   - Update information as necessary.\n"
  echo -e "${green}$current_directory/chia_nas/system_logging.py${nc}:"
  echo -e "   - Verify sys.path.append, default_logging() and read_logging_config() for correct paths.\n"
  echo -e "${green}$current_directory/chiaplot/logging.yaml${nc}:"
  echo -e "   - Verify correct filename and paths for your logging files, should be ${green}$current_directory/logs${nc}\n"
  echo -e "${green}$current_directory/chiaplot/plot_manager.py${nc}:"
  echo -e "   - Verify sys.path.append, nas_server, plot_server(.self), network_interface, plot_dir, & remote_checkfile"
  echo -e "   - Also verify paths in process_plot().\n"
  echo -e "${green}$current_directory/chiaplot/send_plot.sh${nc}:"
  echo -e "   - Verify correct hostnames and paths. Change ${green}chianas01-internal${nc} to your nas hostname.\n"
  echo -e "${green}$current_directory/chiaplot/system_logging.py${nc}:"
  echo -e "   - Verify sys.path.append, default_logging() and read_logging_config() for correct paths.\n"
  echo -e "${green}$current_directory/coin_monitor/coin_monitor.py${nc}:"
  echo -e "   - Verify sys.path.append, chia_log, new_coin_log and read_config_data() for correct paths.\n"
  echo -e "${green}$current_directory/coin_monitor/coin_monitor_config${nc}:"
  echo -e "   - Verify notification settings and how many current coins you have.\n"
  echo -e "${green}$current_directory/coin_monitor/logging.yaml${nc}:"
  echo -e "   - Verify correct filename and paths for your logging files, should be ${green}$current_directory/logs${nc}\n"
  echo -e "${green}$current_directory/coin_monitor/system_info.py${nc}:"
  echo -e "   - Update information as necessary.\n"
  echo -e "${green}$current_directory/coin_monitor/system_logging.py${nc}:"
  echo -e "   - Verify sys.path.append, default_logging() and read_logging_config() for correct paths.\n\n"
  echo -e "To view this list again at any time run ${yellow}$current_directory/install.sh notes${nc}\n"
}

thank_you(){
  echo -e "\n\nInstall Process Complete - Thank You and have a ${red}G${yellow}R${white}E${green}A${blue}T${nc} Day!\n\n"
}

## Print out help when needed
help (){
echo -e "\nWelcome to ${green}Chia Plot Manager${nc} and associated utilities!\n"
echo -e "Options:"
echo -e "   ${yellow}install${nc}      Starts the install process."
echo -e "   ${yellow}network${nc}      Only install network performance updates and exits."
echo -e "   ${yellow}cron${nc}         Updates root crontab."
echo -e "   ${yellow}notes${nc}        Shows after-installation notes."
echo -e "   ${yellow}help${nc}         Shows this help message.\n"
echo -e "For additional help, please open an issue on my github page.\n"
}


## Here is where we start our install....
start_install(){
    must_run_as_root
    welcome_message
    get_current_directory
    nuke_snap
    update_software_and_system
    set_permissions
    create_example_directory_structure
    improve_network_performance
    update_crontab
    final_notes
    thank_you
}

## And we're off....
case "$1" in
  install)  start_install ;;
  help)     help ;;
  network)  improve_network_performance ;;
  notes)    final_notes ;;
  cron)     update_crontab ;;
  *) echo -e "\n${yellow}Usage${nc}: $0 [ install | network | cron | notes | help ]\n" >&2
     exit 1
     ;;
   esac
