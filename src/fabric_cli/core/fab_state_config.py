# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from os.path import expanduser

from fabric_cli.core import fab_constant
from fabric_cli.utils.fab_secure_io import (
    create_restricted_dir,
    write_restricted_file,
)


def config_location():
    _location = expanduser("~/.config/fab/")
    create_restricted_dir(_location)
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
    write_restricted_file(config_file, json.dumps(data, indent=4))


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
