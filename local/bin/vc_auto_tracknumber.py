#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import isdir, splitext, join as pjoin
from os import getcwd, listdir

from vc_addtag import addtag


##########################################################################################
# Internal functions
##########################################################################################

def _pad_tracknumber(i: int, t: int) -> str:
    '''
    Construct tracknumber string with padding.
    '''

    assert(i <= 999 and t <= 999)
    assert(i <= t)

    if t >= 100:
        targetlen = 3
    elif t >= 10:
        targetlen = 2
    else:
        targetlen = 1

    if i >= 100:
        padding = targetlen - 3
    elif i >= 10:
        padding = targetlen - 2
    else:
        padding = targetlen - 1

    return padding * '0' + str(i)

def _auto_tracknumber(dir_name: str) -> int:
    if not isdir(dir_name):
        print(f'error: directory not found: {dir_name}', file=sys.stderr)

        return 1

    filelist = []
    for file in listdir(dir_name):
        splitfile = splitext(file)

        if len(splitfile) >= 2 and splitfile[1] == '.flac':
            filelist.append(pjoin(dir_name, file))

    filelist.sort()

    tracktotal = len(filelist)

    index = 1
    for file in filelist:
        vc_args = [
            file,
            f'--tracknumber={_pad_tracknumber(index, tracktotal)}',
            f'--tracktotal={tracktotal}'
        ]

        addtag(vc_args)
        index += 1

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    '''
    Main function.
    '''

    if len(args) < 2:
        work_dir = getcwd()

        print(f'info: using current directory: {work_dir}', file=sys.stdout)
    else:
        work_dir = args[1]

    ret = _auto_tracknumber(work_dir)

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
