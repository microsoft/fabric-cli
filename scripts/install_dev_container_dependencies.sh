#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

local_env="${repo_root}/.devcontainer/local.env"
if [ -f "$local_env" ]; then
    pip_index_url="$(sed -n 's/^PIP_INDEX_URL=//p' "$local_env" | tail -n 1)"
    if [ -n "$pip_index_url" ]; then
        export PIP_INDEX_URL="$pip_index_url"
    fi
fi

pip3 install -r "${repo_root}/requirements-dev.txt" -r "${repo_root}/requirements-docs.txt"