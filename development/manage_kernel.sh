#!/usr/bin/env bash

declare -r __version="6.13.y"

declare -r __push_remote="github-linux"

declare -r __upstream_remote="stable"
declare -r __upstream_branch="linux-${__version}"
declare -r __downstream_prefix="tjakobi-${__version}"

declare -r -a __downstream_components=(
    "amd-tsc"
    "amdgpu-color"
    "ayaneo-fanctrl"
    "dellg5-amdgpu"
    "misc"
    "rockchip-aw87xxx"
    "winesync"
)

function __get_merge_base {
    local head_commit
    local merge_base
    local merge_heads

    IFS=' ' read head_commit merge_base merge_heads <<<$(git -C "${1}" rev-list --parents --max-count=1 HEAD)

    echo "${merge_base}"
}

function __push_branches {
    local kernel_dir
    local errcode

    if [[ -z "${1}" ]]; then
        echo "error: missing kernel directory argument"

        return 1
    fi

    if [[ ! -d "${1}" ]]; then
        echo "error: invalid kernel directory argument: ${1}"

        return 2
    fi

    kernel_dir="${1}"

    for entry in "${__downstream_components[@]}"; do
        git -C "${kernel_dir}" checkout --quiet "${__downstream_prefix}/${entry}"
        errcode=$?

        if [[ $errcode -ne 0 ]]; then
            echo "error: failed to checkout: ${__downstream_prefix}/${entry}: ${errcode}"

            return 3
        fi

        git -C "${kernel_dir}" push --force "${__push_remote}"
        errcode=$?

        if [[ $errcode -ne 0 ]]; then
            echo "error: failed to push: ${__downstream_prefix}/${entry}: ${errcode}"

            return 4
        fi
    done
}

function __rebase_and_create_patch {
    local kernel_dir
    local merge_names=()
    local merge_base
    local errcode

    if [[ -z "${1}" ]]; then
        echo "error: missing kernel directory argument"

        return 1
    fi

    if [[ ! -d "${1}" ]]; then
        echo "error: invalid kernel directory argument: ${1}"

        return 2
    fi

    kernel_dir="${1}"

    git -C "${kernel_dir}" fetch "${__upstream_remote}"

    for entry in "${__downstream_components[@]}"; do
        git -C "${kernel_dir}" checkout --quiet "${__downstream_prefix}/${entry}"
        errcode=$?

        if [[ $errcode -ne 0 ]]; then
            echo "error: failed to checkout: ${__downstream_prefix}/${entry}: ${errcode}"

            return 3
        fi

        git -C "${kernel_dir}" branch --set-upstream-to "${__upstream_remote}/${__upstream_branch}"
        git -C "${kernel_dir}" rebase --quiet "${__upstream_remote}/${__upstream_branch}"
        errcode=$?

        if [[ $errcode -ne 0 ]]; then
            echo "error: failed to rebase: ${__downstream_prefix}/${entry}: ${errcode}"

            return 4
        fi
    done

    git -C "${kernel_dir}" branch --delete --force "${__downstream_prefix}/merged"

    git -C "${kernel_dir}" checkout -b "${__downstream_prefix}/merged" "${__upstream_remote}/${__upstream_branch}"
    errcode=$?

    if [[ $errcode -ne 0 ]]; then
        echo "error: failed to checkout: merged: ${errcode}"

        return 5
    fi

    for entry in "${__downstream_components[@]}"; do
        merge_names+=("${__downstream_prefix}/${entry}")
    done

    git -C "${kernel_dir}" merge --quiet --no-ff --no-edit ${merge_names[@]}
    errcode=$?

    if [[ $errcode -ne 0 ]]; then
        echo "error: failed to merge: ${errcode}"

        return 6
    fi

    merge_base=$(__get_merge_base "${kernel_dir}")

    git -C "${kernel_dir}" format-patch --stdout "${merge_base}" > "${kernel_dir}/${__downstream_prefix}-full.patch"
    errcode=$?

    if [[ $errcode -ne 0 ]]; then
        echo "error: failed to format patch: ${errcode}"

        return 7
    fi
}

function manage_kernel {
    local operation_mode

    if [[ -z "${1}" ]]; then
        echo "error: missing operation mode argument"

        return 1
    fi

    operation_mode="${1}"
    shift

    case "${operation_mode}" in
        "--rebase" )
            __rebase_and_create_patch "$@" ;;

        "--push" )
            __push_branches "$@" ;;

        * )
            echo "Usage: ${FUNCNAME} --rebase|--push <directory>" ;;
    esac
}

manage_kernel "$@"
