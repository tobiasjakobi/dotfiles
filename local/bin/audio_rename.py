#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from enum import IntEnum
from magic import Magic
from os.path import isdir, isfile, abspath, splitext, join as pjoin
from os import listdir, rename

from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

from id3_addtag import is_mp3


##########################################################################################
# Class definitions
##########################################################################################

class PaddingType(IntEnum):
    Track = 0
    Disc  = 1


##########################################################################################
# Constants
##########################################################################################

'''
Minimum padding we want to have to the track number.
'''
_track_minimum_padding = 2


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <directory>', file=sys.stdout)

    msg = '''
Renames audio files in the first level of the directory to canonical format.'''
    
    print(msg, file=sys.stdout)

def _number_padding(input: str, target: str, minimum: int) -> str:
    len_i = len(input)
    len_t = len(target)

    if minimum != 0 and len_t < minimum:
        len_t = minimum

    return '0' * max(0, len_t - len_i)

def _padded_number(number: str, total: str, type: PaddingType) -> str:
    if type == PaddingType.Track:
        ret = _number_padding(number, total, _track_minimum_padding)
    elif type == PaddingType.Disc:
        ret = _number_padding(number, total, 0)
    else:
        raise RuntimeError(f'unknown padding type {type}')

    return ret + number


##########################################################################################
# Functions
##########################################################################################

def rename_flac_ogg(filename: str, is_flac: bool):
    audio = FLAC(filename) if is_flac else OggVorbis(filename)

    '''
    The mandatory tags are 'title', 'tracknumber' and 'tracktotal'.
    '''
    try:
        title = audio.tags['title']
        tracknumber = audio.tags['tracknumber']
        tracktotal = audio.tags['tracktotal']

    except Exception:
        return None

    '''
    Optional tags are 'discnumber' and 'disctotal'.
    '''
    try:
        discnumber = audio.tags['discnumber']
        disctotal = audio.tags['disctotal']

    except Exception:
        discnumber = []
        disctotal = []

    '''
    Disallow multiline tags.
    '''
    if len(title) != 1 or len(tracknumber) != 1 or len(tracktotal) != 1:
        return None

    basename = '{} {}'.format(_padded_number(tracknumber[0], tracktotal[0], PaddingType.Track), title[0])

    '''
    Prepend discnumber prefix if available.
    '''
    if len(discnumber) == 1 and len(disctotal) == 1:
        return _padded_number(discnumber[0], disctotal[0], PaddingType.Disc) + basename

    return basename

def rename_mp3(filename):
    print('renaming MP3: ' + filename)
    raise RuntimeError('TODO/FIXME: rename_mp3: not implemented')

    return None

def rename_m4a(filename):
    audio = MP4(filename)

    '''
    The mandatory tags are 'title', 'tracknumber' and 'tracktotal'.
    'tracknumber' and 'tracktotal' are members of 'trackinfo'.
    '''
    try:
        titles = audio.tags['\xa9nam']
        trackinfo = audio.tags['trkn']

    except Exception:
        return None

    if not isinstance(titles, list) or not isinstance(trackinfo, list):
        return None

    if len(titles) != 1 or len(trackinfo) != 1 or len(trackinfo[0]) != 2:
        return None

    title = titles[0]
    tracknumber = trackinfo[0][0]
    tracktotal = trackinfo[0][1]

    '''
    Optional tags are 'discnumber' and 'disctotal'
    TODO/FIXME: verify that this works
    '''
    try:
        discinfo = audio.tags['disk']

    except Exception:
        try:
            discinfo = audio.tags['disknumber']

        except Exception:
            discinfo = None

    discnumber = None
    disctotal = None

    basename = '{0} {1}'.format(_padded_number(str(tracknumber), str(tracktotal), PaddingType.Track), title)

    '''
    Prepend discnumber prefix if available.
    '''
    if discnumber is int and disctotal is int:
        assert(False)
        return _padded_number(str(discnumber), str(disctotal), PaddingType.Disc) + basename

    return basename

def audio_rename(args: list) -> int:
    mime = Magic(mime=True)

    input = args[0]

    if not isdir(input):
        print(f'error: directory not found: {input}', file=sys.stderr)

        return 1

    root = abspath(input)

    retval = 0

    for file in listdir(root):
        absfile = pjoin(root, file)

        if not isfile(absfile):
            continue

        filetype = mime.from_file(absfile)
        extension = splitext(absfile)[1]

        if len(extension) == 0:
            print(f'error: failed to find extension: {file}', file=sys.stderr)
            retval = 2

            continue

        if filetype == 'audio/ogg':
            canonical = rename_flac_ogg(absfile, is_flac=False)
        elif filetype == 'audio/flac':
            canonical = rename_flac_ogg(absfile, is_flac=True)
        elif filetype in ('audio/x-m4a', 'video/mp4'):
            canonical = rename_m4a(absfile)
        elif filetype == 'audio/mpeg' or is_mp3(absfile):
            canonical = rename_mp3(absfile)
        else:
            continue

        if not canonical:
            print(f'error: failed to find canonical name: {file}', file=sys.stderr)
            retval = 3

            continue

        newfile = canonical.replace('/', '~') + extension
        absnewfile = pjoin(root, newfile)

        '''
        Check if the input filename is already in canonical format.
        '''
        if absnewfile == absfile:
            continue

        '''
        Avoid overwriting existing files.
        '''
        if isfile(absnewfile):
            print(f'error: file with canonical name already exists: {newfile}', file=sys.stderr)
            retval = 4

            continue

        try:
            rename(absfile, absnewfile)

        except Exception:
            print(f'error: failed to rename: {file}', file=sys.stderr)
            retval = 5

    return retval


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        print('error: missing directory argument', file=sys.stderr)
        _usage(args[0])

        return 1

    ret = audio_rename(args[1:])

    return ret

if __name__ == '__main__':
    sys.exit(main(sys.argv))
