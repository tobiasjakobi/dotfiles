#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import join as pjoin


##########################################################################################
# Constants
##########################################################################################

_state_file = '/var/state/acpi_acadapter'
_sysfs_base = '/sys/class/power_supply/BAT0'


##########################################################################################
# Functions
##########################################################################################

def read_sysfs(path: str):
    try:
        with open(path, mode='r') as f:
            data = f.read().rstrip()

    except Exception:
        data = None

    return data

def read_battery():
    try:
        charge_now = int(read_sysfs(pjoin(_sysfs_base, 'charge_now')))
        charge_full = int(read_sysfs(pjoin(_sysfs_base, 'charge_full')))

    except Exception:
        return None

    try:
        with open(_state_file, mode='r') as f:
            ac_state = int(f.read())

    except Exception:
        return None

    value = (charge_now * 100) // charge_full
    if ac_state == 0:
        msg = 'unplugged'
    else:
        msg = 'plugged in'

    return f'{value}% ({msg})'


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    ret = read_battery()
    if ret is None:
        print('error: battery not found', file=sys.stderr)

        return 1

    print(f'Battery: {ret}', file=sys.stdout)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
