#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from datetime import datetime
from os.path import expanduser
from subprocess import run as prun

from i3ipc import Connection as I3Connection


##########################################################################################
# Constants
##########################################################################################

_grim = '/usr/bin/grim'
_slurp = '/usr/bin/slurp'


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} --full|--select', file=sys.stdout)

def _save_path() -> str:
    now = datetime.now()

    return expanduser(now.strftime('~/screenshot_%Y-%m-%d-%H%M%S.png'))

def _full_shot(path: str):
    conn = I3Connection()

    focused_output = None
    for output in conn.get_outputs():
        focused = output.ipc_data.get('focused')
        if focused is not None and focused:
            focused_output = output.ipc_data.get('name')
            break

    if focused_output is None:
        grim_args = [_grim, path]
    else:
        grim_args = [_grim, '-o', focused_output, path]

    prun(grim_args, check=True)

def _select_shot(path: str):
    slurp_args = [_slurp]
    p = prun(slurp_args, check=True, capture_output=True, encoding='utf-8')

    slurp_out = p.stdout.splitlines()
    if len(slurp_out) != 1:
        raise RuntimeError('malformed slurp result')

    area = slurp_out[0].rstrip()

    grim_args = [_grim, '-g', area, path]
    prun(grim_args)


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    if len(args) != 2:
        _usage(args[0])
        return 0

    mode = args[1]
    outname = _save_path()

    try:
        if mode == '--full':
            _full_shot(outname)
        elif mode == '--select':
            _select_shot(outname)
        else:
            return 1

    except Exception as exc:
        print(f'error: swayshot {mode} failed: {exc}', file=sys.stderr)

        return 2

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
