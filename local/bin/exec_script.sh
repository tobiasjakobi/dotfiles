#!/bin/bash

source ${HOME}/.bashrc.extern

scriptcmd="${1}"
shift

${scriptcmd} "$@"
