#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from getopt import getopt, GetoptError
from os.path import isdir, isfile, splitext
from os import walk


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} [--remove] --link-list <file> --directory <dir>', file=sys.stdout)


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    link_list = None
    directory = None
    remove_lines = False

    getopt_largs = ['help', 'remove', 'link-list=', 'directory=']

    try:
        opts, oargs = getopt(args[1:], 'hrl:d:', getopt_largs)

    except GetoptError as err:
        print(f'error: getopt parsing failed: {err}' , file=sys.stderr)
        _usage(args[0])

        return 1

    for o, a in opts:
        if o in ('-h', '--help'):
            _usage(args[0])

            return 0
        elif o in ('-l', '--link-list'):
            if not isfile(a):
                print(f'error: invalid link-list: {a}', file=sys.stderr)

                return 1

            link_list = a
        elif o in ('-d', '--directory'):
            if isdir(a):
                print(f'error: invalid directory: {a}', file=sys.stderr)

                return 2

            directory = a
        elif o in ('-r', '--remove'):
            remove_lines = True
        else:
            raise RuntimeError('unhandled options')

    if link_list is None:
        print('error: no link-list given', file=sys.stderr)

        return 4

    if directory is None:
        print('error: no directory given', file=sys.stderr)

        return 5

    prefixes = []
    filelist = []

    for dp, dn, fn in walk(directory):
        filelist += fn

    for file in filelist:
        filesplit = splitext(file)

        ext_switcher = {
            '.jpeg': False,
            '.mkv': True,
            '.mp4': True,
            '.wmv': True,
            '.avi': True
        }

        if len(filesplit) != 2:
            print(f'warn: skipping file with no extension: {file}', file=sys.stderr)

            continue

        fileext = ext_switcher.get(filesplit[1], None)

        if fileext is None:
            print(f'warn: skipping file with unknown extension: {file}', file=sys.stderr)

            continue

        file_components = file.split('.')

        if len(file_components) < 2:
            print(f'warn: skipping file with unknown formatting: {file}', file=sys.stder)

            continue

        prefixes.append(file_components[0])

    prefix_set = set(prefixes)

    if remove_lines:
        output_lines = []

        with open(link_list) as f:
            for links in f.read().splitlines():
                found = False

                for arg in prefix_set:
                    if links.find(arg) != -1:
                        found = True
                        break

                if not found:
                    output_lines.append(links)

        with open(link_list, mode='w') as f:
            map(lambda x: print(x, file=f), output_lines)

    else:
        print('info: the following lines can be removed from the link-list:', file=sys.stdout)

        lineidx = 0

        with open(link_list) as f:
            for links in f.readlines():
                lineidx += 1

                for arg in prefix_set:
                    if links.find(arg) != -1:
                        print(f'{lineidx}: {links.strip()}', file=sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
