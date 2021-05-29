#!/bin/bash
# 
ssh root@$3 "nohup /root/plot_manager/receive_plot.sh $2 > foo.out 2> foo.err < /dev/null &"
sudo /usr/bin/pv "$1" | sudo /usr/bin/nc -q 5 $3 4040
exit
