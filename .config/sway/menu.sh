#!/bin/sh

font="Liberation Sans 16"
white="#ffffff"
black="#000000"
green="#14d711"

bemenu -i --fn "${font}" --prompt="Choose application:" \
  --tb=${white} --tf=${black} --nf=${green} --nb=${black} \
  --hf=${black} --hb=${green} --monitor="all"
