#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from subprocess import run as prun


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <audio file A> <audio file B>', file=sys.stdout)


##########################################################################################
# Internal functions
##########################################################################################

def _hash(filename: str) -> str:
    ffmpeg_args = ['/usr/bin/ffmpeg', '-i', filename, '-f', 'hash', '-hash', 'SHA512', '-']

    p = prun(ffmpeg_args, check=True, capture_output=True, encoding='utf-8')

    output = p.stdout.splitlines()

    if len(output) != 1:
        raise RuntimeError('unexpected ffmpeg output')

    tmp = output[0].rstrip()

    if len(tmp) < 8 or tmp[6] != '=':
        raise RuntimeError('malformed ffmpeg output')

    return tmp[7:]


##########################################################################################
# Functions
##########################################################################################

def audio_compare(first_path: str, second_path: str) -> bool:
    '''
    Compare two audio files.
    
    Arguments:
        first_path  - path to first audio file
        second_path - path to second audio file

    Return True if the two files match, and False otherwise.
    '''

    return _hash(first_path) == _hash(second_path)


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 3:
        _usage(args[0])
        return 0

    return 0 if audio_compare(args[1], args[2]) else -1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
