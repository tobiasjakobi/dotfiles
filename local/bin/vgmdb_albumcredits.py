#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations


'''
TODOs:
- handle enumerated composers, performers, comments
- merge composer/performer/comment entries
'''


##########################################################################################
# Imports
##########################################################################################

import sys

from argparse import ArgumentParser
from dataclasses import dataclass
from enum import IntEnum, unique
from itertools import pairwise
from pathlib import Path
# TODO: make use of Generic and TypeVar
from typing import Any, Generator, Generic, TypeVar


# TODO: where to put this?
T = TypeVar('T')


##########################################################################################
# Enumerator definitions
##########################################################################################

@unique
class ParsingState(IntEnum):
    '''
    State of the album credits parser.

    SearchingBlock - parser is searching for a new credit block
    BlockFound     - parser is found a credit block
    Done           - parser is done
    '''

    SearchingBlock = 0
    BlockFound     = 1
    Done           = 2

@unique
class LineType(IntEnum):
    '''
    Type of a line of a credit block.

    Artist    - line contains artist information
    Composer  - line contains composer information
    Performer - line contains performer information
    Comment   - line contains comment information
    '''

    Artist    = 0
    Composer  = 1
    Performer = 2
    Comment   = 3


##########################################################################################
# Dataclass definitions
##########################################################################################

@dataclass(frozen=True, repr=False)
class ArtistEntry:
    '''
    An artist credit entry.

    value - the artist name
    '''

    names: list[str]

    @staticmethod
    def make(value: str) -> ArtistEntry:
        '''
        Format an artist entry.

        Arguments:
            value - the artist value
        '''

        names = _split_names(value)
        if not names:
            raise RuntimeError('invalid artist entry')

        return ArtistEntry(names)

    def fixup(self, post_rules: dict[str, str]) -> ArtistEntry:
        '''
        TODO: desc
        '''

        names = self.names.copy()
        for k, v in post_rules.items():
            names[:] = [n.replace(k, v) for n in names]

        return ArtistEntry(names)

    def is_empty(self) -> bool:
        '''
        TODO: desc
        '''

        return len(self.names) == 0

    def __str__(self) -> str:
        pretty = _pretty_names(self.names)

        return f'Artist({repr(pretty)})'

@dataclass(frozen=True, repr=False)
class ComposerEntry:
    '''
    A composer credit entry.

    function - the composer function
    names    - the composer names
    '''

    function: str
    names: list[str]

    keys = (
        'Composer',
        'Lyrics',
        'Music',
        'Lyricist',
    )

    fixup_map = {
        'Composer': 'Music',
        'Lyricist': 'Lyrics',
    }

    def __str__(self) -> str:
        pretty = _pretty_names(self.names) + f' ({self.function})'

        return f'Composer({repr(pretty)})'

    @staticmethod
    def make(value: str, idx: int) -> ComposerEntry:
        '''
        Format a composer entry.

        Arguments:
            value - the composer value
            idx   - index into the composer keys
        '''

        names = _split_names(value)
        if not names:
            raise RuntimeError('invalid composer entry')

        return ComposerEntry(ComposerEntry.keys[idx], names)

    def fixup(self, post_rules: dict[str, str]) -> ComposerEntry:
        '''
        TODO: desc
        '''

        f = ComposerEntry.fixup_map.get(self.function)
        function = self.function if f is None else f

        names = self.names.copy()
        for k, v in post_rules.items():
            names[:] = [n.replace(k, v) for n in names]

        return ComposerEntry(function, names)

    def is_empty(self) -> bool:
        '''
        TODO: desc
        '''

        return len(self.names) == 0

