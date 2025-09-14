# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
from argparse import Namespace
from typing import Any

from fabric_cli.client import fab_api_capacity as capacity_api
from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils import fab_util as utils


def exec_command(args: Namespace) -> None:
    key = _normalize_key(args.key.lower())
    value = args.value.strip().strip("'").strip('"')

    if key not in fab_constant.CONFIG_KEYS:
        raise FabricCLIError(
            ErrorMessages.Config.unknown_configuration_key(key),
            fab_constant.ERROR_INVALID_INPUT,
        )

    if _can_key_contain_value(key, value):
        utils_ui.print_grey(f"Updating '{key}' value...")
        if key == fab_constant.FAB_DEFAULT_CAPACITY:
            _set_capacity(args, value)
        else:
            _set_config(args, key, value)
    else:
        raise FabricCLIError(
            ErrorMessages.Config.invalid_configuration_value(
                value, key, fab_constant.CONFIG_KEYS[key]
            ),
            fab_constant.ERROR_INVALID_INPUT,
        )


def _can_key_contain_value(key: str, value: str) -> bool:
    if key in fab_constant.CONFIG_KEYS:
        allowed_values = fab_constant.CONFIG_KEYS[key]
        if allowed_values == []:  # Empty list means it can accept any value
            return True
        return value in allowed_values
    return False


def _normalize_key(key: str) -> str:
    """
    Removes the 'fab_' prefix from the key if it exists.
    Otherwise returns the original key.
    """
    if key.startswith("fab_"):
        return key[4:]
    return key


def _set_config(args: Namespace, key: str, value: Any, verbose: bool = True) -> None:
    if key in (fab_constant.FAB_LOCAL_DEFINITION_LABELS,):
        if value is None:
            raise FabricCLIError(
                "The provided path for value is None, which is invalid",
                fab_constant.ERROR_INVALID_PATH,
            )

        if not os.path.exists(value):
            raise FabricCLIError(
                ErrorMessages.Common.file_or_directory_not_exists(),
                fab_constant.ERROR_INVALID_PATH,
            )

    previous_mode = fab_state_config.get_config(key)
    fab_state_config.set_config(key, value)
    if verbose:
        utils_ui.print_output_format(args, message=f"Configuration '{key}' set to '{value}'")
    current_mode = fab_state_config.get_config(fab_constant.FAB_MODE)

    # Clean up context files when changing mode
    if key == fab_constant.FAB_MODE:
        from fabric_cli.core.fab_context import Context

        Context().cleanup_context_files(cleanup_all_stale=True, cleanup_current=True)

    if (
        key == fab_constant.FAB_MODE
        and current_mode == fab_constant.FAB_MODE_COMMANDLINE
        and previous_mode == fab_constant.FAB_MODE_INTERACTIVE
    ):
        utils_ui.print("Exiting interactive mode. Goodbye!")
        os._exit(0)


def _set_capacity(args: Namespace, value: str) -> None:
    value = utils.remove_dot_suffix(value, ".Capacity")

    response = capacity_api.list_capacities(args)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        for item in data.get("value", []):
            if item.get("displayName", "").lower() == value.lower():
                _set_config(args, fab_constant.FAB_DEFAULT_CAPACITY, value)
                _set_config(
                    args, fab_constant.FAB_DEFAULT_CAPACITY_ID, item.get("id"), False
                )
                return
        raise FabricCLIError(
            ErrorMessages.Config.invalid_capacity(value),
            fab_constant.ERROR_INVALID_INPUT,
        )
