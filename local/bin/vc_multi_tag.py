#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Add a list of tag values (for a single tag, e.g. 'title') to
a list of FLAC files (VorbisComment).
'''


##########################################################################################
# Imports
##########################################################################################

import sys

from argparse import ArgumentParser
from pathlib import Path
from subprocess import run as prun
from tempfile import TemporaryDirectory

from vc_addtag import TagEntry, vc_addtag


##########################################################################################
# Constants
##########################################################################################

_editor = '/usr/bin/featherpad'


##########################################################################################
# Functions
##########################################################################################

def vc_multi_tag(path: Path, tag_key: str) -> int:
    '''
    Apply multiple tag values to FLAC files in a given directory.

    Arguments:
        path    - path to the directory which we should process
        tag_key - key of the tag

    This open an editor where the user can enter tag values. Each line
    is a single tag value. After the editor is closed, the values
    (v_1, ..., v_N) are collected and applied to the files in the
    directory.

    I.e. the tag (tag_key, v_i) is applied to the file f_i.
    '''

    if not path.is_dir():
        raise RuntimeError(f'path is not a directory: {path}')

    if tag_key is None or len(tag_key) == 0:
        raise RuntimeError(f'invalid tag key: {tag_key}')

    candidates = list(path.glob('*.flac'))

    with TemporaryDirectory(prefix='/tmp/') as tmp:
        input_path = Path(tmp) / Path('input.txt')

        prun([_editor, '--standalone', input_path.as_posix()], check=True)

        tag_values = input_path.read_text(encoding='utf-8').splitlines()

    if len(candidates) != len(tag_values):
        raise RuntimeError(f'list size mismatch: {len(candidates)}: {len(tag_values)}')

    [vc_addtag(cand, [TagEntry(tag_key, val)]) for cand, val in zip(sorted(candidates), tag_values)]


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    '''
    Main function.

    Arguments:
        args - list of string arguments from the CLI
    '''

    parser = ArgumentParser(description='Copy VorbisComment and picture metadata.')

    parser.add_argument('-d', '--directory', help='Directory where tags should be applied')
    parser.add_argument('-t', '--tag-key', help='Key of the tag', required=True)

    parsed_args = parser.parse_args()

    if parsed_args.tag_key is not None:
        if parsed_args.directory is None:
            work_dir = Path.cwd()

            print(f'info: using current directory: {work_dir.name}', file=sys.stdout)
        else:
            work_dir = Path(parsed_args.directory)

    try:
        vc_multi_tag(work_dir, parsed_args.tag_key)

    except Exception as exc:
        print(f'error: failed to multi tag: {work_dir.name}: {exc}', file=sys.stderr)

        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
