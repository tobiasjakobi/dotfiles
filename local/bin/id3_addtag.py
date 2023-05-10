#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import exists

from eyed3.core import load as eload
from eyed3.id3 import ID3_V2_4
from eyed3.mp3 import MIME_TYPES, Mp3AudioFile
from eyed3.utils import guessMimetype

from vc_addtag import InternalTag, handle_arg


##########################################################################################
# Constants
##########################################################################################

valid_tags = [
    'replaygain_algorithm',
    'replaygain_reference_loudness',
    'replaygain_track_gain',
    'replaygain_track_peak',
    'replaygain_track_range',
    'replaygain_album_gain',
    'replaygain_album_peak',
    'replaygain_album_range',
]


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <filename> [--tag1name=tag1content] [--tag2name=tag2content] ...', file=sys.stdout)

def _is_valid_tag(t: InternalTag) -> bool:
    return t.key in valid_tags


##########################################################################################
# Functions
##########################################################################################

def is_mp3(path: str) -> bool:
    mimetype = guessMimetype(path)

    if mimetype == 'application/octet-stream':
        object = eload(path)
        return isinstance(object, Mp3AudioFile)
    else:
        return mimetype in MIME_TYPES

def addtag(args: list) -> int:
    input = args[0]
    tag_args = args[1:]

    if not exists(input):
        print(f'error: input not found: {input}', file=sys.stderr)

        return 1

    try:
        new_tags = [handle_arg(x) for x in tag_args]

    except Exception as exc:
        print(f'error: invalid tag argument: {exc}', file=sys.stderr)

        return 2

    try:
        audio = eload(path=input, tag_version=ID3_V2_4)

    except Exception as exc:
        print(f'error: opening file failed: {input}: {exc}', file=sys.stderr)

        return 3

    if not audio:
        print(f'error: file is not of type MP3: {input}', file=sys.stderr)

        return 4

    if len(new_tags) == 0:
        if not audio.tags:
            print(f'info: no tags found: {input}', file=sys.stdout)

            return 0

        print(f'info: printing all user text frames of: {input}', file=sys.stdout)
        for arg in audio.tag.user_text_frames:
            print(f'{arg.description} = {arg.text}', file=sys.stdout)

        return 0

    if not audio.tag:
        audio.initTag()

    t = audio.tag

    for arg in new_tags:
        if _is_valid_tag(arg):
            t.user_text_frames.set(text=arg.value, description=arg.key)
        else:
            print(f'warn: skipping invalid tag: {arg.key}', file=sys.stderr)

    try:
        t.save(version=ID3_V2_4)

    except Exception as exc:
        print(f'error: failed to save new tags: {exc}', file=sys.stderr)

        return 5

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        print('error: missing filename argument', file=sys.stderr)
        _usage(args[0])

        return 1

    ret = addtag(args[1:])

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
