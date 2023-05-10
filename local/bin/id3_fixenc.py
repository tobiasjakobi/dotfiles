#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from argparse import ArgumentParser
from os.path import exists

from eyed3 import core as eyeD3, id3 as ID3


##########################################################################################
# Internal functions
##########################################################################################

def _recode(input: str, src_enc: str) -> str:
    return input.encode('latin1').decode(src_enc)

def _print_tag(tag: str, name: str, src_enc: str):
    if not tag:
        return

    rtag = _recode(tag, src_enc)

    print(f'{name}: {rtag}', file=sys.stdout)


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    parser = ArgumentParser(description='Helper to fix tag encoding issues.')

    parser.add_argument('-e', '--enc', type=str, help='encoding', required=True)
    parser.add_argument('-s', '--src', type=str, help='source filename', required=True)

    args = parser.parse_args()

    enc = args.enc
    src = args.src

    if not exists(src):
        print(f'error: source file not found: {src}', file=sys.stderr)

        return 1

    try:
        audio = eyeD3.load(path=src, tag_version=ID3.ID3_V2_4)

    except Exception as exc:
        print(f'error: failed to open source: {exc}', file=sys.stderr)

        return 2

    if not audio:
        print(f'error: source is not of type MP3: {src}', file=sys.stderr)

        return 3

    t = audio.tag

    if not t:
        print(f'info: no tags found in source: {src}', file=sys.stdout)

        return 0

    _print_tag(t.title, 'title', enc)
    _print_tag(t.album, 'album', enc)
    _print_tag(t.artist, 'artist', enc)
    _print_tag(t.album_artist, 'album artist', enc)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
