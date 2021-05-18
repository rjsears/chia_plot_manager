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
</h2>  
  <h3>Installation and usage Instructions:</h3>
  
  1) Download a copy of this script and the `get_drive_uuid.sh` shell script and place it in your working directory
  
  2) Edit the auto_drive.py script and alter the line pointing to your chia configuration file:<br>
     `chia_config_file = '/root/.chia/mainnet/config/config.yaml'`
  
  3) Alter the path_glob line to match your mount point directory structure. This script is specifically set up and tested
     with the directory structure that I have laid out in the main readme file for chia_plot_manager. It is possible that 
     it will work with other structures but it is way beyond my capability to test for every possible directory structure
     combination. I would recommend reading and understanding what the `get_next_mountpoint()` function does and then 
     see if it will work with your directory structure.<br>
     `path_glob = '/mnt/enclosure[0-9]/*/column[0-9]/*`

  4) Alter the following line to point to where you have installed the `get_drive_uuid.sh` shell script.<br>
     `uuid_results = subprocess.check_output(['/root/plot_manager/plot_manager/get_drive_uuid.sh', drive]).decode('ascii').rstrip()` 
  
  5) `chmod +x` both the auto_drive.py script and the `get_drive_uuid.sh` script.
  
  6) Change to the directory where you have installed this script and `./auto_drive.py` If the script finds any new drives it will
     then prompt you to accept the drive and mountpoint it plans to use. Once the drive has been readied for the system and mounted
     it will ask you if you want it added to your chia configuration file.
  
  <br>
  
  <h3>Notes......</h3><br>
  
  There are a couple of things to remember with `auto_drive.py`. First, in order to protect any possible data on drives, we will only 
  look for drives that <em>do not</em> include a partition already on the drive. If you are reusing drives, and they have a partition
  already on the drive, `auto_drive.py` <em>will not</em> select any of those drive to work on. The best way to `reuse` a drive is to
  manually `fdisk` the drive in question, delete any existing partitions, and then `auto_drive.py` will then be able to use those
  drives. <br>
  <br>
  Second, I have determined that drives that have previously had VMFS partitions on them require special handling. `SGDisk` does not
  appear to have the ability to overwrite that partition information. In fact, `fdisk` seems to have an issue as well. After multiple
  attempts to figure this litte problem out, I found that this is the best solution:<br><br>
  
  1) Using `fdisk`, access the device in question.
  2) Delete any existing partition and issue the `w` command.
  3) Rerun the `fdisk` command on the disk, utilize the `g` command to create a new GPT signature.
  4) Create a new partition by using the `n` command.
  5) When you go to save the partition with the `w` command, you should get a notice that there is an existing VMFS partition.
  6) Answer `y` to this question and issue the `w` command, exiting `fdisk`.
  7) Once again, rerun `fdisk` and delete this new partition and issue the `w` command. 
  8) You should now be ready to use `auto_drive.py` with that drive. 
  
  
  
  
  
  Enjoy!
