#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from magic import Magic
from os.path import exists

from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis


##########################################################################################
# Constants
##########################################################################################

_switcher = {
    'audio/ogg': OggVorbis,
    'audio/flac': FLAC,
}


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <filename> [tag1name] [tag2name] ...', file=sys.stdout)


##########################################################################################
# Functions
##########################################################################################

def cleantags(args: list) -> int:
    mime = Magic(mime=True)

    input_name = args[0]
    tag_args = args[1:]

    if not exists(input_name):
        print(f'error: input file not found: {input_name}', file=sys.stderr)

        return 1

    input_type = mime.from_file(input_name)

    audiotype = _switcher.get(input_type, None)
    if audiotype is None:
        print(f'error: input has unsupported type: {input_type}', file=sys.stderr)

        return 2

    if len(tag_args) == 0:
        return 0

    try:
        audio = audiotype(input_name)

    except Exception as exc:
        print(f'error: failed to open file: {exc}', file=sys.stderr)

        return 3

    for it in tag_args:
        it_lower = it.lower()
        if it_lower in audio:
            del audio[it_lower]

    try:
        audio.save()

    except Exception as exc:
        print(f'error: failed to save new tags: {exc}', file=sys.stderr)

        return 4

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    '''
    Main function.
    '''

    if len(args) < 2:
        print('error: missing filename argument', file=sys.stderr)
        _usage(args[0])

        return 1

    ret = cleantags(args[1:])

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
