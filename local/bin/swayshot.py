#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from datetime import datetime
from json import loads as jloads
from os.path import expanduser
from subprocess import run as prun


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} --full|--select', file=sys.stdout)

def _save_path() -> str:
    now = datetime.now()

    return expanduser(now.strftime('~/screenshot_%Y-%m-%d-%H%M%S.png'))

def _full_shot(path: str):
    swaymsg_args = ['/usr/bin/swaymsg', '-r', '-t', 'get_outputs']
    p = prun(swaymsg_args, check=True, capture_output=True, encoding='utf-8')

    json_data = jloads(p.stdout)

    output = None
    for o in json_data:
        if o['focused']:
            output = o['name']
            break

    if output is None:
        grim_args = ['/usr/bin/grim', path]
    else:
        grim_args = ['/usr/bin/grim', '-o', output, path]

    prun(grim_args, check=True)

def _select_shot(path: str):
    slurp_args = ['/usr/bin/slurp']
    p = prun(slurp_args, check=True, capture_output=True, encoding='utf-8')

    slurp_out = p.stdout.splitlines()
    if len(slurp_out) != 1:
        raise RuntimeError('malformed slurp result')

    area = slurp_out[0].rstrip()

    grim_args = ['/usr/bin/grim', '-g', area, path]
    prun(grim_args)


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
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
