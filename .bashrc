# /etc/skel/.bashrc
#
# This file is sourced by all *interactive* bash shells on startup,
# including some apparently interactive shells such as scp and rcp
# that can't tolerate any output. So make sure this doesn't display
# anything or bad things will happen!

# set more safe/conservative umask
umask 0027

# import environment variables
source ${HOME}/.environment

# Test for an interactive shell. There is no need to set anything
# past this point for scp and rcp, and it's important to refrain from
# outputting anything in those cases.
if [[ $- != *i* ]]; then
  # Shell is non-interactive. Be done now!
  return
fi

if [[ -n "${SSH_CONNECTION}" ]]; then
  export PS1="\[\e[01;34m\](SSH) ${PS1}"
fi

# Aliases
alias chidori_ssh="ssh -YC -c chacha20-poly1305@openssh.com chidori-bt"
alias dolphin="QT_QPA_PLATFORM=xcb PULSE_SERVER=audioserver dolphin-emu"
alias editor="featherpad --standalone"
alias vvv="${HOME}/local/VirtualVolumesView-1.4.0/vvv-start.sh"

# Load functions
source ${HOME}/.bashrc.extern
