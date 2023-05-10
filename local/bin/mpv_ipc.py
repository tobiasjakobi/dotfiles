#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from io import StringIO
from json import loads as jloads, dumps as jdumps
from os.path import exists
from random import seed, randint
from socket import AF_UNIX, SOCK_STREAM, SHUT_WR, SHUT_RD, socket


##########################################################################################
# Constants
##########################################################################################

_mpv_ctrl = '/tmp/mpv.control'


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        print('error: missing command argument', file=sys.stderr)

        return 1

    seed()

    if not exists(_mpv_ctrl):
        print(f'error: mpv control socket not found: {_mpv_ctrl}', file=sys.stderr)

        return 2

    sock = socket(AF_UNIX, SOCK_STREAM)

    try:
        sock.connect(_mpv_ctrl)

    except OSError as msg:
        sock.close()
        print(f'error: failed to connect to socket: {msg}', file=sys.stderr)

        return 3

    req_id = randint(0, 1024)

    mpv_cmd = {
        'command': args[1:],
        'request_id': req_id,
    }

    json_out = jdumps(mpv_cmd) + '\n'

    try:
        sock.sendall(json_out.encode('utf-8'))

    except OSError as msg:
        sock.close()
        print(f'error: failed to send data to socket: {msg}', file=sys.stderr)

        return 4

    sock.shutdown(SHUT_WR)

    try:
        bytes = sock.recv(2048)

    except OSError as msg:
        ssock.close()
        print(f'error: failed to receive data from socket: {msg}', file=sys.stderr)

        return 5

    sock.shutdown(SHUT_RD)
    sock.close()

    reply = StringIO(bytes.decode('utf-8'))

    for arg in reply.read().splitlines():
        json_in = jloads(arg)

        if json_in.get('request_id') == req_id:
            print('reply: {0}'.format(json_in['error']), file=sys.stdout)

    reply.close()

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