@dataclass(frozen=True, repr=False)
class PerformerEntry:
    '''
    A performer credit entry.

    function - the performer function
    names    - the performer names
    '''

    function: str
    names: list[str]

    keys = (
        '1st Choir',
        '1st Violin',
        '2nd Choir',
        '2nd Violin',
        'Acoustic Guitar',
        'Bass',
        'Cello',
        'Choir',
        'Dizi',
        'Double Bass',
        'Electric Guitar',
        'Erhu',
        'Female Solo Vocals',
        'Guitar',
        'Guzheng',
        'Harp',
        'Harpsichord',
        'Koto',
        'Orchestra',
        'Piano',
        'Pipa',
        'Shakuhachi',
        'Shaoqin',
        'Singer',
        'Steel-Stringed Guitar',
        'Taiko',
        'Tsugaru Shamisen',
        'Viola',
        'Violin',
        'Xiao',
    )

    fixup_map = {
        'Orchestra': '',
        'Choir': '',
    }

    def __str__(self) -> str:
        pretty = _pretty_names(self.names)
        if pretty is None:
            pretty = f'{self.function}:'
        elif self.function is not None:
            pretty += f' ({self.function})'

        return f'Performer({repr(pretty)})'

    @staticmethod
    def make(value: str, idx: int) -> PerformerEntry:
        '''
        Format a performer entry.

        Arguments:
            value - the performer value
            idx   - index into the performer keys
        '''

        return PerformerEntry(PerformerEntry.keys[idx], _split_names(value))

    def fixup(self, post_rules: dict[str, str]) -> PerformerEntry:
        '''
        TODO: desc
        '''

        function = self.function

        f = PerformerEntry.fixup_map.get(function)
        if f is not None:
            is_function_explicit = self.names and all([function in n for n in self.names])

            if is_function_explicit:
                function = None if len(f) == 0 else f

        names = self.names.copy()
        for k, v in post_rules.items():
            names[:] = [n.replace(k, v) for n in names]

        return PerformerEntry(function, names)

    def is_empty(self) -> bool:
        '''
        TODO: desc
        '''

        return len(self.names) == 0

@dataclass(frozen=True, repr=False)
class CommentEntry:
    '''
    A comment credit entry.

    function - the comment function
    names    - the comment names

    The field :function: can be None if this is an unstructured entry.
    Unstructured entries always have a :names: list of length one.
    '''

    function: str
    names: list[str]

    fixup_map = {
        'Mixing Studio': 'Mixing Location',
        'Mastering Studio': 'Mastering Location',
        'Recording Studio': 'Recording Location',
        'Co-produced by': 'Co-Producer',
        'Produced by': 'Producer',
    }

    def __str__(self) -> str:
        pretty = f'{self.function}: {_pretty_names(self.names)}'

        return f'Comment({repr(pretty)})'

    @staticmethod
    def make_unstructed(line: str) -> CommentEntry:
        '''
        Format an unstructured comment entry.

        Arguments:
            line - the comment line
        '''

        # TODO: extend handling

        return CommentEntry(None, [line])

    @staticmethod
    def make(key: str, value: str) -> CommentEntry:
        '''
        Format a (structured) key/value comment entry.

        Arguments:
            key   - the coment key
            value - the comment value
        '''

        return CommentEntry(key, _split_names(value))

    def fixup(self, post_rules: dict[str, str]) -> CommentEntry:
        '''
        TODO: desc
        '''

        if self.function is not None:
            f = CommentEntry.fixup_map.get(self.function)
            function = self.function if f is None else f
        else:
            function = None

        names = self.names.copy()
        for k, v in post_rules.items():
            names[:] = [n.replace(k, v) for n in names]

        return CommentEntry(function, names)

    def is_empty(self) -> bool:
        '''
        TODO: desc
        '''

        return len(self.names) == 0

@dataclass(frozen=True)
class BlockHeader:
    discnumber: int
    tracknumber: int
    trackname: str

    @staticmethod
    def from_line(line: str) -> BlockHeader:
        '''
        TODO: desc
        '''

        try:
            prefix, trackname = line.split(' ', maxsplit=1)

        except ValueError:
            return None

        try:
            first, second = prefix.split('.', maxsplit=1)

            discnumber = int(first)
            tracknumber = int(second)

        except ValueError:
            return None

        if discnumber <= 0 or discnumber >= 30:
            return None

        if tracknumber <= 0 or tracknumber >= 99:
            return None

        return BlockHeader(discnumber, tracknumber, trackname)

    @staticmethod
    def is_header(line: str) -> bool:
        '''
        TODO: desc
        '''

        return BlockHeader.from_line(line) is not None


##########################################################################################
# Class definitions
##########################################################################################

