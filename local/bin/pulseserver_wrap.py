#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from argparse import ArgumentParser
from dataclasses import dataclass
from json import loads as jloads
from os import environ, sched_setaffinity
from pathlib import Path
from socket import AF_INET, IPPROTO_TCP, SHUT_RDWR, SOCK_STREAM, gaierror, getaddrinfo, socket
from subprocess import run as prun
from time import time


##########################################################################################
# Constants
##########################################################################################

_pulseaudio_tcp_port = 4713
_config_path_template = Path('~/.config/pulseserver_wrap.conf')
_flatpak_args_template = ('/usr/bin/flatpak', 'run', '--branch=stable', '--arch=x86_64', '--filesystem=home', '--command={0}')
_env_helper_template = Path('~/local/bin/flatpak_env_helper.sh')
_affinity_mask = (0, 2, 4, 6)
_logfile_template = Path('~/local/log')


##########################################################################################
# Dataclass definitions
##########################################################################################

@dataclass(frozen=True)
class ConfigArguments:
    flatpak: bool
    affinity: bool
    print_log: bool
    dxvk_config: str
    args: list[str]


##########################################################################################
# Internal functions
##########################################################################################

def _defer_func(func, *parms, **kwparms):
    def caller():
        func(*parms, **kwparms)

    return caller

def _make_flatpak_args(cmd: str) -> list[str]:
    return [x.format(cmd) for x in _flatpak_args_template]

def _is_server_available(server: str) -> bool:
    '''
    Helper to check if a PulseAudio server is available.

    Arguments:
        server - server to check
    '''

    try:
        addr_infos = getaddrinfo(server, _pulseaudio_tcp_port, proto=IPPROTO_TCP)

    except gaierror:
        return False

    sock_addr = None

    for info in addr_infos:
        if info[0] == AF_INET:
            sock_addr = info[4]
            break

    if sock_addr is None:
        return False

    with socket(AF_INET, SOCK_STREAM) as _s:
        _s.settimeout(2.0)

        server_available = False

        try:
            _s.connect(sock_addr)
            _s.shutdown(SHUT_RDWR)

            server_available = True

        except Exception as exc:
            print(f'warn: error while connecting: {exc}', file=sys.stderr)

    return server_available


##########################################################################################
# Functions
##########################################################################################

def pulseserver_wrap(config_args: ConfigArguments) -> None:
    '''
    Wrapper to launch a process with modified environment if a given
    PulseAudio server is online.

    The server and the cookie are extracted from a config file.
    '''

    if len(config_args.args) == 0:
        raise RuntimeError('missing arguments')

    real_args = config_args.args.copy()

    try:
        config = jloads(_config_path_template.expanduser().read_text(encoding='utf-8'))

    except Exception as exc:
        raise RuntimeError(f'failed to load config: {exc}') from exc

    pulse_server = config.get('pulseserver')
    if pulse_server is None or not isinstance(pulse_server, str):
        raise RuntimeError('invalid config: missing server')

    pulse_cookie = config.get('pulsecookie')
    if pulse_cookie is None or not isinstance(pulse_cookie, str):
        raise RuntimeError('invalid config: missing cookie')

    dxvk_map = config.get('dxvkmap')
    if dxvk_map is None or not isinstance(dxvk_map, dict):
        raise RuntimeError('invalid config: missing DXVK map')

    # TODO: can we validate this some more?

    p_env = None

    if _is_server_available(pulse_server):
        print(f'info: pulse server available: {pulse_server}', file=sys.stdout)

        if p_env is None:
            p_env = environ.copy()

        key_server = 'PULSE_SERVER'
        key_cookie = 'PULSE_COOKIE'

        if config_args.flatpak:
            key_server = 'ENV_' + key_server
            key_cookie = 'ENV_' + key_cookie

        p_env[key_server] = f'tcp:{pulse_server}'
        p_env[key_cookie] = Path(pulse_cookie).expanduser().as_posix()

    if config_args.dxvk_config is not None:
        print(f'info: DXVK config selected: {config_args.dxvk_config}', file=sys.stdout)

        if p_env is None:
            p_env = environ.copy()

        dxvk_config = dxvk_map.get(config_args.dxvk_config)
        if dxvk_config is None:
            raise RuntimeError(f'unknown DXVK config')

        p_env['DXVK_CONFIG_FILE'] = Path(dxvk_config).expanduser()

    if config_args.flatpak:
        print('info: flatpak mode enabled', file=sys.stdout)

        env_helper = _env_helper_template.expanduser()

        logfile_base = 'flatpak'
        real_args = _make_flatpak_args(env_helper) + real_args

    else:
        logfile_base = Path(real_args[0]).name

    if config_args.affinity:
        print('info: fixing core affinity', file=sys.stdout)

        affinity_func = _defer_func(sched_setaffinity, 0, _affinity_mask)
    else:
        affinity_func = None

    logfile_path = _logfile_template.expanduser() / Path(f'{logfile_base}.{int(time())}.log')

    p_named_args = {'env': p_env, 'check': False, 'preexec_fn': affinity_func}

    if not config_args.print_log:
        p_named_args.update({'capture_output': True, 'encoding': 'utf-8'})

    _p = prun(real_args, **p_named_args)

    if not config_args.print_log:
        with open(logfile_path, mode='w', encoding='utf-8') as _f:
            if len(_p.stdout) != 0:
                print(f'info: stdout for: {real_args}', file=_f)
                _f.write(_p.stdout)

            if len(_p.stderr) != 0:
                print(f'info: stderr for: {real_args}', file=_f)
                _f.write(_p.stderr)

    if _p.returncode != 0:
        raise RuntimeError(f'wrapped application failed: {_p.returncode}')


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    '''
    Main function.

    Arguments:
        args - list of string arguments from the CLI
    '''

    parser = ArgumentParser()

    parser.add_argument('-f', '--flatpak', action='store_true', help='Are we wrapping a flatpak application?')
    parser.add_argument('-a', '--affinity', action='store_true', help='Should we set the CPU affinity when launching the application?')
    parser.add_argument('-p', '--print-log', action='store_true', help='Should we print the log of the application?')
    parser.add_argument('-d', '--dxvk-config', help='DXVK config which should be used')

    parsed_args, additional_args = parser.parse_known_args()

    config = ConfigArguments(
        parsed_args.flatpak,
        parsed_args.affinity,
        parsed_args.print_log,
        parsed_args.dxvk_config,
        additional_args,
    )

    try:
        pulseserver_wrap(config)

    except Exception as exc:
        print(f'error: pulseserver wrap failed: {exc}', file=sys.stderr)

        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
