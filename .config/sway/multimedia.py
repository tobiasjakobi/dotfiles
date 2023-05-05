#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from subprocess import run as prun


##########################################################################################
# Constants
##########################################################################################

_mpc_toggle_args = ['mpc', '--quiet', 'toggle']
_mpc_next_args = ['mpc', '--quiet', 'next']
_mpc_prev_args = ['mpc', '--quiet', 'prev']


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} --play|--next|--prev', file=sys.stdout)
    print('Wrapper script for multimedia keys.', file=sys.stdout)

def _multimedia_play():
    p = prun(_mpc_toggle_args)

    return p.returncode

def _multimedia_next():
    p = prun(_mpc_next_args)

    return p.returncode

def _multimedia_prev():
    p = prun(_mpc_prev_args)

    return p.returncode


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])
        return 1

    if args[1] == '--play':
        ret = _multimedia_play()
    elif args[1] == '--next':
        ret = _multimedia_next()
    elif args[1] == '--prev':
        ret = _multimedia_prev()
    else:
        ret = 2

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
