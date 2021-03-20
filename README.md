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
    <a href="https://github.com/rjsears/GardenPi/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc">
      Todo List
    </a>
    <span> | </span>
    <a href="https://github.com/rjsears/GardenPi#icons">
      Icons
    </a>
  </h4>
</div>
<p align="left">
#### <a name="overview"></a>Overview & Theory of Operation
This project was designed around my desire to "farm" the Chia crypto currency. In my particular configuration I have a singe plotting server (chisplot01) creating Chia plots. Once the plotting server has completed a plot, this plot then needs to be moved to a storage server (chisnas01) where it resides while being "farmed". The process of creating the plot is pretty straight forward, but the process of managing that plot once compelte was a little more interesting. My plotting server has the capacity to plot 40 parallel plots at a time and that is where I started to have issues.

One of those issues that I faced was the relative slow speed at which plots could be moved from the plotting server to the storage server. The long and short of it was simple - I could not continue to plot 40 at a time as I could not move them off the plotting server fast enough not to run out of insanely expensive NVMe drive space. Even with 10Gbe connections directly between the two devices, using ```mv``` or ```cp``` on an NFS mount was pretty slow, others suggested ```rsync``` which was also pretty slow due to encryption. The same held true for ```scp```. I even went so far as scrapping the ssh that came with Ubunti 20.04 and compiling and installing High Performance SSH from the Pittsburgh Supercomputing Center. While it was faster it did not come close to maxing out my dedicated 10Gbe link. What I did know is that the problem was not the network. Each machine was connected to a dedicated 10Gbe port on a Cisco Nexus 9000 on a dedicated data VLAN specifically for moving those plots. Iperf was able to saturate the 10Gbe link with zero problems. 

Next I wanted to make sure the problem was not related to the media I was copying the data to across the wire. I installed a pair of Intel P3700 PCIe NVMe drives in a strip RAID configuration and did a bunch of tests to and from that mountpoint locally and across the wire. As suspected, locally the drives performed like magic, across the wire, they performed at exactly the same speed as my spinners. Clearly the drive medium was also not the problem. It had to be the network. 

I spent a <em>lot<em> of time playing around with all of the network settings, changing kernel parameters, turning on and off jumbo frames and adjusting irqbalancing. In the end some of the changes gave me marginal changes but nothing really helped <em>a lot</em>. It was then that I stated looking at the mechanism I was using to move the files again. In researching I ran across a couple of people with the same situation, network spped on heavily loaded systems and lightly loaded network where traditional methods of moving files around did not work for them. So they used Netcat instead. 

After reading up on the pros and cons of netcat vs rsync (which most recommended) I decided to give it a test. I tested cp, mv, rsync, scp and HPSSH across NFS, SMB (miserable) and SSH. With the exception of SMB they all pretty much worked the same. I was getting better performance than I had been using the stock Ubuntu ssh after replacing it with the High Perfomance SSH and nuking encryption, but still nothing to write home about. Then I tested Netcat. I was blown away. I went from much less than 1Gbe to peaks of 5Gbe with netcat. 100G files that had been taking 18 minutes to transfer were now transferring in 3 to 4 minutes. 

The system designed for <em>our</em> needs ended up with the following configuration:
<ul>
  <li>27  x "Water" Zones (Expandable to 32 Zones total)</li>
  <li>8 x "Power" Zones</li>
  <li>6 x "Temperature" Zones (including one for our worm farm)</li>
  <li>3 x "Humidity" Zones</li>
  <li>1 x Barometric Sensor</li>
  <li>DC Current and Voltage Sensors</li>
  <li>AC Current and Voltage Sensors</li>
  <li>4 x Ultrasonic Water Level Detectors</li>
  <li>4 x Non-Contact Liquid Level Sensors</li>
  <li>7" Touchscreen for local control</li>
</ul>
</p>
