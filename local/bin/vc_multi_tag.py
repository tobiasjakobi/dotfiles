#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Add a list of tag values (for a single tag, e.g. 'title') to
a list of FLAC files (VorbisComment).
'''


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import isdir, splitext, join as pjoin
from os import getcwd, listdir
from subprocess import run as prun
from tempfile import TemporaryDirectory

from vc_addtag import addtag


##########################################################################################
# Constants
##########################################################################################

_editor = '/usr/bin/featherpad'


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} [directory] <tag argument>', file=sys.stdout)


##########################################################################################
# Functions
##########################################################################################

def multi_tag(dir_name: str, tag: str) -> int:
    if not isdir(dir_name):
        print(f'error: directory not found: {dir_name}', file=sys.stderr)

        return 1

    if tag.find('=') != -1:
        print(f'error: invalid tag name: {tag}', file=sys.stderr)

        return 2

    filelist = []
    for file in listdir(dir_name):
        splitfile = splitext(file)

        if len(splitfile) >= 2 and splitfile[1] == '.flac':
            filelist.append(pjoin(dir_name, file))

    filelist.sort()

    tempdir = TemporaryDirectory(prefix='/dev/shm/')

    input_name = pjoin(tempdir.name, 'input.txt')
    prun([_editor, '--standalone', input_name], check=True)

    with open(input_name, encoding='utf-8') as f:
        taglist = f.read().splitlines()

    tempdir.cleanup()

    if len(filelist) != len(taglist):
        print('error: size of filelist not matching size of taglist', file=sys.stderr)
        print(f'\tfilelist = {len(filelist)}, taglist = {len(taglist)}', file=sys.stderr)

        return 3

    for file, entry in zip(filelist, taglist):
        vc_args = [file, f'--{tag}={entry}']

        addtag(vc_args)

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    '''
    Main function.
    '''

    if len(args) < 2:
        print('error: missing tag argument', file=sys.stderr)
        _usage(args[0])

        return 1

    if len(args) > 2:
        work_dir, tagarg = args[1:3]
    else:
        work_dir = getcwd()
        tagarg = args[1]

        print(f'info: using current directory: {work_dir}', file=sys.stdout)

    ret = multi_tag(work_dir, tagarg)

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
