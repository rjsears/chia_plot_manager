 <h2 align="center">
 <br>
  Chia Plot, Drive Manager & Coin Monitor (V0.3 - April 6th, 2021)
  </h2>
  <p align="center">
   Multi Server Chia Plot and Drive Management Solution
  </p>
<h4 align="center">Be sure to  :star:  my repo so you can keep up to date on any updates and progress!</h4>
<br>
<div align="center">
    <a href="https://github.com/rjsears/chia_plot_manager/commits/master"><img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/rjsears/chia_plot_manager?style=plastic"></a>
    <a href="https://github.com/rjsears/chia_plot_manager/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/rjsears/chia_plot_manager?style=plastic"></a>
    <a href="https://github.com/rjsears/chia_plot_manager/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/rjsears/chia_plot_manager?style=plastic"></a>
</h4>
</div>
<br>
<p align="left"><font size="3">
Hopefully if you are reading this you know what Chia is and what a plot is. I am pretty new to Chia myself but I determined that I needed to come up with a way to manage my plots and hard drives that hold thse plots somewhat automatically since my job as a pilot keeps me gone a lot. I <em>am not</em> a programmer, so please, use this code with caution, test it yourself and provide feedback. This is a working version that is currently running and working for my setup which I will explain below. Hopefully it will be of some help to others, it is the least I can do to give back to the Chia community.
  

Hopefully, this might provide some inspiration for others in regard to their automation projects. Contributions are always welcome.</p>

<div align="center"><a name="top_menu"></a>
  <h4>
    <a href="https://github.com/rjsears/chia_plot_manager#overview">
      Overview
    </a>
    <span> | </span>
    <a href="https://github.com/rjsears/chia_plot_manager#dependencies">
      Dependencies
    </a>
    <span> | </span>
    <a href="https://github.com/rjsears/chia_plot_manager#install">
      Installation & Configuration
    </a>
   <span> | </span>
    <a href="https://github.com/rjsears/chia_plot_manager#cli">
      Command Line Options
    </a>
   <span> | </span>
    <a href="https://github.com/rjsears/chia_plot_manager#cli">
      Command Line Options
    </a>
   <span> | </span>
    <a href="https://github.com/rjsears/chia_plot_manager#hardware">
      Hardware
    </a>
   <span> | </span>
    <a href="https://github.com/rjsears/chia_plot_manager/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc">
      Todo List
    </a>
  </h4>

<hr>

### <a name="overview"></a>Overview & Theory of Operation
<div align="left">
This project was designed around my desire to "farm" the Chia crypto currency. In my particular configuration I have a singe plotting server (chisplot01) creating Chia plots. Once the plotting server has completed a plot, this plot then needs to be moved to a storage server (chisnas01) where it resides while being "farmed". The process of creating the plot is pretty straight forward, but the process of managing that plot once completed was a little more interesting. My plotting server has the capacity to plot 40 parallel plots at a time and that is where I started to have issues.<br><br>

One of those issues that I faced was the relative slow speed at which plots could be moved from the plotting server to the storage server. The long and short of it was simple - I could not continue to plot 40 at a time as I could not move them off the plotting server fast enough not to run out of insanely expensive NVMe drive space. Even with 10Gbe connections directly between the two devices, using ```mv``` or ```cp``` on an NFS mount was pretty slow, others suggested ```rsync``` which was also pretty slow due to encryption. The same held true for ```scp```. I even went so far as scrapping the ssh that came with Ubunti 20.04 and compiling and installing High Performance SSH from the Pittsburgh Supercomputing Center. While it was faster it did not come close to maxing out my dedicated 10Gbe link. What I did know is that the problem was not the network. Each machine was connected to a dedicated 10Gbe port on a Cisco Nexus 9000 on a dedicated data VLAN specifically for moving those plots. Iperf was able to saturate the 10Gbe link with zero problems. <br>

Next I wanted to make sure the problem was not related to the media I was copying the data to across the wire. I installed a pair of Intel P3700 PCIe NVMe drives in a strip RAID configuration and did a bunch of tests to and from that mountpoint locally and across the wire. As suspected, locally the drives performed like magic, across the wire, they performed at exactly the same speed as my spinners. Clearly the drive medium was also not the problem. It had to be the network. <br>

