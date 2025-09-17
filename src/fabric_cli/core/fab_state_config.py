# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from os.path import exists, expanduser

from fabric_cli.core import fab_constant


def config_location():
    _location = expanduser("~/.config/fab/")
    if not exists(_location):
        os.makedirs(_location)
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
    with open(config_file, "w") as file:
        json.dump(data, file, indent=4)


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

    for key in fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES:
        old_key = f"fab_{key}"
        if old_key in current_config:
            # Transfer value if not already set under the new key
            if key not in current_config:
                current_config[key] = current_config[old_key]
            del current_config[old_key]
        if key not in current_config and key in fab_constant.CONFIG_DEFAULT_VALUES:
            current_config[key] = fab_constant.CONFIG_DEFAULT_VALUES[key]

    write_config(current_config)
