# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from os.path import exists, expanduser

from fabric_cli.core import fab_constant


def config_location():
    _location = expanduser("~/.config/fab/")
    if not exists(_location):
        os.makedirs(_location, mode=0o700)
    return _location


config_file = os.path.join(config_location(), "config.json")


def read_config(file_path) -> dict:
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def write_config(data):
    _write_restricted_file(config_file, json.dumps(data, indent=4))


def _write_restricted_file(file_path, content):
    """Write content to a file with owner-only permissions (0o600)."""
    fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as file:
            file.write(content)
    except BaseException:
        # fd is already closed by os.fdopen on success; only close on failure
        # before os.fdopen wraps it
        raise


def set_config(key, value):
    config = read_config(config_file)
    config[key] = value
    write_config(config)


def get_config(key):
    config = read_config(config_file)
    return config.get(key)


def list_configs():
    config = read_config(config_file)
    return {**config}


def init_defaults():
    """
    Ensures that all known config keys have default values if they are not already set.
    """
    current_config = read_config(config_file)
    changed = False

    # Migration: remove the deprecated 'mode' key (mode is now detected at runtime)
    if fab_constant.FAB_MODE in current_config:
        del current_config[fab_constant.FAB_MODE]
        changed = True

    for key in fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES:
        old_key = f"fab_{key}"
        if old_key in current_config:
            # Transfer value if not already set under the new key
            if key not in current_config:
                current_config[key] = current_config[old_key]
            del current_config[old_key]
            changed = True
        if key not in current_config and key in fab_constant.CONFIG_DEFAULT_VALUES:
            current_config[key] = fab_constant.CONFIG_DEFAULT_VALUES[key]
            changed = True

    if changed:
        write_config(current_config)
