<h2 align="center">
  <a name="chia_drive_logo" href="https://github.com/rjsears/chia_plot_manager"><img src="https://github.com/rjsears/chia_plot_manager/blob/main/images/chia_plot_manager_v2.png" alt="Chia Plot Manager"></a><br>
Auto Drive - Automatice Drive Formatting, Mounting & Chia Config Updating!
  <p align="center">

  </h2>
  </p>
  <p align="left"><font size="3">
As the title implies, I designed this script to help with the adding of new hard drives to your Chia Harvester/NAS. This is a command line drive interactive python script. Please see the top fo the script for more information. 
  
  Hopefully, this will be useful for someone!
  
  
<h2 align="center">
  <a name="chia_auto_drive_screen" href="https://github.com/rjsears/chia_plot_manager/tree/main/auto_drive"><img src="https://github.com/rjsears/chia_plot_manager/blob/main/images/chia_auto_drive_output.png" alt="Chia Auto Drive"></a><br>
  <br><hr><br>
  
  Installation and usage Instructions:
  
  1) Download a copy of this script and the `get_drive_uuid.sh` shell script and place it in your working directory
  
  2) Edit the auto_drive.py script and alter the line pointing to your chia configuration file:
     `chia_config_file = '/root/.chia/mainnet/config/config.yaml'`
  
  3) Alter the path_glob line to match your mount point directory structure. This script is specifically set up and tested
     with the directory structure that I have laid out in the main readme file for chia_plot_manager. It is possible that 
     it will work with other structures but it is way beyond my capability to test for every possible directory structure
     combination. I would recommend reading and understanding what the `get_next_mountpoint()` function does and then 
     see if it will work with your directory structure.
     `path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*'

  4) Alter the following line to point to where you have installed the `get_drive_uuid.sh` shell script.
     `uuid_results = subprocess.check_output(['/root/plot_manager/plot_manager/get_drive_uuid.sh', drive]).decode('ascii').rstrip()` 
  
  5) `chmod +x` both the auto_drive.py script and the `get_drive_uuid.sh` script.
  
  6) Change to the directory where you have installed this script and `./auto_drive.py` If the script finds any new drives it will
     then prompt you to accept the drive and mountpoint it plans to use. Once the drive has been readied for the system and mounted
     it will ask you if you want it added to your chia configuration file.
  
  
  
  
  Enjoy!
