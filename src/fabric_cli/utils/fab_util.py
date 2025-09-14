# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Fabric CLI General Utilities

This module contains general utility functions that don't depend on Fabric API layers.
These utilities are kept separate from item-specific functions to avoid circular imports
with the API and UI layers.

The module includes functions for:
- JSON serialization with custom handling
- Parameter parsing and manipulation
- Dictionary operations
- Path and string processing
- OS-specific operations
- Azure capacity configuration management
"""

import json
import platform
import re
from typing import Any

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages


# JSON utilities
def dumps(obj: Any, **kw) -> str:
    """JSON dumps with custom handling for bytes/bytearray objects.
    
    Args:
        obj: Object to serialize to JSON
        **kw: Additional keyword arguments passed to json.dumps
        
    Returns:
        JSON string representation of the object
        
    Raises:
        TypeError: If object contains non-serializable types other than bytes/bytearray
    """
    def _default(o):
        if isinstance(o, (bytes, bytearray)):
            return "__REDACTED__bytes__"
        raise TypeError(
            f"Object of type {o.__class__.__name__} is not JSON serializable"
        )

    return json.dumps(obj, default=_default, **kw)


# General utils
def process_nargs(arg: str | list[str]) -> str:
    if isinstance(arg, list):
        return " ".join(arg).strip("\"'")
    return arg


def remove_dot_suffix(path: str, dot_string_to_rm: str = ".Shortcut") -> str:
    return path.replace(dot_string_to_rm, "").replace(dot_string_to_rm.lower(), "")



def get_dict_from_params(params: str | list[str], max_depth: int = 2) -> dict:
    """
    Convert args to dict with a specified max nested level.
    Example:
    args.params = "key1.key2=value2,key1.key3=value3,key4=value4" -> {"key1": {"key2": "value2", "key3": "value3"}, "key4": "value4"}
    """

    params_dict: dict = {}
    # Split the params using a regular expression that matches a comma that is not inside a pair of quotes, brackets or braces
    # Example key1.key2=hello,key2={"hello":"testing","bye":2},key3=[1,2,3],key4={"key5":"value5"}
    # Result ['key1.key2=hello', 'key2={"hello":"testing","bye":2}', 'key3=[1,2,3]', 'key4={"key5":"value5"}']
    # Example key1.key2=hello
    # Result ['key1.key=hello']
    pattern = r"((?:[\w\.]+=.+?)(?=(?:,[\w\.]+=)|$))"

    if params:
        if isinstance(params, list):
            norm_params = " ".join(params)
        else:
            norm_params = params

        # Remove from multiline
        norm_params = norm_params.replace("\\", "").strip()

        matches = re.findall(pattern, norm_params)
        if not matches:
            raise FabricCLIError(
                ErrorMessages.Config.invalid_parameter_format(norm_params),
                fab_constant.ERROR_INVALID_INPUT,
            )

        params_dict = {}
        for param in matches:
            key, value = param.split("=", 1)
            params_dict = merge_dicts(
                params_dict, get_dict_from_parameter(key, value, max_depth)
            )

    return params_dict


def get_dict_from_parameter(
    param: str, value: str, max_depth: int = 2, current_depth: int = 1
) -> dict:
    """
    Convert args to dict with a specified max nested level.
    Example:
    param = key1.key2 and max_depth=2 -> {"key1": {"key2": value}}
    param = key1.key2 and max_depth=1 -> {"key1.key2": value}
    param = key1.key2.key3 and max_depth=2 -> {"key1": {"key2.key3": value}}
    """
    if max_depth != -1 and current_depth >= max_depth:
        return {param: value}

    if "." in param:
        key, rest = param.split(".", 1)
        return {key: get_dict_from_parameter(rest, value, max_depth, current_depth + 1)}
    else:
        clean_value = value.replace("'", "").replace('"', "")
        return {param: clean_value}


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Merge two dictionaries.
    """
    if not dict1:
        return dict2
    if not dict2:
        return dict1

    for key, value in dict2.items():
        if key in dict1 and isinstance(value, dict):
            dict1[key] = merge_dicts(dict1[key], value)
        else:
            dict1[key] = value

    return dict1


def remove_keys_from_dict(_dict: dict, keys: list) -> dict:
    for key in keys:
        if key in _dict.keys():
            del _dict[key]
    return _dict




def get_os_specific_command(command: str) -> str:
    if platform.system() == "Windows":
        return fab_constant.OS_COMMANDS.get(command, {}).get("windows", command)
    else:
        return fab_constant.OS_COMMANDS.get(command, {}).get("unix", command)


def replace_bypath_to_byconnection() -> bool:
    return True


def get_capacity_settings(
    params: dict = {},
) -> tuple:
    """Get Azure capacity settings from parameters and configuration.
    
    Args:
        params: Dictionary containing capacity parameters
        
    Returns:
        Tuple containing (admin, location, subscription_id, resource_group, sku)
        
    Raises:
        FabricCLIError: If required configuration values are missing
    """
    az_subscription_id = params.get(
        "subscriptionid",
        fab_state_config.get_config(fab_constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID),
    )
    az_resource_group = params.get(
        "resourcegroup",
        fab_state_config.get_config(fab_constant.FAB_DEFAULT_AZ_RESOURCE_GROUP),
    )
    az_default_location = params.get(
        "location", fab_state_config.get_config(fab_constant.FAB_DEFAULT_AZ_LOCATION)
    )
    az_default_admin = params.get(
        "admin", fab_state_config.get_config(fab_constant.FAB_DEFAULT_AZ_ADMIN)
    )
    sku = params.get("sku", "F2")

    if not az_subscription_id:
        raise FabricCLIError(
            ErrorMessages.Config.azure_subscription_id_not_set(),
            fab_constant.ERROR_INVALID_INPUT,
        )
    if not az_resource_group:
        raise FabricCLIError(
            ErrorMessages.Config.azure_resource_group_not_set(),
            fab_constant.ERROR_INVALID_INPUT,
        )
    if not az_default_location:
        raise FabricCLIError(
            ErrorMessages.Config.azure_location_not_set(),
            fab_constant.ERROR_INVALID_INPUT,
        )
    if not az_default_admin:
        raise FabricCLIError(
            ErrorMessages.Config.azure_admin_not_set(),
            fab_constant.ERROR_INVALID_INPUT,
        )

    return (
        az_default_admin,
        az_default_location,
        az_subscription_id,
        az_resource_group,
        sku,
    )


