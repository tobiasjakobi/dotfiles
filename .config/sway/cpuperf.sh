#!/bin/bash

swaynag --type info --message 'Select CPU performance:' \
        --button-dismiss 'Low (4 cores, no boost)' 'sudo cpufreq_perf.py --set low' \
        --button-dismiss 'Mid (4 cores,	boost)' 'sudo cpufreq_perf.py --set mid' \
        --button-dismiss 'High (8 cores, boost)' 'sudo cpufreq_perf.py --set high'
