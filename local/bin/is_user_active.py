#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from subprocess import run as prun


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <user>', file=sys.stdout)

def _get_sessions() -> list[int]:
    p_args = ['loginctl', '--no-legend', 'list-sessions']

    p = prun(p_args, check=True, capture_output=True, encoding='utf-8')

    sessions = []

    for arg in p.stdout.splitlines():
        line = arg.rstrip()

        try:
            session_id = int(line.split(' ', maxsplit=1)[0])

        except Exception:
            session_id = -1

        sessions.append(session_id)

    return sessions

def _is_active_x11(id: int, user: str) -> bool:
    p_args = ['loginctl', '--all', 'show-session', str(id)]

    p = prun(p_args, check=True, capture_output=True, encoding='utf-8')

    name = None
    active = None
    type = None

    for arg in p.stdout.splitlines():
        line = arg.rstrip()

        prop, value = line.split('=', maxsplit=1)

        if prop == 'Name':
            name = value
        elif prop == 'Active':
            active = value
        elif prop == 'Type':
            type = value

    if name != user:
        return False

    if active != 'yes':
        return False

    if type not in ('x11', 'wayland'):
        return False

    return True


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])
        return 0

    user = args[1]

    sessions = _get_sessions()

    user_active = False

    for arg in sessions:
        if arg < 0:
            continue

        if _is_active_x11(arg, user):
            user_active = True

    return 0 if user_active else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
