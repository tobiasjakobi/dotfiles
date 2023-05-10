#!/usr/bin/env bash


# References:
#   https://github.com/edisionnano/Screenshare-with-audio-on-Discord-with-Linux
#   https://askubuntu.com/questions/421014/share-an-audio-playback-stream-through-a-live-audio-video-conversation-like-sk

# TODO/FIXME: latency settings are ineffective:
#   pulseaudio[101158]: Configured latency of 10.00 ms is smaller than minimum latency, using minimum instead
#   pulseaudio[101158]: Cannot set requested sink latency of 3.33 ms, adjusting to 250.00 ms
#   pulseaudio[101158]: No remapping configured, proceeding nonetheless!
#   pulseaudio[101158]: Too many underruns, increasing latency to 15.00 ms

function _lm {
  pactl load-module "$@" > /dev/null
}

function _getobj {
  pacmd list | grep -o -E "name: <${1}>" | cut -d'<' -f2 | cut -d'>' -f1
}

function pa_streamsetup {
  local default_output_template='tunnel\.audioserver.*\.local\.alsa_output\.usb-Burr-Brown_from_TI_USB_Audio_DAC-00\.analog-stereo'
  local default_input_template='alsa_input\.pci-0000_08_00\.5-platform-acp_pdm_mach\..*\.stereo-fallback'

  local sink_main="stream_main"
  local sink_sub="stream_sub"

  local default_output
  local default_input
  
  default_output=$(_getobj "${default_output_template}")

  if [[ -z "${default_output}" ]]; then
    echo "error: default output not detected (audioserver not connected?)"
    return 1
  fi

  echo "info: using default output: ${default_output}"

  default_input=$(_getobj "${default_input_template}")

  if [[ -z "${default_input}" ]]; then
    echo "error: default input not detected"
    return 2
  fi

  echo "info: using default input: ${default_input}"

  _lm module-null-sink sink_name="${sink_main}"
  _lm module-null-sink sink_name="${sink_sub}"

  pacmd update-sink-proplist "${sink_main}" device.description="'Main streaming device'"
  pacmd update-sink-proplist "${sink_sub}" device.description="'Sub streaming device'"

  _lm module-loopback latency_msec=10 sink="${sink_sub}" source="${default_input}"
  _lm module-loopback latency_msec=10 sink="${sink_sub}" source="${sink_main}.monitor"
  _lm module-loopback latency_msec=10 sink="${default_output}" source="${sink_main}.monitor" 

  _lm module-remap-source master="${sink_sub}.monitor" source_name=virtmic remix=no

  pacmd update-source-proplist virtmic device.description="'Virtual microphone'"
  
  echo "info: use the..."
  echo " - main streaming device, if you want to stream and hear the streamed audio yourself"
  echo " - sub streaming device, if you just want to stream the audio"
}

pa_streamsetup "$@"
