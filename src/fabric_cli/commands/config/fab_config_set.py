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
    key = args.key.lower()
    value = args.value.strip().strip("'").strip('"')

    if key not in fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES:
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
                value, key, fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES[key]
            ),
            fab_constant.ERROR_INVALID_INPUT,
        )


def _can_key_contain_value(key: str, value: str) -> bool:
    if key in fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES:
        allowed_values = fab_constant.FAB_CONFIG_KEYS_TO_VALID_VALUES[key]
        if allowed_values == []:  # Empty list means it can accept any value
            return True
        return value in allowed_values
    return False


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
        utils_ui.print_output_format(
            args, message=f"Configuration '{key}' set to '{value}'"
        )
    current_mode = fab_state_config.get_config(fab_constant.FAB_MODE)

    # Clean up context files when changing mode
    if key == fab_constant.FAB_MODE:
        from fabric_cli.core.fab_context import Context

        Context().cleanup_context_files(cleanup_all_stale=True, cleanup_current=True)

    # Enhanced mode transition handling
    if key == fab_constant.FAB_MODE:
        if (current_mode == fab_constant.FAB_MODE_INTERACTIVE
            and previous_mode == fab_constant.FAB_MODE_COMMANDLINE):
            # Handle command_line → interactive transition
            if _is_user_authenticated():
                utils_ui.print("Switching to interactive mode...")
                _start_interactive_mode(args)
            else:
                utils_ui.print("Please login first to use interactive mode")
                
        elif (current_mode == fab_constant.FAB_MODE_COMMANDLINE
              and previous_mode == fab_constant.FAB_MODE_INTERACTIVE):
            # Handle interactive → command_line transition
            utils_ui.print("Exiting interactive mode. Goodbye!")
            os._exit(0)


def _is_user_authenticated() -> bool:
    """Check if user has valid authentication tokens"""
    try:
        from fabric_cli.core.fab_auth import FabAuth
        auth = FabAuth()
        # Try to get a token without interactive renewal
        token = auth.get_access_token(
            fab_constant.SCOPE_FABRIC_DEFAULT,
            interactive_renew=False
        )
        return token is not None
    except FabricCLIError as e:
        # Handle specific authentication errors
        if e.status_code in [
            fab_constant.ERROR_UNAUTHORIZED,
            fab_constant.ERROR_AUTHENTICATION_FAILED,
        ]:
            return False
        raise e
    except Exception:
        return False


def _start_interactive_mode(args: Namespace) -> None:
    """Launch interactive mode with current parser context"""
    try:
        # Import parser setup from main module
        from fabric_cli.main import _create_parser_and_subparsers
        
        parser, subparsers = _create_parser_and_subparsers()
        
        from fabric_cli.core.fab_interactive import InteractiveCLI
        interactive_cli = InteractiveCLI(parser, subparsers)
        interactive_cli.start_interactive()
        
    except (KeyboardInterrupt, EOFError):
        utils_ui.print("Interactive mode cancelled.")
    except Exception as e:
        utils_ui.print(f"Failed to start interactive mode: {str(e)}")
        utils_ui.print("Please restart the CLI to use interactive mode.")


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
