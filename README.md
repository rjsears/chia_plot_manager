 <h2 align="center">
 <br>
  Chia Plot and Drive Manager (V0.1 - March 19th, 2021)
  </h2>
  <p align="center">
   Multi Server Chia Plot and Drive Management Solution
  </p>
<h4 align="center">Be sure to :star: my repo so you can keep up to date on any updates and progress!</h4>
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
    <a href="https://github.com/rjsears/chia_plot_manager/tree/master/chia_plot_manager">
      Code
    </a>
   <span> | </span>
    <a href="https://github.com/rjsears/chia_plot_manager/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc">
      Todo List
    </a>
  </h4>

<hr>

### <a name="overview"></a>Overview & Theory of Operation
<div align="left">
This project was designed around my desire to "farm" the Chia crypto currency. In my particular configuration I have a singe plotting server (chisplot01) creating Chia plots. Once the plotting server has completed a plot, this plot then needs to be moved to a storage server (chisnas01) where it resides while being "farmed". The process of creating the plot is pretty straight forward, but the process of managing that plot once compelte was a little more interesting. My plotting server has the capacity to plot 40 parallel plots at a time and that is where I started to have issues.<br><br>

One of those issues that I faced was the relative slow speed at which plots could be moved from the plotting server to the storage server. The long and short of it was simple - I could not continue to plot 40 at a time as I could not move them off the plotting server fast enough not to run out of insanely expensive NVMe drive space. Even with 10Gbe connections directly between the two devices, using ```mv``` or ```cp``` on an NFS mount was pretty slow, others suggested ```rsync``` which was also pretty slow due to encryption. The same held true for ```scp```. I even went so far as scrapping the ssh that came with Ubunti 20.04 and compiling and installing High Performance SSH from the Pittsburgh Supercomputing Center. While it was faster it did not come close to maxing out my dedicated 10Gbe link. What I did know is that the problem was not the network. Each machine was connected to a dedicated 10Gbe port on a Cisco Nexus 9000 on a dedicated data VLAN specifically for moving those plots. Iperf was able to saturate the 10Gbe link with zero problems. <br>

Next I wanted to make sure the problem was not related to the media I was copying the data to across the wire. I installed a pair of Intel P3700 PCIe NVMe drives in a strip RAID configuration and did a bunch of tests to and from that mountpoint locally and across the wire. As suspected, locally the drives performed like magic, across the wire, they performed at exactly the same speed as my spinners. Clearly the drive medium was also not the problem. It had to be the network. <br>

I spent a <em>lot</em> of time playing around with all of the network settings, changing kernel parameters, turning on and off jumbo frames and adjusting irqbalancing. In the end some of the changes gave me marginal changes but nothing really helped <em>a lot</em>. It was then that I stated looking at the mechanism I was using to move the files again. In researching I ran across a couple of people with the same situation, network spped on heavily loaded systems and lightly loaded network where traditional methods of moving files around did not work for them. So they used Netcat instead. <br>

After reading up on the pros and cons of netcat vs rsync (which most recommended) I decided to give it a test. I tested cp, mv, rsync, scp and HPSSH across NFS, SMB (miserable) and SSH. With the exception of SMB they all pretty much worked the same. I was getting better performance than I had been using the stock Ubuntu ssh after replacing it with the High Perfomance SSH and nuking encryption, but still nothing to write home about. Then I tested Netcat. I was blown away. I went from much less than 1Gbe to peaks of 5Gbe with netcat. 100G files that had been taking 18 minutes to transfer were now transferring in 3 to 4 minutes. <br>

As far as plots go, most folks recommend not using some type of RAID array to protect your plots from loss. the thought process is that if you lose a single plotting drive, no big deal, tos itin the trash and put a replacement drive in and fill it back up with plots. Since I really like FreeNAS, I had just planned on dropping in a new FreeNAS server, throwing a bunch of nine drive RAIDZ2 vdevs in place and move forward. But as many pointed out, that was a LOT of wasted space for data pretty easily replaced. And space is the name of the game with Chia. So with that thought in mind, I decided to build out a jbod as usggested by many others. The question was how to manage getting the plots onto the drives and what to do when the drives filled up.<br>

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

<b>On the NAS side (every 1 minute):</b>
<ul>
  <li>Checks for all available plot storage drives on the system in real time (in case new ones were added)</li>
  <li>Based on number of plots on drives, selects the next available plot drive to receive plots</li>
  <li>Updates the receive script with the currently selected plot drive</li>
  <li>Once that drive is full, selects the next available plot drive and updates the receive script </li>
  <li>Complete, selectable notifications via EMail, SMS and Pushbullet about the drive change, includes some SMART drive information</li>
  <li>Sends a daily email report including # of drives, # of plots currently and # of plots total based on current drive storage</li>
  <li>Since notifications are already built in, will extend it to alert on drive temps and smartctl warnings</li>
  <li>Eventually integrate information into Influx with a Grafana dashboard (including power monitoring via UPS)</li>
</ul>
</p>

<hr>

### <a name="dependencies"></a>Dependencies

This was designed and is running on Ubuntu 20.04 for both the Plotter and the NAS so pretty much any linux flavor should work. Listed below are the things that I am using on both systems. The one thing to watch out for on the NAS is the version of pySMART you are using. I ran into a bug with the version (1.0) on PyPi and ended up using the version from the TrueNAS Folks. DO NOT use the version from PyPi, it won't work until patched.<br>

I am running on Python 3.8.5 and pretty much everything else came installed with the default Ubuntu Server 20.04 installation. 

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

You will see this in the logs:
```2021-03-19 18:50:01,830 - plot_manager:155 - process_control: DEBUG Checkfile Exists, We are currently Running a Transfer, Exiting```

As I grow, I plan on adding in a second dedicated 10Gbe link for moving plots and I can expand this out to include the ability to track sessions across each link.

```remote_checkfile``` is used on the NAS system to prevent our drive_manager.py script from altering the destination drive in the middle of a plot move. On the NAS, I run everything as the ```root``` user hence the directory path. Alter to meet your needs.










</p>