class CreditBlock:
    '''
    TODO: desc
    '''

    _post_fixup_map = {
        'SHANGRI-LA Inc.': 'Shangri-La Inc.',
    }

    _all_caps = (
        'Crescente Studio',
        'MonolithSoft',
        'Onkio Haus',
        'Procyon Studio',
        'Studio Sunshine',
    )

    @staticmethod
    def get_type(line: str) -> tuple[LineType, Any]:
        '''
        Get the type of a line of the credit block.

        Arguments:
            line - the credit block line
        '''

        try:
            key, value = line.split(':', maxsplit=1)

        except ValueError:
            return (LineType.Comment, CommentEntry.make_unstructed(line))

        if key in ('Arranger'):
            return (LineType.Artist, ArtistEntry.make(value.lstrip()))

        try:
            idx = ComposerEntry.keys.index(key)

            return (LineType.Composer, ComposerEntry.make(value.lstrip(), idx))

        except ValueError:
            pass

        try:
            idx = PerformerEntry.keys.index(key)

            return (LineType.Performer, PerformerEntry.make(value.lstrip(), idx))

        except ValueError:
            pass

        return (LineType.Comment, CommentEntry.make(key, value.lstrip()))

    def __init__(self, header: str) -> None:
        '''
        Constructor.

        Arguments:
            header - header line of the credit block
        '''

        self._header = BlockHeader.from_line(header)

        self._artist: list[ArtistEntry] = list()
        self._composer: list[ComposerEntry] = list()
        self._performer: list[PerformerEntry] = list()
        self._comment: list[CommentEntry] = list()

    def __str__(self) -> str:
        '''
        Format credit block as a human-readable string.
        '''

        # TODO: we should use the merged stuff here

        artist = [f'\t{a}' for a in self._artist]
        composer = [f'\t{c}' for c in self._composer]
        performer = [f'\t{p}' for p in self._performer]
        comment = [f'\t{c}' for c in self._comment]

        everything = artist + composer + performer + comment

        return format(self._header) + '\n' + '\n'.join(everything)

    def parse(self, line: str) -> None:
        '''
        TODO: desc
        '''

        line_type, result = CreditBlock.get_type(line)

        if line_type == LineType.Artist:
            self._artist.append(result)
        elif line_type == LineType.Composer:
            self._composer.append(result)
        elif line_type == LineType.Performer:
            self._performer.append(result)
        elif line_type == LineType.Comment:
            self._comment.append(result)
        else:
            raise RuntimeError('not implemented')

    def merge(self) -> None:
        '''
        TODO: desc
        '''

        fixup_map = CreditBlock._post_fixup_map.copy()

        for arg in CreditBlock._all_caps:
            fixup_map[arg.upper()] = arg

        fixed_artist = [a.fixup(fixup_map) for a in self._artist]
        fixed_composer = [c.fixup(fixup_map) for c in self._composer]
        fixed_performer = [p.fixup(fixup_map) for p in self._performer]
        fixed_comment = [c.fixup(fixup_map) for c in self._comment]

        artist_merged = ArtistEntry([name for entry in fixed_artist for name in entry.names])
        self._artist = [artist_merged]

        self._composer = _merge_entries_generic(fixed_composer)
        self._performer = _merge_entries_generic(fixed_performer)
        self._comment = _merge_entries_generic(fixed_comment)

    def get_functions(self, entry_type: Any) -> list[str]:
        '''
        Get the list of functions from this credit block for a given entry type.

        Arguments:
            entry_type - the entry type
        '''

        if entry_type is PerformerEntry:
            functions = [p.function for p in self._performer]
        elif entry_type is ComposerEntry:
            functions = [p.function for p in self._composer]
        elif entry_type is CommentEntry:
            functions = [p.function for p in self._comment]
        else:
            raise RuntimeError(f'invalid entry type: {entry_type}')

        return functions

class AlbumCreditsParser:
    '''
    TODO: desc
    '''

    def __init__(self, lines: list[str]) -> None:
        '''
        Constructor.

        Arguments:
            lines - the album credit lines the parser should work on
        '''

        if lines is None or len(lines) == 0:
            raise RuntimeError('invalid lines argument')

        self._line_storage: list[str] = lines.copy()
        self._state: ParsingState = ParsingState.SearchingBlock
        self._new_block: CreditBlock = None
        self._blocks: list[CreditBlock] = list()

    def __str__(self) -> str:
        '''
        Pretty format the album credits.
        '''

        formatted_blocks = map(format, self._blocks)

        return '\n'.join(formatted_blocks)

    def _consume_line(self) -> str:
        '''
        Consume a line from the line storage and return it.

        If the line storage is empty, None is returned.
        '''

        if len(self._line_storage) == 0:
            return None

        return self._line_storage.pop(0)

    def parse(self) -> bool:
        '''
        TODO: desc
        '''

        if self._state == ParsingState.SearchingBlock:
            current_line = self._consume_line()
            if current_line is None:
                self._state = ParsingState.Done
            elif BlockHeader.is_header(current_line):
                self._state = ParsingState.BlockFound
                self._new_block = CreditBlock(current_line)

            return True

        elif self._state == ParsingState.BlockFound:
            current_line = self._consume_line()
            if current_line is None:
                self._state = ParsingState.Done
            elif len(current_line) == 0:
                self._state = ParsingState.SearchingBlock
                self._blocks.append(self._new_block)
                self._new_block = None
            else:
                self._new_block.parse(current_line)

            return True

        elif self._state == ParsingState.Done:
            if self._new_block is not None:
                self._blocks.append(self._new_block)
                self._new_block = None

            return False

    def merge(self) -> bool:
        '''
        TODO: desc
        '''

        list(map(lambda b: b.merge(), self._blocks))

    def get_functions(self, entry_type: Any) -> list[str]:
        '''
        Get the list of functions from all credit blocks for a given entry type.

        Arguments:
            entry_type - the entry type
        '''

        functions = set()

        list(map(lambda b: functions.update(b.get_functions(entry_type)), self._blocks))

        return list(functions)

