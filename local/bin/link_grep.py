#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from requests import get as rget
from re import compile


##########################################################################################
# Constants
##########################################################################################

_matchwd = compile('https://www\.wdupload\.com/file/[^/]+/[^\"]+\.(mkv|wmv)')


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <URL>', file=sys.stdout)
    print('Extracts download links from a website.', file=sys.stdout)


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])

        return 0

    r = rget(args[1])
    if r.status_code != 200:
        return 1

    for m in _matchwd.finditer(r.text):
        print(m.group(0), file=sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
