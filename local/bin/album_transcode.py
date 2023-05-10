#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import basename, isdir, realpath, splitext, join as pjoin
from os import makedirs, walk
from magic import Magic
from multiprocessing import Pool
from subprocess import CalledProcessError, run as prun

from flac_encode import StandardOutputProtector, is_flac
from rename_vfat import sanitize_vfat


##########################################################################################
# Constants
##########################################################################################

_default_output = '/mnt/storage/transfer/fiio'


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} [--tmpfs] <album directory> [<more album dirs>...]', file=sys.stdout)


##########################################################################################
# Constants
##########################################################################################

'''
Ogg Vorbis encoding quality.
'''
_quality = 5.0


##########################################################################################
# Internal functions
##########################################################################################

def _transcode(input_path: str, output_path: str):
    '''
    Internal transcode helper.

    Arguments:
        input_path  - path of the input file
        output_path - path of the output file
    '''

    print(f'info: processing: {basename(input_path)}', file=sys.stdout)

    p_args = [
        'oggenc',
        '--quiet',
        f'--quality={_quality}',
        f'--output={output_path}',
        input_path
    ]

    try:
        p = prun(p_args, check=True, capture_output=True, encoding='utf-8')

    except CalledProcessError as err:
        print(f'warn: transcoding failed: {input_path}: {err}')
        print(err.stdout)

def _mk_output_directory(prefix: str, name: str) -> str:
    '''
    Make and create output directory.

    Arguments:
        prefix - prefix for path
        name   - name of the album
    '''

    base_original = basename(realpath(name))
    base_sanitized = sanitize_vfat(base_original)

    output_dir = pjoin(prefix, base_sanitized.replace('(FLAC)', '(Vorbis)'))

    makedirs(output_dir)

    return output_dir

def _mk_output_path(prefix: str, name: str) -> str:
    '''
    Make output path for an album file.

    Arguments:
        prefix - prefix for path
        name   - name of the album file
    '''

    base_original = basename(name)
    base_root, _ = splitext(base_original)

    base_sanitized = f'{sanitize_vfat(base_root)}.ogg'

    return pjoin(prefix, base_sanitized)


##########################################################################################
# Functions
##########################################################################################

def album_transcode(tmpfs: bool, album_path: str):
    '''
    Transcode FLAC album to Ogg Vorbis.

    Arguments:
        tmpfs      - use tmpfs as output
        album_path - path of the album
    '''

    if not isdir(album_path):
        raise RuntimeError('album path is not a directory')

    mime = Magic(mime=True)

    output_dir = _mk_output_directory('/tmp' if tmpfs else _default_output, album_path)

    print(f'info: transcoding album: {album_path} -> {output_dir}', file=sys.stdout)

    album_files = []

    for dirpath, dirnames, filenames in walk(top=album_path):
        for fn in filenames:
            tmp = pjoin(dirpath, fn)

            if is_flac(mime, tmp):
                album_files.append(tmp)

    transcoding_args = [(x, _mk_output_path(output_dir, x)) for x in album_files]

    with Pool() as p:
        p.starmap(_transcode, transcoding_args)
        p.close()
        p.join()

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    transcode_error = False

    if len(args) < 2:
        _usage(args[0])
        return 0

    use_tmpfs = False

    if args[1] == '--tmpfs':
        if len(args) < 3:
            _usage(args[0])
            return 0

        use_tmpfs = True
        albums = args[2:]
    else:
        albums = args[1:]

    with StandardOutputProtector():
        for album in albums:
            try:
                album_transcode(use_tmpfs, album)

            except Exception as exc:
                print(f'warn: error occured while transcoding: {album}: {exc}', file=sys.stderr)

                transcode_error = True

        return 1 if transcode_error else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
