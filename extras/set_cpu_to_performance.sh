#! /bin/bash

# This should be chmod +x and set in your crontab:
# @reboot /root/set_cpu_to_performance.sh

cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
for file in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo "performance" > $file; done
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
