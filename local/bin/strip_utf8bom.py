#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
If the file has a UTF-8 byte order mark (BOM), then strip the BOM.
'''


##########################################################################################
# Imports
##########################################################################################

import sys

from os.path import exists


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <input> [<output>]', file=sys.stdout)

def _is_bom(h: bytes) -> bool:
    return h == b'\xef\xbb\xbf'


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        print('error: missing input argument', file=sys.stderr)
        _usage(args[0])

        return 1

    input = args[1]

    if not exists(input):
        print(f'error: input not found: {input}', file=sys.stderr)

        return 2

    if len(args) < 3:
        output = input + '.noBOM'
    else:
        output = args[2]

    if exists(output):
        print(f'error: output already exists: {output}', file=sys.stderr)

        return 3

    try:
        with open(input, mode='rb') as f:
            header = f.read(3)

            if len(header) == 3:
                strip = _is_bom(header)
                if not strip:
                    print('warn: no UTF8 byte order mark found', file=sys.stderr)
            else:
                strip = False

            with open(output, mode='wb') as g:
                if not strip:
                    g.write(header)

                while True:
                    input_data = f.read()
                    if len(input_data) == 0:
                        break

                    g.write(input_data)

    except Exception as exc:
        print(f'error: failed to write output: {exc}', file=sys.stderr)

        return 4

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
