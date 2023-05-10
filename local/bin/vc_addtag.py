#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from dataclasses import dataclass
from os.path import exists

from magic import Magic
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
# Dataclass definitions
##########################################################################################

@dataclass(frozen=True)
class InternalTag:
    key: str
    value: str


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <filename> [--tag1name=tag1content] [--tag2name=tag2content] ...', file=sys.stdout)


##########################################################################################
# Functions
##########################################################################################

def handle_arg(arg: str) -> InternalTag:
    if len(arg) < 5:
        raise RuntimeError('short argument')

    if not arg.startswith('--'):
        raise RuntimeError('unprefixed argument')

    raw_arg = arg[2:]

    tmp = raw_arg.split('=', maxsplit=1)

    if len(tmp) != 2:
        raise RuntimeError('malformed argument')

    return InternalTag(key=tmp[0], value=tmp[1])

def addtag(args: list) -> int:
    mime = Magic(mime=True)

    input = args[0]
    tag_args = args[1:]

    if not exists(input):
        print(f'error: input file not found: {input}', file=sys.stderr)

        return 1

    input_type = mime.from_file(input)

    audiotype = _switcher.get(input_type, None)
    if audiotype is None:
        print(f'error: input has unsupported type: {input_type}', file=sys.stderr)

        return 2

    try:
        new_tags = [handle_arg(x) for x in tag_args]

    except Exception as exc:
        print(f'error: invalid tag argument: {exc}', file=sys.stderr)

        return 3

    try:
        audio = audiotype(input)

    except Exception as exc:
        print(f'error: failed to open file: {exc}', file=sys.stderr)

        return 4

    if len(new_tags) == 0:
        if not audio.tags:
            print(f'info: no tags found: {input}', file=sys.stdout)

            return 0

        print(f'info: printing all tags of: {input}', file=sys.stdout)
        for tag in audio.tags:
            print(f'{tag[0]} = {tag[1]}', file=sys.stdout)

        return 0

    for it in new_tags:
        if len(it.value) == 0:
            if it.key in audio:
                del audio[it.key]
        else:
            audio[it.key] = it.value

    try:
        audio.save()

    except Exception as exc:
        print(f'error: failed to save new tags: {exc}', file=sys.stderr)

        return 5

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

    ret = addtag(args[1:])

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
