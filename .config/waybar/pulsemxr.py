#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from getopt import GetoptError, getopt
from json import dumps as jdumps
from time import sleep

import pulsectl


##########################################################################################
# Constants
##########################################################################################

_sink_name = 'alsa_output.pci-0000_08_00.6.analog-stereo'


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} --daemon|--action=<action type>', file=sys.stdout)

def refresh(p, s):
    status = {
        'text': None,
        'tooltip': None,
        'class': 'pulsemxr',
        'percentage': 0
    }

    #ctrl.update()

    #mute = ctrl.is_muted()

    #volume_str = str(ctrl.get_volume())
    #mute_str = get_mute_str(ctrl.is_muted())

    print(s)

    volume_str = s.volumes
    cardname = None
    mixername = None
    mute_str = None

    status['text'] = volume_str
    status['tooltip'] = f'{cardname}:{mixername} = {volume_str} ({mute_str})'

    pipe_lost = False

    try:
        print(jdumps(status), file=sys.stdout, flush=True)

    except Exception:
        pipe_lost = True

    return pipe_lost


##########################################################################################
# Functions
##########################################################################################

def pulsemxr_action(action):
    assert False

def pulsemxr_daemon():
    try:
        pulse = pulsectl.Pulse('pulsemxr')
        sink = pulse.get_sink_by_name(_sink_name)

    except Exception:
        print(f'error: failed to lookup sink {_sink_name}', file=sys.stderr)

        return 1

    def print_events(ev):
        print('Pulse event:', ev)
        print(dir(ev))
        ### Raise PulseLoopStop for event_listen() to return before timeout (if any)
        # raise pulsectl.PulseLoopStop

    pulse.event_mask_set('all')
    pulse.event_callback_set(print_events)
    pulse.event_listen(timeout=10)

    #pulse.volume_change_all_chans(sink, -0.1)
    #pulse.volume_set_all_chans(sink, 0.5)

    while True:
        if refresh(pulse, sink):
            break

        sleep(1.0)

    return 0

def main(args: list) -> int:
    getopt_largs = ('help', 'daemon', 'action=')

    try:
        opts, oargs = getopt(sys.argv[1:], 'hdl:', getopt_largs)

    except GetoptError as err:
        print(f'error: getopt parsing failed: {err}', file=sys.stderr)
        _usage(args[0])

        return 1

    for o, a in opts:
        if o in ('-h', '--help'):
            _usage(args[0])

            return 0

        elif o in ('-d', '--daemon'):
            return pulsemxr_daemon()

        elif o in ('-a', '--action'):
            return pulsemxr_action(a)

        else:
            raise RuntimeError('unhandled option')

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
