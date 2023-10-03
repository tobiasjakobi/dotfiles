#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from subprocess import DEVNULL, run as prun
from typing import Generator


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <user>', file=sys.stdout)

def _get_sessions() -> list[int]:
    p_args = ('loginctl', '--no-legend', 'list-sessions')

    p = prun(p_args, check=True, stdin=DEVNULL, capture_output=True, encoding='utf-8')

    def _solve(lines: list[str]) -> Generator[int, None, None]:
        for line in lines:
            try:
                tmp, _ = line.rstrip().split(' ', maxsplit=1)
                yield int(tmp)

            except ValueError:
                pass

    return list(_solve(p.stdout.splitlines()))

def _is_active_x11(id: int, user: str) -> bool:
    p_args = ('loginctl', '--all', 'show-session', str(id))

    p = prun(p_args, check=True, stdin=DEVNULL, capture_output=True, encoding='utf-8')

    name = None
    active = None
    type = None

    for line in p.stdout.splitlines():
        try:
            prop, value = line.rstrip().split('=', maxsplit=1)

        except ValueError:
            continue

        if prop == 'Name':
            name = value
        elif prop == 'Active':
            active = value
        elif prop == 'Type':
            type = value

    return name == user and active == 'yes' and type in ('x11', 'wayland')


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    if len(args) < 2:
        _usage(args[0])
        return 0

    user = args[1]

    sessions = _get_sessions()

    if not any(map(lambda s: _is_active_x11(s, user), sessions)):
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