I spent a <em>lot</em> of time playing around with all of the network settings, changing kernel parameters, turning on and off jumbo frames and adjusting irqbalancing. In the end some of the changes gave me marginal increases in performance but nothing really helped <em>a lot</em>. It was then that I stated looking at the mechanism I was using to move the files again. In researching I ran across a couple of people with the same situation, network speed on heavily loaded systems and lightly loaded networks where traditional methods of moving files around did not work for them. So they used Netcat instead. <br>

After reading up on the pros and cons of netcat vs rsync (which most recommended) I decided to give it a test. I tested cp, mv, rsync, scp and HPSSH across NFS, SMB (miserable) and SSH. With the exception of SMB they all pretty much worked the same. I was getting better performance than I had been using the stock Ubuntu ssh after replacing it with the High Perfomance SSH and nuking encryption, but still nothing to write home about. Then I tested Netcat. I was blown away. I went from much less than 1Gbe to peaks of 5Gbe with netcat. 100G files that had been taking 18 minutes to transfer were now transferring in 3 to 4 minutes. <br>

As far as plots go, most folks recommend not using some type of RAID array to protect your plots from loss. the thought process is that if you lose a single plotting drive, no big deal, toss it in the trash and put a replacement drive in and fill it back up with plots. Since I really like FreeNAS, I had just planned on dropping in a new FreeNAS server, throwing a bunch of nine drive RAIDZ2 vdevs in place and move forward. But as many pointed out, that was a LOT of wasted space for data pretty easily replaced. And space is the name of the game with Chia. So with that thought in mind, I decided to build out a jbod as suggested by many others. The question was how to manage getting the plots onto the drives and what to do when the drives filled up.<br>

Welcome to my project! I ended up with basically a client/server arrangement. The software on the plotting server would watch for completed plots and then send those plots (using netcat) to the NAS server. The software on the NAS server would automatically monitor all available drives in the system and place the plot where it needed to go, pretty much all on its own. As I said earlier, my job as a pilot keeps me in the air a lot and I really needed a hands off approach to make this work. 

<b>On the Plotter side (every 5 minutes):</b>
<ul>
  <li>Monitors my -d directory for completed plots</li>
  <li>Determines if the plot is complete based on the size and name of the plot (currently k32 only)</li>
  <li>Checks to see if we are already sending a plot to the NAS, if so, stops</li>
  <li>When it is clear to send, picks which plot to send and netcats it to the NAS</li>
  <li>Utilizing an ssh subprocess, starts a receiving netcat on the NAS</li>
  <li>After the transfer is complete, checks the exact file size of the plot on both systems as a basic verification</li>
  <li>Once files sizes are verified, deletes the sent plot</li>
  <li>Kills any lingering netcat connections on the NAS</li>
</ul>
<br>
<b>On the NAS side (every 1 minute):</b>
<ul>
  <li>Checks for all available plot storage drives on the system in real time (in case new ones were added)</li>
  <li>Based on number of plots on drives, selects the next available plot drive to receive plots</li>
  <li>Updates the receive script with the currently selected plot drive</li>
  <li>Once that drive is full, selects the next available plot drive and updates the receive script </li>
  <li>Complete, selectable notifications via EMail, SMS and Pushbullet about the drive change, includes some SMART drive information</li>
  <li>Sends a daily email report including # of drives, # of plots currently and # of plots total based on current drive storage</li>
  <li>Daily email also includes plot speed, total plots in last 24 hours and TiB plotting in last 24 hours</li>
  <li>Since notifications are already built in, will extend it to alert on drive temps and smartctl warnings</li>
  <li>Eventually integrate information into Influx with a Grafana dashboard (including power monitoring via UPS)</li>
