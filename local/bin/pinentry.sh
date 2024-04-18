#!/usr/bin/env bash

function __pinentry {
  local font="Liberation Sans 22"

  local white="#ffffff"
  local black="#000000"
  local green="#14d711"

  /usr/bin/pinentry-bemenu --center --fn="${font}" --monitor="focused" "$@"
}

__pinentry "$@"
