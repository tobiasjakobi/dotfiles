#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from dataclasses import dataclass
from magic import Magic
from os.path import abspath, basename, isdir, isfile, join as pjoin
from subprocess import run as prun
from xml.dom.minidom import parseString as xml_parse

from id3_addtag import is_mp3, addtag as id3_addtag
from mp4_addtag import addtag as mp4_addtag
from vc_addtag import addtag as vc_addtag


##########################################################################################
# Constants
##########################################################################################

_bs1770_template = [
    '/usr/bin/bs1770gain',
    '--integrated',
    '--range',
    '--truepeak',
    '--ebu',
    '--suppress-progress',
    '--xml'
]


##########################################################################################
# Class definitions
##########################################################################################

@dataclass(frozen=True)
class _R128Tuple:
    gain: str
    peak: str
    range: str


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <directory>', file=sys.stdout)
    print('bs1770gain wrapper for tagging audio files in a directory.', file=sys.stdout)

def _mk_tuple(track) -> _R128Tuple:
    for arg in track.childNodes:
        if arg.nodeName == 'integrated':
            integrated = arg
        elif arg.nodeName == 'range':
            range = arg
        elif arg.nodeName == 'true-peak':
            truepeak = arg

    return _R128Tuple(
        gain = integrated.getAttribute('lu'),
        peak = truepeak.getAttribute('amplitude'),
        range = range.getAttribute('lra')
    )


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    mime = Magic(mime=True)

    if len(args) < 2:
        print('error: missing directory argument', file=sys.stderr)
        _usage(args[0])

        return 1

    input = args[1]

    if not isdir(input):
        print(f'error: directory not found: {input}', file=sys.stderr)

        return 2

    root = abspath(input)

    p_args = _bs1770_template + [root]

    try:
        p = prun(p_args, check=True, capture_output=True, encoding='utf-8')

        dom_tree = xml_parse(p.stdout)
        for n in dom_tree.childNodes:
            if n.nodeName == 'bs1770gain':
                main_node = n

        for n in main_node.childNodes:
            if n.nodeName == 'album' and n.getAttribute('folder') == basename(root):
                album_node = n

        tracks = album_node.getElementsByTagName('track')
        summary = main_node

    except Exception as exc:
        print(f'error: bs1770gain XML parsing failed: {exc}', file=sys.stderr)

        return 3

    try:
        album_info = _mk_tuple(summary)

    except Exception as exc:
        print(f'error: bs1770gain album summary missing: {exc}', file=sys.stderr)

        return 4

    for track in tracks:
        if not track.hasAttribute('file'):
            print('warn: skipping track with missing file attribute', file=sys.stderr)

            continue

        track_info = _mk_tuple(track)
        filename = track.getAttribute('file')

        abs_file = pjoin(root, filename)

        if not isfile(abs_file):
            print(f'warn: skipping non-existing file: {abs_file}', file=sys.stderr)

            continue

        file_type = mime.from_file(abs_file)

        func_args = [
            abs_file,
            '--replaygain_algorithm=EBU R128',
            '--replaygain_reference_loudness=-23.00 LUFS',
            f'--replaygain_track_gain={track_info.gain} dB',
            f'--replaygain_track_peak={track_info.peak}',
            f'--replaygain_track_range={track_info.range} dB',
            f'--replaygain_album_gain={album_info.gain} dB',
            f'--replaygain_album_peak={album_info.peak}',
            f'--replaygain_album_range={album_info.range} dB',
        ]

        if file_type in ('video/mp4', 'audio/x-m4a'):
            func = mp4_addtag
        elif file_type in ('audio/ogg', 'audio/flac'):
            func = vc_addtag
        elif file_type == 'audio/mpeg':
            func = id3_addtag
        elif is_mp3(abs_file):
            func = id3_addtag
        else:
            print(f'warn: skipping file with unsupported type: {abs_file}: {file_type}', file=sys.stderr)

            continue

        ret = func(func_args)
        if ret != 0:
            print(f'error: failed to write tags: {abs_file}: {ret}', file=sys.stderr)

            continue

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
