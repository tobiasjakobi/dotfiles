#!/usr/bin/env bash

function _get_merge_base {
    local head_commit
    local merge_base
    local merge_heads

    IFS=' ' read head_commit merge_base merge_heads <<<$(git -C "${1}" rev-list --parents --max-count=1 HEAD)

    echo "${merge_base}"
}

function manage_kernel {
    local version="6.8.y"

    local upstream_remote="stable"
    local upstream_branch="linux-${version}"
    local downstream_prefix="tjakobi-${version}"

    local downstream_components=("dellg5-amdgpu" "futex-waitv" "misc" "tcp-timewait" "amd-tsc" "winesync" "ayaneo-display" "amdgpu-color")

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

    git -C "${kernel_dir}" fetch "${upstream_remote}"

    for entry in "${downstream_components[@]}"; do
        git -C "${kernel_dir}" checkout --quiet "${downstream_prefix}/${entry}"
        errcode=$?

        if [[ $errcode -ne 0 ]]; then
            echo "error: failed to checkout: ${downstream_prefix}/${entry}: ${errcode}"

            return 3
        fi

        git -C "${kernel_dir}" branch --set-upstream-to "${upstream_remote}/${upstream_branch}"
        git -C "${kernel_dir}" rebase --quiet "${upstream_remote}/${upstream_branch}"
        errcode=$?

        if [[ $errcode -ne 0 ]]; then
            echo "error: failed to rebase: ${downstream_prefix}/${entry}: ${errcode}"

            return 4
        fi
    done

    git -C "${kernel_dir}" branch --delete --force "${downstream_prefix}/merged"

    git -C "${kernel_dir}" checkout -b "${downstream_prefix}/merged" "${upstream_remote}/${upstream_branch}"
    errcode=$?

    if [[ $errcode -ne 0 ]]; then
        echo "error: failed to checkout: merged: ${errcode}"

        return 5
    fi

    for entry in "${downstream_components[@]}"; do
        merge_names+=("${downstream_prefix}/${entry}")
    done

    git -C "${kernel_dir}" merge --quiet --no-ff --no-edit ${merge_names[@]}
    errcode=$?

    if [[ $errcode -ne 0 ]]; then
        echo "error: failed to merge: ${errcode}"

        return 6
    fi

    merge_base=$(_get_merge_base "${kernel_dir}")

    git -C "${kernel_dir}" format-patch --stdout "${merge_base}" > "${kernel_dir}/${downstream_prefix}-full.patch"
    errcode=$?

    if [[ $errcode -ne 0 ]]; then
        echo "error: failed to format patch: ${errcode}"

        return 7
    fi
}

manage_kernel "$@"
