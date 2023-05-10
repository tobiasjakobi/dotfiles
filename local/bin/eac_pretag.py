#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Fill some standard tags via a template.
Apply this to a FLAC encoded EAC rip.
'''


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import expanduser, isdir, splitext, join as pjoin
from os import getcwd, listdir, remove
from subprocess import run as prun
from tempfile import NamedTemporaryFile

from vc_addtag import addtag


##########################################################################################
# Constants
##########################################################################################

_template = expanduser('~/local/tagging.template')

_editor = '/usr/bin/featherpad'


##########################################################################################
# Functions
##########################################################################################

def pretag(dir: str):
    if not isdir(dir):
        print(f'error: directory not found: {dir}', file=sys.stderr)

        return 1

    filelist = []
    for file in sorted(listdir(dir)):
        splitfile = splitext(file)

        if len(splitfile) >= 2 and splitfile[1] == '.flac':
            filelist.append(pjoin(dir, file))

    filelist.sort()

    input_fd = NamedTemporaryFile(mode='w', prefix='/dev/shm/', delete=False)
    input_name = input_fd.name

    # copy template
    template_fd = open(_template, 'r')
    input_fd.write(template_fd.read())
    template_fd.close()

    input_fd.close()

    prun([_editor, '--standalone', input_name], check=True)
    input_fd = open(input_name, 'r')

    tag_args = []

    for arg in input_fd.read().splitlines():
        if arg.find('=') == -1:
            print(f'warn: skipping malformed line: {arg}', file=sys.stderr)

            continue

        arg_split = arg.split('=', maxsplit=1)

        tag_key = arg_split[0].rstrip(' ')
        tag_entry = arg_split[1].lstrip(' ')

        if len(tag_key) == 0:
            print(f'warn: skipping malformed tag key: {tag_key}', file=sys.stderr)

            continue

        if len(tag_entry) == 0:
            continue

        tag_args.append('--' + tag_key + '=' + tag_entry);

    input_fd.close()
    remove(input_name)

    if len(tag_args) == 0:
        return 0

    for file in filelist:
        vc_args = [file] + tag_args
        addtag(vc_args)

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    current_dir = getcwd()

    if len(args) < 2:
        print(f'info: using current directory: {current_dir}', file=sys.stdout)
        ret = pretag(current_dir)
    else:
        ret = pretag(args[1])

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
