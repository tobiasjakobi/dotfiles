#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from argparse import ArgumentParser
from magic import Magic
from os.path import exists

from mutagen.flac import FLAC


##########################################################################################
# Functions
##########################################################################################

def vc_copytags(src_path: str, dst_path: str):
    '''
    Copy VorbisComment tags from one file to another.

    Arguments:
        src_path - path to the source file
        dst_path - path to the destination file
    '''

    if not exists(src_path):
        raise RuntimeError(f'source file not found: {src_path}')

    if not exists(dst_path):
        raise RuntimeError(f'destination file not found: {dst_path}')

    mime = Magic(mime=True)
    src_type = mime.from_file(src_path)
    dst_type = mime.from_file(dst_path)

    if src_type != 'audio/flac':
        raise RuntimeError(f'source has unsupported type: {src_type}')

    if dst_type != 'audio/flac':
        raise RuntimeError(f'destination has unsupported type: {dst_type}')

    try:
        '''
        Mutagen does not provide context management.
        '''
        s = FLAC(src_path)
        d = FLAC(dst_path)

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

def main(args: list) -> int:
    '''
    Main function.
    '''

    parser = ArgumentParser(description='Copy VorbisComment and picture metadata.')

    parser.add_argument('-s', '--src', type=str, help='source filename', required=True)
    parser.add_argument('-d', '--dst', type=str, help='destination filename', required=True)

    args = parser.parse_args()

    try:
        vc_copytags(args.src, args.dst)

    except Exception as exc:
        print(f'error: failed to copy VorbisComment tags: {exc}', file=sys.stderr)

        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
