<h2 align="center">
  <a name="chia_drive_logo" href="https://github.com/rjsears/chia_plot_manager"><img src="https://github.com/rjsears/chia_plot_manager/blob/main/images/chia_plot_manager_new.png" alt="Chia Plot Manager"></a><br>

  Chia Plot, Drive Manager, Coin Monitor & Auto Drive (V0.98 - October 15th, 2021)
  </h2>
  <p align="center">
Multi Server Chia Plot and Drive Management Solution
  </p>
  
  <hr><br>
  
  
### Basic Installation and Configuration Instructions

Please read the notes below from the config file instructions as most of these are self explanatory:
<br><br>

```
# VERSION = "V0.98 (2021-10-15)"

# Once you have made the necessary modifications to this file, change this to
# True.

configured: False

# Enter the hostname of this server:
hostname: chiaplot01
domain_name: mydomain.com

#Are we plotting for pools (prepends `portable.` to the plot name)
pools: True

# Enter Logging Information
logging: True
log_level: DEBUG

# I use Plotman to do my plotting, but this should work for anything. This
# has NOTHING to do with setting up your plotting configuration and is
# only used for monitoring drive space for notifications. Set to True if
# locally plotting and configure the rest of the settings.
local_plotter:
  active: True

  # Make sure to use the actual mountpoint not the device.
  temp_dirs:
    dirs:
      - /mnt/nvme/drive0
      - /mnt/nvme/drive1
      - /mnt/nvme/drive2
      - /mnt/nvme/drive3
    # What critical usage % should we send an error? Do not make this too low
    # or you will get nuisance reports.
    critical: 95
    critical_alert_sent: False

  # This is the `-d` directory that you are using for your plots. Currently
  # we only support a single drive here for monitoring. MUST have the
  # trailing '/'.
  dst_dirs:
    dirs:
      - /mnt/ssdraid/array0/

    # At what % utilization do we send an error?
    critical: 95
    critical_alert_sent: True

# If you are running multiple remote harvesters,
# and enter their hostnames below.These hostnames
# should be configured for passwordless ssh and should be configured
# such that when you ping the hostname, it goes across the fastest
# interface you have between these harvesters. Set to True if you
# have multiple harvesters and want to automate sending plots to
# the Harvester with the least number of plots.  If you are only
# running a single harvester, just list its hostname here.
remote_harvesters:
  - chianas01
  - chianas02
  - chianas03


# If you run multiple harvesters, each of those harvesters can be configured to
# either replace non-pool plots or not. If they are configured to replace non-pool
# plots, you can also configure them to fill empty drives first (which one would think
# would be the best course of actions in most cases). Each harvester will report back
# to the plotter how many old plots it has to replace as well as home many 'free' plot
# spaces it has to fill. Here is where you tell the plotter which of those to prioritize
# in the event there are both. IN MOST CASES this will be fill if you want to maximize
# the total NUMBER of plots on your harvesters. If you choose 'fill' here, then the
# plotter looks to see which harvester has the most number of EMPTY spaces to fill and
# selects that harvester to send the next plot to, however if you select 'replace' here,
# then the plotter looks at the overall space available that each harvester reports and
# utilizes that to determine where to send the plot. In most cases this will be old_plots +
# free_space = total_plots_space_available.
# fill = fill all empty space first
# replace = replace all old plots first, then fill
remote_harvester_priority: fill

# Enter the name (as shown by ifconfig) of the interface that you SEND plots on
# to your plotters. This is used to check for network traffic to prevent multiple
# plots from being transferred at the same time.
network_interface: eth0

# This is a number that represents at what percentage overall utilization of the above
# interface we will assume that a plot transfer is taking place. You should really TEST
# this to make sure it works for your needs. If you have a dedicated interface to move
# plots, then it can be set very low (1 to 2), however if you have a shared interface,
# you should test while a plot transfer is running and set it to what number makes sense.
# To test simply run the following command and look at the very last number:
# /usr/bin/sar -n DEV 1 50 | egrep eth0
network_interface_threshold: 2


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
    per_plot: True
    warnings: True
  # What email addresses will get the emails?
  emails:
    - someone@gmail.com
    - someoneelse@gmail.com
  # What phones numbers will received the SMS text messages? Include '+1'
  phones:
    - '+18584140000'

  # These are your notification account settings. For email, you must configure
  # your locate MTA. Installer installs Postfix by default. Twilio (SMS) requires
  # a paid account, PushBullet is free.
  accounts:
    twilio:
      from: '+18582640000'
      account: your_account_id
      token: your_account_token
    pushBullet:
      api: your_pushbullet_api_token
```
