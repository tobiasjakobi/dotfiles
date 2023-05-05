#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import expanduser
from subprocess import run as prun


##########################################################################################
# Constants
##########################################################################################

_swaymsg_args = 'output eDP-1 power {}'

_idle_lock_args = [expanduser('~/local/bin/fancylock.py')]


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} --lock|--display-on|--display-off', file=sys.stdout)
    print('Wrapper script for swayidle operations.', file=sys.stdout)

def _idle_lock() -> int:
    p = prun(_idle_lock_args)

    return p.returncode

def _idle_display(state: bool) -> int:
    idle_display_args = ['swaymsg', _swaymsg_args.format('on' if state else 'off')]
    p = prun(idle_display_args)

    return p.returncode


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])
        return 1

    if args[1] == '--lock':
        ret = _idle_lock()
    elif args[1] == '--display-on':
        ret = _idle_display(True)
    elif args[1] == '--display-off':
        ret = _idle_display(False)
    else:
        ret = 2

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
