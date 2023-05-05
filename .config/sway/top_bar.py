#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from datetime import datetime
from time import sleep

from psutil import cpu_count, disk_partitions, disk_usage

from mysensors import get_sensor, read_sensor, gpu_busy, sensor_descs
from mybattery import read_battery

'''
References:
https://unix.stackexchange.com/questions/473788/simple-swaybar-example

Additional emojis and characters for the status bar:
Electricity: ⚡ ↯ ⭍ 🔌
Audio: 🔈 🔊 🎧 🎶 🎵 🎤
Separators: \| ❘ ❙ ❚
Misc: 🐧 💎 💻 💡 ⭐ 📁 ↑ ↓ ✉ ✅ ❎
'''


##########################################################################################
# Internal functions
##########################################################################################

def _bytes2human(n: int):
    '''
    http://code.activestate.com/recipes/578019
    >>> bytes2human(10000)
    '9.8K'
    >>> bytes2human(100001221)
    '95.4M'
    '''

    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}

    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10

    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return f'{value:.1f}{s}'

    return f'{n}B'


##########################################################################################
# Class definitions
##########################################################################################

class SwayTopBar:
    def __init__(self, descs: dict):
        self._cpu_info = get_sensor(descs['CPU'])
        self._igpu_info = get_sensor(descs['iGPU'])
        self._dgpu_info = get_sensor(descs['dGPU'])

        self._base_interval = 1

        self._igpu_cur_temp = None
        self._dgpu_cur_temp = None

        self._cpu_status_interval = 5
        self._igpu_status_interval = 5
        self._dgpu_status_interval = 5
        self._battery_status_interval = 8

        self._cpu_status_counter = 0
        self._igpu_status_counter = 0
        self._dgpu_status_counter = 0
        self._battery_status_counter = 0

        self._cpu_status = None
        self._gpu_status = None
        self._battery_status = None
        self._disk_space = None

    def _get_cpu_status(self):
        c = cpu_count()

        temp = read_sensor(self._cpu_info)
        if temp is None:
            self._cpu_status = f'CPU: {c} cores online'
        else:
            self._cpu_status = f'CPU: {temp: >8}, {c} cores online'

    def _get_igpu_status(self):
        self._igpu_cur_temp = read_sensor(self._igpu_info)

        '''
        Handle the case that the dGPU is completely disabled.
        '''
        dgpu_temp = self._dgpu_cur_temp
        if dgpu_temp is None:
            dgpu_temp = '---'

        self._gpu_status = f'GPU: i {self._igpu_cur_temp: >8}, d {dgpu_temp: >8}'

    def _get_dgpu_status(self):
        self._dgpu_cur_temp = read_sensor(self._dgpu_info)

        dgpu_temp = self._dgpu_cur_temp
        if dgpu_temp is None:
            dgpu_temp = '---'

        self._gpu_status = f'GPU: i {self._igpu_cur_temp: >8}, d {dgpu_temp: >8}'

    def _update_dgpu_interval(self):
        busy = gpu_busy(self._dgpu_info)
        
        if busy is None or busy <= 10:
            self._dgpu_status_interval = 60
        else:
            self._dgpu_status_interval = 5

    def _get_battery_status(self):
        bat_state = read_battery()
        if bat_state is None:
            bat_state = 'unknown'

        self._battery_status = f'🔌: {bat_state: <17}'

    def _get_disk_space(self):
        rootfs = None
        home = None
        storage = None

        for p in disk_partitions():
            if p.mountpoint == '/':
                rootfs = disk_usage(p.mountpoint)
            elif p.mountpoint == '/home':
                home = disk_usage(p.mountpoint)
            elif p.mountpoint == '/mnt/storage':
                storage = disk_usage(p.mountpoint)

        if rootfs:
            status = f'root[{_bytes2human(rootfs.used)}/{_bytes2human(rootfs.total)}]'

            if home:
                status = f'{status}, home[{_bytes2human(home.used)}/{_bytes2human(home.total)}]'
        else:
            status = 'unknown'

        self._disk_space = f'Disk: {status}'

    def _update(self):
        if self._cpu_status_counter == 0:
            self._get_cpu_status()
            self._cpu_status_counter = self._cpu_status_interval
        else:
            self._cpu_status_counter -= 1

        if self._igpu_status_counter == 0:
            self._get_igpu_status()
            self._igpu_status_counter = self._igpu_status_interval
        else:
            self._igpu_status_counter -= 1

        if self._dgpu_status_counter == 0:
            self._get_dgpu_status()
            self._update_dgpu_interval()
            self._dgpu_status_counter = self._dgpu_status_interval
        else:
            self._dgpu_status_counter -= 1

        if self._battery_status_counter == 0:
            self._get_battery_status()
            self._battery_status_counter = self._battery_status_interval
        else:
            self._battery_status_counter -= 1

        self._get_disk_space()

    def refresh(self) -> int:
        try:
            self._update()

            date = datetime.now().strftime('%a %Y-%m-%d %k:%M:%S')
            output = f'{self._disk_space} | {self._battery_status} | {self._gpu_status} | {self._cpu_status} | {date}'

            print(output, file=sys.stdout, flush=True)

            sleep(self._base_interval)

            return 0

        except Exception as exc:
            print(f'error: top bar refresh failed: {exc}', file=sys.stdout)

            return 1


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    bar = SwayTopBar(sensor_descs)

    while True:
        ret = bar.refresh()
        if ret != 0:
            break

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
