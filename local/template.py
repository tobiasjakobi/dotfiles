#!/usr/bin/env python3
# -*- coding: utf-8 -*-


##########################################################################################
# Imports
##########################################################################################

import os
import sys

from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Any


##########################################################################################
# Constants
##########################################################################################

_my_constant = 'i am a constant'


##########################################################################################
# Internal functions
##########################################################################################

def _internal_function(args: list) -> Any:
    '''
    An internal function. Should not called from the outside.

    Arguments:
        args - argument list for the function
    '''

    return None


##########################################################################################
# Functions
##########################################################################################

def regular_function(args: list) -> int:
    '''
    A regular function. Part of the public API of this Python module

    Arguments:
        args - argument list for the command
    '''

    my_args = [None]

    _internal_function(my_args)

    return 0


##########################################################################################
# Main
##########################################################################################

def main(args: list) -> int:
    if len(args) < 2:
        return 0

    return regular_function(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
