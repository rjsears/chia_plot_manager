<h2 align="center">
  <a name="chia_drive_logo" href="https://github.com/rjsears/chia_plot_manager"><img src="https://github.com/rjsears/chia_plot_manager/blob/main/images/chia_plot_manager_new.png" alt="Chia Plot Manager"></a><br>

  Chia Plot, Drive Manager, Coin Monitor & Auto Drive (V0.96 - September 5th, 2021)
  </h2>
  <p align="center">
Multi Server Chia Plot and Drive Management Solution
  </p>
  
  <hr><br>
  
  
### Basic Installation and Configuration Instructions

It would be virtually impossible to account for every single configuration for each person's server farm setup, but many people are running this code on many different kinds 
of configurations. If you have issues, please open an issue and I will try my best to work throught them with you.

In order to run this code, you should start with the main readme one level above this one. It covers things such as the Overview and Theory of operation, how the directory 
structories were designed, all of the various command line options and a **lot** of other information about my setup and configuration. This also includes discussions about
network configurations and the like. It really is a **must read** before moving on to this readme.

So on to the **basic** installation and configuration. In order to install the **NAS** portion of this setup (which can be both a NAS and a Plotter if you wish), start with
a fresh installation of Ubuntu 20.04 (or whatever may work for you) and then run the following:

```git clone https://github.com/rjsears/chia_plot_manager.git && mv chia_plot_manager plot_manager && cd plot_manager && chmod +x install.sh && ./install.sh help```<br><br>

This will clone the currnet main branch of my repo, move it into the recommended directory ```(/root/plot_manager)```, set the correct file permissions and then launch the install
script with the `-h` option which will print out the help menu. To run the actual install for the NAS, simply type ```./install.sh nas``` and hit enter. You will be prompted to
answer a series of questions. Read the aformentioned readme to understand these questions, and continue with the install. The install will update your Ubuntu system completely, 
install all required dependancies, create the director to hold tha main configuration file ```(plot_manager.yaml)```, create a skel directory structure (if you request it to), and
cleanup after itself. It is **highly** recommended that you do this on a clean system, however it should work on an in-use system as well. I have done a lot of testing on various
production servers and have never had an issue.

Before going further with this, make sure you have your ```Chia``` insalled and configured to your liking. You will need the full path to the logfile as well as the config file.

Remember that you need to configure things like ```postfix``` once you have completed the initial install, otherwise you will not get notification or the daily emailed reports.
Once complete, test it from the command line to make sure you can receive mail. We use the linux mail command to send out all email notifications. Lastly you need to edit your
main configuration file prior to running ```./drive_manager.py``` for the first time. failure to do so will result in an error message telling you to do so!

Some of the entries in the configu file (shown below) you set and some are set by the system. They can be overriden if you know what you are doing, but if not, I would leave them
be. This is a standard YAML file, so leave the formatting as you see it or you will get errors when attempting to run ```drive_manager.py```. Start be setting the following options:
<br>

