#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
https://docs.python.org/3/howto/curses.html
https://docs.python.org/3/library/curses.html
'''


##########################################################################################
# Imports
##########################################################################################

import subprocess
import sys

from json import load as jload
from time import sleep

import curses


##########################################################################################
# Constants
##########################################################################################

_keymap_translator = {
    'key:space': { 'desc': 'Space', 'value': ord(' ') },
    'key:plus':  { 'desc': 'Plus', 'value': ord('+') },
    'key:minus': { 'desc': 'Minus', 'value': ord('-') },
    'key:a':     { 'desc': 'a', 'value': ord('a') },
    'key:b':     { 'desc': 'b', 'value': ord('b') },
    'key:c':     { 'desc': 'c', 'value': ord('c') },
    'key:d':     { 'desc': 'd', 'value': ord('d') },
    'key:e':     { 'desc': 'e', 'value': ord('e') },
    'key:f':     { 'desc': 'f', 'value': ord('f') },
    'key:g':     { 'desc': 'g', 'value': ord('g') },
    'key:h':     { 'desc': 'h', 'value': ord('h') },
    'key:i':     { 'desc': 'i', 'value': ord('i') },
    'key:j':     { 'desc': 'j', 'value': ord('j') },
    'key:k':     { 'desc': 'k', 'value': ord('k') },
    'key:l':     { 'desc': 'l', 'value': ord('l') },
    'key:m':     { 'desc': 'm', 'value': ord('m') },
    'key:n':     { 'desc': 'n', 'value': ord('n') },
    'key:o':     { 'desc': 'o', 'value': ord('o') },
    'key:p':     { 'desc': 'p', 'value': ord('p') },
    'key:q':     { 'desc': 'q', 'value': ord('q') },
    'key:r':     { 'desc': 'r', 'value': ord('r') },
    'key:s':     { 'desc': 's', 'value': ord('s') },
    'key:t':     { 'desc': 't', 'value': ord('t') },
    'key:u':     { 'desc': 'u', 'value': ord('u') },
    'key:v':     { 'desc': 'v', 'value': ord('v') },
    'key:w':     { 'desc': 'w', 'value': ord('w') },
    'key:x':     { 'desc': 'x', 'value': ord('x') },
    'key:y':     { 'desc': 'y', 'value': ord('y') },
    'key:z':     { 'desc': 'z', 'value': ord('z') },
    'key:down':  { 'desc': 'Down', 'value': curses.KEY_DOWN },
    'key:up':    { 'desc': 'Up', 'value': curses.KEY_UP },
    'key:left':  { 'desc': 'Left', 'value': curses.KEY_LEFT },
    'key:right': { 'desc': 'Right', 'value': curses.KEY_RIGHT },
    'key:f1':    { 'desc': 'F1', 'value': curses.KEY_F1 },
    'key:f2':    { 'desc': 'F2', 'value': curses.KEY_F2 },
    'key:f3':    { 'desc': 'F3', 'value': curses.KEY_F3 },
    'key:f4':    { 'desc': 'F4', 'value': curses.KEY_F4 },
    'key:f5':    { 'desc': 'F5', 'value': curses.KEY_F5 },
    'key:f6':    { 'desc': 'F6', 'value': curses.KEY_F6 },
    'key:f7':    { 'desc': 'F7', 'value': curses.KEY_F7 },
    'key:f8':    { 'desc': 'F8', 'value': curses.KEY_F8 },
    'key:f9':    { 'desc': 'F9', 'value': curses.KEY_F9 },
    'key:f10':   { 'desc': 'F10', 'value': curses.KEY_F10 },
    'key:f11':   { 'desc': 'F11', 'value': curses.KEY_F11 },
    'key:f12':   { 'desc': 'F12', 'value': curses.KEY_F12 },
}


##########################################################################################
# Class definitions
##########################################################################################

class sshpipe:
    def __init__(self, hostname: str):
        ssh_args = ['ssh', hostname, 'bash -s']

        self.ssh_p = subprocess.Popen(ssh_args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding='utf-8')
        sleep(0.2)

        self.pipe_died = False

        try:
            print('echo test', file=self.ssh_p.stdin, flush=True)

        except Exception:
            self.pipe_died = True

    def alive(self):
        if self.pipe_died:
            return False

        if self.ssh_p.poll() != None:
            self.pipe_died = True
            return False
        else:
            return True

    def exec(self, cmd: str):
        print(cmd, file=self.ssh_p.stdin, flush=True)

    def close(self, dump):
        if not self.alive():
            return 0

        self.exec('exit')

        try:
            ret = self.ssh_p.wait(timeout=0.2)

        except subprocess.TimeoutExpired:
            self.ssh_p.terminate()
            ret = -1

        ssh_out = self.ssh_p.stdout.read.splitlines()

        if len(ssh_out) != 0 and dump:
            print('info: ssh output:', file=sys.stdout)
            for line in ssh_out:
                print(line, file=sys.stdout)

        return ret

class cmd_dispatcher:
    def __init__(self, commands, keymap):
        self.dispatcher = dict()

        for key, value in keymap.items():
            if not key in _keymap_translator:
                continue

            if not value in commands:
                continue

            t = _keymap_translator[key]
            c = commands[value]

            self.dispatcher[t['value']] = { 'key_desc': t['desc'], 'desc': value, 'cmd': c }

    def dispatch(self, input, pipe):
        if not input in self.dispatcher:
            return

        cmd = self.dispatcher[input]['cmd']
        pipe.exec(cmd)

    def get_layout(self, layout):
        for arg in self.dispatcher.values():
            layout.append({'action': arg['key_desc'], 'desc': arg['desc']})


##########################################################################################
# Internal functions
##########################################################################################

def _usage(app: str):
    print(f'Usage: {app} <config file>', file=sys.stdout)

def _is_ascii(ch):
    return ch >= 33 and ch <= 126

def _is_ascii_digit(ch):
    return ch >= 48 and ch <= 57

def _mkdigit(ch):
    return ch - 48

def _pipe_selection_menu(win, cfg):
    win.clear()
    win.nodelay(False)

    win.addstr(0, 0, 'Choose a pipe configuration:')

    pipes = dict()

    index = 0
    for key, value in cfg.items():
        x_offset = index + 2
        selection = index + 1

        pipes[selection] = key

        win.addstr(x_offset, 0, f'[{selection}]: {key}')
        index += 1

    win.addstr(x_offset + 2, 0, '[q]: Quit application')

    win.refresh()

    while True:
        ch = win.getch()

        if ch == -1 or not _is_ascii(ch):
            continue

        if _is_ascii_digit(ch):
            digit = _mkdigit(ch)

            if digit in pipes:
                key = pipes[digit]

                return key, cfg[key]
        else:
            input = chr(ch)

            if input == 'q':
                return None, None

def _pipe_menu(win, name, pipe):
    win.nodelay(True)

    hostname = pipe['hostname'];

    p = sshpipe(hostname)
    c = cmd_dispatcher(pipe['commands'], pipe['keymap'])

    layout = []
    c.get_layout(layout)

    layout_y_offset = 14

    while True:
        win.erase()

        win.addstr(0, 0, f'Current pipe selection: {name}')

        x_offset = 2

        win.addstr(x_offset, 1, f'Hostname: {hostname}')
        x_offset += 1
        win.addstr(x_offset, 1, f'Connection state: {p.alive()}')

        x_offset += 2
        for arg in layout:
            win.addstr(x_offset, 0, '[{}]:'.format(arg['action']))
            win.addstr(x_offset, layout_y_offset, arg['desc'])
            x_offset += 1

        win.addstr(x_offset + 1, 0, '[0]:')
        win.addstr(x_offset + 1, layout_y_offset, 'Go back')

        win.refresh()
        sleep(0.1)

        ch = win.getch()

        if ch == -1:
            continue

        if _is_ascii_digit(ch):
            digit = _mkdigit(ch)

            if digit == 0:
                break

        c.dispatch(ch, p)

    p.close(False)

def _curses_main(stdscr, args: list) -> int:
    with open(args[0]) as f:
        json_cfg = jload(f)

    curses.curs_set(0)

    while True:
        name, pipe = _pipe_selection_menu(stdscr, json_cfg)
        if name == None:
            break

        _pipe_menu(stdscr, name, pipe)

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        _usage(args[0])

        return 0

    return curses.wrapper(_curses_main, args[1:])

if __name__ == '__main__':
    sys.exit(main(sys.argv))
