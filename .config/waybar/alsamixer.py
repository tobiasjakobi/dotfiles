#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from getopt import GetoptError, getopt
from json import dumps as jdumps
from time import sleep

from alsactl import PyAlsaControl


##########################################################################################
# Constants
##########################################################################################

_cardname = 'PCH'
_mixername = 'Headphone'


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} --daemon|--action=<action type>', file=sys.stdout)

def _get_mute_str(state: bool) -> str:
    return 'muted' if state else 'unmuted'

def _refresh(ctrl) -> bool:
    status = {
        'text': None,
        'tooltip': None,
        'class': 'alsamixer',
        'percentage': 0
    }

    ctrl.update()

    mute = ctrl.is_muted()

    volume_str = str(ctrl.get_volume())
    mute_str = _get_mute_str(ctrl.is_muted())

    status['text'] = volume_str
    status['tooltip'] = f'{_cardname}:{_mixername} = {volume_str} ({mute_str})'

    pipe_lost = False

    try:
        print(jdumps(status), file=sys.stdout, flush=True)

    except Exception:
        pipe_lost = True

    return pipe_lost


##########################################################################################
# Functions
##########################################################################################

def alsamixer_action(action):
    try:
        ctrl = PyAlsaControl(card_name=_cardname, control=_mixername)

    except (ValueError, RuntimeError) as err:
        return 1

    volume = ctrl.get_volume()
    new_volume = None

    mute = ctrl.is_muted()
    new_mute = None

    if action == 'volume_up':
        new_volume = volume + 2
    elif action == 'volume_down':
        new_volume = volume - 2
    elif action == 'mute_toggle':
        new_mute = not mute
    else:
        print(f'error: unknown action requested: {action}', file=sys.stderr)

        return 2

    if new_volume != None:
        ctrl.set_volume(new_volume)

    if new_mute != None:
        ctrl.set_mute(new_mute)

    return 0

def alsamixer_daemon():
    try:
        ctrl = PyAlsaControl(card_name=_cardname, control=_mixername)

    except (ValueError, RuntimeError) as err:
        return 1

    while True:
        if _refresh(ctrl):
            break

        sleep(1.0)

    return 0

def main(args: list) -> int:
    getopt_largs = ('help', 'daemon', 'action=')

    try:
        opts, oargs = getopt(args[1:], 'hdl:', getopt_largs)

    except GetoptError as err:
        print(f'error: getopt parsing failed: {err}', file=sys.stderr)
        _usage(args[0])

        return 1

    for o, a in opts:
        if o in ('-h', '--help'):
            _usage(args[0])

            return 0

        elif o in ('-d', '--daemon'):
            return alsamixer_daemon()

        elif o in ('-a', '--action'):
            return alsamixer_action(a)

        else:
            raise RuntimeError('unhandled option')

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
