#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from argparse import ArgumentParser
from magic import Magic
from pathlib import Path

from mutagen.flac import FLAC


##########################################################################################
# Functions
##########################################################################################

def vc_copytags(src_path: Path, dst_path: Path):
    '''
    Copy VorbisComment tags from one file to another.

    Arguments:
        src_path - path to the source file
        dst_path - path to the destination file
    '''

    if not src_path.is_file():
        raise RuntimeError(f'source path not found: {src_path}')

    if not dst_path.is_file():
        raise RuntimeError(f'destination path not found: {dst_path}')

    mime = Magic(mime=True)
    src_type = mime.from_file(src_path.as_posix())
    dst_type = mime.from_file(dst_path.as_posix())

    if src_type != 'audio/flac':
        raise RuntimeError(f'source has unsupported type: {src_type}')

    if dst_type != 'audio/flac':
        raise RuntimeError(f'destination has unsupported type: {dst_type}')

    try:
        '''
        Mutagen does not provide context management.
        '''
        s = FLAC(src_path.as_posix())
        d = FLAC(dst_path.as_posix())

        if s.tags:
            d.tags += s.tags

        for p in s.pictures:
            d.add_picture(p)

        d.save()

    except Exception as exc:
        raise RuntimeError(f'transfer of tags failed: {exc}')


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    '''
    Main function.
    '''

    parser = ArgumentParser(description='Copy VorbisComment and picture metadata.')

    parser.add_argument('-s', '--source', help='Source path', required=True)
    parser.add_argument('-d', '--destination', help='Destination path', required=True)

    parsed_args = parser.parse_args()

    try:
        source = Path(parsed_args.source)
        destination = Path(parsed_args.destination)

        vc_copytags(source, destination)

    except Exception as exc:
        print(f'error: failed to copy VorbisComment tags: {source}: {exc}', file=sys.stderr)

        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
