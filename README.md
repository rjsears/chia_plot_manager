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
<p><font size="3">
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

#### <a name="overview"></a>Overview & Theory of Operation
This project was designed around my desire to "farm" the Chia crypto currency. In my particular configuration I have a singe plotting server (chisplot01) creating Chia plots. Once the plotting server has completed a plot, this plot then needs to be moved to a storage server (chisnas01) where it resides while being "farmed". The process of creating the plot is pretty straight forward, but the process of managing that plot once compelte was a little more interesting.
