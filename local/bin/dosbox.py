#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import expanduser
from os import environ
from subprocess import Popen, run as prun


##########################################################################################
# Constants
##########################################################################################

_soundfont = '/usr/share/sounds/sf2/FluidR3_GM.sf2'


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <DOSBox config>', file=sys.stdout)


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])
        return 0

    config = args[1]

    fsynth_args = [
        '/usr/bin/fluidsynth',
        '-a', 'pulseaudio',
        '-m', 'alsa_seq',
        '-o', 'midi.autoconnect=1',
        '-g', '1.0',
        _soundfont
    ]

    fsynth_p = Popen(fsynth_args, capture_output=True, encoding='utf-8')

    dosbox_args = ['dosbox', '-conf', config]

    dosbox_env = environ.copy()
    dosbox_env['SDL_AUDIODRIVER'] = 'pulse'
    dosbox_env['SDL_VIDEODRIVER'] = 'wayland'
    dosbox_env['LD_LIBRARY_PATH'] = expanduser('~/local/lib')

    prun(dosbox_args, env=dosbox_env)

    fsynth_p.terminate()

    fsynth_out = fsynth_p.stdout.read().splitlines()
    ret = fsynth_p.wait()

    print('info: fluidsynth output:', file=sys.stdout)
    for line in fsynth_out:
        print(line, file=sys.stdout)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
