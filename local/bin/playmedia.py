#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from json import loads as jloads
from os import environ
from os.path import exists
from subprocess import run as prun


##########################################################################################
# Constants
##########################################################################################

'''
Use mpv provided by system.
'''
_player_binary = 'mpv'

_sound_switcher = {
    'drc': ['custom.drc'],
    'downmix': ['custom.downmix'],
}

_decode_switcher = {
    'swdec': ['custom.swdec'],
}

_vout_switcher = {
    'hdmi': ['custom.extern_hdmi'],
    'dp': ['custom.extern_dp'],
}

_extra_switcher = {
    'bigcache': ['custom.bigcache'],
}

'''
Name of the default external output.
'''
_external_output = 'DP-2'


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <media URL> [optional image filename]', file=sys.stdout)

    msg = '''
media URL: e.g. dvd:// or a filename
optional image filename: filename of ISO when using dvd://, dvdnav:// or bd://


External environment variables used:
  mpv_sound  : drc (dynamic range compression)
               downmix (stereo downmix)
  mpv_decode : swdec (software decoding)
  mpv_vout   : hdmi (output on external HDMI)
               dp (output on external DisplayPort)
  mpv_extra  : bigcache (use bigger cache)
  mpv_custom : string is passed unmodified to the mpv options'''

    print(msg, file=sys.stdout)

def _fetch_env(key: str) -> str:
    '''
    Fetch an environment variable.

    Returns None if the variable does not exist.
    '''

    if key in environ:
        return environ[key]

    return None

def _has_active_output(output_name: str) -> bool:
    '''
    Check if we have an active video output.

    Arguments:
        output_name - name of the video output
    '''

    p_args = ['/usr/bin/swaymsg', '--raw', '--type', 'get_outputs']
    p = prun(p_args, check=True, capture_output=True, encoding='utf-8')

    for output in jloads(p.stdout):
        if output['name'] == output_name and output['active']:
            return True

    return False


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])

        return 0

    input = args[1]

    if input.startswith('dvdnav://'):
        input_type = 'dvdnav'
    elif input.startswith('dvdread://'):
        input_type = 'dvdread'
    elif input.startswith('bd://'):
        input_type = 'bluray'
    else:
        input_type = 'other'

    profiles = []

    mpv_sound = _fetch_env('mpv_sound')
    mpv_decode = _fetch_env('mpv_decode')
    mpv_vout = _fetch_env('mpv_vout')
    mpv_extra = _fetch_env('mpv_extra')
    mpv_custom = _fetch_env('mpv_custom')

    if mpv_sound is not None and len(mpv_sound) != 0:
        p = _sound_switcher.get(mpv_sound, None)
        if p is None:
            print(f'warn: unknown sound option: {mpv_sound}', file=sys.stderr)
        else:
            profiles.extend(p)

    if mpv_decode is not None and len(mpv_decode) != 0:
        p = _decode_switcher.get(mpv_decode, None)
        if p is None:
            print(f'warn: unknown decode option: {mpv_decode}', file=sys.stderr)
        else:
            profiles.extend(p)

    if mpv_vout is not None and len(mpv_vout) != 0:
        p = _vout_switcher.get(mpv_vout, None)
        if p is None:
            print(f'warn: unknown vout option: {mpv_vout}', file=sys.stderr)
        else:
            profiles.extend(p)

    if mpv_extra is not None and len(mpv_extra) != 0:
        p = _extra_switcher.get(mpv_extra, None)
        if p is None:
            print(f'warn: unknown extra option: {mpv_extra}', file=sys.stderr)
        else:
            profiles.extend(p)

    if _has_active_output(_external_output):
        print(f'info: using {_external_output} as preferred output')
        profiles.extend(['custom.wayland_extern'])

    config = ['--fs']

    if mpv_custom is not None:
        config.extend(mpv_custom.split())

    if len(profiles) != 0:
        config.append('--profile={0}'.format(','.join(profiles)))

    # Debug:
    #print(config)

    if input_type in ['dvdread', 'dvdnav']:
        if len(args) > 2 and exists(args[2]):
            config.append(f'--dvd-device={args[2]}')
    elif input_type == 'bluray':
        if len(args) > 2 and exists(args[2]):
            config.append(f'--bluray-device={args[2]}')

        mpv_env = environ.copy()
        mpv_env['LIBAACS_PATH'] = 'libmmbd'
        mpv_env['LIBBDPLUS_PATH'] = 'libmmbd'
    else:
        mpv_env = None

    mpv_args = [_player_binary] + config + ['--', input]

    prun(mpv_args, env=mpv_env)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