</ul>
<br>
<b>Command Line Options on the NAS</b>
<ul>
 <li>Ability to run quick reports to the screen (basically daily email dumped to the screen</li>
 <li>Ability to send a Drive update email</li>
 <li>Ability to monitor drive temperatures by device and serial number</li>
 </ul>
</p>

<hr>

### <a name="dependencies"></a>Dependencies

This was designed and is running on Ubuntu 20.04 for both the Plotter and the NAS so pretty much any linux flavor should work. Listed below are the things that I am using on both systems. The one thing to watch out for on the NAS is the version of pySMART you are using. I ran into a bug with the version (1.0) on PyPi and ended up using the version from the TrueNAS Folks. DO NOT use the version from PyPi, it won't work until patched.<br>

I am running on Python 3.8.5 and pretty much everything else came installed with the default Ubuntu Server 20.04 installation. Be sure to install smartmontools ```apt install smartmontools``` as well as the following:

<ul>
  <li><a href="https://docs.sentry.io/platforms/python/">Sentry-SDK</a> - (Optional, I use it for error tracking)</li>
 <li><a href="https://pypi.org/project/pushbullet.py/0.12.0/">Pushbullet (0.12.0)</a> - (Optional, used for PB notifications)</li>
 <li><a href="https://pypi.org/project/twilio/">Twilio (6.54.0)</a> - (Optional, used for SMS notifications)</li>
  <li><a href="https://pypi.org/project/Jinja2/">JinJa2 (2.11.3)</a> - (Optional, Used for Email notifications)</li>
  <li><a href="https://pypi.org/project/configparser/">ConfigParser (5.0.2)</a> - Used for reading and updating config files</li>
  <li><a href="https://github.com/truenas/py-SMART">py-SMART (0.3)</a> - Used for reading drive information</li>
 </ul>
 <hr>

### <a name="install"></a>Installation & Configuration

The installation of the actual scripts are pretty easy. Just clone the repo and drop it on your server. A <em>lot</em> of what happens is very specific to how I have my systems set up so I will explain my layout in detail along with where in the code you may need to look to make changes to fit your needs. The plotter is pretty easy. 

#### Plotter Configuration

Here is the directry structure I use on my plotter for my main plotting and -d drives:

```
/mnt
├── nvme
│   ├── drive0
│   ├── drive1
│   ├── drive2
│   └── drive3
└── ssdraid
    └── array0
```
The ```/mnt/nvme/driveX``` drives are used as my temp drives for plotting. These are Intel DC P4510 NVMe drives capable of running 10 plots each (based on k32 plot size). The ```/mnt/ssdraid/array0``` is my ```-d``` drive. This is a RAID0 array of HGST 1.6TB Enterprise SSD drives. This is where the completed plots are stored before they are moved by the plot_manager.py script.

All of my plotting is done as the ```chia``` user and so all of my plot_manager files are stored in the ```/home/chia``` directory. I do have a little bit of testing built into the script and that is what the test_plots directory is used for. I simple ```dd``` 10G of zeros into a test plot file and turn on testing in the script to test everything before going live.

```
/home/chia/plot_manager
├── logs
└── test_plots
```

Depending on how your system is set up, you need to make changes at the top of the ```plot_manager.py``` script:

```
# Are we testing?
testing = False
if testing:
    plot_dir = '/home/chia/plot_manager/test_plots/'
    plot_size = 10000000
else:
    plot_dir = "/mnt/ssdraid/array0/"
    plot_size = 108644374730  # Based on K32 plot size
```

Change the ```plot_dir``` and ```plot_size``` for both testing and not testing to suit your system and needs. 

Next you will need to update these status and checkfile locations to meet your needs:

```
status_file = '/home/chia/plot_manager/transfer_job_running'
remote_checkfile = '/root/plot_manager/remote_transfer_is_active'
```

```status_file``` is a local file that is created when we start a plot move and deleted once we have completed that move. We check for that when we first run to make sure we are not attempting to move several plots at the same time. 

You will see this in the logs:<br>
```2021-03-19 18:50:01,830 - plot_manager:155 - process_control: DEBUG Checkfile Exists, We are currently Running a Transfer, Exiting```
<br>
As I grow, I plan on adding in a second dedicated 10Gbe link for moving plots and I can expand this out to include the ability to track sessions across each link.
<br><br>
```remote_checkfile``` is used on the NAS system to prevent our NAS drive_manager.py script from altering the destination drive in the middle of a plot move. On the NAS, I run everything as the ```root``` user hence the directory path. Alter to meet your needs.

That is pretty much everything on the plotter side. The final part of the puzzle is the ```send_plot.sh``` shell script. On line 99 of the ```plot_manager.py``` script you will find this line:<br>
```subprocess.call(['/home/chia/plot_manager/send_plot.sh', plot_path, plot_to_process])```
You need to alter the directory and name of the script to suite you needs. This is the script that is called that actually send the plot to the nas. This is the contents:

```
#!/bin/bash
#
ssh root@chianas01-internal "nohup /root/plot_manager/receive_plot.sh $2 > foo.out 2> foo.err < /dev/null &"
sudo /usr/bin/pv "$1" | sudo /usr/bin/nc -q 5 chianas01-internal 4040
```

Depending on how you have your NAS setup, we may have to change a few more lines of code. I will come back to that after we talk about the NAS.
<hr>

#### NAS Configuration

The NAS setup is pretty unique to me but it should be pretty easy to reconfigure the script to meet other needs. <br>
Coming from running three very large Plex systems (PBs worth), I designed my drive layout and naming so that I could at any moment just by looking at a mountpoint go pull a drive if I needed to do so. 

My basic layout is a single SuperMicro storage server with motherboard, 256GB ram and 36 drive bays. This I call ```enclosure0```. This is a Supermicro 847, it has 24 drive bays in front and 12 in the rear. This is my directory structure for that system:

```
/mnt/enclosure0
├── front
│   ├── column0
│   │   ├── drive0
│   │   ├── drive1
│   │   ├── drive2
│   │   ├── drive3
│   │   ├── drive4
│   │   └── drive5
│   ├── column1
│   │   ├── drive6
│   │   ├── drive7
│   │   ├── drive8
│   │   ├── drive9
│   │   ├── drive10
│   │   └── drive11
│   ├── column2
│   │   ├── drive12
│   │   ├── drive13
│   │   ├── drive14
│   │   ├── drive15
│   │   ├── drive16
│   │   └── drive17
│   └── column3
│       ├── drive18
│       ├── drive19
│       ├── drive20
│       ├── drive21
│       ├── drive22
│       └── drive23
└── rear
    ├── column0
    │   ├── drive24
    │   ├── drive25
    │   └── drive26
    ├── column1
    │   ├── drive27
    │   ├── drive28
    │   └── drive29
    ├── column2
    │   ├── drive30
    │   ├── drive31
    │   └── drive32
    └── column3
        ├── drive33
        ├── drive34
        └── drive35
```       

As you can see just by looking at a mount point I can tell exactly where a drive is located in my system. In addition to that, when I add additional external drive arrays, I just do the same thing with ```enclosure1```, ```enclosure2```, etc and my ```drive_manager.py``` script will work no problem. I plug in a new drive, format it ```XFS```, mount it, add it to ```fstab``` and that's it. The script does everything else.


I am basically using ``psutil`` to get drive space information and then use that to determine where to put plots. When I call ```psutil``` I just tell it I want it to look at any device that starts with ```/dev/sd``` and any mountpoint that includes ```enclosure``` and ends with the word ```drive```:

```
if p.device.startswith('/dev/sd') and p.mountpoint.startswith('/mnt/enclosure') and p.mountpoint.endswith(drive):
```

In this manner I will never get swap, temp, boot, home, etc. Nothing at all but my plot storage drives. In order for this to work with your setup, you would have to modify all of these lines to match your paticular configuration. 

Once you have that figured out, there are just a couple of other little things that need to be set:

At the top of the script you want to set these to meet your needs:

```
nas_server = 'chianas01'
plot_size_k = 108995911228
plot_size_g = 101.3623551
receive_script = '/root/plot_manager/receive_plot.sh'
```

The ```receive_plot.sh``` script is created dynamically by the script here:

```
f = open(receive_script, 'w+')
f.write('#! /bin/bash \n')
f.write(f'nc -l -q5 -p 4040 > "{get_plot_drive_to_use()}/$1" < /dev/null')
f.close()
```

Once the system determines which drive it wants to use to store plots, it stores that information in a configuration file called ```plot_manager_config``` and it looks like this:
```
[plotting_drives]
current_plotting_drive = /mnt/enclosure0/front/column3/drive18
```
This is important for several reasons. First this is what tells the system our current plotting drive and it is also used by the plotting server to map the correct path for file size verification after a plot is sent. If you change this file or it's location, you need to update lines 167 on the plotter. Notice that I am specifically grepping for the word ```enclosure```, you want to make sure all of this matches up with how you plan on doing things!

```
remote_mount = str(subprocess.check_output(['ssh', nas_server, 'grep enclosure /root/plot_manager/plot_manager_config | awk {\'print $3\'}']).decode(('utf-8'))).strip("\n")
```

OK, once you have everything setup, on the plotter you simply run the script and if everything is setup correctly you should see the following:

```
2021-03-19 19:20:01,543 - plot_manager:92 - process_plot: DEBUG process_plot() Started
2021-03-19 19:20:01,543 - plot_manager:126 - process_control: DEBUG process_control() called with [check_status] and [0]
2021-03-19 19:20:01,543 - plot_manager:158 - process_control: DEBUG Checkfile Does Not Exist
2021-03-19 19:20:01,543 - plot_manager:74 - get_list_of_plots: DEBUG get_list_of_plots() Started
2021-03-19 19:20:01,544 - plot_manager:77 - get_list_of_plots: DEBUG plot-k32-2021-03-18-02-33-xxx.plot
2021-03-19 19:20:01,544 - plot_manager:82 - get_list_of_plots: INFO We will process this plot next: plot-k32-2021-03-18-02-33-xxx.plot
2021-03-19 19:20:01,545 - plot_manager:126 - process_control: DEBUG process_control() called with [set_status] and [start]
2021-03-19 19:20:02,228 - plot_manager:98 - process_plot: INFO Processing Plot: /mnt/ssdraid/array0/plot-k32-2021-03-18-02-33-xxx.plot
2021-03-19 19:25:00,697 - plot_manager:165 - verify_plot_move: DEBUG verify_plot_move() Started
2021-03-19 19:25:01,433 - plot_manager:171 - verify_plot_move: DEBUG Verifing: chianas01-internal: /mnt/enclosure0/front/column3/drive18/plot-k32-2021-03-18-02-33-xxx.plot
2021-03-19 19:25:02,102 - plot_manager:176 - verify_plot_move: DEBUG Remote Plot Size Reported as: 108898704182
2021-03-19 19:25:02,103 - plot_manager:178 - verify_plot_move: DEBUG Local Plot Size Reported as: 108898704182
2021-03-19 19:25:02,103 - plot_manager:101 - process_plot: INFO Plot Sizes Match, we have a good plot move!
2021-03-19 19:25:02,103 - plot_manager:126 - process_control: DEBUG process_control() called with [set_status] and [stop]
2021-03-19 19:25:03,465 - plot_manager:147 - process_control: DEBUG Remote nc kill called!
2021-03-19 19:25:06,741 - plot_manager:109 - process_plot: INFO Removing: /mnt/ssdraid/array0/plot-k32-2021-03-18-02-33-xxx.plot
```

This tells you that everything has gone smoothly. You should be able to log into your NAS and verify that the plot is where it is supposed to be. Needless to say I would stick with a bunch of test plots until I had it right, I would also comment out this line:

```
os.remove(plot_path)
```

Until you are absolutely certain it is running the way that you would like it to run!

Now on the NAS server, I run my script once per minute. This is what you should see if everything is going well:

```
drive_manager:258 - update_receive_plot: DEBUG update_receive_plot() Started
drive_manager:266 - update_receive_plot: DEBUG Currently Configured Plot Drive: /mnt/enclosure0/front/column3/drive18
drive_manager:267 - update_receive_plot: DEBUG System Selected Plot Drive:      /mnt/enclosure0/front/column3/drive18
drive_manager:268 - update_receive_plot: DEBUG Configured and Selected Drives Match!
drive_manager:269 - update_receive_plot: DEBUG No changes necessary to /root/plot_manager/receive_plot.sh
drive_manager:270 - update_receive_plot: DEBUG Plots left available on configured plotting drive: 58
```
<br><br>

When the plot drives does change, you get a nicely formatted email:
```
Server: chiaplot01
New Plot Drive Selected at 23:34:01
Previous Plotting Drive.............................../mnt/enclosure0/front/column3/drive17
# of Plots on Previous Plotting Drive.................109
New Plotting Drive (by mountpoint)..................../mnt/enclosure0/front/column3/drive18
New Plotting Drive (by device)......................../dev/sdx1
Drive Size............................................10.9T
# of Plots on we can put on this Drive................109

Environmental & Health
Drive Serial Number...................................00000000
Current Drive Temperature.............................23°C
Last Smart Test Health Assessment.....................PASS

Other Information
Total Plots on chiaplot01.............................1853
Current Total Number of Plot Drives...................24
Number of k32 Plots until full........................787
Max # of Plots with current # of Drives...............2640
```

and a text or pushbullet message:
```Plot Drive Updated: Was: /mnt/enclosure0/front/column3/drive17,  Now: /mnt/enclosure0/front/column3/drive18```


And if you choose, once a day you can get a daily update email:

```
NAS Server: chianas01
Daily Update Email - Generated at 11:23:53
Current Plotting Drive (by mountpoint).................../mnt/enclosure0/front/column2/drive13
Current Plotting Drive (by device)......................./dev/sdo1
Drive Size...............................................10.9T

Environmental & Health
Drive Serial Number......................................00000000
Current Drive Temperature................................29°C
Last Smart Test Health Assessment........................PASS

Other Information
Total Plots on chianas01.................................1455
Current Total Number of Plot Drives......................24
Number of k32 Plots until full...........................1161
Max # of Plots with current # of Drives..................2640

Plotting Speed
Total Plots Last 24 Hours................................57
Average Plots Per Hour...................................2.375
Average Plotting Speed Last 24 Hours.....................5.757 TiB/Day
```

### <a name="cli"></a>Command Line Options

Staring with V0.3 (April 4th, 2021) I have started to add in command line options to make getting plot and other information easier and to generate reports on the fly. Currently the command line options that are availare are:

<ul>
 <li><em>-h</em> or <em>--help</em></li>
  <li><em>-v</em> or <em>--version</em></li>
  <li><em>-ct</em> or <em>--check_temps</em></li>
  <li><em>-pr</em> or <em>--plot_report</em></li>
  <li><em>-ud</em> or <em>--update_daily</em></li>
</ul>

<b> -h --help</b>  and  <b>-v --version</b><br>
These options print out the help message or version information and exits.

```
******** ChiaNAS Drive Manager - 0.3 (2021-04-04) ********
Running drive_manager.py with no arguments causes drive_manager to run in 'normal' mode.
In this mode drive_manager will check the drive utilization and update which drive your
Chia plots will be sent to when they arrive from your plotter. This is generally called
from a cronjob on a regular basis. Please read the full information about how it works
on my github page.

There are several commandline switches you can use to get immediate reports and feedback:

-dr or --drive_report       Runs the Daily ChiaNAS Report (if configured), and emails
                            it to you. This can be called from a crontab job as well.

-ct or --check_temps        This will query all of your hard drives using smartctl and
                            return a list of drive temperatures to you.

-pr or --plot_report        This queries the NAS and returns a report letting you know
                            how many plots are currently on the system and how many more
                            you can add based on the current drive configuration. It also
                            includes plotting speed information for the last 24 hours.

-ud or --update_daily       This updates the total number of plots the system has created
                            over the past 24 hours. Use with CAUTION!. This should be ran
                            from crontab once every 24 hours only! It updates the total
                            from the last time is was run until now, hence why you should
                            only run this once per 24 hours.

USAGE:

optional arguments:
  -h, --help           show this help message and exit
  -v, --version        show program's version number and exit
  -dr, --daily_report  Run the ChiaPlot Daily Email Report and exit
  -ct, --check_temps   Return a list of drives and their temperatures and exit
  -pr, --plot_report   Return the total # of plots on the system and total you can add and exit
  -ud, --update_daily  Updates 24 hour plot count. USE WITH CAUTION, USE WITH CRONTAB
  ```
<br><br>
<b> -dr    --drive_report</b><br>
This option outputs the HTML versionof the Daily Drive Report email to the screen and also emails.
This only works if configured. If this notification is set to off, this will do nothing.<br>

<br>
<b> -ct    --check_temps</b><br>
This options prints the serial number, device name, drive number and temperature of all devices
desiginated as plot drives.

```
#################################################################
################# chianas01 Temperature Report ##################
#################################################################
#    Serial#     #     Device     #     Drive     #    Temp     #
#################################################################
#   00000000     #   /dev/sdb1    #    drive0    #     29°C     #
#   00000000     #   /dev/sdc1    #    drive1    #     30°C     #
#   00000000     #   /dev/sdd1    #    drive2    #     29°C     #
#   00000000     #   /dev/sde1    #    drive3    #     29°C     #
#   00000000     #   /dev/sdf1    #    drive4    #     28°C     #
#   00000000     #   /dev/sdg1    #    drive5    #     25°C     #
#   00000000     #   /dev/sdh1    #    drive6    #     29°C     #
#   00000000     #   /dev/sdi1    #    drive7    #     31°C     #
#   00000000     #   /dev/sdj1    #    drive8    #     30°C     #
#   00000000     #   /dev/sdk1    #    drive9    #     29°C     #
#   00000000     #   /dev/sdl1    #    drive10    #     28°C     #
#   00000000     #   /dev/sdm1    #    drive11    #     25°C     #
#   00000000     #   /dev/sdn1    #    drive12    #     29°C     #
#   00000000     #   /dev/sdo1    #    drive13    #     30°C     #
#   00000000     #   /dev/sdp1    #    drive14    #     28°C     #
#   00000000     #   /dev/sdq1    #    drive15    #     27°C     #
#   00000000     #   /dev/sdr1    #    drive16    #     25°C     #
#   00000000     #   /dev/sds1    #    drive17    #     23°C     #
#   00000000     #   /dev/sdt1    #    drive18    #     26°C     #
#   00000000     #   /dev/sdu1    #    drive19    #     27°C     #
#   00000000     #   /dev/sdv1    #    drive20    #     27°C     #
#   00000000     #   /dev/sdw1    #    drive21    #     26°C     #
#   00000000     #   /dev/sdx1    #    drive22    #     25°C     #
#   00000000     #   /dev/sdy1    #    drive23    #     23°C     #
##################################################################
```

<br><br>
<b> -pr    --plot_report</b><br>
This options prints out a quick version of the daily plot report to the screen
and exits.

```
############################################################
################### chianas01 Plot Report ##################
############################################################
Total Plots on chianas01:                               1456
Total Number of Systemwide Plots Drives:                  24
Total Number of k32 Plots until full:                   1160
Maximum # of plots when full:                           2640
Plots completed in the last 24 Hours:                     57
Average Plots per Hours:                               2.375
Average Plotting Speed Last 24 Hours (TiB/Day):        5.757 
Current Plot Storage Drive:                        /dev/sdo1
Temperature of Current Plot Drive:                      30°C
Latest Smart Drive Assessment of Plot Drive:            PASS
############################################################
```

<br><br>
<b>-ud --update_daily</b><br>
This option is really designed to be called from your crontab riught before you run your daily email:

```
01 00 * * * /usr/bin/python3 /root/plot_manager/drive_manager.py -ud >/dev/null 2>&1
02 00 * * * /usr/bin/python3 /root/plot_manager/drive_manager.py -dr >/dev/null 2>&1
```

It is designed to calculate the information necessary for the daily plot report. You can run it anytime
you want but it will reset this information to the point in time you called it as oppoed to giving you
a 24 hour view of your system.
<br>

### <a name="coins"></a>Coin Monitor

I wanted a simple way to keep track of when I won coins and how many I had so I added `coin_monitor.py` to the mix.
As I said, in my configuration I have three servers, my `plotter`, my `nas` and my `farmer`. Coin Monitor sits on my
farmer and watches the log files for new coins. When it sees that there is a new coin, it checks the coin logfile 
(`/root/coin_monitor/logs/new_coins.log`) to make sure we have not already counted those coins. If it is a new coin
it writes that coin information to the logfile (`new_coins.log`) and depending on what notifications you have setup
you can receive a notification via SMS, Email and PushBullet. If you have `per_coin_email` set to True/1 in 
`coin_monitoring_config` you will also receive a nicely formatted email on top of your other notifications.

<img src="https://github.com/rjsears/chia_plot_manager/blob/main/images/chia_new_coin_email.png" alt="You Have Chia" height="250" width="300"></a>
<br><br>

This is stand alone and can be used in combination with or without my plot_manager scripts. 


### <a name="hardware"></a>Hardware I use in my setup
I have had a couple of people ask about the hardware that I use in my setup so I thought I would include it here. 
Almost everything I purchased was used off eBay. There were minor exceptions but 95% was eBay.

*** Plotting Server ***



<h2>In Closing....</h2>
I still have a <em><b>lot</b></em> that I want to do with these scripts. I need to do a lot more error checking and management, additional notification capabilities and types and eventually add a web driven interface via Flask. I am <em><b>not</b></em> a programmer, I do it for fun so I am sure there may be better ways to do some of the stuff I did her, but it works for me, and hopefully may work for someone else as well. 

</p>
