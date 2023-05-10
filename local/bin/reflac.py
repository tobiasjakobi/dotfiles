#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import basename, exists, isdir, isfile, realpath, join as pjoin
from os import walk
from magic import Magic
from multiprocessing import Pool
from shutil import move
from subprocess import run as prun
from tempfile import TemporaryDirectory

from flac_encode import StandardOutputProtector, flac_encode, is_flac
from vc_copytags import vc_copytags


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <file or directory item> [<another item>...]', file=sys.stdout)

def _recode(input_path: str, verbose: bool):
    '''
    Internal recoding helper.

    Arguments:
        input_path - path to input file
    '''

    if verbose:
        print(f'info: processing: {basename(input_path)}', file=sys.stdout)

    with TemporaryDirectory() as d:
        decoding_output = pjoin(d, 'output.wav')
        temp_output = pjoin(d, 'output.flac')

        decode_args = ['flac', '--decode', '--totally-silent', f'--output-name={decoding_output}', input_path]
        prun(decode_args, check=True, capture_output=True, encoding='utf-8')

        flac_encode(decoding_output, False)

        vc_copytags(input_path, temp_output)

        move(temp_output, input_path)


##########################################################################################
# Functions
##########################################################################################

def reflac(file_path: str, verbose: bool):
    '''
    Recode a single FLAC file.

    Arguments:
        file_path - path to filedirectory
        verbose   - enable verbose output?
    '''

    if not isfile(file_path):
        raise RuntimeError('path is not a file')

    mime = Magic(mime=True)
    if not is_flac(mime, file_path):
        raise RuntimeError('invalid file content (expected FLAC)')

    if verbose:
        print(f'info: recoding file: {file_path}', file=sys.stdout)

    _recode(file_path, verbose=True)

def reflac_dir(directory_path: str, verbose: bool):
    '''
    Recode all FLAC files in a directory.

    Arguments:
        directory_path - path to directorydirectory
        verbose        - enable verbose output?
    '''

    if not isdir(directory_path):
        raise RuntimeError('path is not a directory')

    mime = Magic(mime=True)

    if verbose:
        print(f'info: recoding directory: {directory_path}', file=sys.stdout)

    directory_files = []

    for dirpath, dirnames, filenames in walk(top=directory_path):
        for fn in filenames:
            tmp = pjoin(dirpath, fn)

            if is_flac(mime, tmp):
                directory_files.append(tmp)

    recording_args = [(x, True) for x in directory_files]

    with Pool() as p:
        p.starmap(_recode, recording_args)
        p.close()
        p.join()

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])
        return 0

    recoding_error = False

    with StandardOutputProtector():
        for arg in args[1:]:
            if not exists(arg):
                print(f'warn: skipping non-existing argument: {arg}', file=sys.stderr)
                continue

            path = realpath(arg)

            try:
                if isdir(path):
                    reflac_dir(path, verbose=True)
                elif isfile(path):
                    reflac(path, verbose=True)
                else:
                    raise RuntimeError('invalid argument type')

            except Exception as exc:
                print(f'warn: error occured while recoding: {arg}: {exc}', file=sys.stderr)

                recoding_error = True

    return 1 if recoding_error else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
