#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import basename, dirname, exists, isdir, join as pjoin
from os import rename, walk


##########################################################################################
# Constants
##########################################################################################

'''
Tuple of characters that are not allowed in VFAT filenames.
'''
_reserved_chars = ('<', '>', ':', '"', '/', '\\', '|', '?', '*')

'''
Character used to replace non-allowed chars.
'''
_replacement_char = '_'


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <directory> [<another directory>...]', file=sys.stdout)


##########################################################################################
# Functions
##########################################################################################

def sanitize_vfat(name: str) -> str:
    '''
    Sanitize a name for a VFAT filesystem.

    Arguments:
        name - name to sanitize
    '''

    for r in _reserved_chars:
        name = name.replace(r, _replacement_char)

    return name

def rename_vfat(file_path: str):
    '''
    Rename a file so it becomes suitable for a VFAT filesystem.

    Arguments:
        file_path - path to file which should be renamed
    '''

    base_original = basename(file_path)
    dir_original = dirname(file_path)
    base_sanitized = sanitize_vfat(base_original)

    if base_original == base_sanitized:
        return

    sanitized_path = pjoin(dir_original, base_sanitized)

    if exists(sanitized_path):
        print(f'warn: sanitized version exists: {base_original}', file=sys.stdout)
        return

    print(f'info: sanitizing: {base_original} -> {base_sanitized}')

    rename(file_path, sanitized_path)

def rename_vfat_dir(directory_path: str):
    '''
    Rename the file contents of a directory, so that they
    become suitable for a VFAT filesystem.

    Arguments:
        directory_path - path to directory which should be processed
    '''

    if not isdir(directory_path):
        raise RuntimeError('path is not a directory')

    for dirpath, dirnames, filenames in walk(top=directory_path):
        for fn in filenames:
            rename_vfat(pjoin(dirpath, fn))


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])
        return 0

    rename_error = False

    for arg in args[1:]:
        try:
            rename_vfat_dir(arg)

        except Exception as exc:
            print(f'warn: error occured while renaming: {arg}: {exc}', file=sys.stderr)

            rename_error = True

    return 1 if rename_error else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
