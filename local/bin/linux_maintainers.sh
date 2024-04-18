#!/usr/bin/env bash

function linux_maintainers {
  local repo="${HOME}/development/linux-kernel"

  "${repo}/scripts/get_maintainer.pl" --nogit --nogit-fallback --norolestats "$@"
}

linux_maintainers "$@"
