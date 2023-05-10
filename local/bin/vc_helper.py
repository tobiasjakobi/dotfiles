#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

from os.path import isfile

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
# Functions
##########################################################################################

def gettag(input_path: str, tags: list[str]) -> list[str]:
    '''
    Get a number of tag values from a given file.

    Arguments:
        input_path - path to the file used as input
        tags       - list of tag keys

    Returns a list of strings, containing the values corresponding
    to the given tag keys.

    Should some tag key not exist, then None is put at this position
    in the list.
    '''

    mime = Magic(mime=True)

    if not isfile(input_path):
        raise RuntimeError(f'input path not found: {input_path}')

    input_type = mime.from_file(input_path)

    audiotype = _switcher.get(input_type, None)
    if audiotype is None:
        raise RuntimeError(f'input has unsupported type: {input_type}')

    try:
        audio = audiotype(input_path)

    except Exception as exc:
        raise RuntimeError(f'failed to open file: {exc}') from exc

    ret = []

    for _t in tags:
        _v = audio.tags[_t] if _t in audio.tags else None

        if _v is not None:
            if len(_v) != 1:
                raise RuntimeError(f'multi-key tag not supported: {_t}')

            ret.append(_v[0])
        else:
            ret.append(_v)

    return ret
