#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from argparse import ArgumentParser
from pathlib import Path
from subprocess import run as prun

from mutagen.flac import FLAC


##########################################################################################
# Constants
##########################################################################################

_ffmpeg = '/usr/bin/ffmpeg'

_args_template = [_ffmpeg, '-hide_banner', '-loglevel', 'quiet']


##########################################################################################
# Functions
##########################################################################################

def flac_md5(path: Path) -> bool:
    '''
    Check the MD5 signature of a FLAC file.

    Arguments:
        path - path to the FLAC file

    Returns True if the signature matches, and False otherwise.
    '''

    flac = FLAC(path.as_posix())

    ref_md5 = flac.info.md5_signature.to_bytes(length=16, byteorder='big')

    bps = flac.info.bits_per_sample

    if bps in (16, 32):
        codec_args = []
    elif bps == 24:
        codec_args = ['-acodec', 'pcm_s24le']
    else:
        raise RuntimeError('invalid bits-per-sample')

    p_args = _args_template + ['-i', path.as_posix()] + codec_args + ['-f', 'hash', '-hash', 'MD5', '-']

    p = prun(p_args, check=True, capture_output=True, encoding='utf-8')

    output_lines = p.stdout.splitlines()
    if len(output_lines) != 1:
        raise RuntimeError('unexpected ffmpeg output')

    key, value = output_lines[0].rstrip().split('=')
    if key != 'MD5':
        raise RuntimeError('malformed ffmpeg output')

    current_md5 = bytes.fromhex(value)

    return ref_md5 == current_md5


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    parser = ArgumentParser(description='Helper to check MD5 signature of FLAC files.')

    parser.add_argument('-f', '--file', help='FLAC file to check', required=True)

    parsed_args = parser.parse_args()

    if parsed_args.file is not None:
        file = Path(parsed_args.file)

        if not file.is_file():
            print(f'error: invalid input file: {file}', file=sys.stderr)

            return 1

        try:
            result = flac_md5(file)

        except Exception as exc:
            print(f'error: error checking MD5 signature: {exc}', file=sys.stderr)

            return 2

        if not result:
            print('error: MD5 signature invalid', file=sys.stderr)

            return 3

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
