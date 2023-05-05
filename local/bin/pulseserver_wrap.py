#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import socket
import sys

from json import load as jload
from os.path import basename, expandvars, join as pjoin
from os import environ
from subprocess import run as prun
from time import time


##########################################################################################
# Constants
##########################################################################################

_pulseaudio_tcp_port = 4713
_config_path_template = '${HOME}/.config/pulseserver_wrap.conf'
_flatpak_args = ['/usr/bin/flatpak', 'run', '--branch=stable', '--arch=x86_64', '--command=sh']
_schedtool_template = '${HOME}/local/bin/schedtool'
_affinity_settings = '0,2,4,6'
_logfile_template = '${HOME}/local/log'


##########################################################################################
# Internal functions
##########################################################################################

def _is_server_available(server: str) -> bool:
    '''
    Helper to check if a PulseAudio server is available.

    Arguments:
        server - server to check
    '''

    try:
        addr_infos = socket.getaddrinfo(server, _pulseaudio_tcp_port, proto=socket.IPPROTO_TCP)

    except socket.gaierror:
        return False

    sock_addr = None

    for info in addr_infos:
        if info[0] == socket.AF_INET:
            sock_addr = info[4]
            break

    if sock_addr is None:
        return False

    _s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _s.settimeout(2.0)

    server_available = False

    try:
        _s.connect(sock_addr)
        _s.shutdown(socket.SHUT_RDWR)

        server_available = True

    except Exception as exc:
        print(f'warn: error while connecting: {exc}', file=sys.stderr)

    finally:
        _s.close()

    return server_available


##########################################################################################
# Functions
##########################################################################################

def pulseserver_wrap(args: list[str]) -> int:
    '''
    Wrapper to launch a process with modified environment if a given
    PulseAudio server is online.

    The server and the cookie are extracted from a config file.
    '''

    flatpak = False
    affinity = False
    direct = False

    while True:
        if len(args) == 0:
            break

        if args[0] == '--flatpak':
            flatpak = True
        elif args[0] == '--affinity':
            affinity = True
        elif args[0] == '--direct':
            direct = True
        else:
            break

        args = args[1:]

    if len(args) == 0:
        print('error: missing arguments', file=sys.stderr)

        return 1

    try:
        config_path = expandvars(_config_path_template)
        with open(config_path, encoding='utf-8') as _f:
            config = jload(_f)

    except Exception as exc:
        print(f'error: failed to load config: {exc}', file=sys.stderr)

        return 2

    pulse_server = config.get('pulseserver')
    if pulse_server is None or not isinstance(pulse_server, str):
        print('error: invalid config: missing server', file=sys.stderr)

        return 3

    pulse_cookie = config.get('pulsecookie')
    if pulse_cookie is None or not isinstance(pulse_cookie, str):
        print('error: invalid config: missing cookie', file=sys.stderr)

        return 4

    p_env = None

    if _is_server_available(pulse_server):
        print(f'info: pulse server available: {pulse_server}', file=sys.stdout)

        p_env = environ.copy()

        key_server = 'PULSE_SERVER'
        key_cookie = 'PULSE_COOKIE'

        if flatpak:
            key_server = 'ENV_' + key_server
            key_cookie = 'ENV_' + key_cookie

        p_env[key_server] = f'tcp:{pulse_server}'
        p_env[key_cookie] = pulse_cookie

    if flatpak:
        print('info: flatpak mode enabled', file=sys.stdout)

        logfile_base = 'flatpak'
        args = _flatpak_args + args
    else:
        logfile_base = basename(args[0])

    if affinity:
        print('info: fixing core affinity', file=sys.stdout)

        args = [expandvars(_schedtool_template), '-a', _affinity_settings, '-e'] + args

    logfile_path = pjoin(expandvars(_logfile_template), f'{logfile_base}.{int(time())}.log')

    if direct:
        _p = prun(args, env=p_env, check=False)
    else:
        _p = prun(args, env=p_env, check=False, capture_output=True, encoding='utf-8')

        with open(logfile_path, mode='w', encoding='utf-8') as _f:
            if len(_p.stdout) != 0:
                print(f'info: stdout for: {args}', file=_f)
                _f.write(_p.stdout)

            if len(_p.stderr) != 0:
                print(f'info: stderr for: {args}', file=_f)
                _f.write(_p.stderr)

    return _p.returncode


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    '''
    Main function.
    '''

    return pulseserver_wrap(args[1:])

if __name__ == '__main__':
    sys.exit(main(sys.argv))
