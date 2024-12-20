#!/usr/bin/env bash

function dispconf {
    local position="1920,0"
    local output

    if [[ -z "${1}" ]]; then
        echo "error: output argument missing"
        return 1
    fi

    output="${1}"

    swaynag --type info --message "External display configuration:" \
            --button-dismiss "FHD (1920x1080)" "wlr-randr --output ${output} --on --pos ${position} --mode 1920x1080@60.000"  \
            --button-dismiss "UHD (3840x2160)" "wlr-randr --output ${output} --on --pos ${position} --mode 3840x2160@59.997"
}

dispconf "$@"