##########################################################################################
# Internal Functions
##########################################################################################

def _escaped_split(line: str) -> list[str]:
    '''
    TODO: desc
    '''

    parts: list[str] = list()
    braces_level = 0
    current = list()

    '''
    Trick to remove special-case of trailing chars.
    '''
    tmp = line + ','

    for c in tmp:
        if c == ',' and braces_level == 0:
            parts.append(''.join(current))
            current = list()
        else:
            if c == '(':
                braces_level += 1
            elif c == ')':
                braces_level -= 1

            current.append(c)

    return parts

def _pretty_names(names: list[str]) -> str:
    '''
    TODO: desc
    '''

    if len(names) == 0:
        return None

    if len(names) == 1:
        return names[0]

    return ', '.join(names[0:-1]) + ' and ' + names[-1]

def _split_names(value: str) -> list[str]:
    '''
    TODO: desc
    '''

    if len(value) == 0:
        return list()

    if ',' not in value:
        return [value]

    return list(map(lambda x: x.strip(), _escaped_split(value)))

def _partition_by_entries(entries: list[T], partition_entries: list[T]) -> Generator[list[T]]:
    '''
    TODO: desc
    '''

    if not partition_entries:
        yield entries
    else:
        part_indices = {entries.index(pe) for pe in partition_entries}

        part_indices.add(0)
        part_indices.add(len(entries))

        for i, j in pairwise(sorted(list(part_indices))):
            yield entries[i:j]

def _merge_entries_generic(entries: list[Any]) -> list[Any]:
    '''
    TODO: desc
    '''

    if len(entries) == 0:
        return list()

    entry_type = type(entries[0])

    empty_entries = list(filter(lambda e: e.is_empty(), entries))
    partitions = _partition_by_entries(entries, empty_entries)

    def _merge_by_function(entries: list[entry_type], function: str) -> entry_type:
        '''
        TODO: desc
        '''

        matching_entries = filter(lambda x: x.function == function, entries)

        merged_names = [n for entry in matching_entries for n in entry.names]

        return entry_type(function, merged_names)

    result = list()

    for part in partitions:
        if part[0].is_empty():
            result.append(part[0])
            part_entries = part[1:]
        else:
            part_entries = part

        functions = [e.function for e in part_entries]

        result.extend([_merge_by_function(part_entries, f) for f in functions])

    return result


##########################################################################################
# Functions
##########################################################################################

def vgmdb_albumcredits(path: Path) -> None:
    '''
    Apply VGMdb album credits to FLAC files in a given directory.

    Arguments:
        path - path to the directory which we should process
    '''

    lines = path.read_text(encoding='utf-8').splitlines()

    credits_parser = AlbumCreditsParser(lines)

    while credits_parser.parse():
        pass

    credits_parser.merge()

    #print(credits_parser.get_functions(CommentEntry))

    print(credits_parser, file=sys.stdout)


##########################################################################################
# Main
##########################################################################################

def main(args: list[str]) -> int:
    '''
    Main function.

    Arguments:
        args - list of string arguments from the CLI
    '''

    parser = ArgumentParser(description='Copy VorbisComment and picture metadata.')

    parser.add_argument('-d', '--directory', help='Directory where tags should be applied', required=True)
    parser.add_argument('-c', '--credits-file', help='TODO', required=True)

    parsed_args = parser.parse_args()

    if parsed_args.directory is not None and parsed_args.credits_file is not None:
        directory = Path(parsed_args.directory)
        if not directory.is_dir():
            print(f'error: path is not a directory: {directory}', file=sys.stderr)

            return 1

        credits_file = Path(parsed_args.credits_file)
        if not directory.is_dir():
            print(f'error: path is not a file: {credits_file}', file=sys.stderr)

            return 2

        try:
            vgmdb_albumcredits(credits_file)

        except Exception as exc:
            print(f'error: failed to apply album credits: {exc}', file=sys.stderr)

            return 3

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
