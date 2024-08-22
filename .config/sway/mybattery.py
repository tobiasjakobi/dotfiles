#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys
from pathlib import Path

from tjtools.sysfs_helper import read_sysfs


##########################################################################################
# Constants
##########################################################################################

_state_file = Path('/run/acpi_acadapter')
_sysfs_base = Path('/sys/class/power_supply/BAT0')


##########################################################################################
# Functions
##########################################################################################

def read_battery() -> str:
    try:
        charge_now = int(read_sysfs(_sysfs_base / 'charge_now'))
        charge_full = int(read_sysfs(_sysfs_base / 'charge_full'))

    except Exception:
        return None

    try:
        ac_state = int.from_bytes(_state_file.read_bytes(), byteorder='little')

    except Exception:
        return None

    value = (charge_now * 100) // charge_full
    msg = 'unplugged' if ac_state == 0 else 'plugged in'

    return f'{value}% ({msg})'


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    ret = read_battery()
    if ret is None:
        print('error: battery not found', file=sys.stderr)

        return 1

    print(f'Battery: {ret}', file=sys.stdout)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
