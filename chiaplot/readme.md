<h2 align="center">
  <a name="chia_drive_logo" href="https://github.com/rjsears/chia_plot_manager"><img src="https://github.com/rjsears/chia_plot_manager/blob/main/images/chia_plot_manager_new.png" alt="Chia Plot Manager"></a><br>

  Chia Plot, Drive Manager, Coin Monitor & Auto Drive (V0.94 - August 8th, 2021)
  </h2>
  <p align="center">
Multi Server Chia Plot and Drive Management Solution
  </p>
  
  <hr><br>
  
  
### Basic Installation and Configuration Instructions

Please read the notes below from the config file instructions as most of these are self explanatory:
<br><br>

```
# Once you have made the necessary modifications to this file, change this to
# True.
configured: False

# Enter the hostname of this server:
hostname: chiaplot01

# Are we plotting for pools (prepends `portable.` to the plot name)
pools: True

# Enter Logging Information
logging: True
log_level: DEBUG

# I use MadMax to do my plotting, but this should work for anything. This
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
    critical_alert_sent: False

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

# This is our high speed, internal Network interface name that we send plots over
network_interface: eno1


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
