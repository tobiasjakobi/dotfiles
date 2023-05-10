#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import basename, exists, isdir, isfile, realpath, splitext, join as pjoin
from os import walk
from magic import Magic
from multiprocessing import Pool
from shutil import move
from subprocess import run as prun
from tempfile import TemporaryDirectory
from termios import TCSADRAIN, tcgetattr, tcsetattr, error as termios_err

from audio_compare import audio_compare


##########################################################################################
# Constants
##########################################################################################

'''
Distance between seekpoints that are placed in newly encoded FLAC files.
'''
_seekpoint_distance = '25s'


##########################################################################################
# Class definitions
##########################################################################################

class StandardOutputProtector:
    '''
    Context manager that protects the standard output from changes.
    '''

    def __init__(self):
        self._stdout_fd = sys.stdout.fileno()

        try:
            self._stdout_attr = tcgetattr(self._stdout_fd)

        except termios_err:
            self._stdout_attr = None

    def __enter__(self):
        return None

    def __exit__(self, type, value, traceback):
        if self._stdout_attr is not None:
            tcsetattr(self._stdout_fd, TCSADRAIN, self._stdout_attr)


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <file or directory item> [<another item>...]', file=sys.stdout)

def _encode(input_path: str, verbose: bool):
    '''
    Internal encoding helper.

    Arguments:
        input_path - path to input file
        verbose    - enable verbose output?
    '''

    input_base, input_ext = splitext(input_path)
    output = f'{input_base}.flac'

    if exists(output):
        raise RuntimeError(f'output file already exists: {output}')

    if verbose:
        print(f'info: processing: {basename(input_path)}', file=sys.stdout)

    with TemporaryDirectory() as d:
        temp_output = pjoin(d, 'output.flac')
        reference_output = pjoin(d, 'reference.wav')

        flake_args = ['flake', '-q', '-12', input_path, '-o', temp_output]
        prun(flake_args, check=True, capture_output=True, encoding='utf-8')

        decode_args = ['flac', '--decode', '--silent', f'--output-name={reference_output}', temp_output]
        prun(decode_args, check=True, capture_output=True, encoding='utf-8')

        if not audio_compare(input_path, reference_output):
            raise RuntimeError('mismatch between original source and reference decoding')

        '''
        flake doesn't add a seektable by default, so add one here.
        '''
        seekpoint_args = ['metaflac', f'--add-seekpoint={_seekpoint_distance}', temp_output]
        prun(seekpoint_args, check=True, capture_output=True, encoding='utf-8')

        move(temp_output, output)


##########################################################################################
# Functions
##########################################################################################

def is_wav(m: Magic, file_path: str) -> bool:
    '''
    Simple helper to check if a file is WAV.

    Arguments:
        m         - magic object to check MIME type
        file_path - path of the file to check
    '''

    if not file_path.endswith('.wav'):
        return False

    if m.from_file(file_path) != 'audio/x-wav':
        return False

    return True

def is_flac(m: Magic, file_path: str) -> bool:
    '''
    Simple helper to check if a file is FLAC.

    Arguments:
        m         - magic object to check MIME type
        file_path - path of the file to check
    '''

    if not file_path.endswith('.flac'):
        return False

    if m.from_file(file_path) != 'audio/flac':
        return False

    return True

def flac_encode(file_path: str, verbose: bool):
    '''
    Encode a single WAV file to FLAC.

    Arguments:
        file_path - path to file
        verbose   - enable verbose output?

    Encoding is done using the flake encoder. After encoding the resulting file is decoded
    with the reference decoder and compared against the original file.
    '''

    if not isfile(file_path):
        raise RuntimeError('path is not a file')

    mime = Magic(mime=True)
    if not is_wav(mime, file_path):
        raise RuntimeError('invalid file content (expected WAV)')

    if verbose:
        print(f'info: encoding file: {file_path}', file=sys.stdout)

    _encode(file_path, False)

def flac_encode_dir(directory_path: str, verbose: bool):
    '''
    Encode all WAV files in a directory to FLAC.

    Arguments:
        directory_path - path to directory
        verbose        - enable verbose output?
    '''

    if not isdir(directory_path):
        raise RuntimeError('path is not a directory')

    mime = Magic(mime=True)

    if verbose:
        print(f'info: encoding directory: {directory_path}', file=sys.stdout)

    directory_files = []

    for dirpath, dirnames, filenames in walk(top=directory_path):
        for fn in filenames:
            tmp = pjoin(dirpath, fn)

            if is_wav(mime, tmp):
                directory_files.append(tmp)

    encoding_args = [(x, True) for x in directory_files]

    with Pool() as p:
        p.starmap(_encode, encoding_args)
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

    encoding_error = False

    with StandardOutputProtector():
        for arg in args[1:]:
            if not exists(arg):
                print(f'warn: skipping non-existing argument: {arg}', file=sys.stderr)
                continue

            path = realpath(arg)

            try:
                if isdir(path):
                    flac_encode_dir(path, True)
                elif isfile(path):
                    flac_encode(path, True)
                else:
                    raise RuntimeError('invalid argument type')

            except Exception as exc:
                print(f'warn: error occured while encoding: {arg}: {exc}', file=sys.stderr)

                encoding_error = True

    return 1 if encoding_error else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