<ul>
  <li><b>configured</b> (set this to <b>true</b>) </li>
  <li><b>hostname</b> (set this to the hostname of the system - should match IP address used by all other systems to comunicate to this box)</li>
  <li><b>plot_receive_interface</b> (set this tot he name of the interface as shown by ifconfig that you use to receive plots)</li>
  <li><b>plot_receive_interface_threshold</b> (set this the the percentage utilization on the bove inteface that indicates that we are receiving plot) </li>
  <li><b>pools</b> (set these setting according to your configuration, see notes) </li>
  <li><b>chia_log_file</b> (full path to your chia log file (usually debug.log) (Make sure to set logging level to INFO or DEBIG in your Chia Config)</li>
  <li><b>chia_config_file</b> (same as above)</li>
  <li><b>remote_harvester_reports</b> (Set according to your configuration. See notes in config file)</li>
  <li><b>current_plotting_drive</b> (Generally the first drive you want to store inbound plot on)</li>
  <li><b>total_plot_highwater_warning</b> (When you get below this number of available plot space, you will get a warning)</li>
  <li><b>offlined_drive</b> (Enter drives here you do not want <b>drive_manager.py</b> to touch or write to)</li>
  <li><b>local_plotter</b> (Configure per your setup, see notes in configuration file)</li>
  <li><b>notifications</b> (Set according to your preferences)</li>
  </ul>


```
# v0.95 2021-09-03
# Once you have made the necessary modifications to this file, change this to
# True.
configured: False

# Enter the hostname of this server:
hostname: chianas01

# Enter the name (as shown by ifconfig) of the interface that you RECEIVE plots on
# from your plotters. This is used to check for network traffic to prevent multiple
# plots from being transferred at the same time.
plot_receive_interface: eth0

# This is a number that represents at what percentage overall utilization of the above
# interface we will assume that a plot transfer is taking place. You should really TEST
# this to make sure it works for your needs. If you have a dedicated interface to move
# plots, then it can be set very low (1 to 2), however if you have a shared interface,
# you should test while a plot transfer is running and set it to what number makes sense.
# To test simply run the following command and look at the very last number:
# /usr/bin/sar -n DEV 1 50 | egrep eth0
plot_receive_interface_threshold: 2

# Are we plotting for pools? This has nothing to do with the actual plotting of
# plots but rather just naming of the new plots and eventually the replacing of
# old plots with portable plots.
pools:
  active: False
  # Do we want to replace non-pool plots with new plots
  replace_non_pool_plots: True
  # Should we fill up empty drive space before replacing old non-pool plots?
  fill_empty_drives_first: True
  # When we get below this number of plots available on the system
  # we will switch to replacing plots. Has no effect is active: False is
  # set above
  empty_drives_low_water_mark: 100
  # How many Portable Plots per day are we generating
  current_portable_plots_daily: 0
  # What is our Midnight portable plot count?
  current_portable_plots_midnight: 1
  # What drive are we currently using to replace plots?
  current_plot_replacement_drive: /mnt/enclosure0/front/column0/drive4

# Enter Logging Information
logging: True
log_level: DEBUG


# Where is your chia log file located? Remember to set the logging level
# in your chia config to INFO. By default, it is set to WARNING.
chia_log_file: not_set
chia_config_file: not_set

# If you are running multiple remote harvesters, set this to true
# and enter their hostnames below. These hostnames should NOT
# include your local hostname listed above. Also, these hostname
# should be configured for passwordless ssh and should be configured
# such that when you ping the hostname, it goes across the fastest
# interface you have between these harvesters. Set to True if you
# have multiple harvesters and want combined reporting.
remote_harvester_reports:
  active: False
  remote_harvesters:
    - chianas02
    - chianas03

# This is the local drive where we store inbound plots from our
# main plotter. Also stores information about our current plots
# on our server. The total plot high water warning is the number
# of plots left when the alert will be sent. When you have LESS
# than this number of plots, you will get an alert.
harvester:
  current_plotting_drive: /mnt/enclosure1/front/column1/drive36
  current_total_plots_midnight: 1
  current_total_plots_daily: 1
  total_plot_highwater_warning: 300
  total_plots_alert_sent: False

  # List of 'offlined' drives that we do not want plots written to
  # for any reason. In this case maybe 'drive0' and 'drive1' are our
  # OS drives, or maybe they are throwing errors and we don't want to
  # use them until they are replaced. If you have no offlined drives,
  # this line should look like this:   offlined_drives: []
  offlined_drives:
    - drive0
    - drive1

# I use Plotman to do my plotting, but this should work for anything. This
# has NOTHING to do with setting up your plotting configuration and is
# only used for monitoring drive space for notifications. Set to True if
# locally plotting and configure the rest of the settings.
local_plotter:
  active: False

  # Make sure to use the mountpoint
  temp_dirs:
    dirs:
    - /mnt/nvme_drive0
    - /mnt/nvme_drive1
    # What critical usage % should we send an error? Do not make this too low
    # or you will get nuisance reports.
    critical: 99
    critical_alert_sent: False

  # This is the directory that you are using for your plots. If you will be
  # utilizing the integrated 'move_local_plots.py' scripts, this is usually
  # just a single drive. The plots are then moved out of this directory to
  # their final resting place on the harvester. move_local_plots.py is
  # currently only written to support a single drive here.
  dst_dirs:
    dirs:
      - /mnt/enclosure1/rear/column3/drive79

    # At what % utilization do we send an error?
    critical: 95
    critical_alert_sent: False

  # This is the current internal drive we are using to stop plots moved off
  # of dst_dir above. This is not the same drive we use for storing plots
  # coming from an outside plotter. We use a different drive to prevent
  # drive IO saturation.
  current_internal_drive: /mnt/enclosure1/front/column3/drive59

  # During local moves where we are replacing plots, it is very important that
  # we stop all local processing if we detect an error, otherwise we could delete
  # a bunch of plots without meaning to, each time our script is run. This error is
  # set if we encounter an error and must be MANUALLY unset to continue to process
  # local plots if you have chosen to replace old plots:
  local_move_error: False
  # Once we get a local move error, did we send an alert?
  local_move_error_alert_sent: False

# This is where we set up our notifications
notifications:
  active: True
  methods:
    pb: False
    email: True
    sms: False
  types:
    new_plot_drive: True
    daily_update: True
    per_plot: False
    warnings: True
  # What email addresses will get the emails?
  emails:
    - someone@gmail.com
    - someoneelse@gmail.com

  # What phones numbers will received the SMS text messages? Include '+1'
  phones:
    - '+18584150987'

  # These are your notification account settings. For email, you must configure
  # your locate MTA. Installer installs Postfix by default. Twilio (SMS) requires
  # a paid account, PushBullet is free.
  accounts:
    twilio:
      from: '+18587491119'
      account: your_account_key
      token: your_account_token
    pushBullet:
      api: your_account_api
```

<br><br>

Once you have completed all of the configuration changes same the file, switch to ```/root/plot_manager``` and run ```./drive_manager.py -h```
If you get the help screen, it means that we see that you have configured your config file and we are ready to run. Next run it by itself:
```./drive_manager.py```, this will initialize everything and create the necessary files to run the system. If you get any error messages at
this point, you should stop and address them before bringing you plotter online. One of the number one errors is **NOT** running it prior
to starting your plotter process. If you so not run ```./drive_manager.py``` initially, it will **NOT** create the necessary receive scripts
based on your system configuration and will not be able to receive inbound plots from your plotter.
