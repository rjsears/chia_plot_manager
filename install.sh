#! /bin/bash


install_directory='/root/plot_manager'


red='\033[0;31m'
yellow='\033[0;33m'
green='\033[0;32m'
white='\033[0;37m'
blue='\033[0;34m'
nc='\033[0m'

how_called=$1
now=$(date +%y%m%d%H%M%S)


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
        echo -e "\n\nWelcome to the ${green}Chia_Plot_Manager${nc} Install Menu\n"
}

select_install() {
      #  echo -e "What would you like to install?"
        nl software_components
        count="$(wc -l software_components | cut -f 1 -d' ')"
		    n=""
	     	while true; do
         			echo
         			read -p 'Please Select Component to Install: ' n
         			if [ "$n" -eq "$n" ] && [ "$n" -gt 0 ] && [ "$n" -le "$count" ]
         			then
       			      	break
         			fi
	     	done
	     	component_selected="$(sed -n "${n}p" software_components)"
	     	echo
	     	echo -e -n "You selected ${yellow}$component_selected${nc}. Is this ${yellow}CORRECT${nc}? "
	     	read -n 1 -r
            		echo
            	if [[ $REPLY =~ ^[Yy]$ ]]
             	then
                     	echo -e "We will Install ${blue}$component_selected${nc}"
             	else
              select_install
              fi
}

get_install_directory(){
      if [[ -n "$install_directory" ]]; then
          echo
            echo -e -n "Default install directory set to [ ${yellow}$install_directory${nc} ]. OVERRIDE? "
            read -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                install_directory=""
                get_install_directory
            else
                return
            fi
      else
          while [[ $install_directory == '' ]]
          do
              echo
              echo -e -n "Please enter the directory where you would like to install ${green}plot_manager${nc}:  "
              read install_directory
          done
          echo -e -n "\nYou entered [${blue}$install_directory${nc}], is this correct? "
          read -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
              return
          else
              install_directory=""
              get_install_directory
          fi
      fi
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
         			read -p "Please Select Drive Structure to ${green}CREATE${nc}: "  n
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


nuke_snap (){
    echo -e -n "\nShould we [${yellow}UNINSTALL${nc}] SNAP? "
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl stop snapd && systemctl disable snapd
        apt purge snapd
        rm -rf ~/snap
        rm -rf /snap /var/snap /var/lib/snapd /var/cache/snapd /usr/lib/snapd
        mv $current_directory/extras/no-snap.pref /etc/apt/preferences.d/
        chown root:root /etc/apt/preferences.d/no-snap.pref
    else
        echo -e -n "\nSNAP ${yellow}PRESERVED${nc}!"
    fi
}


## Here is where we do all of the software updating that we need to do to
update_software_and_system(){
  apt update && apt upgrade -y  # Let's do the basic update of the Rpi software before we do anything else
  apt install locate vim wget dstat smartmontools tree unzip net-tools tmux glances python3-pip postfix mailutils -y
}

get_current_directory(){
  SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
current_directory="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
}








## Help Information

help() {
  clear
  echo
  echo -e "    *** Welcome to the ${red}P${yellow}l${green}o${white}t ${blue}M${red}a${yellow}n${green}g${white}e${blue}r${nc} Install Script ***"
  echo


}

while getopts ":h" option; do
   case $option in
      h) # display Help
         must_run_as_root
         help
         exit;;
     \?) # incorrect option
         echo -e "${red}ERROR${nc}: Invalid option"
         exit;;
   esac
done


must_run_as_root
get_current_directory
welcome_message
nuke_snap
#update_software_and_system
create_example_directory_structure

