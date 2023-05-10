#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Interactively add a list of tag values (for a single tag, e.g. 'title') to
a list of media files (VorbisComment).
'''


##########################################################################################
# Imports
##########################################################################################

import sys

from dataclasses import dataclass
from os.path import isdir, splitext, join as pjoin
from os import getcwd, listdir
from subprocess import run as prun
from tempfile import TemporaryDirectory
from typing import Any

from magic import Magic
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC


##########################################################################################
# Constants
##########################################################################################

_editor = '/usr/bin/featherpad'

_switcher = {
    'audio/ogg': OggVorbis,
    'audio/flac': FLAC,
}


##########################################################################################
# Class definitions
##########################################################################################

@dataclass(frozen=True)
class _InternalEntry:
    audio: Any
    input: list
    edit: str


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} [--single] [directory] <tag argument>', file=sys.stdout)


##########################################################################################
# Functions
##########################################################################################

def interactive_tag(dir_name: str, tag: str) -> int:
    mime = Magic(mime=True)

    if not isdir(dir_name):
        print(f'error: directory not found: {dir_name}', file=sys.stderr)

        return 1

    if tag.find('=') != -1:
        print(f'error: invalid tag name: {tag}', file=sys.stderr)

        return 2

    tempdir = TemporaryDirectory(prefix='/dev/shm/')

    files = []

    for file in sorted(listdir(dir_name)):
        split_file = splitext(file)

        if len(split_file) != 2 or split_file[1] not in ('.flac', '.ogg'):
            continue

        file_type = mime.from_file(file)

        audiotype = _switcher.get(file_type, None)
        if audiotype is None:
            print(f'warn: skipping unsupported type: {file}: {file_type}', file=sys.stderr)

            continue

        try:
            a = audiotype(file)

        except Exception as exc:
            print(f'warn: skipping broken file: {file}: {exc}', file=sys.stderr)

            continue

        edit_file = pjoin(tempdir.name, split_file[0] + '.txt')

        with open(edit_file, mode='w+', encoding='utf-8') as f:
            for t in a.tags:
                if t[0].lower() == tag:
                    f.write(t[1])

        ie = _InternalEntry(
            audio = a,
            input = split_file,
            edit = edit_file,
        )

        files.append(ie)

    prun([_editor, '--standalone'] + [x.edit for x in files], check=True)

    for entry in files:
        with open(entry.edit, encoding='utf-8') as f:
            entry.audio[tag] = f.read()

        try:
            entry.audio.save()

        except Exception as exc:
            print(f'warn: failed to save tags: {entry.input[0]}: {exc}', file=sys.stderr)

    tempdir.cleanup()

    return 0

def single_tag(dir_name: str, tag: str) -> int:
    mime = Magic(mime=True)

    if not isdir(dir_name):
        print(f'error: directory not found: {dir_name}', file=sys.stderr)

        return 1

    if tag.find('=') != -1:
        print(f'error: invalid tag name: {tag}', file=sys.stderr)

        return 2

    tempdir = TemporaryDirectory(prefix='/dev/shm/')

    input_name = pjoin(tempdir.name, 'input.txt')
    prun([_editor, '--standalone', input_name], check=True)

    with open(input_name, encoding='utf-8') as f:
        v = f.read()

    tempdir.cleanup()

    for file in sorted(listdir(dir_name)):
        split_file = splitext(file)

        if len(split_file) != 2 or split_file[1] not in ('.flac', '.ogg'):
            continue

        file_type = mime.from_file(file)

        audiotype = _switcher.get(file_type, None)
        if audiotype is None:
            print(f'warn: skipping unsupported type: {file}: {file_type}', file=sys.stderr)

            continue

        try:
            audio = audiotype(file)

        except Exception as exc:
            print(f'warn: skipping broken file: {file}: {exc}', file=sys.stderr)

            continue

        audio[tag] = v

        try:
            audio.save()

        except Exception as exc:
            print(f'warn: failed to save tags: {file}: {exc}', file=sys.stderr)

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    '''
    Main function.
    '''

    single_mode = False

    if len(args) >= 2 and args[1] == '--single':
        single_mode = True
        args = args[1:]

    if len(args) < 2:
        print('error: missing tag argument', file=sys.stderr)
        _usage(args[0])

        return 1

    if len(args) >= 3:
        work_dir = args[1]
        tagarg = args[2]
    else:
        work_dir = getcwd()
        tagarg = args[1]

        print(f'info: using current directory: {work_dir}', file=sys.stdout)

    if single_mode:
        ret = single_tag(work_dir, tagarg.lower())
    else:
        ret = interactive_tag(work_dir, tagarg.lower())

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
