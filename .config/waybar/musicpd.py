#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from enum import Enum
from json import dumps as jdumps
from html import escape as html_escape
from subprocess import CalledProcessError, run as prun
from time import sleep


##########################################################################################
# Enumerator definitions
##########################################################################################

class MPDErrorType(Enum):
    Generic   = 0
    Empty     = 1
    Malformed = 2
    Unknown   = 3


##########################################################################################
# Class definitions
##########################################################################################

class MPDException(Exception):
    def __init__(self, type: MPDErrorType):
        self._type = type

    def get_type(self) -> MPDErrorType:
        return self._type


##########################################################################################
# Functions
##########################################################################################

def _callmpc(args: list):
    p_args = ['/usr/bin/mpc'] + args

    try:
        p = prun(p_args, capture_output=True, check=True, encoding='utf-8')

    except CalledProcessError as exc:
        type = MPDErrorType.Unknown

        stderr = exc.stderr.splitlines()
        if len(stderr) >= 1 and stderr[0].rstrip().startswith('MPD error:'):
            type = MPDErrorType.Generic

        raise MPDException(type)

    stdout = p.stdout.splitlines()

    if len(stdout) == 0:
        raise MPDException(MPDErrorType.Empty)

    if len(stdout) != 1:
        raise MPDException(MPDErrorType.Malformed)

    return stdout[0].rstrip()

def musicpd_refresh():
    status = {
        'text': None,
        'tooltip': None,
        'class': 'MusicPD',
        'percentage': 0,
    }

    delay = 10

    artist_args = ['--format=%artist%', 'current']
    title_args = ['--format=%title%', 'current']
    album_args = ['--format=%album%', 'current']

    album = None

    try:
        artist = _callmpc(artist_args)

        try:
            title = _callmpc(title_args)
            album = _callmpc(album_args)

        except:
            pass

    except MPDException as exc:
        etype = exc.get_type()

        if etype != MPDErrorType.Empty:
            print(f'warn: MPD exception ({etype}) during artist info fetch', file=sys.stderr)

            '''
            An MPD exception is most likely due to missing network connectivity to the
            server, so increase the delay here.
            '''
            delay *= 5

    except Exception as exc:
        print(f'warn: unexpected exception during artist info fetch: {exc}', file=sys.stderr)

    try:
        if album != None:
            mpc_long = f'{artist} - [{album}] {title}'
        else:
            mpc_long = None

        mpc_short = f'{artist} - {title}'

    except:
        mpc_short = 'silence'

    status['text'] = html_escape(mpc_short)
    status['tooltip'] = html_escape(mpc_long)

    pipe_lost = False

    try:
        print(jdumps(status), file=sys.stdout, flush=True)

    except Exception as exc:
        print(f'error: failed to dump JSON to stdout: {exc}', file=sys.stderr)
        pipe_lost = True

    return pipe_lost, delay


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    while True:
        pipe_lost, delay = musicpd_refresh()

        if pipe_lost:
            break

        sleep(delay)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
