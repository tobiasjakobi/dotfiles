#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from magic import Magic
from os.path import exists
from typing import Any

from mutagen.mp4 import MP4, MP4FreeForm, AtomDataType as MP4Atom

from id3_addtag import valid_tags
from vc_addtag import InternalTag, handle_arg


##########################################################################################
# Constants
##########################################################################################

_canonical_switcher = {
    '\xa9alb': 'album',
    '\xa9nam': 'title',
    '\xa9ART': 'artist',
    'aART': 'album artist',
    '\xa9wrt': 'composer',
    '\xa9day': 'year',
    '\xa9cmt': 'comment',
    '\xa9gen': 'genre',
    '\xa9des': 'description',
    '\xa9too': 'encoded by',
    'disk': 'disknumber',
    'trkn': 'tracknumber',
    'pgap': 'part of gapless album',
    'tmpo': 'tempo/BPM',
    'cpil': 'part of a compilation',
}

_unprintable_tags = [
    'covr',
]


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <filename> [--tag1name=tag1content] [--tag2name=tag2content] ...', file=sys.stdout)

def _is_valid_canonical(c: str) -> bool:
    '''
    Test if the canonical name is valid (for adding/removal).
    '''

    return c in valid_tags

def _is_printable(tag_key: str) -> bool:
    '''
    Test if the content of a MP4 tag is printable.
    '''

    return tag_key not in _unprintable_tags

def _freeform_to_canonical(tag_key: str) -> str:
    '''
    Translates a MP4 freeform tag key.
    '''

    if len(tag_key) < 4 or not tag_key.startswith('----'):
        raise RuntimeError('malformed freeform key')

    freeform = tag_key.split(':', maxsplit=2)

    if len(freeform) == 3 and freeform[1] == 'com.apple.iTunes':
        return freeform[2]

    return f'unknown freeform key: {tag_key}'

def _key_to_canonical(tag_key: str) -> str:
    '''
    Translates a MP4 tag key to a canonical form.
    '''

    if len(tag_key) >= 4 and tag_key.startswith('----'):
        return _freeform_to_canonical(tag_key)

    can = _canonical_switcher.get(tag_key, None)
    if can is None:
        return f'unknown tag key: {tag_key}'

    return can

def _remove_tag_canonical(tags, canonical):
    '''
    Remove a tag via its canonical name.
    '''

    raise RuntimeError('TODO: not implemented')

def _add_tag_canonical(tags, canonical: str, content: str):
    '''
    Add a tag via its canonical name.

    TODO/FIXME: currently only freeform tags are supported
    '''

    tag_key = f'----:com.apple.iTunes:{canonical}'
    tag_value = MP4FreeForm(content.encode('utf-8'), dataformat=MP4Atom.UTF8)

    tags[tag_key] = tag_value

def _freeform_to_string(ff: MP4FreeForm) -> str:
    '''
    Convert a MP4 freeform object to a regular string.
    '''

    if ff.dataformat == MP4Atom.IMPLICIT:
        return format(ff)
    elif ff.dataformat == MP4Atom.UTF8:
        return bytes(ff).decode('utf-8')
    elif ff.dataformat == MP4Atom.UTF16:
        return bytes(ff).decode('utf-16')

    raise RuntimeError('unsupported freeform format')

def _printable_to_string(p: Any) -> str:
    '''
    Convert the value of a printable MP4 tag to a regular string.
    '''

    if isinstance(p, bool):
        return str(p)

    if not isinstance(p, list) or len(p) != 1:
        raise RuntimeError('malformed tag')

    data = p[0]

    if isinstance(data, tuple):
        if len(data) != 2:
            raise RuntimeError('unhandled tuple size')

        return '{0}/{1}'.format(*data)

    if isinstance(data, MP4FreeForm):
        return _freeform_to_string(data)

    if isinstance(data, int):
        return str(data)

    if isinstance(data, str):
        return data

    raise RuntimeError('unhandled tag type')

def _value_to_string(tag_key: str, tag_value: Any) -> str:
    '''
    Convert a MP4 tag value to a regular string.
    '''

    if tag_key == 'tmpo':
        ret = str(tag_value[0])
    elif tag_key == '----:com.apple.iTunes:Encoding Params':
        ret = bytes(tag_value[0]).decode('utf-8') # FIXME: wrong encoding
    elif _is_printable(tag_key):
        ret = _printable_to_string(tag_value)
    else:
        ret = None

    return ret


##########################################################################################
# Functions
##########################################################################################

def addtag(args: list) -> int:
    mime = Magic(mime=True)

    input = args[0]
    tag_args = args[1:]

    if not exists(input):
        print(f'error: input file not found: {input}', file=sys.stderr)

        return 1

    input_type = mime.from_file(input)

    if input_type not in ('video/mp4', 'audio/x-m4a'):
        print(f'error: input file has unsupported type: {input}: {input_type}', file=sys.stderr)

        return 2

    try:
        new_tags = [handle_arg(x) for x in tag_args]

    except Exception as exc:
        print(f'error: invalid tag argument: {exc}', file=sys.stderr)

        return 3

    try:
        audio = MP4(input)

    except Exception as exc:
        print(f'error: opening file failed: {exc}', file=sys.stderr)

        return 4

    if not new_tags:
        if not audio.tags:
            print(f'info: no tags found: {input}', file=sys.stdout)

            return 0

        print(f'info: printing all tags of: {input}', file=sys.stdout)

        for key, value in audio.tags.items():
            canonical = _key_to_canonical(key)
            content = _value_to_string(key, value)

            if content is None:
                print(f'warn: skipping tag with key: {key}', file=sys.stderr)

                continue

            print(f'{canonical} = {content}', file=sys.stdout)

        return 0

    for arg in new_tags:
        if not _is_valid_canonical(arg.key):
            print(f'warn: skipping invalid tag: {arg.key}', file=sys.stderr)

            continue

        if len(arg.value) == 0:
            _remove_tag_canonical(audio.tags, arg.key)
        else:
            _add_tag_canonical(audio.tags, arg.key, arg.value)

    try:
        audio.save()

    except Exception as exc:
        print(f'error: saving new tags failed: {exc}', file=sys.stderr)

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
