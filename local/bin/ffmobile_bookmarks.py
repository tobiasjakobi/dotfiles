#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import sys

from csv import reader as creader
from subprocess import run as prun

'''
Fetch Firefox bookmarks dump via SSH and format everything into a simple HTML list.
'''


##########################################################################################
# Constants
##########################################################################################

_html_header = '''<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">\n
<html>\n\t<head>\n\t\t<meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\">\n
\t\t<title>FireFox mobile bookmarks</title>\n\t</head>\n\t<body>'''

_html_footer = '\t\t<br>\n\t</body>\n</html>'

_bookmarks_dump = '/storage/emulated/0/Misc/ff_bookmarks.dump'

_ssh_args = ['/usr/bin/ssh', 'moto-g4', f'cat {_bookmarks_dump}']


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    p = prun(_ssh_args, check=True, capture_output=True, encoding='utf-8')

    bookmarks = []

    for arg in p.stdout.splitlines():
        bookmark_raw = arg.rstrip().split(' VALUES(', 1)

        if len(bookmark_raw) <= 1 or bookmark_raw[0] != 'INSERT INTO \"bookmarks\"':
            continue

        csv_data = bookmark_raw[1].rstrip(');')

        for row in creader([csv_data], quotechar='\''):
            bookmarks.append((row[1], row[2]))

    print(_html_header, file=sys.stdout)

    for x, y in bookmarks:
        print(f'\t\t<a target=\"_blank\" href=\"{y}\">{x}</a><br>', file=sys.stdout)

    print(html_footer, file=sys.stdout)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
