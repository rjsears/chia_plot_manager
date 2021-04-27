#!/bin/bash
# 
ssh root@chianas01-internal "nohup /root/plot_manager/plot_manager/receive_plot.sh $2 > foo.out 2> foo.err < /dev/null &"
sudo /usr/bin/pv "$1" | sudo /usr/bin/nc -q 5 chianas01-internal 4040
exit
