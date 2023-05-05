#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

from __future__ import annotations

import sys

from dataclasses import dataclass
from json import loads as jloads
from os.path import join as pjoin
from subprocess import run as prun
from tempfile import TemporaryDirectory


##########################################################################################
# Dataclass definitions
##########################################################################################

@dataclass(frozen=True)
class OutputInfo:
    name: str
    resolution: tuple[int, int]

    @staticmethod
    def from_json(input: dict) -> OutputInfo:
        '''
        Create an OutputInfo object from a JSON dictionary.

        Arguments:
            input - the JSON dictionary to use
        '''

        mode = input['current_mode']

        return OutputInfo(
            name       = input['name'],
            resolution = (mode['width'], mode['height'])
        )


##########################################################################################
# Internal functions
##########################################################################################

def _get_focused_output() -> OutputInfo:
    '''
    Determine the focused output.

    Returns an OutputInfo object, or None if no focused output was found.
    '''

    p_args = ['/usr/bin/swaymsg', '-r', '-t', 'get_outputs']
    p = prun(p_args, check=True, capture_output=True, encoding='utf-8')

    output = None
    for o in jloads(p.stdout):
        if o['focused']:
            output = OutputInfo.from_json(o)
            break

    return output

def _bg(file: str, output: OutputInfo):
    if output is None:
        grim_args = ['/usr/bin/grim', file]
    else:
        grim_args = ['/usr/bin/grim', '-o', output.name, file]

    prun(grim_args, check=True)

def _bgblur(infile: str, outfile: str):
    bgblur_args = ['/usr/bin/convert', infile, '-scale', '25%', '-blur', '0x2', '-scale', '400%', '-fill', 'black', '-colorize', '50%', outfile ]
    prun(bgblur_args, check=True)

def _locktext(file: str, width: int, height: int):
    pango_markup = """pango:<span foreground='#ffffff' background='#000000' font_desc='Liberation Sans 34'>Type password to unlock</span>"""
    locktext_args = ['/usr/bin/convert', '-size', f'{width}x{height}', '-background', 'black', '-gravity', 'center', pango_markup, file]
    prun(locktext_args, check=True)

def _merge(infile1: str, infile2: str, outfile: str):
    merge_args = ['/usr/bin/convert', infile1, infile2, '-gravity', 'center', '-composite', '-matte', outfile]
    prun(merge_args, check=True)

def _makelock(dir: str, outfile: str):
    bg_file = pjoin(dir, 'bg.png')
    locktext_file = pjoin(dir, 'locktext.png')
    bgblur_file = pjoin(dir, 'bgblur.png')

    output = _get_focused_output()

    if output is None:
        locktext_width = 1920
        locktext_height = 60
    else:
        locktext_width = output.resolution[0]
        locktext_height = int(float(output.resolution[1]) * 0.06)

    _bg(bg_file, output)
    _locktext(locktext_file, locktext_width, locktext_height)
    _bgblur(bg_file, bgblur_file)
    _merge(bgblur_file, locktext_file, outfile)


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    tempdir = TemporaryDirectory(prefix='/dev/shm/')

    output_file = pjoin(tempdir.name, 'output.png')

    try:
        _makelock(tempdir.name, output_file)
        lock_args = ['/usr/bin/swaylock', '-f', '-s', 'fill', '-i', output_file]

    except Exception:
        lock_args = ['/usr/bin/swaylock', '-f']

    prun(lock_args, check=True)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
